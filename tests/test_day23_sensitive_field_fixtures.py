"""Day 23: synthetic sensitive-field values stay out of API and telemetry output."""

import copy
import json
import sys
import unittest
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402
from sentinel_adapter import SentinelObservationAdapter, SentinelObservationMiddleware  # noqa: E402

POLICY = {"X-Policy-Version": "AP-1.0"}
TENANT_ADMIN = {
    "Authorization": "Bearer lab-tenant-admin-token",
    **POLICY,
}
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "day23_sensitive_fields.json"


class Day23SensitiveFieldFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)

    def setUp(self):
        self.original_orders = copy.deepcopy(main.load_orders())
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def tearDown(self):
        main.ORDERS.clear()
        main.ORDERS.update(copy.deepcopy(self.original_orders))
        main.USED_NONCES.clear()

    def test_fixture_uses_only_non_operational_synthetic_values(self):
        self.assertEqual(
            self.fixture["classification"],
            "synthetic-test-only",
        )
        records = {item["field"]: item["value"] for item in self.fixture["records"]}
        self.assertEqual(
            set(records),
            {"email", "phone", "card_number", "api_key"},
        )
        self.assertTrue(records["email"].endswith(".invalid"))
        self.assertIn("555-01", records["phone"])
        self.assertEqual(records["card_number"], "0000-0000-0000-0000")
        self.assertEqual(
            records["api_key"],
            "TEST_ONLY_NOT_A_CREDENTIAL_DAY23",
        )

    def test_sensitive_fields_are_rejected_without_mutation_or_echo(self):
        client = TestClient(main.app)
        before = copy.deepcopy(main.ORDERS["order-1001"])

        for record in self.fixture["records"]:
            with self.subTest(field=record["field"]):
                response = client.patch(
                    "/orders/order-1001",
                    headers={
                        **TENANT_ADMIN,
                        "X-Request-Nonce": (
                            f"day23-sensitive-{record['field']}-0001"
                        ),
                    },
                    json={
                        "status": "shipped",
                        record["field"]: record["value"],
                    },
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(main.ORDERS["order-1001"], before)
                self.assertNotIn(record["value"], response.text)

    def test_sensitive_markers_are_not_forwarded_to_sentinel(self):
        events = []

        def handler(request):
            events.append(json.loads(request.content))
            return httpx.Response(200, request=request)

        adapter = SentinelObservationAdapter(
            "http://127.0.0.1:9000",
            "synthetic-sentinel-ingest-token-0123456789",
            "mock_api",
            transport=httpx.MockTransport(handler),
        )
        app = FastAPI()
        app.include_router(main.app.router)
        app.add_exception_handler(
            RequestValidationError,
            main.app.exception_handlers[RequestValidationError],
        )
        app.add_middleware(SentinelObservationMiddleware, adapter=adapter)
        client = TestClient(app)

        payload = {"status": "shipped"}
        for record in self.fixture["records"]:
            payload[record["field"]] = record["value"]

        before = copy.deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers={
                **TENANT_ADMIN,
                "X-Request-Nonce": "day23-sensitive-observer-0001",
            },
            json=payload,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(main.ORDERS["order-1001"], before)
        self.assertEqual(len(events), 1)
        rendered_event = json.dumps(events[0], sort_keys=True)
        for record in self.fixture["records"]:
            self.assertNotIn(record["value"], response.text)
            self.assertNotIn(record["value"], rendered_event)
        self.assertEqual(events[0]["request_target"], "/orders/{orderId}")
        self.assertEqual(events[0]["status_code"], 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
