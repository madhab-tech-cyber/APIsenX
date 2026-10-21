"""Synthetic HTTP, retention, authentication, failure and privacy regressions."""

import asyncio
import copy
import json
import secrets
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from analytics.app import Settings, create_app


class AnalyticsServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32), "synthetic_source", secrets.token_bytes(32)
        )
        self.app = create_app(self.settings, clock=lambda: self.now)
        self.client = TestClient(self.app)
        self.headers = {
            "Authorization": "Bearer " + self.settings.ingest_token,
            "content-type": "application/json",
        }
        self.event = {
            "schema_name": "application_event",
            "schema_version": "1.0",
            "event_id": str(uuid4()),
            "source_id": "synthetic_source",
            "observed_at": self.now.isoformat(),
            "method": "GET",
            "request_target": "/orders/order-1001",
            "status_code": 200,
        }

    def post(self, event=None, **kwargs):
        return self.client.post(
            "/v1/events",
            headers=self.headers,
            json=self.event if event is None else event,
            **kwargs,
        )

    def batch(self, count=1):
        event = {
            "schema_name": "collector_event",
            "schema_version": "1.1",
            "event_id": str(uuid4()),
            "source_id": "synthetic_source",
            "observed_at": self.now.isoformat(),
            "sensor_sequence": 1,
            "sensor_monotonic_ns": 42,
            "correlation_id": None,
            "correlation_quality": "unsupported",
            "direction": "ingress",
            "method": "GET",
            "status_code": None,
            "route_template": None,
            "route_quality": "route_unavailable",
            "data_classification": "restricted",
        }
        return {
            "schema_name": "collector_batch",
            "schema_version": "1.0",
            "batch_id": str(uuid4()),
            "created_at": self.now.isoformat(),
            "events": [{**event, "event_id": str(uuid4())} for _ in range(count)],
        }

    def send_batch(self, batch):
        return self.client.post("/v1/batches", json=batch, headers=self.headers)

    def test_health_is_aggregate_and_sensitive_reads_are_not_available(self):
        self.assertEqual(
            self.client.get("/health").json(),
            {"status": "ok", "mode": "monitor_only", "storage": "volatile"},
        )
        for path in (
            "/v1/events",
            "/v1/batches",
            "/inventory",
            "/alerts",
            "/docs",
            "/openapi.json",
        ):
            self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(
                self.client.get(path, headers=self.headers).status_code, 404
            )

    def test_authentication_before_body_parsing_and_source_authorization(self):
        for token in (None, "wrong", "Basic synthetic"):
            headers = {} if token is None else {"authorization": token}
            result = self.client.post(
                "/v1/events", content=b"not-json", headers=headers
            )
            self.assertEqual(result.status_code, 401)
            self.assertNotIn("not-json", result.text)
        self.event["source_id"] = "other_source"
        self.assertEqual(self.post().status_code, 403)

    def test_duplicate_authorization_and_proxy_identity_spoofing_rejected(self):
        headers = [("authorization", self.headers["Authorization"])] * 2
        self.assertEqual(
            self.client.post(
                "/v1/events", json=self.event, headers=headers
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/v1/events",
                json=self.event,
                headers={
                    "X-Client-Cert": "trusted",
                    "X-Forwarded-User": "synthetic_source",
                },
            ).status_code,
            401,
        )

    def test_event_is_normalized_before_storage(self):
        self.event["request_target"] += "?token=SYNTHETIC_LEAK_MARKER"
        self.assertEqual(self.post().status_code, 200)
        rows = self.app.state.store.snapshot(self.now)
        self.assertEqual(rows[0]["route"], "/orders/{orderId}")
        encoded = repr(rows)
        for excluded in (
            "SYNTHETIC_LEAK_MARKER",
            "order-1001",
            "request_target",
            "token=",
        ):
            self.assertNotIn(excluded, encoded)
        self.assertEqual(rows[0]["expires_at"], self.now + timedelta(seconds=300))

    def test_schema_unknown_fields_versions_types_and_missing_fields(self):
        cases = [
            dict(self.event, schema_version="2.0"),
            dict(self.event, status_code="200"),
            dict(self.event, status_code=True),
            dict(self.event, event_id="not-uuid"),
            dict(self.event, method="GE T"),
            dict(self.event, actor_id="user-a"),
            dict(self.event, authorization="SYNTHETIC_LEAK_MARKER"),
            dict(self.event, nested={"cookie": "SYNTHETIC_LEAK_MARKER"}),
        ]
        missing = self.event.copy()
        del missing["event_id"]
        cases.append(missing)
        for value in cases:
            with self.subTest(fields=list(value)):
                result = self.post(value)
                self.assertEqual(result.status_code, 422)
                self.assertEqual(result.json(), {"detail": "SCHEMA_INVALID"})
        self.assertEqual(self.app.state.store.snapshot(self.now), [])

    def test_json_encoding_duplicate_fields_nonfinite_and_depth_rejection(self):
        for body in (
            b"{",
            b'"text"',
            b"[]",
            b"\xff",
            b'{"a":1,"a":2}',
            b'{"x":NaN}',
            b'{"x":Infinity}',
            b"[" * 1100 + b"]" * 1100,
        ):
            result = self.client.post("/v1/events", content=body, headers=self.headers)
            self.assertIn(result.status_code, (400, 422))
            self.assertNotIn("Traceback", result.text)

    def test_body_size_and_unsupported_media_encoding(self):
        for size, expected in ((4096, 400), (4097, 413)):
            result = self.client.post(
                "/v1/events", content=b" " * size, headers=self.headers
            )
            self.assertEqual(result.status_code, expected)
        for changed in ({"content-type": "text/plain"}, {"content-encoding": "gzip"}):
            self.assertEqual(
                self.client.post(
                    "/v1/events", json=self.event, headers={**self.headers, **changed}
                ).status_code,
                415,
            )

    def test_streaming_body_limit_without_content_length(self):
        result = self.client.post(
            "/v1/events", content=iter([b" " * 2000] * 3), headers=self.headers
        )
        self.assertEqual(result.status_code, 413)

    def test_replayed_event_is_idempotent_but_conflicting_id_is_rejected(self):
        self.assertEqual(self.post().status_code, 200)
        expiry = self.app.state.store.snapshot(self.now)[0]["expires_at"]
        self.now += timedelta(seconds=1)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(len(self.app.state.store.snapshot(self.now)), 1)
        self.assertEqual(
            self.app.state.store.snapshot(self.now)[0]["expires_at"], expiry
        )
        self.event["status_code"] = 403
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(self.app.state.store.snapshot(self.now)[0]["status_code"], 200)

    def test_query_only_change_does_not_change_dedup_key(self):
        self.assertEqual(self.post().status_code, 200)
        self.event["request_target"] += "?secret=SYNTHETIC_QUERY"
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(len(self.app.state.store.snapshot(self.now)), 1)

    def test_stale_future_naive_and_invalid_time_rejected(self):
        for stamp in (
            self.now - timedelta(seconds=3),
            self.now + timedelta(seconds=2),
            self.now.replace(tzinfo=None),
        ):
            self.event["observed_at"] = stamp.isoformat()
            self.assertEqual(self.post().status_code, 422)

    def test_capacity_retention_and_recovery(self):
        app = create_app(
            Settings(
                self.settings.ingest_token,
                self.settings.source_id,
                self.settings.hmac_key,
                capacity=1,
                retention_seconds=1,
            ),
            clock=lambda: self.now,
        )
        client = TestClient(app)
        self.assertEqual(
            client.post(
                "/v1/events", json=self.event, headers=self.headers
            ).status_code,
            200,
        )
        self.event["event_id"] = str(uuid4())
        self.assertEqual(
            client.post(
                "/v1/events", json=self.event, headers=self.headers
            ).status_code,
            503,
        )
        self.now += timedelta(seconds=1)
        self.event["observed_at"] = self.now.isoformat()
        self.assertEqual(
            client.post(
                "/v1/events", json=self.event, headers=self.headers
            ).status_code,
            200,
        )
        self.assertEqual(len(app.state.store.snapshot(self.now)), 1)

    def test_shadow_candidates_and_invalid_routes(self):
        for target in ("/synthetic/shadow-person", "/orders/order-1001"):
            self.event["event_id"] = str(uuid4())
            self.event["method"] = "DELETE"
            self.event["request_target"] = target
            self.assertEqual(self.post().status_code, 200)
        rows = self.app.state.store.snapshot(self.now)
        self.assertEqual(
            {row["classification"] for row in rows},
            {"path_not_documented", "method_not_documented"},
        )
        self.assertTrue(all(row["alert"]["mode"] == "monitor_only" for row in rows))
        self.event["request_target"] = "/orders/%2e%2e"
        self.assertEqual(self.post().status_code, 422)
        self.assertEqual(len(self.app.state.store.snapshot(self.now)), 2)

    def test_collector_batch_exact_ack_and_minimized_unavailable_context(self):
        batch = self.batch(2)
        response = self.send_batch(batch)
        expected = {
            "batch_id": batch["batch_id"],
            "accepted_event_ids": [event["event_id"] for event in batch["events"]],
        }
        self.assertEqual(response.json(), expected)
        self.assertEqual(self.send_batch(batch).json(), expected)
        rows = self.app.state.store.snapshot(self.now)
        self.assertEqual(len(rows), 2)
        self.assertTrue(
            all(row["classification"] == "visibility_unavailable" for row in rows)
        )
        self.assertTrue(all("alert" not in row for row in rows))

    def test_collector_approved_template_vs_unapproved_raw_route(self):
        batch = self.batch()
        event = batch["events"][0]
        event.update(
            route_template="/orders/{orderId}", route_quality="approved_template"
        )
        self.assertEqual(self.send_batch(batch).status_code, 200)
        for route in (
            "/orders/order-1001",
            "/unknown/SYNTHETIC_LEAK_MARKER",
            "/orders?secret=synthetic",
        ):
            event["route_template"] = route
            self.assertEqual(self.send_batch(batch).status_code, 422)

    def test_collector_route_quality_correlation_and_unknown_fields(self):
        for changes in (
            {"route_template": "/orders"},
            {"correlation_id": str(uuid4())},
            {"correlation_quality": "authoritative"},
            {"sensor_sequence": -1},
            {"sensor_monotonic_ns": 2**64},
            {"cookie": "synthetic"},
        ):
            batch = self.batch()
            batch["events"][0].update(changes)
            self.assertEqual(self.send_batch(batch).status_code, 422)

    def test_collector_batch_limits_and_duplicate_event_ids(self):
        self.assertEqual(self.send_batch(self.batch(64)).status_code, 200)
        self.assertEqual(self.send_batch(self.batch(65)).status_code, 422)
        self.assertEqual(self.send_batch(self.batch(0)).status_code, 422)
        batch = self.batch(2)
        batch["events"][1]["event_id"] = batch["events"][0]["event_id"]
        self.assertEqual(self.send_batch(batch).status_code, 422)
        self.assertEqual(
            self.client.post(
                "/v1/batches", content=b" " * 262145, headers=self.headers
            ).status_code,
            413,
        )

    def test_mixed_batch_atomic_rejection_and_recovery(self):
        batch = self.batch(2)
        batch["events"][1]["source_id"] = "unapproved"
        self.assertEqual(self.send_batch(batch).status_code, 403)
        self.assertEqual(self.app.state.store.snapshot(self.now), [])
        batch["events"][1]["source_id"] = "synthetic_source"
        self.assertEqual(self.send_batch(batch).status_code, 200)
        conflicting = copy.deepcopy(batch)
        conflicting["events"][0]["status_code"] = 403
        conflicting["events"][1]["event_id"] = str(uuid4())
        self.assertEqual(self.send_batch(conflicting).status_code, 409)
        self.assertEqual(len(self.app.state.store.snapshot(self.now)), 2)

    def test_privacy_logs_errors_and_store_RN_P05_P06(self):
        """RN-P05, RN-P06: no raw inputs or high-cardinality diagnostic labels."""
        with self.assertLogs("apisenx.analytics", level="INFO") as capture:
            for target in (
                "/orders/order-1001?token=SYNTHETIC_SECRET",
                "/unknown/SYNTHETIC_PERSON?token=SYNTHETIC_SECRET",
                "/orders/%ZZ",
            ):
                self.event.update(event_id=str(uuid4()), request_target=target)
                response = self.post()
                self.assertNotIn("SYNTHETIC_", response.text)
            self.post(dict(self.event, cookie="SYNTHETIC_COOKIE"))
            with patch.object(
                self.app.state.store,
                "append",
                side_effect=RuntimeError("SYNTHETIC_EXCEPTION"),
            ):
                self.event["request_target"] = "/orders"
                self.assertEqual(self.post().status_code, 503)
        outputs = repr(capture.output) + repr(self.app.state.store.snapshot(self.now))
        for marker in (
            "SYNTHETIC_SECRET",
            "SYNTHETIC_PERSON",
            "SYNTHETIC_COOKIE",
            "SYNTHETIC_EXCEPTION",
            self.settings.ingest_token,
        ):
            self.assertNotIn(marker, outputs)
        # No metrics exporter/high-cardinality labels: only fixed outcome codes in logs.
        self.assertTrue(all("ingestion outcome=" in line for line in capture.output))

    def test_configuration_has_no_default_secret_or_secret_repr(self):
        self.assertNotIn(self.settings.ingest_token, repr(self.settings))
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(ValueError):
            create_app()
        with self.assertRaises(ValueError):
            Settings("short", "source", b"short")

    def test_schema_exports_match_strict_wire_models(self):
        from analytics.schemas import schemas

        exported = schemas()
        self.assertEqual(len(exported), 5)
        for name in (
            "application_event.v1",
            "collector_event.v1.1",
            "collector_batch.v1",
            "analytics_alert.v1",
        ):
            self.assertFalse(exported[name]["additionalProperties"])
        for excluded in (
            "authorization",
            "cookies",
            "actor_id",
            "tenant_id",
            "owner_id",
        ):
            self.assertNotIn(excluded, exported["application_event.v1"]["properties"])

    def test_lifespan_sweeper_purges_without_reads_or_writes(self):
        import time

        with TestClient(self.app) as client:
            self.assertEqual(
                client.post(
                    "/v1/events", headers=self.headers, json=self.event
                ).status_code,
                200,
            )
            self.now += timedelta(seconds=301)
            deadline = time.monotonic() + 2
            while self.app.state.store._rows and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertFalse(self.app.state.store._rows)

    def test_body_timeout_and_concurrency_backpressure(self):
        async def run():
            release = asyncio.Event()
            entered = asyncio.Event()
            count = 0

            async def slow_body():
                nonlocal count
                count += 1
                if count == 4:
                    entered.set()
                await release.wait()
                yield json.dumps(self.event).encode()

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                base_url="http://testserver",
            ) as client:
                tasks = [
                    asyncio.create_task(
                        client.post(
                            "/v1/events", content=slow_body(), headers=self.headers
                        )
                    )
                    for _ in range(4)
                ]
                await asyncio.wait_for(entered.wait(), 0.5)
                busy = await client.post(
                    "/v1/events", json=self.event, headers=self.headers
                )
                self.assertEqual(busy.status_code, 503)
                release.set()
                self.assertTrue(
                    all(
                        response.status_code == 200
                        for response in await asyncio.gather(*tasks)
                    )
                )

                async def timeout_body():
                    await asyncio.Event().wait()
                    yield b"{}"

                timed = await client.post(
                    "/v1/events", content=timeout_body(), headers=self.headers
                )
                self.assertEqual(timed.status_code, 408)

        asyncio.run(run())
