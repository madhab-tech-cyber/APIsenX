
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_json, load_orders, load_users


class AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users = load_users()
        cls.orders = load_orders()
        cls.cases = load_json("authorization_cases.json")["cases"]

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
            "user-a", "orders:read", "order-1001",
            self.users, self.orders
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "owner_read_allowed")

    def test_bola_is_denied(self):
        allowed, reason = authorize(
            "user-a", "orders:read", "order-1002",
            self.users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "order_ownership_required")

    def test_bfla_is_denied(self):
        allowed, reason = authorize(
            "user-a", "orders:manage", "order-1001",
            self.users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "admin_role_required")

    def test_admin_can_read_and_manage(self):
        for action in ("orders:read", "orders:manage"):
            with self.subTest(action=action):
                allowed, _ = authorize(
                    "admin-1", action, "order-1002",
                    self.users, self.orders
                )
                self.assertTrue(allowed)

    def test_unknown_user_is_denied(self):
        allowed, reason = authorize(
            "unknown-user", "orders:read", "order-1001",
            self.users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "unknown_user")

    def test_missing_order_is_denied(self):
        allowed, reason = authorize(
            "user-a", "orders:read", "order-9999",
            self.users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "order_not_found")

    def test_inactive_user_is_denied(self):
        users = dict(self.users)
        users["user-disabled"] = {
            "id": "user-disabled",
            "role": "customer",
            "active": False,
        }
        allowed, reason = authorize(
            "user-disabled", "orders:read", "order-1001",
            users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "inactive_user")

    def test_unknown_action_is_denied(self):
        allowed, reason = authorize(
            "admin-1", "users:delete", "order-1001",
            self.users, self.orders
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "unknown_action")

    def test_unknown_role_is_denied(self):
        users = dict(self.users)
        users["user-strange"] = {
            "id": "user-strange",
            "role": "superuser",
            "active": True,
        }
        allowed, _ = authorize(
            "user-strange", "orders:read", "order-1001",
            users, self.orders
        )
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
