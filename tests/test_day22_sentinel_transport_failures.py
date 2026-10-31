"""Day 22: Sentinel transport failures remain bounded and non-authoritative."""

import asyncio
import logging
import sys
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mock-api"))

from sentinel_adapter import SentinelObservationAdapter  # noqa: E402

TOKEN = chr(116) * 40
ENDPOINT = "http://127.0.0.1:9000"


class DelayedTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        await asyncio.sleep(0.05)
        return httpx.Response(200, json={"accepted": True}, request=request)


class Day22SentinelTransportFailureTests(unittest.IsolatedAsyncioTestCase):
    def adapter(self, transport, timeout=0.01):
        return SentinelObservationAdapter(
            ENDPOINT, TOKEN, "mock_api", timeout=timeout, transport=transport
        )

    async def test_timeout_is_bounded_and_logs_no_exception_data(self):
        adapter = self.adapter(DelayedTransport(), timeout=0.01)
        with self.assertLogs("apisenx.sentinel", level="INFO") as captured:
            result = await adapter.publish("GET", "/orders/{orderId}", 200)
        self.assertFalse(result)
        rendered = "\\n".join(captured.output)
        self.assertIn("sentinel_delivery outcome=unavailable", rendered)
        self.assertNotIn(TOKEN, rendered)
        self.assertNotIn(ENDPOINT, rendered)
        self.assertNotIn("Timeout", rendered)

    async def test_non_200_is_not_accepted_or_logged(self):
        response_marker = "SYNTHETIC_SENTINEL_RESPONSE_MARKER"
        def handler(request):
            return httpx.Response(503, text=response_marker, request=request)
        adapter = self.adapter(httpx.MockTransport(handler))
        with self.assertNoLogs("apisenx.sentinel", level="INFO"):
            result = await adapter.publish("PATCH", "/orders/{orderId}", 200)
        self.assertFalse(result)

    async def test_client_error_status_is_not_accepted(self):
        def handler(request):
            return httpx.Response(429, json={"error": "limited"}, request=request)
        adapter = self.adapter(httpx.MockTransport(handler))
        self.assertFalse(await adapter.publish("GET", "/orders", 429))

    async def test_exact_200_status_is_accepted(self):
        def handler(request):
            return httpx.Response(200, json={"accepted_event_ids": []}, request=request)
        adapter = self.adapter(httpx.MockTransport(handler))
        self.assertTrue(await adapter.publish("GET", "/orders", 200))

    async def test_redirect_is_not_followed_or_accepted(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(
                302,
                headers={"Location": "http://127.0.0.1:9001/redirect-target"},
                request=request,
            )

        adapter = self.adapter(httpx.MockTransport(handler))
        self.assertFalse(await adapter.publish("GET", "/orders", 200))
        self.assertEqual(len(requests), 1)

    async def test_event_body_is_allowlisted_and_token_stays_in_header(self):
        captured = {}

        def handler(request):
            captured["body"] = request.read()
            captured["authorization"] = request.headers.get("Authorization")
            return httpx.Response(200, request=request)

        adapter = self.adapter(httpx.MockTransport(handler))
        self.assertTrue(await adapter.publish("GET", "/orders/{orderId}", 200))
        import json
        event = json.loads(captured["body"])
        self.assertEqual(
            set(event),
            {"schema_name", "schema_version", "event_id", "source_id",
             "observed_at", "method", "request_target", "status_code"},
        )
        self.assertEqual(event["request_target"], "/orders/{orderId}")
        self.assertEqual(captured["authorization"], "Bearer " + TOKEN)
        self.assertNotIn(TOKEN.encode(), captured["body"])

    async def test_invalid_observation_is_rejected_without_transport_call(self):
        called = False
        def handler(request):
            nonlocal called
            called = True
            return httpx.Response(200, request=request)
        adapter = self.adapter(httpx.MockTransport(handler))
        self.assertFalse(await adapter.publish("GET", "", 200))
        self.assertFalse(await adapter.publish("GET", "/orders", 99))
        self.assertFalse(called)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main(verbosity=2)
