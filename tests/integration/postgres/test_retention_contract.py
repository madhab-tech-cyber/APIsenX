"""Policy arithmetic for Day 20 retention classes; not runtime DB evidence."""

import unittest
from datetime import datetime, timedelta, timezone


RETENTION = {
    "RT-03": timedelta(days=7),
    "RT-04": timedelta(days=30),
    "RT-05": timedelta(days=90),
    "RT-06": timedelta(hours=24),
    "RT-07": timedelta(days=7),
}


class RetentionBoundaryContractTests(unittest.TestCase):
    def setUp(self):
        self.received_at = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)

    def test_policy_windows_match_audit_retention_policy(self):
        self.assertEqual(RETENTION["RT-03"], timedelta(days=7))
        self.assertEqual(RETENTION["RT-04"], timedelta(days=30))
        self.assertEqual(RETENTION["RT-05"], timedelta(days=90))
        self.assertEqual(RETENTION["RT-06"], timedelta(hours=24))
        self.assertEqual(RETENTION["RT-07"], timedelta(days=7))

    def test_expiry_is_derived_from_trusted_receipt_time(self):
        for policy_id, duration in RETENTION.items():
            with self.subTest(policy_id=policy_id):
                expires_at = self.received_at + duration
                self.assertEqual(expires_at - self.received_at, duration)
                self.assertGreater(expires_at, self.received_at)

    def test_naive_receipt_time_is_not_a_valid_utc_receipt_timestamp(self):
        naive = datetime(2026, 11, 7, 12, 0)
        self.assertIsNone(naive.tzinfo)
        self.assertIsNotNone(self.received_at.tzinfo)
