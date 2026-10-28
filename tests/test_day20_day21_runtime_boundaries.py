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
        with patch.object(
            self.app.state.store,
            "append",
            side_effect=StoreError("STORE_UNAVAILABLE"),
        ):
            response = self.client.post(
                "/v1/events", headers=self.headers, json=self.event
            )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(marker, response.text)
        self.assertNotIn("order-1001", response.text)
        self.assertNotIn(self.settings.ingest_token, response.text)
        self.assertEqual(self.app.state.store.snapshot(self.now), [])


if __name__ == "__main__":
    unittest.main()
