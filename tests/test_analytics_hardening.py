"""Days 21–23/27: outage, stale policy, masking gates and context regression fixes."""

import copy
import secrets
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.decisions import RequestContext, rules_digest
from analytics.detection import Observation
from analytics.store import StoreError


class HardeningTests(unittest.TestCase):
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

    def recommend(self):
        request = RequestContext(
            event_id=self.observation.event_id, nonce=uuid4(), requested_at=self.now
        )
        return self.client.post(
            "/v1/recommendations",
            content=request.model_dump_json(),
            headers={
                "authorization": "Bearer " + self.settings.decision_token,
                "content-type": "application/json",
            },
        )

    def test_expired_policy_never_renews_itself_for_fresh_observation(self):
        self.now += timedelta(seconds=300)
        self.observation = replace(self.observation, observed_at=self.now)
        response = self.recommend()
        self.assertEqual(
            (response.status_code, response.json()), (503, {"detail": "POLICY_STALE"})
        )
        self.assertNotIn("signature", response.text)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_source_code_contract_permissions_or_flow_change_requires_new_instance(
        self,
    ):
        service = self.app.state.decisions
        with patch("analytics.decisions.rules_digest", return_value="0" * 64):
            self.assertEqual(self.recommend().json(), {"detail": "POLICY_STALE"})
        original = service.engine.normalizer.contract_version
        service.engine.normalizer.contract_version = "sha256:" + "0" * 64
        self.assertEqual(self.recommend().status_code, 503)
        service.engine.normalizer.contract_version = original
        service.engine.flow.threshold += 1
        self.assertEqual(self.recommend().status_code, 503)
        service.engine.flow.threshold -= 1
        service.engine.roles["admin"].clear()
        self.assertEqual(self.recommend().status_code, 503)

    def test_policy_source_or_analysis_outage_returns_no_signed_allow(self):
        with patch(
            "analytics.decisions.load_json",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            response = self.recommend()
        self.assertEqual(response.json(), {"detail": "POLICY_UNAVAILABLE"})
        with patch.object(
            self.app.state.decisions.engine,
            "evaluate",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            response = self.recommend()
        self.assertEqual(response.json(), {"detail": "ANALYSIS_UNAVAILABLE"})
        self.assertNotIn("SYNTHETIC_SECRET", response.text)
        self.assertNotIn("signature", response.text)

    def test_clock_rollback_cannot_extend_policy_lease(self):
        self.now -= timedelta(seconds=1)
        self.assertEqual(self.recommend().json(), {"detail": "POLICY_STALE"})

    def test_code_digest_binds_file_boundaries_not_just_concatenated_bytes(self):
        def contents(first, second):
            return lambda path: {"app.py": first, "audit.py": second}.get(
                path.name, b""
            )

        with patch(
            "analytics.decisions.Path.read_bytes",
            autospec=True,
            side_effect=contents(b"a", b"bc"),
        ):
            first = rules_digest()
        with patch(
            "analytics.decisions.Path.read_bytes",
            autospec=True,
            side_effect=contents(b"ab", b"c"),
        ):
            self.assertNotEqual(first, rules_digest())

    def test_malformed_nonstring_owner_is_unknown_not_a_false_bola_finding(self):
        engine = self.app.state.decisions.engine
        engine.orders["order-1001"]["owner_id"] = 42
        result = engine.evaluate(self.observation)
        self.assertEqual(result.reason_code, "CONTEXT_UNAVAILABLE")
        self.assertIsNone(result.finding_class)

    def summary(self):
        return {
            **self.app.state.normalizer.normalize("GET", "/orders").to_dict(),
            "status_code": 200,
        }

    def test_storage_gate_rejects_extra_secret_fields_without_mutation(self):
        for field in (
            "authorization",
            "cookie",
            "request_target",
            "body",
            "actor_id",
            "tenant_id",
        ):
            summary = {**self.summary(), field: "SYNTHETIC_SECRET"}
            with self.assertRaises(StoreError) as failure:
                self.app.state.store.append(
                    [("synthetic", uuid4(), "opaque_digest", summary)], self.now
                )
            self.assertEqual(str(failure.exception), "MASKING_REJECTED")
        self.assertEqual(self.app.state.store.snapshot(self.now), [])

    def test_masking_is_deterministic_and_no_raw_unregistered_route_is_stored(self):
        masker = self.app.state.store.masker
        self.assertEqual(masker.project(self.summary()), masker.project(self.summary()))
        malformed = {**self.summary(), "route": "/orders/SYNTHETIC_PERSON"}
        with self.assertRaises(StoreError):
            self.app.state.store.append(
                [("synthetic", uuid4(), "digest", malformed)], self.now
            )

    def test_nested_alert_fields_are_not_a_redaction_bypass(self):
        summary = self.summary()
        summary["alert"] = {
            "finding_id": str(uuid4()),
            "finding_class": "shadow_candidate",
            "reason_code": "PATH_NOT_IN_CONTRACT",
            "cookie": "SYNTHETIC_SECRET",
        }
        with self.assertRaises(StoreError):
            self.app.state.store.append(
                [("synthetic", uuid4(), "digest", summary)], self.now
            )

    def test_snapshot_cannot_mutate_retained_nested_alert(self):
        store = self.app.state.store
        summary = {
            **self.app.state.normalizer.normalize("GET", "/synthetic/new").to_dict(),
            "status_code": 200,
            "alert": {
                "finding_id": str(uuid4()),
                "finding_class": "shadow_candidate",
                "reason_code": "PATH_NOT_IN_CONTRACT",
            },
        }
        store.append([("synthetic", uuid4(), store.digest(summary), summary)], self.now)
        snapshot = store.snapshot(self.now)
        before = copy.deepcopy(snapshot)
        snapshot[0]["alert"]["reason_code"] = "SYNTHETIC_SECRET"
        self.assertEqual(store.snapshot(self.now), before)

    def test_backend_mask_failure_is_generic_and_does_not_change_fixture_objects(self):
        before = copy.deepcopy(self.app.state.decisions.engine.orders)
        with patch.object(
            self.app.state.decisions.audit.store.masker,
            "project",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            response = self.recommend()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SYNTHETIC_SECRET", response.text)
        self.assertEqual(before, self.app.state.decisions.engine.orders)
