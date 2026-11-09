"""Disposable PostgreSQL role checks for the Day 20 preparation harness.

Opt-in only. These checks cover the synthetic bootstrap fixture, not the
approved runtime architecture or a complete case-authorization mechanism.
"""

import os
import unittest
import uuid
from unittest.mock import patch

try:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
except ImportError:  # pragma: no cover - depends on optional test environment
    psycopg = None
    conninfo_to_dict = None


ACK = "DISPOSABLE_SYNTHETIC_DATABASE"
SCHEMA = "apisenx_audit_it"
TABLE = f"{SCHEMA}.audit_records"
VIEW = f"{SCHEMA}.case_records"
RECEIPTS = f"{SCHEMA}.deletion_receipts"
ROLE_USERS = {
    "WRITER": "apisenx_it_writer",
    "READER": "apisenx_it_reader",
    "RETENTION": "apisenx_it_retention",
    "MIGRATION": "apisenx_it_migration",
}


def dsn(name):
    return os.environ.get(f"APISENX_PG_{name}_DSN")


def role_dsns_are_isolated():
    """Fail closed unless each DSN names its intended role on one DB target."""
    if (
        psycopg is None
        or conninfo_to_dict is None
        or os.environ.get("APISENX_PG_TEST_ACK") != ACK
    ):
        return False

    values = {role: dsn(role) for role in ROLE_USERS}
    if any(not value for value in values.values()):
        return False

    try:
        configs = {
            role: conninfo_to_dict(value) for role, value in values.items()
        }
    except Exception:  # Never expose connection-string parser details.
        return False

    if any(
        configs[role].get("user") != expected_user
        for role, expected_user in ROLE_USERS.items()
    ):
        return False

    # All four identities must target the same explicitly named disposable DB.
    if any(not config.get("dbname") for config in configs.values()):
        return False
    targets = {
        tuple(config.get(field) for field in ("host", "hostaddr", "port", "dbname"))
        for config in configs.values()
    }
    return len(targets) == 1


class PostgreSQLDsnConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.env = {"APISENX_PG_TEST_ACK": ACK}
        self.configs = {}
        for role, username in ROLE_USERS.items():
            value = f"dsn-{role.lower()}"
            self.env[f"APISENX_PG_{role}_DSN"] = value
            self.configs[value] = {
                "user": username,
                "host": "db.example.test",
                "hostaddr": None,
                "port": "5432",
                "dbname": "apisenx_disposable",
            }

    def run_guard(self):
        def parse(value):
            return self.configs[value]

        with (
            patch.dict(os.environ, self.env, clear=True),
            patch(f"{__name__}.psycopg", new=object()),
            patch(f"{__name__}.conninfo_to_dict", side_effect=parse),
        ):
            return role_dsns_are_isolated()

    def test_accepts_four_expected_roles_on_one_named_database(self):
        self.assertTrue(self.run_guard())

    def test_rejects_reused_or_privileged_login_identity(self):
        self.configs["dsn-writer"]["user"] = "postgres"
        self.assertFalse(self.run_guard())

    def test_rejects_role_dsns_pointing_at_different_databases(self):
        self.configs["dsn-reader"]["dbname"] = "another_database"
        self.assertFalse(self.run_guard())


@unittest.skipUnless(
    role_dsns_are_isolated(),
    "requires psycopg, explicit disposable-DB acknowledgement, and four "
    "role-specific DSNs targeting the same disposable database",
)
class PostgreSQLRoleBoundaryTests(unittest.TestCase):
    def connect(self, role):
        return psycopg.connect(dsn(role), connect_timeout=5)

    def test_writer_can_insert_but_cannot_read_or_mutate_existing_rows(self):
        record_id = f"writer-{uuid.uuid4()}"
        with self.connect("WRITER") as conn:
            conn.execute(
                f"INSERT INTO {TABLE} "
                "(record_id, case_id, received_at, expires_at, summary) "
                "VALUES (%s, %s, now(), now() + interval '1 day', %s)",
                (record_id, "case-a", psycopg.types.json.Jsonb({"kind": "synthetic"})),
            )
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute(f"SELECT record_id FROM {TABLE}")
            conn.rollback()

    def test_reader_view_filters_by_supplied_case_context_and_cannot_write(self):
        record_id = f"reader-{uuid.uuid4()}"
        with self.connect("MIGRATION") as conn:
            conn.execute(
                f"INSERT INTO {TABLE} "
                "(record_id, case_id, received_at, expires_at, summary) "
                "VALUES (%s, %s, now(), now() + interval '1 day', %s)",
                (record_id, "case-a", psycopg.types.json.Jsonb({"kind": "synthetic"})),
            )
        with self.connect("READER") as conn:
            conn.execute("SELECT set_config('app.case_id', %s, true)", ("case-a",))
            rows = conn.execute(f"SELECT record_id FROM {VIEW}").fetchall()
            self.assertIn((record_id,), rows)
            conn.execute("SELECT set_config('app.case_id', %s, true)", ("case-b",))
            rows = conn.execute(f"SELECT record_id FROM {VIEW}").fetchall()
            self.assertNotIn((record_id,), rows)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute(
                    f"INSERT INTO {TABLE} "
                    "(record_id, case_id, received_at, expires_at, summary) "
                    "VALUES ('forbidden', 'case-a', now(), "
                    "now() + interval '1 day', '{}')"
                )

    def test_retention_worker_can_delete_and_append_receipt_but_not_read(self):
        record_id = f"retention-{uuid.uuid4()}"
        with self.connect("MIGRATION") as conn:
            conn.execute(
                f"INSERT INTO {TABLE} "
                "(record_id, case_id, received_at, expires_at, summary) "
                "VALUES (%s, %s, now() - interval '2 days', "
                "now() - interval '1 day', %s)",
                (record_id, "case-a", psycopg.types.json.Jsonb({"kind": "synthetic"})),
            )
        with self.connect("RETENTION") as conn:
            conn.execute(f"DELETE FROM {TABLE} WHERE record_id = %s", (record_id,))
            conn.execute(
                f"INSERT INTO {RECEIPTS} "
                "(receipt_id, record_id, deleted_at, reason_code) "
                "VALUES (%s, %s, now(), 'RETENTION_EXPIRED')",
                (f"receipt-{uuid.uuid4()}", record_id),
            )
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute(f"SELECT record_id FROM {TABLE}")

    def test_application_roles_cannot_create_schema_objects(self):
        for role in ("WRITER", "READER", "RETENTION"):
            with self.subTest(role=role), self.connect(role) as conn:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    conn.execute(f"CREATE TABLE {SCHEMA}.forbidden_ddl (id integer)")
