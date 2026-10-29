
import asyncio
import logging
import sys
import unittest
from copy import deepcopy
from itertools import count
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.requests import Request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main  # noqa: E402

app = main.app
client = TestClient(app)
_nonce_counter = count(1)


def patch_request(*args, **kwargs):
    """Give ordinary PATCH tests unique nonces unless a test supplies one."""
    headers = dict(kwargs.get("headers") or {})
    headers.setdefault("X-Request-Nonce", f"test-nonce-{next(_nonce_counter):08d}")
    kwargs["headers"] = headers
    return client.patch(*args, **kwargs)


POLICY = {"X-Policy-Version": "AP-1.0"}
USER_A = {"Authorization": "Bearer lab-user-a-token", **POLICY}
USER_B = {"Authorization": "Bearer lab-user-b-token", **POLICY}
ADMIN = {"Authorization": "Bearer lab-admin-token", **POLICY}
SUPPORT = {"Authorization": "Bearer lab-support-token", **POLICY}
TENANT_ADMIN = {"Authorization": "Bearer lab-tenant-admin-token", **POLICY}


class MockAPITests(unittest.TestCase):

    def setUp(self):
        # Start every test from canonical fixtures and isolated replay state.
        main.USED_NONCES.clear()
        self.original_orders = main.load_orders()
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))

    def tearDown(self):
        # Restore fixtures and replay cache after every test.
        main.USED_NONCES.clear()
        main.ORDERS.clear()
        main.ORDERS.update(deepcopy(self.original_orders))


    def test_policy_version_is_required_and_unknown_version_is_rejected(self):
        missing = client.get(
            "/orders", headers={"Authorization": "Bearer lab-user-a-token"}
        )
        unknown = client.get(
            "/orders",
            headers={
                "Authorization": "Bearer lab-user-a-token",
                "X-Policy-Version": "AP-9.9",
            },
        )
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(missing.json()["error"]["code"], "INVALID_REQUEST")
        self.assertEqual(unknown.json()["error"]["code"], "INVALID_REQUEST")
        self.assertEqual(missing.json()["error"], unknown.json()["error"])

    def test_support_view_returns_only_assigned_masked_fields(self):
        response = client.get("/support/orders", headers=SUPPORT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["orders"],
            [{"id": "order-1002", "status": "shipped"}],
        )
        self.assertNotIn("total", response.text)
        self.assertNotIn("owner_id", response.text)
        self.assertNotIn("currency", response.text)

    def test_support_cannot_use_customer_order_route(self):
        response = client.get("/orders/order-1002", headers=SUPPORT)
        self.assertIn(response.status_code, (403, 404))
        self.assertNotIn("total", response.json())

    def test_tenant_admin_can_read_same_tenant_orders_with_explicit_permission(self):
        response = client.get("/orders", headers=TENANT_ADMIN)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["orders"]), 3)

    def test_tenant_admin_can_manage_same_tenant_order_with_permission(self):
        response = patch_request(
            "/orders/order-1001",
            headers=TENANT_ADMIN,
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

    def test_tenant_admin_cannot_access_global_admin_inventory(self):
        response = client.get("/admin/orders", headers=TENANT_ADMIN)
        self.assertEqual(response.status_code, 403)

    def test_active_same_tenant_share_grant_allows_read_only_access(self):
        grant = {
            "grant_id": "grant-test",
            "resource_type": "order",
            "issuer": "apisenx-test-fixture",
            "policy_version": "AP-1.0",
            "tenant_id": "lab-tenant",
            "resource_id": "order-1002",
            "grantee_subject": "user-a",
            "actions": ["orders:read"],
            "expires_at": "2099-01-01T00:00:00+00:00",
            "revoked": False,
        }
        with patch("authorization.load_sharing_grants", return_value=[grant]):
            response = client.get("/orders/order-1002", headers=USER_A)
        self.assertEqual(response.status_code, 200)

    def test_share_grant_missing_required_schema_fields_is_denied(self):
        base_grant = {
            "grant_id": "grant-schema-test",
            "resource_type": "order",
            "issuer": "apisenx-test-fixture",
            "policy_version": "AP-1.0",
            "tenant_id": "lab-tenant",
            "resource_id": "order-1002",
            "grantee_subject": "user-a",
            "actions": ["orders:read"],
            "expires_at": "2099-01-01T00:00:00+00:00",
            "revoked": False,
        }

        for missing_field in ("grant_id", "resource_type", "issuer"):
            grant = deepcopy(base_grant)
            grant.pop(missing_field)

            with (
                self.subTest(missing_field=missing_field),
                patch("authorization.load_sharing_grants", return_value=[grant]),
            ):
                response = client.get("/orders/order-1002", headers=USER_A)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.json()["error"],
                    {"code": "NOT_FOUND", "message": "Order not found"},
                )

    def test_revoked_or_expired_share_grants_are_denied_without_disclosure(self):
        grants = [
            {
                "grant_id": "revoked",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "expires_at": "2099-01-01T00:00:00+00:00",
                "revoked": True,
            },
            {
                "grant_id": "expired",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "expires_at": "2000-01-01T00:00:00+00:00",
                "revoked": False,
            },
        ]
        for grant in grants:
            with (
                self.subTest(grant=grant["grant_id"]),
                patch("authorization.load_sharing_grants", return_value=[grant]),
            ):
                response = client.get("/orders/order-1002", headers=USER_A)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.json()["error"],
                    {"code": "NOT_FOUND", "message": "Order not found"},
                )

    def test_malformed_future_wrong_tenant_and_wrong_version_grants_fail_closed(self):
        grants = [
            {
                "grant_id": "not-yet-valid",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "starts_at": "2099-01-01T00:00:00+00:00",
                "expires_at": "2100-01-01T00:00:00+00:00",
                "revoked": False,
            },
            {
                "grant_id": "wrong-tenant",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "other-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "expires_at": "2099-01-01T00:00:00+00:00",
                "revoked": False,
            },
            {
                "grant_id": "wrong-version",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-9.9",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "expires_at": "2099-01-01T00:00:00+00:00",
                "revoked": False,
            },
            {
                "grant_id": "malformed-actions",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": "orders:read",
                "expires_at": "2099-01-01T00:00:00+00:00",
                "revoked": False,
            },
            {
                "grant_id": "naive-expiry",
                "resource_type": "order",
                "issuer": "apisenx-test-fixture",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "expires_at": "2099-01-01T00:00:00",
                "revoked": False,
            },
        ]
        for grant in grants:
            with (
                self.subTest(grant=grant["grant_id"]),
                patch("authorization.load_sharing_grants", return_value=[grant]),
            ):
                response = client.get("/orders/order-1002", headers=USER_A)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.json()["error"],
                    {"code": "NOT_FOUND", "message": "Order not found"},
                )

    # Customer access and ownership

    def test_customer_sees_only_own_orders(self):
        response = client.get("/orders", headers=USER_A)

        self.assertEqual(response.status_code, 200)
        ids = {order["id"] for order in response.json()["orders"]}
        self.assertEqual(ids, {"order-1001", "order-1003"})

    def test_customer_list_excludes_cross_tenant_owned_order(self):
        # Ownership alone must not override the tenant boundary.
        main.ORDERS["order-1003"]["tenant_id"] = "other-tenant"

        response = client.get("/orders", headers=USER_A)

        self.assertEqual(response.status_code, 200)
        ids = {order["id"] for order in response.json()["orders"]}
        self.assertEqual(ids, {"order-1001"})

    def test_owner_can_read_order(self):
        response = client.get("/orders/order-1001", headers=USER_A)
        self.assertEqual(response.status_code, 200)

    def test_cross_user_order_is_denied(self):
        response = client.get("/orders/order-1002", headers=USER_A)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_cross_tenant_single_order_read_is_denied(self):
        main.ORDERS["order-1001"]["tenant_id"] = "other-tenant"

        response = client.get(
            "/orders/order-1001",
            headers=USER_A,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

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
        response = patch_request(
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
        response = patch_request(
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
            response = patch_request(
                "/orders/order-1001",
                headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
                json={"status": "shipped"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_cross_tenant_order_update_is_denied_without_mutation(self):
        main.ORDERS["order-1001"]["tenant_id"] = "other-tenant"
        original_status = main.ORDERS["order-1001"]["status"]

        response = patch_request(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertEqual(
            main.ORDERS["order-1001"]["status"],
            original_status,
        )

    def test_admin_list_denies_mixed_tenant_inventory(self):
        # Do not return partial inventory if any order crosses the boundary.
        main.ORDERS["order-1002"]["tenant_id"] = "other-tenant"

        response = client.get("/admin/orders", headers=ADMIN)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )
        self.assertNotIn("orders", response.json())

    def test_admin_list_denies_order_with_missing_tenant(self):
        main.ORDERS["order-1002"].pop("tenant_id")

        response = client.get("/admin/orders", headers=ADMIN)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"], "FORBIDDEN"
        )
        self.assertNotIn("orders", response.json())

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

    def test_altered_demo_token_is_denied(self):
        # Opaque demo tokens must match the configured token exactly.
        altered_headers = {
            **POLICY,
            "Authorization": "Bearer lab-user-a-tokeN",
        }

        response = client.get("/orders", headers=altered_headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["error"]["code"], "UNAUTHENTICATED"
        )
        self.assertNotIn("orders", response.json())

    def test_customer_token_cannot_access_admin_orders(self):
        response = client.get("/admin/orders", headers=USER_A)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.assertNotIn("orders", response.json())

    def test_replayed_valid_read_request_follows_bearer_policy(self):
        # The current demo-token design permits repeated use of a valid token.
        first = client.get("/orders", headers=USER_A)
        second = client.get("/orders", headers=USER_A)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())

    def test_denied_customer_update_does_not_mutate_order(self):
        before = deepcopy(main.ORDERS["order-1001"])

        response = patch_request(
            "/orders/order-1001",
            headers=USER_A,
            json={"status": "delivered"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.assertEqual(main.ORDERS["order-1001"], before)

    # Admin permissions and valid updates

    def test_admin_can_list_all_orders(self):
        response = client.get("/admin/orders", headers=ADMIN)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["orders"]), 3)

    def test_admin_can_update_order_status(self):
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

    # Invalid update payloads

    def test_update_rejects_extra_fields(self):
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"status": "shipped", "owner_id": "user-b"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_invalid_order_status_is_rejected(self):
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"status": "hacked"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_empty_update_payload_is_rejected(self):
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
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
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "NOT_FOUND"
        )

    def test_unknown_order_update_returns_404(self):
        response = patch_request(
            "/orders/order-9999",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "NOT_FOUND"
        )

    def test_malformed_json_is_rejected(self):
        response = patch_request(
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
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"owner_id": "user-b"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "INVALID_REQUEST"
        )

    def test_null_status_is_rejected(self):
        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
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
                response = patch_request(
                    "/orders/order-1001",
                    headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
                    json=payload,
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_REQUEST"
                )
                self.assertEqual(main.ORDERS["order-1001"], before)

    def test_protected_total_field_cannot_be_modified(self):
        original_total = main.ORDERS["order-1001"]["total"]

        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
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

        response = patch_request(
            "/orders/order-1001",
            headers={**ADMIN, "X-Request-Nonce": "nonce-test-0001"},
            json={"status": "shipped"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "shipped")

        # tearDown restores the original order after this test.
        self.assertNotEqual(
            main.ORDERS["order-1001"]["status"],
            original_status,
        )

    # Privacy-safe observation logging

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

        logged = "\n".join(captured.output)
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


    # Day 13: token lifecycle and request replay

    def test_expired_token_is_rejected(self):
        from datetime import timedelta
        metadata = main.TOKEN_METADATA["lab-user-a-token"].copy()
        try:
            main.TOKEN_METADATA["lab-user-a-token"]["expires_at"] = (
                main.utc_now() - timedelta(seconds=1)
            )
            response = client.get("/orders", headers=USER_A)
        finally:
            main.TOKEN_METADATA["lab-user-a-token"] = metadata
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")

    def test_revoked_token_is_rejected(self):
        main.REVOKED_TOKENS.add("lab-user-a-token")
        try:
            response = client.get("/orders", headers=USER_A)
        finally:
            main.REVOKED_TOKENS.discard("lab-user-a-token")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")

    def test_unknown_token_is_rejected(self):
        response = client.get(
            "/orders",
            headers={"Authorization": "Bearer unknown-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_requires_nonce_and_does_not_mutate(self):
        before = deepcopy(main.ORDERS["order-1001"])
        response = client.patch(
            "/orders/order-1001",
            headers=ADMIN,
            json={"status": "shipped"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_duplicate_patch_nonce_is_rejected_without_second_mutation(self):
        headers = {**ADMIN, "X-Request-Nonce": "nonce-replay-0001"}
        first = patch_request(
            "/orders/order-1001",
            headers=headers,
            json={"status": "shipped"},
        )
        self.assertEqual(first.status_code, 200)
        before = deepcopy(main.ORDERS["order-1001"])
        second = patch_request(
            "/orders/order-1001",
            headers=headers,
            json={"status": "delivered"},
        )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(main.ORDERS["order-1001"], before)

    def test_get_requests_remain_repeatable(self):
        first = client.get("/orders", headers=USER_A)
        second = client.get("/orders", headers=USER_A)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)


    def test_token_issued_in_the_future_is_rejected(self):
        from datetime import timedelta

        metadata = main.TOKEN_METADATA["lab-user-a-token"].copy()
        try:
            main.TOKEN_METADATA["lab-user-a-token"]["issued_at"] = (
                main.utc_now() + timedelta(seconds=60)
            )
            response = client.get("/orders", headers=USER_A)
        finally:
            main.TOKEN_METADATA["lab-user-a-token"] = metadata

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["error"]["code"],
            "UNAUTHENTICATED",
        )

    def test_malformed_patch_nonces_are_rejected_without_mutation(self):
        invalid_nonces = [
            None,
            "short",
            "contains whitespace",
            "!" * 8,
            "x" * 129,
        ]

        for nonce in invalid_nonces:
            with self.subTest(nonce=repr(nonce)):
                before = deepcopy(main.ORDERS["order-1001"])
                headers = dict(ADMIN)
                if nonce is not None:
                    headers["X-Request-Nonce"] = nonce

                response = client.patch(
                    "/orders/order-1001",
                    headers=headers,
                    json={"status": "shipped"},
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"],
                    "INVALID_REQUEST",
                )
                self.assertEqual(main.ORDERS["order-1001"], before)

    def test_nonce_can_be_reused_only_after_replay_window_expires(self):
        from datetime import datetime, timedelta, timezone

        nonce = "nonce-expiry-check-0001"
        first_seen = datetime.now(timezone.utc)
        after_window = first_seen + timedelta(
            seconds=main.REPLAY_WINDOW_SECONDS + 1
        )

        with patch("main.utc_now", side_effect=[first_seen, after_window]):
            main.require_fresh_nonce(nonce)
            # The second use is accepted only after the first entry is stale
            # and removed from the process-local replay cache.
            main.require_fresh_nonce(nonce)

        self.assertEqual(main.USED_NONCES[nonce], after_window)


if __name__ == "__main__":
    unittest.main()
