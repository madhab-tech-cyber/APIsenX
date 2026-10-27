import asyncio
import unittest

import main
from fastapi.testclient import TestClient


class TokenBucketLimiterTests(unittest.TestCase):
    def setUp(self):
        main.SERVICE_LIMITER.buckets.clear()
        main.SUBJECT_LIMITER.buckets.clear()
        main.ROUTE_COST_LIMITER.buckets.clear()
        main.SOURCE_LIMITER.buckets.clear()

    def test_orders_pagination_caps_page_size(self):
        client = TestClient(main.app)
        headers = {
            "Authorization": "Bearer lab-user-a-token",
            "X-Policy-Version": "AP-1.0",
        }
        response = client.get("/orders?limit=1&offset=0", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()["orders"]), 1)

    def test_orders_pagination_rejects_limit_above_cap(self):
        client = TestClient(main.app)
        headers = {
            "Authorization": "Bearer lab-user-a-token",
            "X-Policy-Version": "AP-1.0",
        }
        response = client.get("/orders?limit=101", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")

    def test_subject_concurrency_gate_returns_429_when_full(self):
        client = TestClient(main.app)
        key = ("user-a", "read")
        semaphore = main.threading.BoundedSemaphore(5)
        for _ in range(5):
            self.assertTrue(semaphore.acquire(blocking=False))
        with main.SUBJECT_SEMAPHORE_LOCK:
            main.SUBJECT_SEMAPHORES[key] = semaphore
        try:
            response = client.get("/orders", headers={
                "Authorization": "Bearer lab-user-a-token",
                "X-Policy-Version": "AP-1.0",
            })
        finally:
            with main.SUBJECT_SEMAPHORE_LOCK:
                main.SUBJECT_SEMAPHORES.pop(key, None)
            for _ in range(5):
                semaphore.release()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertEqual(response.headers["Retry-After"], "1")

    def test_patch_subject_concurrency_gate_uses_tighter_limit(self):
        client = TestClient(main.app)
        key = ("admin-1", "PATCH")
        semaphore = main.threading.BoundedSemaphore(2)
        for _ in range(2):
            self.assertTrue(semaphore.acquire(blocking=False))
        with main.SUBJECT_SEMAPHORE_LOCK:
            main.SUBJECT_SEMAPHORES[key] = semaphore
        try:
            response = client.patch(
                "/orders/order-1001",
                headers={
                    "Authorization": "Bearer lab-admin-token",
                    "X-Policy-Version": "AP-1.0",
                    "X-Request-Nonce": "nonce-12345678",
                },
                json={"status": "shipped"},
            )
        finally:
            with main.SUBJECT_SEMAPHORE_LOCK:
                main.SUBJECT_SEMAPHORES.pop(key, None)
            for _ in range(2):
                semaphore.release()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")

    def test_streaming_body_limit_checks_actual_bytes(self):
        async def run_test():
            async def receive():
                return {
                    "type": "http.request",
                    "body": b"x" * (main.MAX_JSON_BODY_BYTES + 1),
                    "more_body": True,
                }

            sent = []

            async def capture(message):
                sent.append(message)

            async def app(scope, receive, send):
                message = await receive()
                self.assertEqual(message["body"], b"")
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b"ok", "more_body": False})

            middleware = main.BoundedHTTPPayloadMiddleware(
                app,
                max_request_bytes=main.MAX_JSON_BODY_BYTES,
                max_response_bytes=main.MAX_RESPONSE_BYTES,
            )
            await middleware(
                {"type": "http", "method": "POST", "path": "/test"},
                receive,
                capture,
            )
            self.assertEqual(sent[0]["status"], 413)
            self.assertIn(b"INVALID_REQUEST", sent[1]["body"])

        asyncio.run(run_test())

    def test_response_body_limit_replaces_oversized_response(self):
        async def run_test():
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            sent = []

            async def capture(message):
                sent.append(message)

            async def app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({
                    "type": "http.response.body",
                    "body": b"x" * (main.MAX_RESPONSE_BYTES + 1),
                    "more_body": False,
                })

            middleware = main.BoundedHTTPPayloadMiddleware(
                app,
                max_request_bytes=main.MAX_JSON_BODY_BYTES,
                max_response_bytes=main.MAX_RESPONSE_BYTES,
            )
            await middleware(
                {"type": "http", "method": "GET", "path": "/test"},
                receive,
                capture,
            )
            self.assertEqual(sent[0]["status"], 500)
            self.assertIn(b"RESPONSE_TOO_LARGE", sent[1]["body"])

        asyncio.run(run_test())

    def test_unauthenticated_source_limit_returns_429(self):
        client = TestClient(main.app)
        main.SOURCE_LIMITER.buckets.clear()
        now = main.SOURCE_LIMITER.clock()
        main.SOURCE_LIMITER.buckets[("source", "testclient")] = (
            0.0, now, now
        )
        try:
            response = client.get("/orders")
        finally:
            main.SOURCE_LIMITER.buckets.clear()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertGreaterEqual(int(response.headers["Retry-After"]), 1)

    def test_oversized_content_length_rejected_before_dispatch(self):
        client = TestClient(main.app)
        response = client.post(
            "/orders",
            headers={"Content-Length": str(main.MAX_JSON_BODY_BYTES + 1)},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")

    def test_service_concurrency_gate_returns_429_when_full(self):
        client = TestClient(main.app)
        acquired = 0
        try:
            for _ in range(10):
                self.assertTrue(main.SERVICE_IN_FLIGHT.acquire(blocking=False))
                acquired += 1
            response = client.get("/health")
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        finally:
            for _ in range(acquired):
                main.SERVICE_IN_FLIGHT.release()

    def test_multi_gate_rejection_does_not_partially_debit(self):
        now = [100.0]
        limiter = main.TokenBucketLimiter(clock=lambda: now[0])
        limiter.buckets[("limited",)] = (0.0, now[0], now[0])
        result = limiter.consume_many([
            (("fresh",), 1.0, 2.0, 1.0),
            (("limited",), 1.0, 1.0, 1.0),
        ])
        self.assertEqual(result[0], False)
        self.assertNotIn(("fresh",), limiter.buckets)

    def test_weighted_route_budget_rejects_without_order_mutation(self):
        main.SERVICE_LIMITER.buckets.clear()
        main.SUBJECT_LIMITER.buckets.clear()
        main.ROUTE_COST_LIMITER.buckets.clear()
        now = main.ROUTE_COST_LIMITER.clock()
        main.ROUTE_COST_LIMITER.buckets[("route", "GET /orders")] = (
            0.0, now, now
        )
        client = TestClient(main.app)
        original_status = main.ORDERS["order-1001"]["status"]
        try:
            response = client.get("/orders", headers={
                "Authorization": "Bearer lab-user-a-token",
                "X-Policy-Version": "AP-1.0",
            })
        finally:
            main.SERVICE_LIMITER.buckets.clear()
            main.SUBJECT_LIMITER.buckets.clear()
            main.ROUTE_COST_LIMITER.buckets.clear()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertEqual(main.ORDERS["order-1001"]["status"], original_status)

    def test_burst_is_bounded_and_retry_after_is_positive(self):
        now = [100.0]
        limiter = main.TokenBucketLimiter(clock=lambda: now[0])
        self.assertEqual(
            limiter.consume(("subject", "user-a"), 1.0, 2.0), (True, 0, 200)
        )
        self.assertEqual(
            limiter.consume(("subject", "user-a"), 1.0, 2.0), (True, 0, 200)
        )
        allowed, retry_after, status = limiter.consume(("subject", "user-a"), 1.0, 2.0)
        self.assertFalse(allowed)
        self.assertEqual(status, 429)
        self.assertGreaterEqual(retry_after, 1)

    def test_bucket_refills_using_monotonic_elapsed_time(self):
        now = [100.0]
        limiter = main.TokenBucketLimiter(clock=lambda: now[0])
        limiter.consume(("subject", "user-a"), 1.0, 1.0)
        now[0] += 1.0
        self.assertEqual(
            limiter.consume(("subject", "user-a"), 1.0, 1.0), (True, 0, 200)
        )

    def test_live_bucket_is_not_evicted_to_grant_a_fresh_burst(self):
        now = [100.0]
        limiter = main.TokenBucketLimiter(max_keys=1, clock=lambda: now[0])
        limiter.consume(("subject", "user-a"), 1.0, 1.0)
        allowed, retry_after, status = limiter.consume(("subject", "user-b"), 1.0, 1.0)
        self.assertFalse(allowed)
        self.assertEqual((retry_after, status), (1, 503))

    def test_idle_bucket_can_be_evicted_after_ttl(self):
        now = [100.0]
        limiter = main.TokenBucketLimiter(
            max_keys=1, idle_ttl=60.0, clock=lambda: now[0]
        )
        limiter.consume(("subject", "user-a"), 1.0, 1.0)
        now[0] += 60.0
        self.assertEqual(
            limiter.consume(("subject", "user-b"), 1.0, 1.0), (True, 0, 200)
        )

    def test_subject_limit_returns_429_without_mutating_order(self):
        client = TestClient(main.app)
        original_status = main.ORDERS["order-1001"]["status"]
        main.SERVICE_LIMITER.buckets.clear()
        main.SUBJECT_LIMITER.buckets.clear()
        main.ROUTE_COST_LIMITER.buckets.clear()
        now = main.ROUTE_COST_LIMITER.clock()
        main.ROUTE_COST_LIMITER.buckets[("subject", "user-a", "GET /orders")] = (
            0.0,
            now,
            now,
        )
        try:
            response = client.get(
                "/orders",
                headers={
                    "Authorization": "Bearer lab-user-a-token",
                    "X-Policy-Version": "AP-1.0",
                },
            )
        finally:
            main.SERVICE_LIMITER.buckets.clear()
            main.SUBJECT_LIMITER.buckets.clear()
            main.ROUTE_COST_LIMITER.buckets.clear()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertGreaterEqual(int(response.headers["Retry-After"]), 1)
        self.assertEqual(main.ORDERS["order-1001"]["status"], original_status)

    def test_service_limit_returns_generic_429_and_correlation_id(self):
        client = TestClient(main.app)
        main.SERVICE_LIMITER.buckets.clear()
        main.SUBJECT_LIMITER.buckets.clear()
        now = main.SERVICE_LIMITER.clock()
        main.SERVICE_LIMITER.buckets[("service",)] = (0.0, now, now)
        try:
            response = client.get("/orders", headers={
                "Authorization": "Bearer lab-user-a-token",
                "X-Policy-Version": "AP-1.0",
            })
        finally:
            main.SERVICE_LIMITER.buckets.clear()
            main.SUBJECT_LIMITER.buckets.clear()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertIn("X-Correlation-ID", response.headers)
        self.assertGreaterEqual(int(response.headers["Retry-After"]), 1)


if __name__ == "__main__":
    unittest.main()
