"""Day 21 tests for bounded, privacy-minimized monitor-only API telemetry."""

import asyncio
import json
import unittest

import httpx

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
