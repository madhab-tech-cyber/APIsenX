"""Regression tests for the current bounded volatile store.

These tests intentionally do not claim durable audit storage or Day 20 acceptance.
"""

import unittest
from datetime import datetime, timedelta, timezone

from analytics.store import MemoryStore, StoreError


CONTRACT = "sha256:" + "a" * 64


def summary(route="/orders"):
    return {
        "schema_name": "normalized_summary",
        "schema_version": "1.0",
        "method": "GET",
        "route": route,
        "classification": "documented",
        "reason_code": "DOCUMENTED_OPERATION",
        "contract_version": CONTRACT,
        "status_code": 200,
    }


class VolatileStoreRegressionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)
        self.store = MemoryStore(b"k" * 32, capacity=3, retention_seconds=60, routes={"/orders"})

    def append(self, event_id, item=None, digest=None, store=None, now=None):
        target = store or self.store
        target.append(
            [("source-a", event_id, digest or ("d" * 64), item or summary())],
            now or self.now,
        )

    def test_expired_entries_are_purged_before_capacity_check(self):
        self.append("event-1")
        self.append("event-2")
        self.append("event-3")
        self.append("event-4", now=self.now + timedelta(seconds=60))
        rows = self.store.snapshot(self.now + timedelta(seconds=60))
        self.assertEqual([row["event_id"] for row in rows], ["event-4"])

    def test_conflicting_duplicate_rejects_entire_batch_without_partial_append(self):
        self.append("existing", digest="a" * 64)
        with self.assertRaisesRegex(StoreError, "EVENT_ID_CONFLICT"):
            self.store.append(
                [
                    ("source-a", "new-before-conflict", "b" * 64, summary()),
                    ("source-a", "existing", "c" * 64, summary()),
                ],
                self.now,
            )
        self.assertEqual([r["event_id"] for r in self.store.snapshot(self.now)], ["existing"])

    def test_identical_duplicate_is_idempotent(self):
        self.append("same", digest="a" * 64)
        self.append("same", digest="a" * 64, now=self.now + timedelta(seconds=1))
        rows = self.store.snapshot(self.now + timedelta(seconds=1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["received_at"], self.now)

    def test_snapshot_is_deep_copied_and_cannot_mutate_store(self):
        self.append("stable")
        first = self.store.snapshot(self.now)
        first[0]["route"] = "/attacker-controlled"
        second = self.store.snapshot(self.now)
        self.assertEqual(second[0]["route"], "/orders")

    def test_unknown_route_is_rejected_without_persisting_any_row(self):
        with self.assertRaisesRegex(StoreError, "MASKING_REJECTED"):
            self.append("bad-route", item=summary("/unapproved"))
        self.assertEqual(self.store.snapshot(self.now), [])

    def test_capacity_rejection_does_not_partially_append(self):
        self.append("one")
        self.append("two")
        self.append("three")
        with self.assertRaisesRegex(StoreError, "STORE_CAPACITY"):
            self.append("four")
        self.assertEqual(len(self.store.snapshot(self.now)), 3)


if __name__ == "__main__":
    unittest.main()
