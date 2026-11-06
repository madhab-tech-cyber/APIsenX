"""Disposable PostgreSQL role checks for the Day 20 preparation harness.

Opt-in only. These checks cover the synthetic bootstrap fixture, not the
approved runtime architecture or a complete case-authorization mechanism.
"""

import os
import unittest
import uuid

try:
    import psycopg
except ImportError:  # pragma: no cover - depends on optional test environment
    psycopg = None


ACK = "DISPOSABLE_SYNTHETIC_DATABASE"
SCHEMA = "apisenx_audit_it"
TABLE = f"{SCHEMA}.audit_records"
VIEW = f"{SCHEMA}.case_records"
RECEIPTS = f"{SCHEMA}.deletion_receipts"


def dsn(name):
    return os.environ.get(f"APISENX_PG_{name}_DSN")


@unittest.skipUnless(
    psycopg is not None
    and os.environ.get("APISENX_PG_TEST_ACK") == ACK
    and all(dsn(role) for role in ("WRITER", "READER", "RETENTION", "MIGRATION")),
    "requires optional psycopg, four isolated role DSNs and explicit disposable-DB acknowledgement",
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
                    "VALUES ('forbidden', 'case-a', now(), now() + interval '1 day', '{}')"
                )

    def test_retention_worker_can_delete_and_append_receipt_but_not_read(self):
        record_id = f"retention-{uuid.uuid4()}"
        with self.connect("MIGRATION") as conn:
            conn.execute(
                f"INSERT INTO {TABLE} "
                "(record_id, case_id, received_at, expires_at, summary) "
                "VALUES (%s, %s, now() - interval '2 days', now() - interval '1 day', %s)",
                (record_id, "case-a", psycopg.types.json.Jsonb({"kind": "synthetic"})),
            )
        with self.connect("RETENTION") as conn:
            conn.execute(f"DELETE FROM {TABLE} WHERE record_id = %s", (record_id,))
            conn.execute(
                f"INSERT INTO {RECEIPTS} (receipt_id, record_id, deleted_at, reason_code) "
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
