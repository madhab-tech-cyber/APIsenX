"""Day 22: API authority remains independent of optional Sentinel telemetry."""

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


class Day22APIAuthorityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.original_orders = copy.deepcopy(main.load_orders())
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()
        self.events = []

    def tearDown(self):
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def make_client(self, response_status=200, fail=False):
        def handler(request):
            self.events.append(httpx.Request(
                request.method,
                request.url,
                headers=request.headers,
                content=request.content,
            ))
            if fail:
                raise httpx.ConnectError("SYNTHETIC_SENTINEL_OUTAGE", request=request)
            return httpx.Response(response_status, json={"accepted_event_ids": []})

        adapter = SentinelObservationAdapter(
            "http://127.0.0.1:9000",
            "synthetic-sentinel-ingest-token-0123456789",
            "mock_api",
            timeout=0.2,
            transport=httpx.MockTransport(handler),
        )
        test_app = FastAPI()
        test_app.include_router(main.app.router)
        test_app.add_middleware(SentinelObservationMiddleware, adapter=adapter)
        return TestClient(test_app)

    def event_payload(self):
        self.assertEqual(len(self.events), 1)
        import json
        return json.loads(self.events[0].content)

    def test_sentinel_outage_does_not_change_authorized_patch_or_state(self):
        client = self.make_client(fail=True)

        response = client.patch(
            "/orders/order-1001",
            headers={
                **TENANT_ADMIN,
                "X-Request-Nonce": "day22-sentinel-outage-patch-0001",
            },
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")
        self.assertEqual(main.ORDERS["order-1001"]["status"], "shipped")
        event = self.event_payload()
        self.assertEqual(event["method"], "PATCH")
        self.assertEqual(event["request_target"], "/orders/{orderId}")
        self.assertEqual(event["status_code"], 200)

    def test_sentinel_acceptance_cannot_override_denied_customer_patch(self):
        client = self.make_client(response_status=200)
        before = copy.deepcopy(main.ORDERS["order-1001"])

        response = client.patch(
            "/orders/order-1001",
            headers={
                **USER_A,
                "X-Request-Nonce": "day22-sentinel-accepted-denial-0001",
            },
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)
        event = self.event_payload()
        self.assertEqual(event["request_target"], "/orders/{orderId}")
        self.assertEqual(event["status_code"], 403)

    def test_telemetry_uses_route_template_and_excludes_query_and_object_values(self):
        client = self.make_client(response_status=200)

        response = client.get(
            "/orders/order-1001?token=SYNTHETIC_QUERY_SECRET",
            headers=TENANT_ADMIN,
        )

        self.assertEqual(response.status_code, 200)
        event = self.event_payload()
        self.assertEqual(event["request_target"], "/orders/{orderId}")
        rendered = repr(event)
        self.assertNotIn("order-1001", rendered)
        self.assertNotIn("SYNTHETIC_QUERY_SECRET", rendered)
        self.assertNotIn("authorization", event)
        self.assertNotIn("body", event)


if __name__ == "__main__":
    unittest.main(verbosity=2)
