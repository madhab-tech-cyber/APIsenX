"""Regression guards for Day 20/21 human-decision and runtime boundaries.

These checks reconcile recorded architecture decisions without treating a
conditional review, documentation change, or CI result as runtime acceptance.
They do not connect to PostgreSQL or provision infrastructure.
"""

import unittest
from pathlib import Path

from analytics.audit import AuditWriter
from analytics.store import MemoryStore

ROOT = Path(__file__).resolve().parents[1]


def read_repo_file(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def normalized(value):
    return " ".join(value.lower().split())


class Day20ArchitectureDecisionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = normalized(
            read_repo_file("docs/day20-durable-audit-architecture-decision.md")
        )
        cls.template = normalized(
            read_repo_file("docs/day20-storage-approval-record-template.md")
        )
        cls.plan = normalized(
            read_repo_file("docs/day20-retention-restore-integrity-test-plan.md")
        )

    def test_architecture_record_is_not_human_approval(self):
        for required in (
            "**role issuing this record:** member 1",
            "**not** the service-owner approval",
            "**not** an independent review",
            "approval is not inferred from a pr merge",
            "reviewer closure confirmation remains **pending**",
            "runtime authorization: blocked",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.decision)

    def test_selected_architecture_and_rejected_candidate_are_unambiguous(self):
        for required in (
            "adopt the postgresql design",
            "sqlite `durablestore` candidate is **not** selected",
            "at most seven days",
            "rt-05's 90-day class",
            "`auditwriter` keeps defaulting to `memorystore`",
            "no default changes as part of this decision",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.decision)

    def test_architecture_record_covers_all_eight_control_domains(self):
        for required in (
            "1. **hosting, ownership, isolation, capacity, availability.**",
            "2. **tls, encryption, keys.**",
            "3. **identities and permissions.**",
            "4. **checkpoints and immutable destination.**",
            "5. **backups and restore.**",
            "6. **retention, deletion, exports, holds.**",
            "7. **incident response, outage, ownership, cost.**",
            "8. **release posture.**",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.decision)

    def test_approval_template_requires_separate_owner_and_reviewer_records(self):
        for required in (
            "decision: approve / approve with amendments / reject",
            "service owner (github handle or role)",
            "independent reviewer (github handle or role; must be a different person)",
            "## required service-owner decisions",
            "## independent review",
            "## implementation acceptance",
            "## release gate",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.template)

    def test_current_owner_reviewer_and_a6_decisions_are_not_overstated(self):
        for required in (
            "recorded decision: approve",
            "approve with amendments / clarifications",
            "reviewer closure of all six findings: pending",
            "100,000 synthetic audit events",
            "rolling 7 days",
            "lab-hours only, single instance, no ha",
            "rpo: 15 minutes maximum",
            "rto: 4 business hours",
            "remaining a6 targets remain unapproved",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.template)

    def test_runtime_default_stays_volatile_and_injection_seam_is_preserved(self):
        key = b"day20-architecture-contract-test-key"
        default_writer = AuditWriter(key)
        self.assertIsInstance(default_writer.store, MemoryStore)

        injected_store = object()
        injected_writer = AuditWriter(key, store=injected_store)
        self.assertIs(injected_writer.store, injected_store)

    def test_day20_plan_does_not_claim_runtime_acceptance(self):
        for required in (
            "test-plan preparation only",
            "a skipped test",
            "no checkbox above is complete by virtue of this plan",
            "dated service-owner architecture and operating-model decision",
            "separate independent architecture review",
            "separate service-owner implementation acceptance and "
            "independent reviewer acceptance",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.plan)


class Day21IntegratedExecutionGateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = normalized(
            read_repo_file("docs/day21-integrated-route-failure-test-plan.md")
        )

    def test_integrated_execution_requires_owner_and_independent_decisions(self):
        for required in (
            "preparation only — no integrated runtime execution is claimed",
            "service-owner architecture decision: **approve**",
            "reviewer closure confirmation remains pending",
            "service owner confirms or amends the remaining a6 objectives",
            "approved durable audit implementation and "
            "schema/migration version are deployed",
            "do not run the integrated cases until all of the following are evidenced",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.plan)

    def test_route_specific_audit_failure_rules_remain_distinct(self):
        self.assertIn("rf-03", self.plan)
        self.assertIn("generic 503 before mutation", self.plan)
        self.assertIn("rf-04", self.plan)
        self.assertIn("generic 503 before privileged data delivery", self.plan)
        self.assertIn(
            "ordinary owner read may continue with visible audit degradation",
            self.plan,
        )
        self.assertIn(
            "do not generalize rf-01/rf-02 ordinary owner-read degradation",
            self.plan,
        )

    def test_evidence_template_does_not_claim_a_human_run(self):
        for required in (
            "evidence record — fill only after a real run",
            "operator and independent witness",
            "service-owner decision",
            "independent-reviewer decision",
            "no route is accepted until its required cases have exact-sha evidence",
            "keep ap-1.0 `monitor_only`",
            "release **not approved**",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.plan)


class Day20Day21StatusReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = normalized(
            read_repo_file("docs/day20-day21-cross-component-status.md")
        )

    def test_status_uses_the_actual_merged_main_commit(self):
        self.assertIn("ac73eb0d7ec8aedf2ca2c3b5708c68f4089d7dbc", self.status)
        self.assertIn("pr #139 is **merged**, not open", self.status)
        self.assertNotIn("pr #139 remains open and unmerged", self.status)

    def test_pr_head_checks_are_not_misrepresented_as_post_merge_checks(self):
        self.assertIn("these are **pr-head** results", self.status)
        self.assertIn("no post-merge check result is asserted here", self.status)
        for run_id in (
            "42443973096",
            "42443973011",
            "42443972831",
            "42443972811",
        ):
            with self.subTest(run_id=run_id):
                self.assertIn(run_id, self.status)

    def test_day20_and_day21_remain_open_and_unaccepted(self):
        self.assertIn("issue #83", self.status)
        self.assertIn("issue #102", self.status)
        self.assertIn("remains open", self.status)
        self.assertIn("service-owner", self.status)
        self.assertIn("independent architecture review", self.status)
        self.assertIn("no exact-sha live route-failure", self.status)
        self.assertIn("reviewer’s separate closure decision remains **pending**", self.status)
        self.assertIn("remaining a6 rpo/rto", self.status)

    def test_latest_main_ci_and_owner_targets_are_pinned(self):
        self.assertIn("758bc24aba9b81c41d74d83863106340bf94b46e", self.status)
        for run_id in ("42668765244", "42668764633", "42668765043"):
            with self.subTest(run_id=run_id):
                self.assertIn(run_id, self.status)
        self.assertIn("100,000 synthetic audit events", self.status)
        self.assertIn("rolling 7-day backups", self.status)
        self.assertIn("lab-hours availability on one instance with no ha", self.status)

    def test_closed_release_gate_is_reopened_without_claiming_acceptance(self):
        self.assertIn("issue #89", self.status)
        self.assertIn("it was reopened on 2026-11-09", self.status)
        self.assertIn("every release requirement pending", self.status)
        self.assertIn("release **not approved**", self.status)
        self.assertIn("no admin/maintain permission", self.status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
