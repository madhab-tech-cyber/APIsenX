"""Deterministic runtime checks for Day 21 route-failure boundaries.

These tests cover authoritative AP-1.0 policy rejection and the RF-05
unknown-route diagnostic boundary. They do not claim optional-overlay,
durable-audit, or integrated sensor/collector failure acceptance.
"""

import logging

import secrets
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from analytics.app import Settings, create_app
from analytics.detection import Observation

import sys
import unittest
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402

POLICY = {"X-Policy-Version": "AP-1.0"}
USER_A = {"Authorization": "Bearer lab-user-a-token", **POLICY}
ADMIN = {"Authorization": "Bearer lab-admin-token", **POLICY}


class Day21RouteFailureMatrixTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.original_orders = main.load_orders()
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def tearDown(self):
        main.USED_NONCES.clear()
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))

    def test_missing_and_unknown_policy_fail_closed_on_rf01_to_rf04(self):
        cases = (
            ("RF-01", "GET", "/orders", USER_A, None),
            ("RF-02", "GET", "/orders/order-1001", USER_A, None),
            ("RF-03", "PATCH", "/orders/order-1001", ADMIN, {"status": "shipped"}),
            ("RF-04", "GET", "/admin/orders", ADMIN, None),
        )

        for route_id, method, path, base_headers, payload in cases:
            for version_label, policy_version in (
                ("missing", None),
                ("unknown", "AP-9.9"),
            ):
                with self.subTest(route=route_id, policy=version_label):
                    headers = dict(base_headers)
                    headers.pop("X-Policy-Version", None)
                    if policy_version is not None:
                        headers["X-Policy-Version"] = policy_version
                    if method == "PATCH":
                        headers["X-Request-Nonce"] = (
                            f"day21-policy-{route_id.lower()}-{version_label}-0001"
                        )

                    before = deepcopy(main.ORDERS)
                    request = {"headers": headers}
                    if payload is not None:
                        request["json"] = payload
                    response = self.client.request(method, path, **request)

                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(
                        response.json()["error"]["code"], "INVALID_REQUEST"
                    )
                    self.assertNotIn("orders", response.json())
                    self.assertEqual(main.ORDERS, before)

    def test_patch_policy_recovery_accepts_same_nonce_after_context_is_restored(self):
        nonce = "day21-policy-recovery-0001"
        before = deepcopy(main.ORDERS["order-1001"])
        invalid = self.client.patch(
            "/orders/order-1001",
            headers={
                "Authorization": "Bearer lab-admin-token",
                "X-Policy-Version": "AP-9.9",
                "X-Request-Nonce": nonce,
            },
            json={"status": "shipped"},
        )

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(main.ORDERS["order-1001"], before)

        recovered = self.client.patch(
            "/orders/order-1001",
            headers={
                "Authorization": "Bearer lab-admin-token",
                "X-Policy-Version": "AP-1.0",
                "X-Request-Nonce": nonce,
            },
            json={"status": "shipped"},
        )

        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.json()["status"], "shipped")
        self.assertEqual(main.ORDERS["order-1001"]["status"], "shipped")

    def test_rf05_unknown_path_and_method_do_not_log_raw_path_or_query(self):
        path_marker = "SYNTHETIC_UNKNOWN_PATH_MARKER"
        query_marker = "SYNTHETIC_QUERY_VALUE_MARKER"
        before = deepcopy(main.ORDERS)

        # httpx's INFO request logger includes the full URL, so suppress it
        # while checking the application logger's privacy-safe diagnostics.
        httpx_logger = logging.getLogger("httpx")
        previous_httpx_level = httpx_logger.level
        httpx_logger.setLevel(logging.WARNING)
        try:
            with self.assertLogs("apisenx.audit", level="INFO") as captured:
                unknown = self.client.get(
                    f"/unmapped/{path_marker}?secret={query_marker}",
                    headers=USER_A,
                )
                wrong_method = self.client.delete("/orders", headers=USER_A)
        finally:
            httpx_logger.setLevel(previous_httpx_level)

        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(wrong_method.status_code, 405)
        combined = unknown.text + wrong_method.text + "\n".join(captured.output)
        self.assertNotIn(path_marker, combined)
        self.assertNotIn(query_marker, combined)
        self.assertIn("route=unmatched", combined)
        self.assertEqual(main.ORDERS, before)


