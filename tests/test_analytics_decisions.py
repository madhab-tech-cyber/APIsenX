"""Days 16–20: authenticated, signed, bound and replay-protected lab proposals."""

import json
import secrets
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.decisions import (
    DecisionError,
    DecisionVerifier,
    ReplayWindow,
    RequestContext,
)
from analytics.detection import Observation


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic",
            secrets.token_bytes(32),
            decision_token=secrets.token_urlsafe(32),
            decision_key=secrets.token_bytes(32),
        )
        self.observation = Observation(
            uuid4(), self.now, "GET", "/orders/order-1001", "user-a", "order-1001", 200
        )
        self.app = create_app(
            self.settings, lambda: self.now, resolver=lambda _: self.observation
        )
        self.client = TestClient(self.app)
        self.request = RequestContext(
            event_id=self.observation.event_id, nonce=uuid4(), requested_at=self.now
        )
        self.headers = {
            "authorization": "Bearer " + self.settings.decision_token,
            "content-type": "application/json",
        }

    def post(self, payload=None, headers=None):
        return self.client.post(
            "/v1/recommendations",
            content=payload or self.request.model_dump_json(),
            headers=headers or self.headers,
        )

    def verify(self, raw, target=("GET", "/orders/{orderId}"), key=None, now=None):
        verifier = DecisionVerifier(
            key or self.settings.decision_key,
            self.app.state.normalizer.contract_version,
        )
        return verifier.verify(raw, self.request, target, now or self.now)

    def test_valid_signed_policy_recommendation_and_target_binding(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        reply = self.verify(response.content)
        self.assertEqual(reply.decision.action, "allow")
        self.assertEqual(reply.decision.reason_code, "AUTHORIZED_OPERATION")
        self.assertEqual(reply.decision.mode, "monitor_only")
        self.assertFalse(reply.decision.enforce)
        self.assertEqual(reply.policy.policy_version, "AP-1.0")
        self.assertEqual(len(reply.policy.rules_digest), 64)
        self.assertLess(len(response.content), 4097)

    def test_ingestion_and_recommendation_credentials_are_separate(self):
        for headers in (
            {"content-type": "application/json"},
            {**self.headers, "authorization": "Bearer " + self.settings.ingest_token},
        ):
            self.assertEqual(self.post(headers=headers).status_code, 401)
        self.assertEqual(
            self.client.post(
                "/v1/events", content="{}", headers=self.headers
            ).status_code,
            401,
        )

    def test_endpoint_is_disabled_without_explicit_keys(self):
        settings = Settings(
            secrets.token_urlsafe(32), "synthetic", secrets.token_bytes(32)
        )
        self.assertEqual(
            TestClient(create_app(settings)).post("/v1/recommendations").status_code,
            404,
        )

    def test_missing_or_mismatched_resolver_never_guesses_principal(self):
        for resolver in (None, lambda _: replace(self.observation, event_id=uuid4())):
            app = create_app(self.settings, lambda: self.now, resolver=resolver)
            response = TestClient(app).post(
                "/v1/recommendations",
                content=self.request.model_dump_json(),
                headers=self.headers,
            )
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "CONTEXT_UNAVAILABLE"})

    def test_replayed_request_nonce_rejects(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post().status_code, 409)

    def test_replayed_signed_response_rejects_at_consumer(self):
        response = self.post()
        verifier = DecisionVerifier(
            self.settings.decision_key, self.app.state.normalizer.contract_version
        )
        verifier.verify(
            response.content, self.request, ("GET", "/orders/{orderId}"), self.now
        )
        with self.assertRaises(DecisionError):
            verifier.verify(
                response.content, self.request, ("GET", "/orders/{orderId}"), self.now
            )

    def test_request_time_future_stale_naive_and_missing_nonce(self):
        for timestamp in (
            self.now - timedelta(seconds=3),
            self.now + timedelta(seconds=2),
            self.now.replace(tzinfo=None),
        ):
            payload = self.request.model_dump(mode="json")
            payload["requested_at"] = timestamp.isoformat()
            self.assertEqual(self.post(json.dumps(payload)).status_code, 422)
        payload.pop("nonce")
        self.assertEqual(self.post(json.dumps(payload)).status_code, 422)

    def test_spoofed_actor_role_target_and_unknown_fields_rejected(self):
        for name in (
            "actor_id",
            "role",
            "tenant_id",
            "owner_id",
            "target",
            "signature",
        ):
            payload = {**self.request.model_dump(mode="json"), name: "SYNTHETIC_SECRET"}
            response = self.post(json.dumps(payload))
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("SYNTHETIC_SECRET", response.text)

    def test_signature_tampering_wrong_key_and_cross_purpose_rejected(self):
        response = self.post()
        with self.assertRaises(DecisionError):
            self.verify(response.content, key=secrets.token_bytes(32))
        original = response.json()
        for section, field, value in (
            ("decision", "action", "deny"),
            ("decision", "reason_code", "ACCESS_PREVENTED"),
            ("policy", "rule_version", "DET-unknown"),
            ("policy", "contract_version", "sha256:" + "0" * 64),
        ):
            changed = json.loads(response.text)
            changed[section][field] = value
            with self.assertRaises(DecisionError):
                self.verify(json.dumps(changed).encode())
        original["decision"]["signature"] = original["policy"]["signature"]
        with self.assertRaises(DecisionError):
            self.verify(json.dumps(original).encode())

    def test_wrong_nonce_event_id_target_and_expired_reply_rejected(self):
        response = self.post()
        for target in (("PATCH", "/orders/{orderId}"), ("GET", "/admin/orders")):
            with self.assertRaises(DecisionError):
                self.verify(response.content, target=target)
        verifier = DecisionVerifier(
            self.settings.decision_key, self.app.state.normalizer.contract_version
        )
        for request in (
            self.request.model_copy(update={"nonce": uuid4()}),
            self.request.model_copy(update={"event_id": uuid4()}),
        ):
            with self.assertRaises(DecisionError):
                verifier.verify(
                    response.content, request, ("GET", "/orders/{orderId}"), self.now
                )
        with self.assertRaises(DecisionError):
            self.verify(response.content, now=self.now + timedelta(seconds=5))

    def test_duplicate_json_keys_and_oversized_reply_rejected(self):
        response = self.post()
        for raw in (b" " * 4097, b"{" + b'"policy":{},"policy":{},"decision":{}}'):
            with self.assertRaises(DecisionError):
                self.verify(raw)
        self.assertEqual(self.post(" " * 4097).status_code, 413)
        self.assertEqual(self.post('{"nonce":1,"nonce":2}').status_code, 400)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_success_recommends_deny_but_cannot_enforce(self):
        self.observation = replace(
            self.observation,
            request_target="/orders/order-1002",
            object_id="order-1002",
        )
        response = self.post()
        decision = self.verify(response.content).decision
        self.assertEqual((decision.action, decision.rule_id), ("deny", "DET-BOLA-1"))
        self.assertFalse(decision.enforce)
        self.assertNotEqual(decision.schema_name, "enforcement_decision")
        self.assertNotIn("approval_id", response.text)

    def test_context_outage_staleness_and_audit_failure_never_issue_a_reply(self):
        self.observation = replace(
            self.observation, observed_at=self.now - timedelta(seconds=3)
        )
        self.assertEqual(self.post().status_code, 503)
        self.observation = replace(self.observation, observed_at=self.now)
        self.request = self.request.model_copy(update={"nonce": uuid4()})
        with patch.object(
            self.app.state.decisions.audit,
            "append",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SYNTHETIC_SECRET", response.text)
        self.assertNotIn("signature", response.text)

    def test_masked_audit_rule_ids_retention_and_credential_exclusion(self):
        self.post()
        rows = self.app.state.decisions.audit.store.snapshot(self.now)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rule_id"], "DET-OBS-1")
        self.assertEqual(rows[0]["expires_at"], self.now + timedelta(seconds=300))
        for forbidden in (
            "user-a",
            "order-1001",
            self.settings.ingest_token,
            self.settings.decision_token,
        ):
            self.assertNotIn(forbidden, repr(rows))
        self.assertEqual(
            self.app.state.decisions.audit.store.snapshot(
                self.now + timedelta(seconds=300)
            ),
            [],
        )

    def test_audit_retry_with_new_nonce_deduplicates_same_event(self):
        self.assertEqual(self.post().status_code, 200)
        self.request = self.request.model_copy(update={"nonce": uuid4()})
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(
            len(self.app.state.decisions.audit.store.snapshot(self.now)), 1
        )

    def test_replay_capacity_fails_closed_and_expiry_reclaims(self):
        window = ReplayWindow(capacity=1)
        window.claim(uuid4(), self.now, self.now + timedelta(seconds=5))
        with self.assertRaises(DecisionError):
            window.claim(uuid4(), self.now, self.now + timedelta(seconds=5))
        window.claim(
            uuid4(), self.now + timedelta(seconds=5), self.now + timedelta(seconds=10)
        )

    def test_incomplete_or_shared_secret_configuration_rejects(self):
        for values in (
            {"decision_token": secrets.token_urlsafe(32)},
            {"decision_key": secrets.token_bytes(32)},
            {
                "decision_token": self.settings.ingest_token,
                "decision_key": secrets.token_bytes(32),
            },
            {
                "decision_token": secrets.token_urlsafe(32),
                "decision_key": self.settings.hmac_key,
            },
        ):
            with self.assertRaises(ValueError):
                Settings(
                    self.settings.ingest_token,
                    "synthetic",
                    self.settings.hmac_key,
                    **values,
                )

    def test_logs_on_success_and_failure_have_only_bounded_codes(self):
        with self.assertLogs("apisenx.analytics", level="INFO") as logs:
            self.post()
            self.post()
        for forbidden in (
            self.settings.decision_token,
            "user-a",
            "order-1001",
            str(self.request.nonce),
        ):
            self.assertNotIn(forbidden, repr(logs.output))

    def test_unknown_issuer_version_and_active_mode_are_rejected(self):
        original = self.post().json()
        for name, value in (
            ("issuer", "untrusted_issuer"),
            ("key_id", "unknown_key"),
            ("schema_version", "2.0"),
            ("enforce", True),
            ("mode", "active"),
        ):
            changed = json.loads(json.dumps(original))
            changed["decision"][name] = value
            with self.assertRaises(DecisionError):
                self.verify(json.dumps(changed).encode())

    def test_policy_configuration_and_source_hash_are_signed(self):
        response = self.post()
        original = response.json()
        for name in ("rules_digest", "permission_digest"):
            changed = json.loads(response.text)
            changed["policy"][name] = "0" * 64
            with self.assertRaises(DecisionError):
                self.verify(json.dumps(changed).encode())
        original["policy"]["flow_profile"]["threshold"] += 1
        with self.assertRaises(DecisionError):
            self.verify(json.dumps(original).encode())
