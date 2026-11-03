"""Days 11–15 and 19: labelled outcomes, context failures and heuristic limits."""

import copy
import json
import secrets
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from analytics.detection import Observation
from analytics.evaluate import CORPUS, execute_case, measure
from analytics.flow import FlowMonitor


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads(CORPUS.read_text())["cases"]
        self.now = datetime.now(timezone.utc)

    def test_all_self_labelled_cases_with_indeterminate_context_separate(self):
        self.assertEqual(len(self.cases), 34)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                result, _ = execute_case(case, self.now)
                actual = (
                    "indeterminate"
                    if result.expected_access == "unavailable"
                    and result.finding_class is None
                    else result.finding_class
                )
                self.assertEqual(actual, case["expected"])

    def test_function_gate_does_not_depend_on_inventory_shape(self):
        for identifier in ("BFLA-02", "BFLA-03", "BFLA-04"):
            case = next(case for case in self.cases if case["id"] == identifier)
            result, _ = execute_case(case)
            self.assertEqual(
                (result.rule_id, result.finding_class), ("DET-BFLA-1", "bfla_candidate")
            )

    def test_query_data_and_encoded_same_id_do_not_change_ownership(self):
        base = self.cases[0]
        for target in (
            "/orders/order-1001?role=admin&owner=synthetic_other",
            "/orders/order%2d1001",
            "/%6Frders/order-1001",
        ):
            result, _ = execute_case({**base, "target": target})
            self.assertEqual(result.reason_code, "AUTHORIZED_OPERATION")

    def test_changed_id_requires_updated_context_and_cannot_grant_access(self):
        base = self.cases[0]
        result, _ = execute_case({**base, "target": "/orders/order-1002"})
        self.assertEqual(result.reason_code, "CONTEXT_CONFLICT")
        result, _ = execute_case(
            {**base, "target": "/orders/order-1002", "object": "order-1002"}
        )
        self.assertEqual(result.finding_class, "bola_candidate")

    def test_policy_outage_has_no_false_finding(self):
        with patch(
            "analytics.detection.authorize",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            result, _ = execute_case(self.cases[0])
        self.assertEqual(result.reason_code, "CONTEXT_UNAVAILABLE")
        self.assertNotIn("SYNTHETIC_SECRET", repr(result))

    def test_zero_denominators_are_unavailable_not_perfect_accuracy(self):
        counts = measure([])
        self.assertIsNone(counts["precision"])
        self.assertIsNone(counts["recall"])
        self.assertIsNone(counts["false_positive_rate"])

    def test_false_positives_negatives_and_unknowns_not_hidden(self):
        counts = measure(
            [
                (None, "bola_candidate", False),
                ("bola_candidate", None, False),
                ("bola_candidate", None, True),
                ("indeterminate", None, True),
            ]
        )
        self.assertEqual(
            (counts["fp"], counts["fn"], counts["tn"], counts["indeterminate"]),
            (1, 2, 0, 2),
        )

    def test_wrong_class_reports_spurious_and_missed_finding(self):
        counts = measure([("bola_candidate", "bfla_candidate", False)])
        self.assertEqual(
            (counts["fp"], counts["fn"], counts["unexpected_findings"]), (1, 1, 1)
        )

    def test_corpus_execution_does_not_mutate_shipped_fixtures(self):
        from src.authorization import load_orders, load_users

        before = copy.deepcopy((load_users(), load_orders()))
        for case in self.cases:
            execute_case(case)
        self.assertEqual(before, (load_users(), load_orders()))


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.flow = FlowMonitor(secrets.token_bytes(32), threshold=3, capacity=2)
        self.observation = Observation(
            uuid4(),
            self.now,
            "PATCH",
            "/orders/order-1001",
            "admin-1",
            "order-1001",
            200,
        )

    def test_threshold_n_minus_one_n_plus_one_and_retry_stability(self):
        for index in range(4):
            observation = replace(self.observation, event_id=uuid4())
            state = self.flow.observe(observation, "lab-tenant")
            self.assertEqual(state, "quiet" if index < 3 else "burst")
        self.assertEqual(self.flow.observe(observation, "lab-tenant"), "burst")

    def test_same_event_retry_does_not_consume_flow_budget(self):
        for _ in range(10):
            self.assertEqual(self.flow.observe(self.observation, "lab-tenant"), "quiet")
        self.assertEqual(len(next(iter(self.flow._buckets.values()))), 1)

    def test_subject_tenant_isolation_and_state_hmac_excludes_identity(self):
        self.flow.observe(self.observation, "lab-tenant")
        self.flow.observe(replace(self.observation, event_id=uuid4()), "other-tenant")
        self.assertEqual(len(self.flow._buckets), 2)
        self.assertNotIn("admin-1", repr(self.flow._buckets))
        self.assertNotIn("tenant", repr(self.flow._buckets))

    def test_capacity_is_unavailable_not_an_evicted_fresh_budget(self):
        for actor in ("a", "b"):
            self.flow.observe(
                replace(self.observation, event_id=uuid4(), actor_id=actor), "lab"
            )
        self.assertEqual(
            self.flow.observe(
                replace(self.observation, event_id=uuid4(), actor_id="c"), "lab"
            ),
            "unavailable",
        )
        self.assertEqual(len(self.flow._buckets), 2)

    def test_window_expiry_recovers_and_clock_rollback_is_unavailable(self):
        self.flow.observe(self.observation, "lab")
        future = replace(
            self.observation,
            event_id=uuid4(),
            observed_at=self.now + timedelta(seconds=60),
        )
        self.assertEqual(self.flow.observe(future, "lab"), "quiet")
        self.assertEqual(self.flow.observe(self.observation, "lab"), "unavailable")

    def test_invalid_configuration_fails(self):
        with self.assertRaises(ValueError):
            FlowMonitor(b"short")

    def test_idle_purge_removes_restricted_flow_state(self):
        self.flow.observe(self.observation, "lab")
        self.flow.purge(self.now + timedelta(seconds=60))
        self.assertFalse(self.flow._events)
        self.assertFalse(self.flow._buckets)
