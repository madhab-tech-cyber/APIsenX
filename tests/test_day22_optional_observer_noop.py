"""Day 22: optional Sentinel middleware is a transparent no-op when disabled."""

import copy
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402
from sentinel_adapter import SentinelObservationMiddleware  # noqa: E402


class Day22OptionalObserverNoopTests(unittest.TestCase):
    def setUp(self):
        self.original_orders = copy.deepcopy(main.load_orders())
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def tearDown(self):
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def make_client(self):
        app = FastAPI()
        app.include_router(main.app.router)
        app.add_middleware(SentinelObservationMiddleware, adapter=None)
        return TestClient(app)

    def test_disabled_observer_preserves_authenticated_api_response(self):
        client = self.make_client()
        response = client.get(
            "/orders",
            headers={
                "Authorization": "Bearer lab-tenant-admin-token",
                "X-Policy-Version": "AP-1.0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("orders", response.json())

    def test_disabled_observer_does_not_bypass_authentication(self):
        client = self.make_client()
        response = client.get("/orders")
        self.assertEqual(response.status_code, 401)

    def test_disabled_observer_does_not_change_patch_authorization_or_state(self):
        client = self.make_client()
        before = copy.deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers={
                "Authorization": "Bearer lab-user-a-token",
                "X-Policy-Version": "AP-1.0",
                "X-Request-Nonce": "day22-observer-disabled-0001",
            },
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
