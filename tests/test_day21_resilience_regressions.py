"""Day 21 resilience regressions for bounded storage and API isolation.

These tests intentionally do not claim a production API-to-Sentinel adapter:
the mock API and analytics service are separate processes today.
"""

import secrets
import unittest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.store import MemoryStore, StoreError

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402


class Day21StoreResilienceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.key = secrets.token_bytes(32)
        self.summary = {
            "method": "GET",
            "route": "/orders",
            "classification": "documented",
            "reason_code": "DOCUMENTED_OPERATION",
            "contract_version": "sha256:" + ("a" * 64),
            "status_code": 200,
        }

    def item(self, event_id):
        store = MemoryStore(self.key, capacity=1, routes=["/orders"])
        digest = store.digest(self.summary)
        return store, (
            "synthetic_source",
            event_id,
            digest,
            self.summary,
        )

    def test_full_store_rejects_new_record_without_partial_append(self):
        store = MemoryStore(self.key, capacity=1, routes=["/orders"])
        first_id, second_id = uuid4(), uuid4()
        first = (
            "synthetic_source",
            first_id,
            store.digest(self.summary),
            self.summary,
        )
        second = (
            "synthetic_source",
            second_id,
            store.digest({**self.summary, "status_code": 201}),
            {**self.summary, "status_code": 201},
        )

        store.append([first], self.now)
        with self.assertRaises(StoreError) as failure:
            store.append([second], self.now)

        self.assertEqual(failure.exception.reason, "STORE_CAPACITY")
        rows = store.snapshot(self.now)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_id"], str(first_id))

    def test_capacity_failure_is_atomic_for_multi_record_batch(self):
        store = MemoryStore(self.key, capacity=1, routes=["/orders"])
        first_id, second_id = uuid4(), uuid4()
        items = [
            (
                "synthetic_source",
                first_id,
                store.digest(self.summary),
                self.summary,
            ),
            (
                "synthetic_source",
                second_id,
                store.digest(self.summary),
                self.summary,
            ),
        ]

        with self.assertRaises(StoreError) as failure:
            store.append(items, self.now)

        self.assertEqual(failure.exception.reason, "STORE_CAPACITY")
        self.assertEqual(store.snapshot(self.now), [])

    def test_restart_creates_empty_volatile_store_and_does_not_claim_durability(self):
        first = MemoryStore(self.key, capacity=2, routes=["/orders"])
        event_id = uuid4()
        item = (
            "synthetic_source",
            event_id,
            first.digest(self.summary),
            self.summary,
        )
        first.append([item], self.now)
        self.assertEqual(len(first.snapshot(self.now)), 1)

        restarted = MemoryStore(self.key, capacity=2, routes=["/orders"])
        self.assertEqual(restarted.snapshot(self.now), [])


class Day21APIAuthorityIsolationTests(unittest.TestCase):
    """API authorization remains authoritative when analytics is unavailable."""

    def setUp(self):
        self.client = TestClient(main.app)
        self.original_orders = main.load_orders()
        main.ORDERS.clear()
        main.ORDERS.update(self.original_orders)

    def tearDown(self):
        main.ORDERS.clear()
        main.ORDERS.update(self.original_orders)

    def test_unauthorized_api_request_stays_denied_independent_of_sentinel(self):
        # No Sentinel client/adapter is wired into mock-api/main.py. A synthetic
        # analytics outage therefore cannot grant access or bypass API auth.
        response = self.client.get(
            "/orders/order-1001",
            headers={
                "Authorization": "Bearer lab-user-b-token",
                "X-Policy-Version": "AP-1.0",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_missing_api_credentials_stay_denied_without_analytics_dependency(self):
        response = self.client.get(
            "/orders",
            headers={"X-Policy-Version": "AP-1.0"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
