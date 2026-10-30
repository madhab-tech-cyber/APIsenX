"""Day 10 regression coverage for server-resolved read-only sharing grants."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_orders, load_users  # noqa: E402


class SharingGrantAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users = load_users()
        cls.orders = load_orders()

    def make_grant(self, **overrides):
        now = datetime.now(timezone.utc)
        grant = {
            "grant_id": "grant-test-001",
            "resource_type": "order",
            "issuer": "user-b",
            "policy_version": "AP-1.0",
            "tenant_id": "lab-tenant",
            "resource_id": "order-1002",
            "grantee_subject": "user-a",
            "actions": ["orders:read"],
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            "revoked": False,
        }
        grant.update(overrides)
        return grant

    def authorize_with_grant(\n        self, grant, policy_version="AP-1.0", action="orders:read"\n    ):
        with patch(
            "authorization.load_sharing_grants",
            return_value=[grant],
        ):
            return authorize(
                "user-a",
                "orders:read",
                "order-1002",
                self.users,
                self.orders,
                policy_version=policy_version,
            )

    def test_active_same_tenant_read_grant_allows_shared_order(self):
        allowed, reason = self.authorize_with_grant(self.make_grant())

        self.assertTrue(allowed)
        self.assertEqual(reason, "shared_read_allowed")

    def test_expired_grant_is_denied(self):
        expired = datetime.now(timezone.utc) - timedelta(minutes=1)
        allowed, reason = self.authorize_with_grant(
            self.make_grant(expires_at=expired.isoformat())
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_revoked_grant_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(revoked=True)
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_not_yet_valid_grant_is_denied(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=1)
        allowed, reason = self.authorize_with_grant(
            self.make_grant(starts_at=future.isoformat())
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_manage_action_cannot_be_granted_to_customer(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(actions=["orders:read", "orders:manage"])
        )

        # Customer management is denied before a sharing grant is considered.
        self.assertFalse(allowed)
        self.assertEqual(reason, "admin_role_required")

    def test_wrong_tenant_grant_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(tenant_id="other-tenant")
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_wrong_resource_grant_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(resource_id="order-1003")
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_wrong_grantee_grant_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(grantee_subject="user-b")
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_wrong_policy_version_grant_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(policy_version="AP-0.9")
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_unsupported_request_policy_version_is_denied(self):
        allowed, reason = self.authorize_with_grant(
            self.make_grant(),
            policy_version="AP-2.0",
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "policy_version_unsupported")

    def test_malformed_grant_is_ignored(self):
        malformed = self.make_grant(expires_at="not-a-timestamp")
        allowed, reason = self.authorize_with_grant(malformed)

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_naive_expiry_timestamp_is_denied(self):
        naive = (datetime.now(timezone.utc) + timedelta(minutes=5))
        allowed, reason = self.authorize_with_grant(
            self.make_grant(expires_at=naive.replace(tzinfo=None).isoformat())
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
