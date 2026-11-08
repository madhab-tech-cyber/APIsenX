"""Regression guards for the newly issued Day 20 architecture decision.

These checks prevent an architecture decision from being mistaken for owner
approval or independent review. They do not connect to PostgreSQL, provision
infrastructure, or constitute implementation acceptance.
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
            "role issuing this record: member 1",
            "not the service-owner approval",
            "not an independent review",
            "approval is not inferred from a pr merge",
            "both remain required",
            "until both are recorded",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.decision)

    def test_selected_architecture_and_rejected_candidate_are_unambiguous(self):
        for required in (
            "adopt the postgresql design",
            "sqlite `durablestore` candidate is not selected",
            "at most seven days",
            "rt-05's 90-day class",
            "auditwriter keeps defaulting to `memorystore`",
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
            "separate dated service-owner and independent-reviewer implementation acceptance",
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
            "service owner records a dated storage architecture",
            "independent reviewer records a separate architecture review",
            "approved durable audit implementation and schema/migration version are deployed",
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
        self.assertIn("do not generalize rf-01/rf-02 ordinary owner-read degradation", self.plan)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
