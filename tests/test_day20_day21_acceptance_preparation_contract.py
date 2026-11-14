"""Static safety contracts for Day 20/21 preparation artifacts.

These tests guard the opt-in PostgreSQL harness and acceptance plans. They do
not execute PostgreSQL, a retention worker, or an integrated runtime.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_repo_file(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class Day20PreparationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read_repo_file("docs/day20-retention-restore-integrity-test-plan.md")
        cls.mock_workflow = read_repo_file(".github/workflows/mock-api-tests.yml")
        cls.day21_plan = read_repo_file(
            "docs/day21-integrated-route-failure-test-plan.md"
        )
        cls.readme = read_repo_file("tests/integration/postgres/README.md")
        cls.role_tests = read_repo_file(
            "tests/integration/postgres/test_postgres_roles.py"
        )
        cls.bootstrap = " ".join(
            read_repo_file("tests/integration/postgres/bootstrap.sql").lower().split()
        )

    def test_retention_plan_pins_each_required_policy_window(self):
        expected_rows = (
            "| RT-03 masked summaries | 7 days |",
            "| RT-04 findings/triage | 30 days |",
            "| RT-05 protected audit/approval/access records | up to 90 days |",
            "| RT-06 investigation exports | 24 hours |",
            "| RT-07 encrypted backups | rolling 7 days |",
        )
        for row in expected_rows:
            with self.subTest(row=row):
                self.assertIn(row, self.plan)

    def test_plan_covers_deletion_hold_restore_and_integrity_failure_modes(self):
        required_sections = (
            "## Deletion and derivative coverage",
            "## Hold and release cases",
            "## Restore and backup re-purge cases",
            "## Integrity checkpoint cases",
            "## Authorization and access-audit cases",
            "## Outage and recovery cases",
        )
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.plan)

        for scenario in (
            "payload tamper",
            "reorder",
            "missing sequence",
            "duplicate/replay",
            "anchor outage",
            "re-purge",
            "fail closed",
        ):
            with self.subTest(scenario=scenario):
                self.assertIn(scenario, self.plan.lower())

    def test_postgres_harness_requires_explicit_disposable_environment(self):
        self.assertIn("DISPOSABLE_SYNTHETIC_DATABASE", self.role_tests)
        self.assertIn("skipUnless", self.role_tests)
        self.assertIn("role_dsns_are_isolated()", self.role_tests)
        self.assertIn("conninfo_to_dict", self.role_tests)
        self.assertIn("configs[role].get(\"user\") != expected_user", self.role_tests)
        self.assertIn("rolsuper, rolcreatedb, rolcreaterole", self.role_tests)
        self.assertIn("rolreplication, rolbypassrls", self.role_tests)
        self.assertIn("WITH RECURSIVE memberships(role_oid)", self.role_tests)
        self.assertIn("all inherited role memberships", self.readme)
        self.assertIn("config.get(\"dbname\")", self.role_tests)
        self.assertIn(
            "role-specific DSNs targeting the same disposable database",
            self.role_tests,
        )
        for role in ("WRITER", "READER", "RETENTION", "MIGRATION"):
            self.assertIn(f"APISENX_PG_{role}_DSN", self.readme)
        for username in (
            "apisenx_it_writer",
            "apisenx_it_reader",
            "apisenx_it_retention",
            "apisenx_it_migration",
        ):
            with self.subTest(username=username):
                self.assertIn(username, self.readme)

    def test_postgres_preflight_requires_explicit_tls_target_without_service_aliases(
        self,
    ):
        required_role_guard = (
            "TLS_MODES",
            'for option in ("service", "servicefile")',
            'not any(config.get(field) for field in ("host", "hostaddr"))',
            'not _is_single_endpoint_value(config.get("port"))',
            'def _is_single_endpoint_value(value):',
            'for field in ("host", "hostaddr")',
            'not _is_single_endpoint_value(config.get(field))',
            'str(config.get("sslmode", "")).lower() not in TLS_MODES',
            '_is_plain_database_name(config.get("dbname"))',
            'getattr(conn.info, "ssl_in_use", False)',
            "def connect_tls(role):",
        )
        for requirement in required_role_guard:
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.role_tests)

        readme = " ".join(self.readme.lower().split())
        self.assertIn("sslmode", readme)
        self.assertIn("`service` or `servicefile`", readme)
        self.assertIn("negotiated tls", readme)
        self.assertIn("comma-separated multi-host", readme.lower())
        self.assertIn("one unambiguous endpoint", readme.lower())
        self.assertIn(
            "uri or conninfo strings embedded in `dbname` are rejected",
            readme,
        )

        day20 = " ".join(self.plan.lower().split())
        self.assertIn("uri/conninfo strings embedded in `dbname`", day20)

        day21 = " ".join(self.day21_plan.lower().split())
        self.assertIn("comma-separated host/hostaddr/port values", day20)
        self.assertIn("ssl_in_use=true", day21)
        self.assertIn(
            "skipped role test or non-tls connection is blocked, not pass",
            day21,
        )

    def test_postgres_harness_unit_suite_runs_in_mock_api_ci(self):
        normalized = " ".join(self.mock_workflow.split())
        self.assertIn(
            "Run disposable PostgreSQL harness guard and retention tests",
            normalized,
        )
        command = (
            "python -m unittest discover -s tests/integration/postgres "
            "-p 'test_*.py' -v"
        )
        self.assertIn(command, normalized)

    def test_postgres_bootstrap_revokes_public_and_grants_narrow_roles(self):
        expected_grants = (
            "grant insert on apisenx_audit_it.audit_records to apisenx_it_writer;",
            "grant select on apisenx_audit_it.case_records to apisenx_it_reader;",
            "grant execute on function "
            "apisenx_audit_it.purge_expired_record(text, text) "
            "to apisenx_it_retention;",
        )
        self.assertTrue(self.bootstrap.startswith("-- test only:"))
        self.assertIn("begin;", self.bootstrap)
        self.assertTrue(self.bootstrap.rstrip().endswith("commit;"))
        self.assertIn(
            "revoke all on schema apisenx_audit_it from public;", self.bootstrap
        )
        self.assertIn(
            "revoke all on all tables in schema apisenx_audit_it from public;",
            self.bootstrap,
        )
        for grant in expected_grants:
            with self.subTest(grant=grant):
                self.assertIn(grant, self.bootstrap)

        self.assertNotIn("grant all", self.bootstrap)
        self.assertNotIn("grant update", self.bootstrap)
        self.assertNotIn(
            "grant delete on apisenx_audit_it.audit_records to apisenx_it_retention",
            self.bootstrap,
        )
        self.assertNotIn(
            "grant insert on apisenx_audit_it.deletion_receipts to "
            "apisenx_it_retention",
            self.bootstrap,
        )
        self.assertIn("security definer", self.bootstrap)
        self.assertIn("set search_path = pg_catalog", self.bootstrap)
        self.assertIn("expires_at <= statement_timestamp()", self.bootstrap)
        self.assertIn(
            "create function apisenx_audit_it.purge_expired_record(", self.bootstrap
        )
        self.assertIn("security definer", self.bootstrap)
        self.assertIn("set search_path = pg_catalog", self.bootstrap)
        self.assertIn(
            "insert into apisenx_audit_it.deletion_receipts", self.bootstrap
        )
        self.assertIn("get diagnostics deleted_count = row_count", self.bootstrap)
        self.assertIn(
            "grant execute on function "
            "apisenx_audit_it.purge_expired_record(text, text) "
            "to apisenx_it_retention;",
            self.bootstrap,
        )
        self.assertIn(
            "revoke all on function "
            "apisenx_audit_it.purge_expired_record(text, text) from public;",
            self.bootstrap,
        )
        self.assertIn(
            "test_retention_worker_cannot_purge_unexpired_rows", self.role_tests
        )
        self.assertIn(
            "test_receipt_conflict_rolls_back_expired_record_deletion",
            self.role_tests,
        )
        self.assertNotIn(
            "grant select on apisenx_audit_it.audit_records to apisenx_it_reader",
            self.bootstrap,
        )

    def test_reader_view_caveat_is_explicit_and_not_misrepresented_as_rbac(self):
        self.assertIn("current_setting('app.case_id', true)", self.bootstrap)
        self.assertIn("caller-settable", self.readme.lower())
        self.assertIn("not an authorization control", self.readme.lower())
        self.assertIn("authenticated, case-scoped grant", self.plan.lower())

    def test_preparation_does_not_claim_runtime_acceptance(self):
        self.assertIn("test-plan preparation only", self.plan.lower())
        self.assertIn("a skipped test", self.plan.lower())
        self.assertIn(
            "no checkbox above is complete by virtue of this plan",
            self.plan.lower(),
        )


class Day21IntegratedFailurePlanContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read_repo_file("docs/day21-integrated-route-failure-test-plan.md")
        cls.policy = read_repo_file("docs/route-failure-policy.md")

    def test_plan_covers_all_five_policy_routes(self):
        route_rows = {
            match.group(1)
            for line in self.plan.splitlines()
            if (match := re.match(r"^\|\s*\*{0,2}(RF-\d{2})\b", line))
        }
        self.assertEqual(
            route_rows, {f"RF-{number:02d}" for number in range(1, 6)}
        )
        for route_id in route_rows:
            self.assertIn(route_id, self.policy)

    def test_plan_covers_dependency_faults_and_restart_recovery(self):
        required_faults = (
            "identity/policy/context provider timeout",
            "optional observer/detector timeout",
            "malformed, stale, unknown or replayed",
            "queue/capacity exhausted",
            "durable audit append timeout",
            "process interruption",
            "restart followed by dependency recovery",
        )
        for fault in required_faults:
            with self.subTest(fault=fault):
                self.assertIn(fault, self.plan.lower())

    def test_privileged_routes_fail_closed_before_side_effects(self):
        normalized = " ".join(self.plan.lower().split())
        self.assertIn("rf-03", normalized)
        self.assertIn("generic 503 before mutation", normalized)
        self.assertIn("rf-04", normalized)
        self.assertIn("generic 503 before privileged data delivery", normalized)
        self.assertIn("no partial response", normalized)
        self.assertIn("no duplicate mutation", normalized)

    def test_plan_preserves_authority_privacy_and_release_boundaries(self):
        normalized = " ".join(self.plan.lower().split())
        self.assertIn("server-side authorization result", normalized)
        self.assertIn("raw path, query values, credentials", normalized)
        self.assertIn("monitor-only", normalized)
        self.assertIn("telemetry-only", normalized)
        self.assertIn("active enforcement rules at zero", normalized)
        self.assertIn("release **not approved**", normalized)
        self.assertIn("issue #83", normalized)
        self.assertIn("issue #102", normalized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
