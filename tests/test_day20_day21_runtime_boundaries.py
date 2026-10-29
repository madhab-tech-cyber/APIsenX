"""Day 20–21 runtime-boundary regressions for masking and safe failures."""

import logging
import secrets
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.store import StoreError


class Day20Day21RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic_source",
            secrets.token_bytes(32),
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
            "request_target": "/orders/order-1001?token=SYNTHETIC_LEAK_MARKER",
            "status_code": 200,
        }

    def batch(self, count=2):
        events = [
            {
                "schema_name": "collector_event",
                "schema_version": "1.1",
                "event_id": str(uuid4()),
                "source_id": "synthetic_source",
                "observed_at": self.now.isoformat(),
                "sensor_sequence": sequence,
                "sensor_monotonic_ns": 42 + sequence,
                "correlation_id": None,
                "correlation_quality": "unsupported",
                "direction": "ingress",
                "method": "GET",
                "status_code": None,
                "route_template": None,
                "route_quality": "route_unavailable",
                "data_classification": "restricted",
            }
            for sequence in range(count)
        ]
        return {
            "schema_name": "collector_batch",
            "schema_version": "1.0",
            "batch_id": str(uuid4()),
            "created_at": self.now.isoformat(),
            "events": events,
        }

    def test_rejected_unknown_secret_field_is_not_echoed_or_logged(self):
        marker = "SYNTHETIC_LEAK_MARKER"
        payload = {**self.event, "authorization": marker}

        with self.assertLogs("apisenx.analytics", level=logging.INFO) as captured:
            response = self.client.post(
                "/v1/events", headers=self.headers, json=payload
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "SCHEMA_INVALID"})
        combined = response.text + "\n" + "\n".join(captured.output)
        self.assertNotIn(marker, combined)
        self.assertNotIn("order-1001", combined)
        self.assertNotIn(self.settings.ingest_token, combined)
        self.assertEqual(self.app.state.store.snapshot(self.now), [])

    def test_successful_query_marker_is_absent_from_store_and_application_logs(self):
        marker = "SYNTHETIC_LEAK_MARKER"
        with self.assertLogs("apisenx.analytics", level=logging.INFO) as captured:
            response = self.client.post(
                "/v1/events", headers=self.headers, json=self.event
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["accepted_event_ids"]), 1)
        rows = self.app.state.store.snapshot(self.now)
        self.assertEqual(len(rows), 1)
        combined = repr(rows) + "\n" + "\n".join(captured.output)
        self.assertNotIn(marker, combined)
        self.assertNotIn("order-1001", combined)
        self.assertNotIn("request_target", combined)
        self.assertNotIn(self.settings.ingest_token, combined)

    def test_storage_failure_response_does_not_expose_secret_or_path(self):
        marker = "SYNTHETIC_LEAK_MARKER"
        internal_detail = "SYNTHETIC_INTERNAL_STORE_DETAIL"
        with self.assertLogs("apisenx.analytics", level=logging.INFO) as captured:
            with patch.object(
                self.app.state.store,
                "append",
                side_effect=StoreError(internal_detail),
            ):
                response = self.client.post(
                    "/v1/events", headers=self.headers, json=self.event
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "STORE_UNAVAILABLE"})
        combined = response.text + "\n" + "\n".join(captured.output)
        for excluded in (
            marker,
            internal_detail,
            "order-1001",
            self.settings.ingest_token,
        ):
            self.assertNotIn(excluded, combined)
        self.assertEqual(self.app.state.store.snapshot(self.now), [])

    def test_batch_storage_failure_is_atomic_and_recovers_without_detail_leak(self):
        batch = self.batch()
        internal_detail = "SYNTHETIC_INTERNAL_BATCH_DETAIL"
        with self.assertLogs("apisenx.analytics", level=logging.INFO) as captured:
            with patch.object(
                self.app.state.store,
                "append",
                side_effect=StoreError(internal_detail),
            ):
                failed = self.client.post(
                    "/v1/batches", headers=self.headers, json=batch
                )

        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.json(), {"detail": "STORE_UNAVAILABLE"})
        self.assertNotIn(
            internal_detail,
            failed.text + "\n" + "\n".join(captured.output),
        )
        self.assertEqual(self.app.state.store.snapshot(self.now), [])

        recovered = self.client.post(
            "/v1/batches", headers=self.headers, json=batch
        )
        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.json()["batch_id"], batch["batch_id"])
        self.assertEqual(
            recovered.json()["accepted_event_ids"],
            [event["event_id"] for event in batch["events"]],
        )
        rows = self.app.state.store.snapshot(self.now)
        self.assertEqual(len(rows), 2)
        self.assertTrue(
            all(row["classification"] == "visibility_unavailable" for row in rows)
        )


if __name__ == "__main__":
    unittest.main()
