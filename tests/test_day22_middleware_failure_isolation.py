"""Day 22: middleware keeps API outcomes stable during telemetry failures."""

import asyncio
import copy
import sys
import unittest
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402
from sentinel_adapter import SentinelObservationAdapter, SentinelObservationMiddleware  # noqa: E402

POLICY = {"X-Policy-Version": "AP-1.0"}
USER_A = {"Authorization": "Bearer lab-user-a-token", **POLICY}
TENANT_ADMIN = {"Authorization": "Bearer lab-tenant-admin-token", **POLICY}


class SlowTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        await asyncio.sleep(0.05)
        return httpx.Response(200, request=request)


class Day22MiddlewareFailureIsolationTests(unittest.TestCase):
    def setUp(self):
        self.original_orders = copy.deepcopy(main.load_orders())
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def tearDown(self):
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def client(self, transport, timeout=0.01):
        adapter = SentinelObservationAdapter(
            "http://127.0.0.1:9000",
            chr(116) * 40,
            "mock_api",
            timeout=timeout,
            transport=transport,
        )
        app = FastAPI()
        app.include_router(main.app.router)
        app.add_middleware(SentinelObservationMiddleware, adapter=adapter)
        return TestClient(app)

    def test_authorized_patch_succeeds_when_telemetry_times_out(self):
        client = self.client(SlowTransport(), timeout=0.01)
        response = client.patch(
            "/orders/order-1001",
            headers={
                **TENANT_ADMIN,
                "X-Request-Nonce": "day22-timeout-authorized-0001",
            },
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")
        self.assertEqual(main.ORDERS["order-1001"]["status"], "shipped")

    def test_denied_customer_patch_stays_denied_when_telemetry_returns_503(self):
        def handler(request):
            return httpx.Response(503, text="unavailable", request=request)

        client = self.client(httpx.MockTransport(handler))
        before = copy.deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers={
                **USER_A,
                "X-Request-Nonce": "day22-503-denied-patch-0001",
            },
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_unauthenticated_request_stays_401_when_telemetry_times_out(self):
        client = self.client(SlowTransport(), timeout=0.01)
        response = client.get("/orders")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
