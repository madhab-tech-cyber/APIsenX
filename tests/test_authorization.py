
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_json, load_orders, load_users  # noqa: E402


class AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users = load_users()
        cls.orders = load_orders()
        cls.cases = load_json("authorization_cases.json")["cases"]

    def setUp(self):
        # Isolate every test from accidental fixture mutation.
        self.users = {
            user_id: user.copy()
            for user_id, user in self.users.items()
        }
        self.orders = {
            order_id: order.copy()
            for order_id, order in self.orders.items()
        }

    def test_all_documented_cases(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                allowed, _ = authorize(
                    case["actor"],
                    case["action"],
                    case["order_id"],
                    self.users,
                    self.orders,
                )
                self.assertEqual(
                    allowed, case["expected"] == "allow"
                )

    def test_customer_reads_own_order(self):
        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "owner_read_allowed")

    def test_bola_is_denied(self):
        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1002",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_bfla_is_denied(self):
        allowed, reason = authorize(
            "user-a",
            "orders:manage",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "admin_role_required")

    def test_admin_can_read_and_manage_same_tenant_orders(self):
        for action in ("orders:read", "orders:manage"):
            with self.subTest(action=action):
                allowed, _ = authorize(
                    "admin-1",
                    action,
                    "order-1002",
                    self.users,
                    self.orders,
                )
                self.assertTrue(allowed)

    def test_unknown_user_is_denied(self):
        allowed, reason = authorize(
            "unknown-user",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "unknown_user")

    def test_missing_order_is_denied(self):
        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-9999",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "order_not_found")

    def test_inactive_user_is_denied(self):
        self.users["user-disabled"] = {
            "id": "user-disabled",
            "role": "customer",
            "active": False,
            "tenant_id": "lab-tenant",
        }

        allowed, reason = authorize(
            "user-disabled",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "inactive_user")

    def test_admin_manage_requires_explicit_role_permission(self):
        users = {
            "admin-1": {
                "id": "admin-1",
                "role": "admin",
                "active": True,
                "tenant_id": "lab-tenant",
            }
        }
        policy = {"roles": {"admin": ["orders:read:any"]}}

        with patch("authorization.load_json", return_value=policy):
            allowed, reason = authorize(
                "admin-1",
                "orders:manage",
                "order-1001",
                users,
                self.orders,
            )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "missing_orders_manage_permission"
        )

    def test_admin_read_requires_explicit_role_permission(self):
        users = {
            "admin-1": {
                "id": "admin-1",
                "role": "admin",
                "active": True,
                "tenant_id": "lab-tenant",
            }
        }
        policy = {"roles": {"admin": ["orders:manage:any"]}}

        with patch("authorization.load_json", return_value=policy):
            allowed, reason = authorize(
                "admin-1",
                "orders:read",
                "order-1001",
                users,
                self.orders,
            )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "missing_orders_read_any_permission"
        )

    def test_unknown_action_is_denied(self):
        allowed, reason = authorize(
            "admin-1",
            "users:delete",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "unknown_action")

    def test_unknown_role_is_denied(self):
        self.users["user-strange"] = {
            "id": "user-strange",
            "role": "superuser",
            "active": True,
            "tenant_id": "lab-tenant",
        }

        allowed, _ = authorize(
            "user-strange",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )
        self.assertFalse(allowed)

    # Tenant-isolation regression tests

    def test_same_tenant_owner_can_read_order(self):
        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertTrue(allowed)
        self.assertEqual(reason, "owner_read_allowed")

    def test_cross_tenant_access_is_denied_before_ownership(self):
        # Even if the actor owns the order, a tenant mismatch must deny.
        self.orders["order-1001"]["tenant_id"] = "other-tenant"

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "tenant_mismatch")

    def test_admin_cannot_read_cross_tenant_order(self):
        self.orders["order-1001"]["tenant_id"] = "other-tenant"

        allowed, reason = authorize(
            "admin-1",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "tenant_mismatch")

    def test_admin_cannot_manage_cross_tenant_order(self):
        self.orders["order-1001"]["tenant_id"] = "other-tenant"

        allowed, reason = authorize(
            "admin-1",
            "orders:manage",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "tenant_mismatch")

    def test_missing_actor_tenant_is_denied(self):
        self.users["user-a"].pop("tenant_id")

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )

    def test_missing_order_tenant_is_denied(self):
        self.orders["order-1001"].pop("tenant_id")

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )

    def test_blank_actor_tenant_is_denied(self):
        self.users["user-a"]["tenant_id"] = "   "

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )

    def test_non_string_actor_tenant_is_denied(self):
        self.users["user-a"]["tenant_id"] = 123

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )

    def test_blank_order_tenant_is_denied(self):
        self.orders["order-1001"]["tenant_id"] = ""

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )

    def test_non_string_order_tenant_is_denied(self):
        self.orders["order-1001"]["tenant_id"] = None

        allowed, reason = authorize(
            "user-a",
            "orders:read",
            "order-1001",
            self.users,
            self.orders,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            reason, "tenant_context_missing_or_invalid"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
