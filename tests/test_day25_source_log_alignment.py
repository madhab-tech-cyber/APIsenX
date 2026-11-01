"""Day 25: reconcile controlled API attack outcomes with source application logs."""

import logging
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402

client = TestClient(main.app)
POLICY = {"X-Policy-Version": "AP-1.0"}
USER_A = {"Authorization": "Bearer lab-user-a-token", **POLICY}


class Day25SourceLogAlignmentTests(unittest.TestCase):
    """The API response is authoritative; logs must corroborate, not decide."""

    def assert_source_log_matches(
        self, path, expected_status, expected_route, headers, forbidden
    ):
        httpx_logger = logging.getLogger("httpx")
        previous_level = httpx_logger.level
        httpx_logger.setLevel(logging.WARNING)
        try:
            with self.assertLogs("apisenx.audit", level="INFO") as captured:
                response = client.get(path, headers=headers)
        finally:
            httpx_logger.setLevel(previous_level)

        self.assertEqual(response.status_code, expected_status)
        correlation_id = response.headers.get("X-Correlation-ID")
        self.assertIsNotNone(correlation_id)
        self.assertRegex(correlation_id, r"^[0-9a-f-]{36}$")

        lines = [
            line for line in captured.output
            if "observation correlation_id=" in line
        ]
        self.assertEqual(len(lines), 1, captured.output)
        log_line = lines[0]
        self.assertIn(f"correlation_id={correlation_id}", log_line)
        self.assertIn("method=GET", log_line)
        self.assertIn(f"route={expected_route}", log_line)
        self.assertIn(f"status={expected_status}", log_line)
        self.assertRegex(log_line, r"elapsed_ms=[0-9]+(?:\.[0-9]+)?")

        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, log_line)

        return response

    def test_owner_read_is_correlated_with_successful_source_log(self):
        self.assert_source_log_matches(
            "/orders/order-1001?debug=day25-query-secret",
            200,
            "/orders/{orderId}",
            USER_A,
            (
                "order-1001",
                "user-a",
                "lab-user-a-token",
                "day25-query-secret",
            ),
        )

    def test_cross_owner_bola_attempt_is_correlated_with_denial_log(self):
        self.assert_source_log_matches(
            "/orders/order-1002?debug=day25-bola-secret",
            404,
            "/orders/{orderId}",
            USER_A,
            (
                "order-1002",
                "user-a",
                "lab-user-a-token",
                "day25-bola-secret",
            ),
        )

    def test_customer_admin_function_attempt_is_correlated_with_denial_log(self):
        self.assert_source_log_matches(
            "/admin/orders?debug=day25-bfla-secret",
            403,
            "/admin/orders",
            USER_A,
            ("user-a", "lab-user-a-token", "day25-bfla-secret"),
        )

    def test_unauthenticated_attempt_is_correlated_without_credential_data(self):
        self.assert_source_log_matches(
            "/orders?debug=day25-unauth-secret",
            401,
            "/orders",
            POLICY,
            ("day25-unauth-secret", "Bearer", "lab-user-a-token"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
