"""Day 21 tests for bounded, privacy-minimized monitor-only API telemetry."""

import asyncio
import copy
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402
from sentinel_adapter import (  # noqa: E402
    SentinelObservationAdapter,
    SentinelObservationMiddleware,
)


class SentinelObservationAdapterTests(unittest.TestCase):
    def make_adapter(self, handler, timeout=0.2):
        transport = httpx.MockTransport(handler)
        return SentinelObservationAdapter(
            "http://127.0.0.1:9000",
            "synthetic-sentinel-ingest-token-0123456789",
            "mock_api",
            timeout=timeout,
            transport=transport,
        )

    def test_successful_delivery_contains_only_route_template_metadata(self):
        captured = {}

        def handler(request):
            captured["headers"] = dict(request.headers)
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"accepted_event_ids": []})

        adapter = self.make_adapter(handler)
        delivered = asyncio.run(
            adapter.publish("GET", "/orders/{orderId}", 200)
        )

        self.assertTrue(delivered)
        body = captured["body"]
        self.assertEqual(body["request_target"], "/orders/apisenx-redacted")
        self.assertEqual(body["method"], "GET")
        self.assertEqual(body["status_code"], 200)
        self.assertEqual(body["source_id"], "mock_api")
        self.assertNotIn("authorization", body)
        self.assertNotIn("query", body)
        self.assertNotIn("body", body)
        self.assertTrue(
            captured["headers"]["authorization"].startswith("Bearer ")
        )

    def test_unavailable_sentinel_fails_open_with_bounded_false_result(self):
        def handler(_request):
            raise httpx.ConnectError("SYNTHETIC_PRIVATE_FAILURE")

        adapter = self.make_adapter(handler)
        delivered = asyncio.run(
            adapter.publish("PATCH", "/orders/{orderId}", 503)
        )
        self.assertFalse(delivered)

    def test_slow_sentinel_times_out_within_configured_bound(self):
        async def handler(_request):
            await asyncio.sleep(0.5)
            return httpx.Response(200)

        adapter = self.make_adapter(handler, timeout=0.05)
        delivered = asyncio.run(
            adapter.publish("GET", "/orders", 200)
        )
        self.assertFalse(delivered)

    def test_invalid_route_or_status_is_not_published(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200)

        adapter = self.make_adapter(handler)
        self.assertFalse(asyncio.run(adapter.publish("GET", None, 200)))
        self.assertFalse(asyncio.run(adapter.publish("GET", "/orders", 99)))
        self.assertEqual(calls, [])

    def test_asgi_middleware_recovers_only_allowlisted_route_template(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200)

        adapter = self.make_adapter(handler)
        async def app(scope, receive, send):
            scope["route"] = None
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = SentinelObservationMiddleware(app, adapter)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/orders/order-1001",
            "headers": [],
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(_message):
            return None

        asyncio.run(middleware(scope, receive, send))
        self.assertEqual(captured["body"]["request_target"], "/orders/apisenx-redacted")
        self.assertNotIn("order-1001", json.dumps(captured["body"]))
        self.assertEqual(captured["body"]["status_code"], 404)

    def test_configuration_requires_loopback_endpoint_and_strong_token(self):
        with self.assertRaises(ValueError):
            SentinelObservationAdapter(
                "https://external.example",
                "synthetic-sentinel-ingest-token-0123456789",
                "mock_api",
            )
        with self.assertRaises(ValueError):
            SentinelObservationAdapter(
                "http://127.0.0.1:9000",
                "short",
                "mock_api",
            )



    def test_supplied_application_correlation_id_is_used_as_event_id(self):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"accepted_event_ids": []})

        adapter = self.make_adapter(handler)
        correlation_id = "6c3a6f9e-2f3b-4a6d-9f1d-8a8f2b8e4c01"
        delivered = asyncio.run(
            adapter.publish("GET", "/orders", 200, event_id=correlation_id)
        )

        self.assertTrue(delivered)
        self.assertEqual(captured["body"]["event_id"], correlation_id)

    def test_invalid_supplied_event_id_is_not_published(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200)

        adapter = self.make_adapter(handler)
        delivered = asyncio.run(
            adapter.publish("GET", "/orders", 200, event_id="not-a-uuid")
        )
        self.assertFalse(delivered)
        self.assertEqual(calls, [])

    def test_analytics_503_preserves_api_response_and_log_correlation(self):
        captured = {}
        failure_marker = "SYNTHETIC_ANALYTICS_STORAGE_FAILURE"

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(503, json={"detail": failure_marker})

        adapter = self.make_adapter(handler)
        before = copy.deepcopy(main.ORDERS)
        headers = {
            "Authorization": "Bearer lab-user-a-token",
            "X-Policy-Version": "AP-1.0",
        }

        with patch.object(main, "SENTINEL_ADAPTER", adapter):
            with self.assertLogs("apisenx.audit", level="INFO") as logged:
                response = TestClient(main.app).get("/orders", headers=headers)

        correlation_id = response.headers["X-Correlation-ID"]
        diagnostics = "\\n".join(logged.output)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(captured["body"]["event_id"], correlation_id)
        self.assertIn(correlation_id, diagnostics)
        self.assertEqual(captured["body"]["method"], "GET")
        self.assertEqual(captured["body"]["request_target"], "/orders")
        self.assertEqual(captured["body"]["status_code"], 200)
        self.assertNotIn(failure_marker, response.text + diagnostics)
        self.assertEqual(main.ORDERS, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
