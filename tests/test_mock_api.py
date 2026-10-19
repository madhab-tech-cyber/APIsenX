import asyncio
import logging
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.requests import Request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main

app = main.app
client = TestClient(app)

USER_A = {"Authorization": "Bearer lab-user-a-token"}
USER_B = {"Authorization": "Bearer lab-user-b-token"}
ADMIN = {"Authorization": "Bearer lab-admin-token"}


class MockAPITests(unittest.TestCase):

    def setUp(self):
        # Start every test from the canonical fixture, not the prior test's state.
        self.original_orders = main.load_orders()
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))

    def tearDown(self):
        # Restore the canonical fixture after every test.
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))

    # Customer access and ownership

    def test_customer_sees_only_own_orders(self):
        response = client.get("/orders", headers=USER_A)

        self.assertEqual(response.status_code, 200)
        ids = {order["id"] for order in response.json()["orders"]}
        self.assertEqual(ids, {"order-1001", "order-1003"})

    def test_owner_can_read_order(self):
        response = client.get("/orders/order-1001", headers=USER_A)
        self.assertEqual(response.status_code, 200)

    def test_cross_user_order_is_denied(self):
        response = client.get("/orders/order-1002", headers=USER_A)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )

    def test_customer_cannot_list_admin_orders(self):
        response = client.get("/admin/orders", headers=USER_A)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )

    def test_admin_function_denied_for_customer_with_empty_inventory(self):
        with patch.dict(main.ORDERS, {}, clear=True):
            response = client.get("/admin/orders", headers=USER_A)
        self.assertEqual(response.status_code, 403)

    def test_admin_function_denied_for_customer_when_all_orders_are_owned(self):
        owned = {
            "order-a": {
                "id": "order-a",
                "owner_id": "user-a",
                "status": "processing",
                "total": 1,
                "currency": "INR",
            },
            "order-b": {
                "id": "order-b",
                "owner_id": "user-a",
                "status": "shipped",
                "total": 2,
                "currency": "INR",
            },
        }
        with patch.dict(main.ORDERS, owned, clear=True):
            response = client.get("/admin/orders", headers=USER_A)
        self.assertEqual(response.status_code, 403)

    def test_admin_function_denied_for_customer_with_mixed_owner_inventory(self):
        response = client.get("/admin/orders", headers=USER_A)
        self.assertEqual(response.status_code, 403)

    def test_admin_function_denied_for_unknown_role_even_if_inventory_owned(self):
        unknown_role_users = {
            "user-a": {"id": "user-a", "active": True, "role": "superuser"}
        }
        owned = {
            "order-a": {
                "id": "order-a",
                "owner_id": "user-a",
                "status": "processing",
                "total": 1,
                "currency": "INR",
            }
        }
        with (
            patch("main.load_users", return_value=unknown_role_users),
            patch.dict(main.ORDERS, owned, clear=True),
        ):
            response = client.get("/admin/orders", headers=USER_A)
        self.assertEqual(response.status_code, 403)

    def test_admin_function_requires_explicit_permission(self):
        no_permission_users = {
            "admin-1": {
                "id": "admin-1",
                "active": True,
                "role": "admin",
                "permissions": [],
            }
        }
        with patch("main.load_users", return_value=no_permission_users), patch(
            "main.load_json", return_value={"roles": {"admin": []}}
        ):
            response = client.get("/admin/orders", headers=ADMIN)
        self.assertEqual(response.status_code, 403)

    def test_inactive_identity_cannot_use_admin_function(self):
        inactive_users = {
            "admin-1": {"id": "admin-1", "active": False, "role": "admin"}
        }
        with patch("main.load_users", return_value=inactive_users):
            response = client.get("/admin/orders", headers=ADMIN)
        self.assertEqual(response.status_code, 401)

    def test_customer_cannot_update_order(self):
        response = client.patch(
            "/orders/order-1001",
            headers=USER_A,
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )

    def test_denied_patch_leaves_order_state_unchanged(self):
        before = deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers=USER_A,
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_patch_requires_manage_permission_independent_of_admin_role(self):
        before = deepcopy(main.ORDERS["order-1001"])
        with patch(
            "main.load_json",
            return_value={"roles": {"admin": ["orders:read:any"]}},
        ):
            response = client.patch(
                "/orders/order-1001",
                headers=ADMIN,
                json={"status": "shipped"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)

    # Authentication

    def test_missing_token_is_denied(self):
        response = client.get("/orders")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["error"]["code"], "UNAUTHENTICATED"
        )

    def test_invalid_token_is_denied(self):
        response = client.get(
            "/orders",
            headers={"Authorization": "Bearer invalid-token"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["error"]["code"], "UNAUTHENTICATED"
        )

    def test_malformed_authorization_scheme_is_denied(self):
        response = client.get(
            "/orders",
            headers={"Authorization": "Basic abc123"},
        )
        self.assertEqual(response.status_code, 401)

    def test_empty_bearer_token_is_denied(self):
        response = client.get(
            "/orders",
            headers={"Authorization": "Bearer "},
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_access_api(self):
        inactive_users = {
            "user-a": {
                "id": "user-a",
                "active": False,
                "role": "customer",
            }
        }

        with patch("main.load_users", return_value=inactive_users):
            response = client.get("/orders", headers=USER_A)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["error"]["code"], "UNAUTHENTICATED"
        )

    def test_unknown_role_cannot_access_admin_endpoint(self):
        unknown_role_users = {
            "user-a": {
                "id": "user-a",
                "active": True,
                "role": "superuser",
            }
        }

        with patch("main.load_users", return_value=unknown_role_users):
            response = client.get("/admin/orders", headers=USER_A)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )

    # Admin permissions and valid updates

    def test_admin_can_list_all_orders(self):
        response = client.get("/admin/orders", headers=ADMIN)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["orders"]), 3)

    def test_admin_can_update_order_status(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

    # Invalid update payloads

    def test_update_rejects_extra_fields(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped", "owner_id": "user-b"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_invalid_order_status_is_rejected(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "hacked"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_empty_update_payload_is_rejected(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    # Day 6: Edge-case hardening

    def test_unknown_order_read_returns_404(self):
        response = client.get(
            "/orders/order-9999",
            headers=ADMIN,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "NOT_FOUND"
        )

    def test_unknown_order_update_returns_404(self):
        response = client.patch(
            "/orders/order-9999",
            headers=ADMIN,
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "NOT_FOUND"
        )

    def test_malformed_json_is_rejected(self):
        response = client.patch(
            "/orders/order-1001",
            headers={
                **ADMIN,
                "Content-Type": "application/json",
            },
            content='{"status":',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_missing_status_field_is_rejected(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"owner_id": "user-b"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_null_status_is_rejected(self):
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": None},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_all_protected_fields_are_rejected_without_mutation(self):
        protected_payloads = [
            {"status": "shipped", "id": "order-attacker"},
            {"status": "shipped", "owner_id": "user-b"},
            {"status": "shipped", "total": 0},
            {"status": "shipped", "currency": "USD"},
        ]
        for payload in protected_payloads:
            with self.subTest(payload=payload):
                before = deepcopy(main.ORDERS["order-1001"])
                response = client.patch(
                    "/orders/order-1001",
                    headers=ADMIN,
                    json=payload,
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_REQUEST"
                )
                self.assertEqual(main.ORDERS["order-1001"], before)

    def test_protected_total_field_cannot_be_modified(self):
        original_total = main.ORDERS["order-1001"]["total"]

        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped", "total": 0},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )
        self.assertEqual(
            main.ORDERS["order-1001"]["total"], original_total
        )

    # Day 6: Test isolation

    def test_admin_update_does_not_leak_between_tests(self):
        original_status = self.original_orders["order-1001"]["status"]

        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

        # tearDown restores the original order after this test.
        self.assertNotEqual(
            main.ORDERS["order-1001"]["status"],
            original_status,
        )


    def test_observation_exception_does_not_log_exception_text_or_traceback(self):
        sentinel = "exception-secret-sentinel"
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/test-route",
            "raw_path": b"/test-route",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 123),
            "server": ("testserver", 80),
            "root_path": "",
            "route": type("Route", (), {"path": "/test-route"})(),
        }
        request = Request(scope)

        async def fail_call_next(_request):
            raise RuntimeError(sentinel)

        with self.assertLogs("apisenx.audit", level="ERROR") as captured:
            with self.assertRaisesRegex(RuntimeError, sentinel):
                asyncio.run(main.observe_request(request, fail_call_next))

        logged = "\\n".join(captured.output)
        self.assertIn("status=500", logged)
        self.assertIn("outcome=unhandled_exception", logged)
        self.assertNotIn(sentinel, logged)
        self.assertNotIn("Traceback", logged)

    def test_observation_hook_emits_route_template_without_sensitive_values(self):
        # Keep httpx's test-client logger from printing the intentionally
        # synthetic query values while the application hook is under test.
        httpx_logger = logging.getLogger("httpx")
        previous_level = httpx_logger.level
        httpx_logger.setLevel(logging.WARNING)
        try:
            with self.assertLogs("apisenx.audit", level="INFO") as captured:
                response = client.get(
                    "/orders/order-1001?tenant_id=tenant-secret&debug=query-secret",
                    headers=USER_A,
                )
        finally:
            httpx_logger.setLevel(previous_level)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("X-Correlation-ID"))
        log_text = "\n".join(captured.output)
        self.assertIn("route=/orders/{orderId}", log_text)
        self.assertIn("method=GET", log_text)
        self.assertIn("status=200", log_text)
        for forbidden_value in (
            "user-a",
            "order-1001",
            "lab-user-a-token",
            "tenant-secret",
            "query-secret",
        ):
            with self.subTest(forbidden_value=forbidden_value):
                self.assertNotIn(forbidden_value, log_text)


if __name__ == "__main__":
    unittest.main()
