"""Read-only policy parity against the same authoritative synthetic lab fixtures."""

import copy
import unittest
from unittest.mock import patch

from analytics.ownership import OwnershipEvaluator
from src.authorization import authorize, load_orders, load_users


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.users = copy.deepcopy(load_users())
        self.orders = copy.deepcopy(load_orders())
        self.engine = OwnershipEvaluator(self.users, self.orders)

    def test_owner_read_allowed_without_finding(self):
        result = self.engine.evaluate("user-a", "order-1001", status_code=200)
        self.assertEqual(
            (result.outcome, result.reason_code, result.alert),
            ("allowed", "AUTHORIZED_READ", None),
        )

    def test_cross_owner_success_is_candidate_not_enforcement(self):
        result = self.engine.evaluate("user-a", "order-1002", status_code=200)
        self.assertEqual(result.outcome, "denied")
        self.assertEqual(result.alert.finding_class, "bola_candidate")
        self.assertEqual(result.alert.mode, "monitor_only")
        self.assertNotIn("user-a", result.alert.model_dump_json())
        self.assertNotIn("order-1002", result.alert.model_dump_json())

    def test_denied_missing_and_failure_status_are_not_successful_bola(self):
        for status in (None, 401, 403, 404, 429, 500, True):
            result = self.engine.evaluate("user-a", "order-1002", status_code=status)
            self.assertIsNone(result.alert)

    def test_missing_identity_resource_policy_and_inactive_are_unavailable(self):
        self.users["user-a"]["active"] = False
        for actor, obj, version in (
            ("unknown", "order-1001", "AP-1.0"),
            ("user-b", "missing", "AP-1.0"),
            ("user-a", "order-1001", "AP-1.0"),
            ("user-b", "order-1001", "unknown"),
        ):
            result = self.engine.evaluate(
                actor, obj, policy_version=version, status_code=200
            )
            self.assertEqual(result.outcome, "unavailable")
            self.assertIsNone(result.alert)

    def test_tenant_before_ownership_or_admin_permission(self):
        self.orders["order-1001"]["tenant_id"] = "synthetic_other_tenant"
        for actor in ("user-a", "admin-1", "tenant-admin-1"):
            self.assertEqual(
                self.engine.evaluate(actor, "order-1001").outcome, "denied"
            )

    def test_missing_tenant_does_not_create_finding(self):
        del self.orders["order-1001"]["tenant_id"]
        self.assertEqual(
            self.engine.evaluate("user-a", "order-1001", status_code=200).outcome,
            "unavailable",
        )

    def test_admin_tenant_admin_and_active_share_have_no_false_bola(self):
        for actor in ("admin-1", "tenant-admin-1"):
            self.assertEqual(
                self.engine.evaluate(actor, "order-1002", status_code=200).outcome,
                "allowed",
            )
        grant = {
            "grant_id": "synthetic-grant",
            "resource_type": "order",
            "issuer": "synthetic-issuer",
            "policy_version": "AP-1.0",
            "tenant_id": "lab-tenant",
            "resource_id": "order-1002",
            "grantee_subject": "user-a",
            "actions": ["orders:read"],
            "revoked": False,
            "expires_at": "2099-01-01T00:00:00+00:00",
        }
        with patch("src.authorization.load_sharing_grants", return_value=[grant]):
            self.assertEqual(
                self.engine.evaluate("user-a", "order-1002", status_code=200).outcome,
                "allowed",
            )
            grant["revoked"] = True
            self.assertEqual(
                self.engine.evaluate("user-a", "order-1002").outcome, "denied"
            )
            grant["revoked"] = False
            grant["expires_at"] = "2000-01-01T00:00:00+00:00"
            self.assertEqual(
                self.engine.evaluate("user-a", "order-1002").outcome, "denied"
            )

    def test_policy_unavailable_is_not_a_finding(self):
        with patch(
            "analytics.ownership.authorize", side_effect=RuntimeError("synthetic")
        ):
            self.assertEqual(
                self.engine.evaluate("user-a", "order-1001").outcome, "unavailable"
            )

    def test_missing_owner_and_unknown_role_are_not_bola_evidence(self):
        self.users["user-a"]["role"] = "unknown"
        self.assertEqual(
            self.engine.evaluate("user-a", "order-1001").outcome, "unavailable"
        )
        del self.orders["order-1002"]["owner_id"]
        self.assertEqual(
            self.engine.evaluate("user-b", "order-1002").outcome, "unavailable"
        )
        self.users["user-b"] = "malformed server context"
        self.assertEqual(
            self.engine.evaluate("user-b", "order-1001").outcome, "unavailable"
        )

    def test_all_shipped_subject_object_pairs_match_member5_read_policy(self):
        for actor in self.users:
            for obj in self.orders:
                allowed, _ = authorize(
                    actor, "orders:read", obj, self.users, self.orders
                )
                result = self.engine.evaluate(actor, obj)
                self.assertEqual(result.outcome == "allowed", allowed)
