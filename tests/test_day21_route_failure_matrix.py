"""Day 21: deterministic optional-Sentinel failure matrix.

These tests exercise the analytics recommendation boundary for the five
protected API route classes. They do not claim an integrated API enforcement
adapter or durable audit implementation; the authoritative API remains the
authorization boundary.
"""

import secrets
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.detection import Observation


ROUTE_CASES = (
    ("RF-01", "GET", "/orders", "user-a", None),
    ("RF-02", "GET", "/orders/order-1001", "user-a", "order-1001"),
    ("RF-03", "PATCH", "/orders/order-1001", "user-a", "order-1001"),
    ("RF-04", "GET", "/admin/orders", "admin-1", None),
)


class Day21RouteFailureMatrixTests(unittest.TestCase):
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
                        event_id, item.observed_at, item.method, item.target,
                        item.actor, item.resource, item.status_code,
                    ),
                )
                with patch.object(
                    app.state.decisions.audit,
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
            "GET", "/orders", "user-a", None
        )
        app = create_app(
            self.settings,
            clock=lambda: self.now,
            resolver=lambda event_id: Observation(
                event_id, observation.observed_at, observation.method,
                observation.target, observation.actor, observation.resource,
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
