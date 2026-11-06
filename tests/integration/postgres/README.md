# Member 5 — isolated PostgreSQL audit contract harness

**Status: preparation only.** This is a disposable synthetic test schema, not the approved Day 20 runtime schema or an architecture decision. It must never point at production or a shared environment.

## Safety and prerequisites

- Use a dedicated, disposable PostgreSQL database created for this integration test.
- Install the optional driver in the test environment: `python -m pip install "psycopg[binary]>=3.2,<4"`. It is intentionally not added to the application requirements.
- Apply `bootstrap.sql` using a database administrator only in that disposable database.
- Supply four independently provisioned connection strings through environment variables: `APISENX_PG_WRITER_DSN`, `APISENX_PG_READER_DSN`, `APISENX_PG_RETENTION_DSN`, and `APISENX_PG_MIGRATION_DSN`.
- Do not place DSNs, passwords, hostnames, certificates, or key material in Git, command output, test reports, or issue comments.
- The test suite refuses to run unless `APISENX_PG_TEST_ACK=DISPOSABLE_SYNTHETIC_DATABASE` is set. It only uses the fixed `apisenx_audit_it` schema and synthetic identifiers.

## Bootstrap roles

Create the four login roles out-of-band, with credentials injected into the test runner environment. The migration role must own the test schema. Apply the SQL file as an administrator after the roles exist. Never reuse application or production roles.

The bootstrap grants:
- writer: insert only into the audit test table;
- reader: select only through a case-filtered view using transaction-local `app.case_id`;
- retention worker: delete expired test rows and append deletion receipts;
- migration: schema ownership/DDL for this isolated test schema.

## Run

From repository root:

```powershell
python -m unittest discover -s tests/integration/postgres -p 'test_*.py' -v
```

Tests are skipped when optional psycopg or the required environment is absent. A skip is **not** a pass or evidence of database integration.

## What this harness proves — and does not prove

It checks isolated role boundaries and a case-filtered reader-view query shape against a disposable PostgreSQL schema. The test session variable is caller-settable, so this view is deliberately NOT an authorization control. The retention contract tests validate the policy's UTC boundary arithmetic only; they do not prove a running retention worker. Deletion receipts, derivative/export/backup deletion, hold/release, restore-time re-purge, external signed checkpoints, outage/recovery and the approved service's exact schema still require implementation-specific integration tests after the service owner approves the architecture.