"""DurableStore parity and restart-recovery tests (issue #83 candidate).

These tests prove the SQLite store keeps MemoryStore's contract — masking
gate, dedup, conflict atomicity, capacity and retention — while surviving a
process restart. They do not claim Day 20 durable-audit acceptance, which
still requires the design review tracked in issue #83.
"""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analytics.durable_store import DurableStore
from analytics.store import StoreError

CONTRACT = "sha256:" + "a" * 64
KEY = b"k" * 32


def summary(route="/orders"):
    return {
        "method": "GET",
        "route": route,
        "classification": "documented",
        "reason_code": "DOCUMENTED_OPERATION",
        "contract_version": CONTRACT,
        "status_code": 200,
    }


class DurableStoreTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "store.db"
        self.store = DurableStore(
            KEY, self.db_path, capacity=3, retention_seconds=60, routes={"/orders"}
        )

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def append(self, event_id, item=None, digest=None, store=None, now=None):
        target = store or self.store
        target.append(
            [("source-a", event_id, digest or ("d" * 64), item or summary())],
            now or self.now,
        )

    def test_in_memory_database_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filesystem database path"):
            DurableStore(KEY, ":memory:")

    def test_naive_clock_is_rejected_without_persisting(self):
        naive_now = datetime(2026, 10, 29, 12, 0)
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.append("naive-event", now=naive_now)
        self.assertEqual(self.store.snapshot(self.now), [])

    def test_offset_clock_is_normalized_to_utc_for_retention(self):
        offset_now = datetime(
            2026, 10, 29, 14, 0, tzinfo=timezone(timedelta(hours=2))
        )
        self.append("offset-event", now=offset_now)
        rows = self.store.snapshot(self.now)
        self.assertEqual(rows[0]["received_at"], self.now)
        self.assertEqual(rows[0]["expires_at"], self.now + timedelta(seconds=60))
        self.assertEqual(
            len(self.store.snapshot(self.now + timedelta(seconds=59))), 1
        )
        self.assertEqual(
            self.store.snapshot(self.now + timedelta(seconds=60)), []
        )

    def test_append_and_snapshot_roundtrip(self):
        self.append("event-1")
        rows = self.store.snapshot(self.now)
        self.assertEqual([row["event_id"] for row in rows], ["event-1"])
        self.assertEqual(rows[0]["route"], "/orders")
        self.assertEqual(rows[0]["received_at"], self.now)

    def test_rows_survive_restart(self):
        self.append("event-1")
        self.append("event-2")
        self.store.close()
        reopened = DurableStore(
            KEY, self.db_path, capacity=3, retention_seconds=60, routes={"/orders"}
        )
        try:
            rows = reopened.snapshot(self.now)
            self.assertEqual(
                [row["event_id"] for row in rows], ["event-1", "event-2"]
            )
        finally:
            reopened.close()
            self.store = DurableStore(
                KEY, self.db_path, capacity=3, retention_seconds=60, routes={"/orders"}
            )

    def test_conflicting_duplicate_rejects_entire_batch(self):
        self.append("existing", digest="a" * 64)
        with self.assertRaisesRegex(StoreError, "EVENT_ID_CONFLICT"):
            self.store.append(
                [
                    ("source-a", "new-before-conflict", "b" * 64, summary()),
                    ("source-a", "existing", "c" * 64, summary()),
                ],
                self.now,
            )
        self.assertEqual(
            [r["event_id"] for r in self.store.snapshot(self.now)], ["existing"]
        )

    def test_identical_duplicate_is_idempotent(self):
        self.append("same", digest="a" * 64)
        self.append("same", digest="a" * 64, now=self.now + timedelta(seconds=1))
        self.assertEqual(len(self.store.snapshot(self.now)), 1)

    def test_capacity_rejected(self):
        self.append("event-1")
        self.append("event-2")
        self.append("event-3")
        with self.assertRaisesRegex(StoreError, "STORE_CAPACITY"):
            self.append("event-4")

    def test_expired_entries_purged_before_capacity_check(self):
        self.append("event-1")
        self.append("event-2")
        self.append("event-3")
        self.append("event-4", now=self.now + timedelta(seconds=60))
        rows = self.store.snapshot(self.now + timedelta(seconds=60))
        self.assertEqual([row["event_id"] for row in rows], ["event-4"])

    def test_masking_rejection_leaves_no_partial_write(self):
        bad = {**summary(), "route": "/not-an-approved-route"}
        with self.assertRaisesRegex(StoreError, "MASKING_REJECTED"):
            self.store.append([("source-a", "event-x", "d" * 64, bad)], self.now)
        self.assertEqual(self.store.snapshot(self.now), [])


if __name__ == "__main__":
    unittest.main()
