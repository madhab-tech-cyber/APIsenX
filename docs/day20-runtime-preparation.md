# Day 20 runtime preparation — interface map and acceptance contract

**Status: preparation only; not architecture approval or implementation acceptance.**  
**Baseline:** `main` at `f49e720010b931c8dd8d919bf078b603007fb107` (2026-11-06).  
**Scope:** synthetic lab only. Keep AP-1.0 `monitor_only`, active enforcement rules at zero, and release NOT APPROVED.

This note records the existing integration surface and the engineering contract to use after the service owner records a storage decision and a different independent reviewer records an architecture review. It does not select a backend, deploy infrastructure, add credentials, or change runtime behavior.

## 1. Current call-site map

| Area | Current behavior | Preparation consequence |
|---|---|---|
| `analytics/audit.py::AuditWriter` | Accepts an optional `store`; otherwise constructs `MemoryStore(key, capacity, retention_seconds=300, routes=routes)`. | Existing injection seam is useful, but the store protocol is implicit. Keep the volatile default until approval and implementation acceptance. |
| `analytics/decisions.py::DecisionService.__init__` | Constructs `AuditWriter(audit_key, routes=...)` without passing a store. | A future explicit dependency-injection parameter is needed to supply the approved audit backend in tests and deployment. Do not silently change the default. |
| `analytics/decisions.py::DecisionService.issue` | Calls audit append before signing/returning the recommendation; comment says to fail before signing if append is unavailable. | Preserve the acknowledgement boundary: no signed recommendation may be returned until durable append is committed and acknowledged. |
| `analytics/app.py::create_app` | Creates a separate ingestion `MemoryStore`; passes it and the optional decision audit writer to `ManagementService`. Its lifespan purges the ingestion store, audit store, and flow state. | Do not conflate ingestion observations, protected audit records, and access-audit records. Each needs an explicit lifecycle and policy. |
| `analytics/management.py::ManagementService` | Creates a separate volatile `MemoryStore` named `access`; records reader outcomes there. It also reads masked observations and audit rows for investigation views. | Case-scoped access events need a protected append path and fail-closed read/export behavior; current in-memory access history is not durable evidence. |

## 2. Backend-neutral audit-store contract

The implementation should depend on a narrow interface, not SQLite- or PostgreSQL-specific calls:

- `digest(value)`: deterministic keyed digest over the canonical, allowlisted projection. It must not expose key material or accept raw request payloads as persisted content.
- `append(items, received_at)`: validate and mask the entire bounded batch; use trusted server receipt time; enforce idempotency for same event reference/digest and reject conflicting reuse; commit the complete batch atomically; return an acknowledgement only after commit.
- `purge(now)`: run the retention worker's bounded expiry operation using an aware UTC clock. The worker must produce a protected deletion receipt and account for primary data and derivatives.
- A separately authorized investigation-read interface: case-scoped, bounded, read-only queries. It must not be exposed through the writer credential or a public unrestricted snapshot method.
- Stable bounded failure categories only (for example capacity, conflict, unavailable, authorization, and integrity failure). Do not return database exception text, SQL, paths, credentials, or submitted values to callers or logs.

The exact Python protocol, transaction boundaries, schema, and adapter lifecycle remain subject to the approved architecture decision. The current `MemoryStore` and opt-in SQLite candidate are parity references, not evidence that this full contract is met.

## 3. Retention and lifecycle test matrix

Use a controlled server clock and synthetic identifiers only.

| Class | Maximum / behavior | Required evidence |
|---|---|---|
| RT-01 | Raw paths, queries, headers, bodies and captures: no routine persistence | Ingress and export leak-marker tests |
| RT-02 | Volatile normalized queue: 2 seconds, bounded; no disk spool | Exact expiry and bounded-loss behavior |
| RT-03 | Masked summaries: 7 days | Before/at/after expiry; derivative deletion |
| RT-04 | Findings/triage: 30 days unless approved time-bounded hold | Expiry, hold, weekly review, release and renewal |
| RT-05 | Protected audit/approval/access records: up to 90 days | 90-day boundary, deletion receipt, backup aging |
| RT-06 | Investigation exports: 24 hours | Named recipient/purpose, expiry and deletion receipt |
| RT-07 | Encrypted backups: rolling 7 days | Backup expiry and restore-time re-purge |
| RT-08 | Sanitized aggregate policy/review documents: repository lifecycle after disclosure review | Disclosure review; no linkable runtime subject/object data |

Retention starts at trusted server receipt time. Expired primary records must be removed within 24 hours; backups may retain a deleted record no longer than the policy's additional seven-day backup window. A row-count reduction alone is not deletion proof.

## 4. Authorization, integrity, and outage acceptance

- Separate writer, reader, retention-worker, migration, and checkpoint/signing identities. Prove writer cannot read/update/delete/DDL; reader cannot mutate; migration credentials are not used by the application.
- Enforce case-scoped, time-bounded grants and deny-by-default authorization on every read/export. Audit allowed and denied reads, exports, grants, holds, releases, deletion, and restore. If the required access-audit append fails, deny the read/export.
- Use a hash chain or equivalent sequence evidence plus signed checkpoints anchored outside the database under separately administered key custody. Test altered, deleted, reordered, missing, and invalidly signed records/checkpoints. A hash stored only beside mutable rows is insufficient.
- On backend outage, return a bounded generic failure and never acknowledge an uncommitted append. Do not fall back to a disk spool, stdout, or unbounded in-memory queue. Keep emergency disable available.
- Restore into isolation; replay deletion/hold state; re-check retention; verify checkpoints; run synthetic integrity/retention checks before enabling access.

## 5. Required implementation sequence after human decisions

1. Record dated service-owner APPROVE / APPROVE WITH AMENDMENTS / REJECT for hosting/ownership, encryption and key ownership, role separation, checkpoint destination, backup/restore, retention/deletion, incident response, availability/capacity, operating costs, and isolated test environment.
2. Obtain a separate independent architecture review with explicit findings/objections. Do not use the service owner's own approval as independent review.
3. Freeze the approved design version and implement the backend-neutral interface plus the approved adapter. Keep production/default selection unchanged until implementation acceptance.
4. Add isolated integration tests for transaction acknowledgement, database role permissions, all RT boundaries, deletion receipts, derivative/export/backup expiry, hold/release, restore re-purge, case RBAC, access-audit fail-closed behavior, checkpoint integrity, outage and recovery.
5. Run full tests, Ruff, secret scan, Bandit and dependency audit on the exact implementation commit; retain sanitized run IDs and evidence digests.
6. Obtain separate dated service-owner and independent-reviewer implementation acceptance. Only then consider a separately reviewed runtime configuration change.

## 6. Rollback and safety

- Before enabling any approved backend, retain the current volatile path as an explicit lab-only rollback configuration; never silently switch to it after a durable write failure.
- A rollback must not claim that records acknowledged by the durable backend are present in volatile memory. Preserve a reconciliation/incident record and keep administrative actions that require audit acknowledgement blocked.
- Do not delete, rewrite, or migrate audit evidence as part of rollback. Do not activate enforcement. AP-1.0 remains `monitor_only`, active rules remain zero, and release remains NOT APPROVED.

## 7. Explicit non-claims

This preparation note does not mean that PostgreSQL/KMS is approved, that the SQLite candidate is acceptable, that authenticated RBAC/deletion/backup/restore/checkpoint controls exist, that any infrastructure is deployed, or that Day 20 is complete. The approval template remains to be completed by the actual decision-makers.
