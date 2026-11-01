"""Synthetic wire-to-protected-read compatibility, not live sensor/UI acceptance."""

import secrets
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.management import ReaderGrant


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.reader = ReaderGrant(
            "synthetic-reader",
            secrets.token_urlsafe(32),
            "handoff-case",
            "analyst",
            self.now + timedelta(hours=1),
        )
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "handoff-lab",
            secrets.token_bytes(32),
            case_id="handoff-case",
            readers=(self.reader,),
        )
        self.app = create_app(self.settings, lambda: self.now)
        self.client = TestClient(self.app)
        self.ingest = {"Authorization": "Bearer " + self.settings.ingest_token}
        self.read = {"Authorization": "Bearer " + self.reader.token}

    def batch(self):
        event = {
            "schema_name": "collector_event",
            "schema_version": "1.1",
            "event_id": str(uuid4()),
            "correlation_id": None,
            "correlation_quality": "unsupported",
            "source_id": "handoff-lab",
            "sensor_sequence": 1,
            "sensor_monotonic_ns": 1,
            "observed_at": self.now.isoformat(),
            "direction": "ingress",
            "method": "GET",
            "status_code": 200,
            "route_template": "/orders",
            "route_quality": "approved_template",
            "data_classification": "restricted",
        }
        return {
            "schema_name": "collector_batch",
            "schema_version": "1.0",
            "batch_id": str(uuid4()),
            "created_at": self.now.isoformat(),
            "events": [event],
        }

    def inventory(self):
        response = self.client.get("/v1/inventory", headers=self.read)
        self.assertEqual(response.status_code, 200)
        return response

    def test_exact_ack_retry_and_protected_inventory_without_raw_wire_fields(self):
        batch = self.batch()
        expected = {
            "batch_id": batch["batch_id"],
            "accepted_event_ids": [batch["events"][0]["event_id"]],
        }
        for _ in range(2):
            response = self.client.post("/v1/batches", headers=self.ingest, json=batch)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected)
        inventory = self.inventory()
        self.assertEqual(inventory.json()["items"][0]["observation_count"], 1)
        for marker in (
            batch["batch_id"],
            batch["events"][0]["event_id"],
            "source_id",
            "sensor_sequence",
            self.reader.token,
        ):
            self.assertNotIn(marker, inventory.text)
        self.assertEqual(
            self.client.get("/v1/inventory", headers=self.ingest).status_code, 401
        )
        self.assertEqual(inventory.headers["cache-control"], "no-store")

    def test_missing_route_is_unavailable_not_documented_or_healthy(self):
        batch = self.batch()
        batch["events"][0].update(
            method="UNKNOWN",
            route_template=None,
            route_quality="route_unavailable",
            correlation_quality="ambiguous",
        )
        self.assertEqual(
            self.client.post(
                "/v1/batches", headers=self.ingest, json=batch
            ).status_code,
            200,
        )
        result = self.inventory().json()
        self.assertEqual(result["items"][0]["classification"], "visibility_unavailable")
        self.assertIsNone(result["items"][0]["route"])
        self.assertEqual(result["visibility"], "partial_lab_visibility")
        self.assertEqual(
            self.client.get("/v1/alerts", headers=self.read).json()["items"], []
        )

    def test_invalid_batch_has_no_partial_visible_write_or_raw_path_echo(self):
        batch = self.batch()
        bad = deepcopy(batch["events"][0])
        bad.update(event_id=str(uuid4()), route_template="/private/SYNTHETIC_SECRET")
        batch["events"].append(bad)
        result = self.client.post("/v1/batches", headers=self.ingest, json=batch)
        self.assertEqual(result.status_code, 422)
        self.assertNotIn("SYNTHETIC_SECRET", result.text)
        self.assertEqual(self.inventory().json()["items"], [])

    def test_conflict_and_stale_retry_cannot_inflate_visible_counts(self):
        batch = self.batch()
        self.assertEqual(
            self.client.post(
                "/v1/batches", headers=self.ingest, json=batch
            ).status_code,
            200,
        )
        changed = deepcopy(batch)
        changed["events"][0]["status_code"] = 403
        self.assertEqual(
            self.client.post(
                "/v1/batches", headers=self.ingest, json=changed
            ).status_code,
            409,
        )
        self.now += timedelta(seconds=3)
        self.assertEqual(
            self.client.post(
                "/v1/batches", headers=self.ingest, json=batch
            ).status_code,
            422,
        )
        self.assertEqual(self.inventory().json()["items"][0]["observation_count"], 1)
