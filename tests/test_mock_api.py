
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

from main import app

client = TestClient(app)

USER_A = {"Authorization": "Bearer lab-user-a-token"}
USER_B = {"Authorization": "Bearer lab-user-b-token"}
ADMIN = {"Authorization": "Bearer lab-admin-token"}


class MockAPITests(unittest.TestCase):

    def test_customer_sees_only_own_orders(self):
        response = client.get("/orders", headers=USER_A)
        self.assertEqual(response.status_code, 200)
        ids = {order["id"] for order in response.json()["orders"]}
        self.assertEqual(ids, {"order-1001", "order-1003"})

    def test_owner_can_read_order(self):
        response = client.get(
            "/orders/order-1001", headers=USER_A
        )
        self.assertEqual(response.status_code, 200)

    def test_cross_user_order_is_denied(self):
        response = client.get(
            "/orders/order-1002", headers=USER_A
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"]["error"]["code"], "FORBIDDEN"
        )

    def test_missing_token_is_denied(self):
        response = client.get("/orders")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_is_denied(self):
        response = client.get(
            "/orders",
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_customer_cannot_list_admin_orders(self):
        response = client.get("/admin/orders", headers=USER_A)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_all_orders(self):
        response = client.get("/admin/orders", headers=ADMIN)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["orders"]), 3)

    def test_customer_cannot_update_order(self):
        response = client.patch(
            "/orders/order-1001",
            headers=USER_A,
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_update_order_status(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

    def test_update_rejects_extra_fields(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped", "owner_id": "user-b"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