if __name__ == "__main__":
    unittest.main()



class Day21AnalyticsFailureBoundaryTests(unittest.TestCase):
    """Optional analytics recommendation failures never create trusted replies."""

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic_source",
            secrets.token_bytes(32),
            decision_token=secrets.token_urlsafe(32),
            decision_key=secrets.token_bytes(32),
        )
        self.headers = {
            "authorization": "Bearer " + self.settings.decision_token,
            "content-type": "application/json",
        }

    def payload(self):
        return {
            "event_id": str(uuid4()),
            "nonce": str(uuid4()),
            "requested_at": self.now.isoformat(),
        }

    def observation_for(self, event_id, method="GET", target="/orders", actor="admin-1"):
        resource = "order-1001" if target.endswith("order-1001") else None
        return Observation(
            event_id, self.now, method, target, actor, resource, 200
        )

    def test_audit_append_failure_returns_bounded_error_without_signature(self):
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda event_id: self.observation_for(event_id),
        )
        with patch.object(
            app.state.decisions.audit,
            "append",
            side_effect=RuntimeError("SYNTHETIC_AUDIT_FAILURE"),
        ):
            response = TestClient(app).post(
                "/v1/recommendations", json=self.payload(), headers=self.headers
            )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SYNTHETIC_AUDIT_FAILURE", response.text)
        self.assertNotIn("signature", response.text)

    def test_unavailable_resolver_returns_bounded_error_without_signature(self):
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda _event_id: (_ for _ in ()).throw(
                RuntimeError("SYNTHETIC_CONTEXT_FAILURE")
            ),
        )
        response = TestClient(app).post(
            "/v1/recommendations", json=self.payload(), headers=self.headers
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "CONTEXT_UNAVAILABLE"})
        self.assertNotIn("SYNTHETIC_CONTEXT_FAILURE", response.text)
        self.assertNotIn("signature", response.text)

    def test_stale_policy_returns_bounded_error_without_signature(self):
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda event_id: self.observation_for(event_id),
        )
        app.state.decisions.policy_expires_at = self.now
        response = TestClient(app).post(
            "/v1/recommendations", json=self.payload(), headers=self.headers
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "POLICY_STALE"})
        self.assertNotIn("signature", response.text)

    def test_replayed_nonce_is_rejected_without_second_audit_record(self):
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda event_id: self.observation_for(event_id, actor="admin-1"),
        )
        client = TestClient(app)
        payload = self.payload()
        first = client.post(
            "/v1/recommendations", json=payload, headers=self.headers
        )
        self.assertEqual(first.status_code, 200)
        count_after_first = len(
            app.state.decisions.audit.store.snapshot(self.now)
        )
        replay = client.post(
            "/v1/recommendations", json=payload, headers=self.headers
        )
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(
            len(app.state.decisions.audit.store.snapshot(self.now)),
            count_after_first,
        )



# Preserved from the conflicted PR branch under a distinct class name.
ROUTE_CASES = (
    ("RF-01", "GET", "/orders", "admin-1", None),
    ("RF-02", "GET", "/orders/order-1001", "admin-1", "order-1001"),
    ("RF-03", "PATCH", "/orders/order-1001", "admin-1", "order-1001"),
    ("RF-04", "GET", "/admin/orders", "admin-1", None),
)


class Day21OptionalSentinelFailureMatrixTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic_source",
            secrets.token_bytes(32),
            decision_token=secrets.token_urlsafe(32),
            decision_key=secrets.token_bytes(32),
        )
        self.headers = {
            "authorization": "Bearer " + self.settings.decision_token,
            "content-type": "application/json",
        }

    def request_payload(self):
        return {
            "event_id": str(uuid4()),
            "nonce": str(uuid4()),
            "requested_at": self.now.isoformat(),
        }

    def make_observation(self, method, target, actor, resource):
        return Observation(
            uuid4(),
            self.now,
            method,
            target,
            actor,
            resource,
            200,
        )

    def test_optional_overlay_audit_failure_is_bounded_for_each_route_class(self):
        for route_id, method, target, actor, resource in ROUTE_CASES:
            with self.subTest(route_id=route_id):
                observation = self.make_observation(
                    method, target, actor, resource
                )
                app = create_app(
                    self.settings,
                    clock=lambda: self.now,
                    resolver=lambda event_id, item=observation: Observation(
                        event_id, item.observed_at, item.method, item.request_target,
                        item.actor_id, item.object_id, item.status_code,
                    ),
                )
                with patch.object(
                    app.state.decisions.audit.store,
                    "append",
                    side_effect=RuntimeError("SYNTHETIC_AUDIT_FAILURE"),
                ):
                    response = TestClient(app).post(
                        "/v1/recommendations",
                        json=self.request_payload(),
                        headers=self.headers,
                    )

                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {"detail": "INGESTION_UNAVAILABLE"})
                self.assertNotIn("SYNTHETIC_AUDIT_FAILURE", response.text)
                self.assertNotIn("signature", response.text)
                self.assertEqual(app.state.decisions.audit.store.snapshot(self.now), [])

    def test_unavailable_resolver_never_creates_a_signed_recommendation(self):
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda _event_id: (_ for _ in ()).throw(
                RuntimeError("SYNTHETIC_CONTEXT_FAILURE")
            ),
        )
        response = TestClient(app).post(
            "/v1/recommendations",
            json=self.request_payload(),
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "CONTEXT_UNAVAILABLE"})
        self.assertNotIn("SYNTHETIC_CONTEXT_FAILURE", response.text)
        self.assertNotIn("signature", response.text)

    def test_stale_policy_never_creates_a_signed_recommendation(self):
        observation = self.make_observation(
            "GET", "/orders", "admin-1", None
        )
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda event_id: Observation(
                event_id, observation.observed_at, observation.method,
                observation.request_target, observation.actor_id, observation.object_id,
                observation.status_code,
            ),
        )
        app.state.decisions.policy_expires_at = self.now
        response = TestClient(app).post(
            "/v1/recommendations",
            json=self.request_payload(),
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "POLICY_STALE"})
        self.assertNotIn("signature", response.text)


    def test_unknown_route_never_gets_a_signed_recommendation(self):
        observation = self.make_observation(
            "GET", "/unregistered-route", "user-a", None
        )
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda _event_id: observation,
        )
        response = TestClient(app).post(
            "/v1/recommendations",
            json=self.request_payload(),
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "CONTEXT_UNAVAILABLE"})
        self.assertNotIn("signature", response.text)

    def test_replayed_nonce_is_rejected_without_second_audit_record(self):
        observation = self.make_observation(
            "GET", "/orders", "user-a", None
        )
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda _event_id: observation,
        )
        client = TestClient(app)
        payload = self.request_payload()
        first = client.post(
            "/v1/recommendations", json=payload, headers=self.headers
        )
        self.assertEqual(first.status_code, 200)
        count_after_first = len(
            app.state.decisions.audit.store.snapshot(self.now)
        )
        replay = client.post(
            "/v1/recommendations", json=payload, headers=self.headers
        )
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(
            len(app.state.decisions.audit.store.snapshot(self.now)),
            count_after_first,
        )




if __name__ == "__main__":
    unittest.main(verbosity=2)
