-- TEST ONLY: apply solely to a disposable synthetic integration database.
-- Provision these roles out-of-band before applying this file:
--   apisenx_it_writer, apisenx_it_reader, apisenx_it_retention,
--   apisenx_it_migration
-- Run as an administrator. The migration role owns this isolated schema.
-- The case_records view is a query-shape fixture only: app.case_id is caller-
-- supplied in this harness and is NOT an authorization boundary. A production
-- implementation needs authenticated case grants and trusted server context.

CREATE SCHEMA apisenx_audit_it AUTHORIZATION apisenx_it_migration;

SET ROLE apisenx_it_migration;

CREATE TABLE apisenx_audit_it.audit_records (
    record_id text PRIMARY KEY,
    case_id text NOT NULL,
    received_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    summary jsonb NOT NULL,
    CHECK (expires_at > received_at)
);

CREATE TABLE apisenx_audit_it.deletion_receipts (
    receipt_id text PRIMARY KEY,
    record_id text NOT NULL,
    deleted_at timestamptz NOT NULL,
    reason_code text NOT NULL
);

CREATE VIEW apisenx_audit_it.case_records
WITH (security_barrier = true) AS
SELECT record_id, case_id, received_at, expires_at, summary
FROM apisenx_audit_it.audit_records
WHERE case_id = current_setting('app.case_id', true);

RESET ROLE;

REVOKE ALL ON SCHEMA apisenx_audit_it FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA apisenx_audit_it FROM PUBLIC;

GRANT USAGE ON SCHEMA apisenx_audit_it
    TO apisenx_it_writer, apisenx_it_reader, apisenx_it_retention;
GRANT INSERT ON apisenx_audit_it.audit_records TO apisenx_it_writer;
GRANT SELECT ON apisenx_audit_it.case_records TO apisenx_it_reader;
GRANT DELETE ON apisenx_audit_it.audit_records TO apisenx_it_retention;
GRANT INSERT ON apisenx_audit_it.deletion_receipts TO apisenx_it_retention;
