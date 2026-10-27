import unittest

import main
from fastapi.testclient import TestClient


class TokenBucketLimiterTests(unittest.TestCase):
    def setUp(self):
        main.SERVICE_LIMITER.buckets.clear()
        main.SUBJECT_LIMITER.buckets.clear()
        main.ROUTE_COST_LIMITER.buckets.clear()
        main.SOURCE_LIMITER.buckets.clear()
        main.UNAUTH_AGGREGATE_LIMITER.buckets.clear()

    def test_unauthenticated_source_limit_returns_429(self):
        client = TestClient(main.app)
        main.SOURCE_LIMITER.buckets.clear()
        main.UNAUTH_AGGREGATE_LIMITER.buckets.clear()
        now = main.SOURCE_LIMITER.clock()
        main.SOURCE_LIMITER.buckets[("source", "testclient")] = (
            0.0, now, now
        )
        try:
            response = client.get("/orders")
        finally:
            main.SOURCE_LIMITER.buckets.clear()
            main.UNAUTH_AGGREGATE_LIMITER.buckets.clear()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertGreaterEqual(int(response.headers["Retry-After"]), 1)

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
