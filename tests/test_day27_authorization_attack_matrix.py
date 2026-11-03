"""Day 27 HTTP-level authorization regressions for the synthetic Mock API."""

import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402

client = TestClient(main.app)
POLICY = {"X-Policy-Version": "AP-1.0"}
USER_A = {"Authorization": "Bearer lab-user-a-token", **POLICY}


class Day27AuthorizationAttackMatrixTests(unittest.TestCase):
    """Keep allowed owner/share cases and denied BOLA/BFLA cases deterministic."""

    def setUp(self):
        self.previous_orders = deepcopy(main.ORDERS)
        self.previous_nonces = dict(main.USED_NONCES)
        main.USED_NONCES.clear()
        main.ORDERS.clear()
        main.ORDERS.update(main.load_orders())

    def tearDown(self):
        main.USED_NONCES.clear()
        main.USED_NONCES.update(self.previous_nonces)
        main.ORDERS.clear()
        main.ORDERS.update(self.previous_orders)

    @staticmethod
    def order_read_grant(resource_type="order"):
        now = datetime.now(timezone.utc)
        return {
            "grant_id": "day27-grant-0001",
            "resource_type": resource_type,
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

    def test_owner_read_remains_allowed(self):
        response = client.get("/orders/order-1001", headers=USER_A)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "order-1001")

    def test_cross_owner_read_remains_generic_bola_denial(self):
        response = client.get("/orders/order-1002", headers=USER_A)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertNotIn("order-1002", response.text)
        self.assertNotIn("user-b", response.text)

    def test_customer_admin_inventory_attempt_remains_denied(self):
        response = client.get("/admin/orders", headers=USER_A)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_customer_patch_remains_denied_without_mutation(self):
        before = deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers={
                **USER_A,
                "X-Request-Nonce": "day27-customer-0001",
            },
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_non_order_grant_cannot_authorize_order_read(self):
        grant = self.order_read_grant(resource_type="customer")
        with patch("authorization.load_sharing_grants", return_value=[grant]):
            response = client.get("/orders/order-1002", headers=USER_A)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertNotIn("order-1002", response.text)

    def test_valid_order_read_grant_still_allows_same_tenant_read(self):
        grant = self.order_read_grant()
        with patch("authorization.load_sharing_grants", return_value=[grant]):
            response = client.get("/orders/order-1002", headers=USER_A)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "order-1002")


if __name__ == "__main__":
    unittest.main(verbosity=2)
