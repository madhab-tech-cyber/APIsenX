# Member 5 — isolated PostgreSQL audit contract harness

**Status: preparation only.** This is a disposable synthetic test schema, not the approved Day 20 runtime schema or an architecture decision. It must never point at production or a shared environment.

## Safety and prerequisites

- Use a dedicated, disposable PostgreSQL database created for this integration test.
- Install the optional driver in the test environment: `python -m pip install "psycopg[binary]>=3.2,<4"`. It is intentionally not added to the application requirements.
- Apply `bootstrap.sql` using a database administrator only in that disposable database.
- The bootstrap is wrapped in one transaction so the SECURITY DEFINER function's default PUBLIC EXECUTE grant is revoked before any schema/function privilege change becomes visible; abort the entire bootstrap on any error.
- Supply four independently provisioned connection strings through environment variables: `APISENX_PG_WRITER_DSN`, `APISENX_PG_READER_DSN`, `APISENX_PG_RETENTION_DSN`, and `APISENX_PG_MIGRATION_DSN`.
- The DSNs must explicitly identify these distinct login roles: `apisenx_it_writer`, `apisenx_it_reader`, `apisenx_it_retention`, and `apisenx_it_migration`. All four must target the same explicitly named disposable database.
- Each DSN must explicitly provide its expected role username, `host` or `hostaddr`, `port`, a plain database name, and a TLS-only `sslmode` (`require`, `verify-ca`, or `verify-full`). URI or conninfo strings embedded in `dbname` are rejected because libpq can interpret them as connection options and override the apparent target. `prefer`, `allow`, `disable`, and a missing TLS mode are rejected because they can permit a cleartext connection.
- Do not use libpq `service` or `servicefile` indirection: the harness rejects those options so the endpoint cannot be hidden outside the DSN. All four DSNs must resolve to the same explicit host/host-address/port/database tuple. After connecting, the suite checks PostgreSQL's `current_user`, rejects superuser/database-creation/role-creation/replication/BYPASSRLS attributes and all inherited role memberships, and verifies negotiated TLS with `conn.info.ssl_in_use`. It does not print DSNs or parser errors.
- Prefer `sslmode=verify-full` with the approved CA configuration. `require` and `verify-ca` are accepted only where the isolated lab's certificate model calls for them. Do not place DSNs, passwords, hostnames, certificates, or key material in Git, command output, test reports, or issue comments.
- The test suite refuses to run unless `APISENX_PG_TEST_ACK=DISPOSABLE_SYNTHETIC_DATABASE` is set. It only uses the fixed `apisenx_audit_it` schema and synthetic identifiers.

## Bootstrap roles

Create the four login roles out-of-band, with credentials injected into the test runner environment. The migration role must own the test schema. Apply the SQL file as an administrator after the roles exist. Never reuse application or production roles.

The bootstrap grants:
- writer: insert only into the audit test table;
- reader: select only through a case-filtered view using transaction-local `app.case_id`;
- retention worker: execute only the narrowly scoped `purge_expired_record(record_id, receipt_id)` function. It atomically deletes a row only when `expires_at <= statement_timestamp()` and inserts the matching `RETENTION_EXPIRED` receipt; it receives no direct table `DELETE`, receipt `INSERT`, or content `SELECT` privilege;
- migration: schema ownership/DDL for this isolated test schema.

## Run

From repository root:

```powershell
python -m unittest discover -s tests/integration/postgres -p 'test_*.py' -v
```

Tests are skipped when optional psycopg or the required environment is absent. A skip is **not** a pass or evidence of database integration.

## What this harness proves — and does not prove

It checks isolated role boundaries, an atomic expiry-guarded purge function, and a case-filtered reader-view query shape against a disposable PostgreSQL schema. The test session variable is caller-settable, so this view is deliberately NOT an authorization control. The retention contract tests validate the policy's UTC boundary arithmetic only; they do not prove a running retention worker. Deletion receipts, derivative/export/backup deletion, hold/release, restore-time re-purge, external signed checkpoints, outage/recovery and the approved service's exact schema still require implementation-specific integration tests after the service owner approves the architecture.
