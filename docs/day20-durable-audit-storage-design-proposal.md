# Day 20 durable audit storage design proposal

**Status:** PROPOSAL ONLY — not an approved architecture and not runtime evidence.
**Scope:** Synthetic lab only. No production data or enforcement activation.
**Decision owner:** Service owner, with independent security review.

## Why a decision is required

The current `analytics/audit.py` sends a masked, allowlisted projection to
`MemoryStore`. That store is volatile and bounded. It does not provide durable
append acknowledgement, independent writer/reader identities, durable retention
receipts, protected integrity checkpoints, backup expiry, or restore-time
re-purging. This document proposes a design for review; it does not change the
runtime or claim any of those controls are implemented.

## Proposed storage boundary

1. Keep collection and masking at the application boundary. Reject unknown
   fields and invalid schema before persistence. Never persist raw request
   bodies, bearer/session tokens, cookies, query values, raw unknown paths, or
   real personal data.
2. Use a dedicated PostgreSQL service for the lab's durable audit records, on a
   private network, with TLS and encrypted storage/backups. Keep credentials in
   the deployment secret manager; never commit keys or connection strings.
3. Give the audit-writer identity INSERT-only access to the audit table and
   sequence, with no UPDATE, DELETE, DDL, or read/export permissions. Separate
   reader, retention-worker, and schema-migration identities. Human operators
   must not share the writer credential.
4. Insert each masked event and its server receipt timestamp in one transaction.
   Enforce uniqueness on the opaque event reference. Same-reference/same-digest
   retries are idempotent; same-reference/different-digest attempts are rejected
   and counted without echoing submitted content. Return success only after the
   database transaction commits.
5. Build a hash chain or signed checkpoint over canonical, ordered audit entries.
   Store checkpoint signatures/keys outside the database in an approved KMS or
   equivalent protected key service. Periodically export checkpoint digests to
   a separately administered immutable destination. A hash stored only beside
   the records is not tamper-proof.
6. Keep AP-1.0 in `monitor_only`; the audit service must not itself enable
   enforcement or replace authoritative API authorization.

## Retention and deletion contract

Retention is calculated from the trusted server receipt time, never caller
timestamps. The retention worker runs at least hourly and targets removal of
expired primary records within 24 hours. It writes a minimal deletion receipt
to a separately protected accountability stream, containing only a receipt ID,
retention class, expiry window, completion time, counts and outcome—not the
deleted payload or identifiers that recreate a subject link.

- RT-03 summaries: maximum 7 days.
- RT-04 findings/triage: maximum 30 days unless a specifically approved,
  time-bounded hold applies.
- RT-05 audit/approval/access records: maximum 90 days.
- RT-06 exports: maximum 24 hours, named recipient and approved purpose.
- RT-07 backups: rolling 7 days; never include raw captures or secrets.
- RT-01/RT-02/RT-08 remain governed by the existing policy and are not grounds
  to persist raw data or create a disk spool.

Deletion must cover primary tables, indexes, caches, exports and derivatives.
On restore, isolate the restored copy, replay the current deletion/hold ledger,
re-check expiry, verify integrity checkpoints, and only then permit access.
Backup expiry is verified separately; a row-count reduction is not sufficient
proof of deletion.

## Access and investigation

Use case-scoped grants with explicit role, case, expiry and allowed operations.
Deny by default. Analysts can read only masked records for assigned cases;
they cannot alter records, grant themselves access, or bypass export approval.
Every sensitive read/export and grant/hold change must itself be audited. If
the required access-audit append fails, deny the read/export. Emergency disable
must remain available during an audit outage.

Holds require a named approver, case ID, minimal record scope, reason, custodian,
access list and expiry no later than 30 days. Review weekly; renewal requires a
new approval before expiry. Release/expiry resumes normal deletion.

## Failure and recovery behavior

- Writer/database unavailable: bounded generic failure; no fallback to disk,
  stdout as a durable substitute, or unbounded memory queue.
- Capacity/oversize: reject with bounded reason counters; do not echo payloads.
- Duplicate reference with conflicting digest: reject and emit a sanitized alert.
- Checkpoint verification failure: quarantine the affected evidence set and
  block investigation export pending review; never silently re-sign history.
- Restore: isolated restore, replay expiry/hold state, verify checkpoints and
  run synthetic integrity/retention tests before access is enabled.

## Required approval before implementation

The service owner must explicitly approve or amend: PostgreSQL hosting/ownership,
encryption and key management, writer/reader/retention roles, immutable
checkpoint destination, backup schedule and expiry, incident response, capacity
limits, availability expectations, and operational costs. Independent review
must record objections or approval. Until these decisions are recorded, this
proposal must not be treated as permission to deploy a durable store.

## Verification gates after approval

1. Unit tests: schema allowlist, masking, duplicate idempotency/conflict,
   atomic append, UTC receipt-time expiry boundaries, and bounded inputs.
2. Integration tests against an isolated ephemeral database: role permissions,
   writer cannot read/update/delete, reader cannot mutate, append acknowledgement,
   retention deletion receipts, and database outage behavior.
3. Integrity tests: changed/deleted/reordered records, missing checkpoints,
   invalid signatures, and checkpoint verification after restore.
4. Retention/restore tests: expiry across all derivatives, hold/release,
   backup aging, restore-time re-purge, and no resurrection of expired records.
5. Access tests: cross-case denial, expired grants, export expiry, and fail-closed
   behavior when access-audit append is unavailable.
6. Exact-head CI, dependency/security checks, sanitized test artifacts, service
   owner sign-off and independent reviewer sign-off.

## Current acceptance status

**BLOCKED.** This is a reviewable design proposal only. No durable store,
retention worker, deletion receipt service, KMS-backed checkpoint, or database
RBAC is implemented by this change. Keep AP-1.0 in `monitor_only`, zero active
enforcement rules, and release **NOT APPROVED** until implementation evidence
and the required human decisions are recorded.
