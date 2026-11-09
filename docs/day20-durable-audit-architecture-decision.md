# Day 20 durable audit storage — architecture decision record

**Role issuing this record:** Member 1 — governance / security architecture.
**Date:** 2026-11-07.
**Status:** ARCHITECTURE DECISION ISSUED — the design below is adopted as the
project's architecture. It is **not** the service-owner approval and **not**
an independent review; both remain required by
[the approval record template](day20-storage-approval-record-template.md)
before any runtime is deployed. Approval is not inferred from a PR merge,
a CI result, or this document.
**Scope:** Isolated synthetic lab only. No production data, no enforcement
activation. AP-1.0 stays `monitor_only`, zero active enforcement rules, and
the release remains **NOT APPROVED** until the approval record is completed
with runtime evidence.
**Decides:** Issue #83 (Day 20 durable audit storage), architecture half.
**Builds on:** [design proposal](day20-durable-audit-storage-design-proposal.md),
[AUDIT-LAB-1.0 retention and investigation policy](audit-retention-and-investigation.md),
[Member 1 Day 20 evidence](day20-member1-evidence.md), the Member 5 isolated
PostgreSQL harness (PR #135, `tests/integration/postgres/`), the retention /
restore / integrity test plan (PR #136) and the Day 20–21 acceptance
contracts (PR #137).

## Decision

Adopt the PostgreSQL design from the design proposal as the durable audit
architecture, without amendment to its storage boundary:

- a dedicated PostgreSQL service on a private network, TLS in transit,
  encrypted storage and backups, credentials only in the deployment secret
  manager;
- four separate identities — writer (INSERT-only), reader (case-scoped),
  retention worker, schema migration — no shared human use of the writer
  credential;
- append acknowledged only after transaction commit; idempotent
  same-reference/same-digest retries; conflicting-digest retries rejected
  and counted;
- a hash chain with signed checkpoints whose keys live outside the
  database (KMS or equivalent), with checkpoint digests periodically
  exported to a separately administered immutable destination;
- retention computed from server receipt time, executed by the retention
  worker, with minimal deletion receipts written to a separately protected
  accountability stream;
- case-scoped, deny-by-default investigation access where every sensitive
  read, export, grant and hold change is itself audited, and the read or
  export is denied if that access-audit append fails.

The SQLite `DurableStore` candidate is **not** selected: its retention
bound is at most seven days, so it cannot satisfy RT-05's 90-day class,
and it provides no independent writer/reader identities. It remains an
opt-in local test double only and must never be presented as the approved
store. `AuditWriter` keeps defaulting to `MemoryStore` until the service
owner's approval is recorded and the implementation acceptance below is
complete; no default changes as part of this decision.

## The eight required decisions — architecture position

Each item mirrors the approval record template. The architecture position
is decided here; the service owner approves or amends each in the record.

1. **Hosting, ownership, isolation, capacity, availability.** Dedicated
   PostgreSQL instance for the lab, owned operationally by the service
   owner, reachable only from the analytics host on a private network.
   Capacity bound: the masked, allowlisted event projection only (no raw
   bodies), sized for lab event volume with bounded request sizes already
   enforced upstream; availability expectation is lab-hours, not HA — a
   single instance with the rolling backups of item 5.
2. **TLS, encryption, keys.** TLS required for every connection;
   encryption at rest on the database volume and on backups. Checkpoint
   signing keys are generated and held in a KMS or equivalent protected
   key service, never in the database, the repo, or the same credential
   as any database identity. Key rotation is an owner-runbook item; the
   architecture requires the key service to support it, not a schedule
   invented here.
3. **Identities and permissions.** Exactly the four identities the
   Member 5 harness already models: writer INSERT-only on the audit
   table and sequence (no SELECT/UPDATE/DELETE/DDL); reader SELECT only
   through case-scoped access; retention worker DELETE of expired rows
   plus INSERT of deletion receipts, nothing else; migration DDL only,
   used at deploy time and disabled otherwise. The harness's honest
   limit is recorded: its case-filtered view is caller-settable and is
   **not** itself an authorization control — the runtime must enforce
   case scope in the service, with the database grants as the second
   barrier, and the access tests of the verification gates must prove
   cross-case denial.
4. **Checkpoints and immutable destination.** Hash chain over canonical,
   ordered entries; checkpoints signed with the external key of item 2;
   digests exported on a fixed cadence to a separately administered
   append-only destination. A checkpoint failure quarantines the affected
   evidence set and blocks investigation export pending review; history
   is never silently re-signed.
5. **Backups and restore.** Rolling 7-day backups (RT-07), never
   containing raw captures or secrets. Restore is always into isolation:
   replay the deletion/hold ledger, re-check expiry, verify checkpoints,
   run the synthetic integrity/retention tests, and only then enable
   access. Backup expiry is verified separately from primary deletion.
6. **Retention, deletion, exports, holds.** AUDIT-LAB-1.0 classes stand:
   RT-03 maximum 7 days, RT-04 maximum 30 days, RT-05 maximum 90 days,
   RT-06 exports expire in 24 hours with a named recipient and approved
   purpose, RT-07 rolling 7-day backups; RT-01/RT-02/RT-08 unchanged.
   Expiry is computed from server receipt time; the retention worker runs
   at least hourly and removes expired primaries within 24 hours, across
   primary tables, indexes, caches, exports and derivatives, writing the
   minimal deletion receipt (receipt ID, class, expiry window, completion
   time, counts, outcome — never payload or subject links). Holds need a
   named approver, case ID, minimal scope, reason, custodian, access
   list and expiry within 30 days, reviewed weekly; release resumes
   normal deletion.
7. **Incident response, outage, ownership, cost.** Writer or database
   unavailable: bounded generic failure — no disk fallback, no stdout as
   a durable substitute, no unbounded memory queue. Emergency disable
   stays available during an audit outage. Checkpoint verification
   failure and conflicting-digest attempts raise sanitized alerts to the
   service owner. Operational ownership (instance, backups, key service,
   retention worker) sits with the service owner; lab cost is the single
   instance plus backup storage, accepted as part of the owner's
   decision.
8. **Release posture.** This decision changes nothing about enforcement:
   AP-1.0 remains `monitor_only` with zero active rules, and the audit
   service must never become an authorization path for the API.


## Independent-review amendments — 2026-11-09 (PR #147)

The independent review by @jayitape on Issue #83 returned **APPROVE WITH AMENDMENTS / CLARIFICATIONS**. The following design constraints resolve the six findings. Numeric operational targets below are proposed isolated-lab limits, not evidence of provisioning; the service owner must confirm them before infrastructure is provisioned or runtime implementation begins. The reviewer must confirm closure after this document is merged.

### A1. Trusted case authorization and database boundary

- A reader never supplies an authoritative case ID. The authenticated application service validates a short-lived, signed case grant (subject, case, permitted operations, expiry, grant ID) issued by the authorization authority and derives the case scope server-side.
- The service opens a transaction and establishes scope through a narrowly granted database function that verifies the service-authenticated principal and grant. A plain caller-settable `app.case_id`, custom GUC, request header, or SQL parameter is never an authorization factor.
- Reader credentials receive EXECUTE only on the constrained case-read function; revoke direct SELECT on base audit, grant, hold, receipt and checkpoint tables. No reader membership in owner, writer, retention or migration roles; no role with BYPASSRLS. Apply RLS with FORCE as defense in depth, not as the sole trust boundary. Table ownership belongs to a non-login owner role.
- The service function validates grant signature/issuer, expiry, case binding and allowed operation before setting transaction-local scope; transaction rollback clears scope. Connection pooling must use transaction pooling/reset semantics and tests must prove no scope survives reuse.
- Negative tests must attempt direct SQL/table reads, forged/changed `app.case_id`, missing/expired/revoked grants, role SET ROLE escalation, connection reuse and cross-case access. Every attempt is denied without revealing record existence and is access-audited; if that audit append fails, deny the operation.

### A2. Checkpoint protocol, ordering and recovery

- Canonicalize each allowlisted event as UTF-8 JSON under RFC 8785 (JCS), reject duplicate keys/non-finite numbers, normalize timestamps to UTC RFC 3339 with fixed precision, and hash domain-separated bytes: `SHA-256("APISENX-AUDIT-v1\0" || canonical_event)`.
- Allocate a single monotonic sequence per lab stream inside the same database transaction as append. Serialize sequence/head updates with a locked stream-head row; concurrent writers retry serialization/deadlock failures with the same idempotency key. No acknowledgement before commit.
- Maintain one chain per environment and policy-version stream. A checkpoint covers a contiguous inclusive sequence range and previous checkpoint digest; it includes environment ID, policy version, first/last sequence, previous checkpoint digest, canonicalization version, key ID and creation time.
- Proposed checkpoint trigger: every 5 minutes or 1,000 committed events, whichever occurs first; maximum unanchored window 10 minutes or 2,000 events. If exceeded, mark integrity state DEGRADED, alert the owner, quarantine the affected range and block investigation export. Do not silently re-sign or reset the chain.
- Sign with an external KMS key (algorithm/key ID recorded; private key never exported). Retain public verification material and key lifecycle metadata for at least the maximum evidence/checkpoint verification period. Rotation creates a new key ID and a cross-signed transition checkpoint; historical signatures are verified against the archived public key and recorded validity/revocation timeline. Revocation blocks new signatures but does not erase historical verification evidence.
- If KMS or immutable anchor is unavailable, retain only the bounded pending checkpoint metadata in the database, do not claim it is externally anchored, alert and quarantine the affected range. On recovery, anchor the original digest and sequence range; never recompute a replacement history.

### A3. Deletion receipt privacy and proof

- Replace the PR #136 example's record identifier/digest in the receipt with a domain-separated keyed reference: `HMAC-SHA-256(K_receipt, environment_id || retention_class || opaque_record_id)`, truncated to 128 bits for display/storage. The key is held in KMS, not the database; no reversible mapping is stored in the receipt stream.
- Receipt fields: random receipt ID, opaque receipt reference, retention class, expiry bucket (UTC day), completion time, deleted/failed counts, outcome, batch ID and policy version. No subject, case, raw record ID, payload digest that is linkable to a subject, or payload.
- Receipt stream is separately access-controlled and append-only; only retention worker may append, custodian may verify aggregates, and all reads are audited. Retain receipts for at most 90 days (RT-05 ceiling), then expire them under the same controlled deletion process. The KMS HMAC key is separately access-controlled and rotated; old verification keys are retained only for the receipt retention window.
- Prove deletion with transactionally committed per-record/batch outcomes, privileged absence checks in isolated tests, derivative/backup inventory reconciliation and signed aggregate batch manifests. The HMAC reference supports deduplication/audit correlation without allowing an ordinary reader to reverse-link it. Do not claim cryptographic erasure unless every key copy and restorable derivative is accounted for.

### A4. Retention, backup and partial-batch semantics

- Primary expiry remains receipt-time based: RT-03 7d, RT-04 30d, RT-05 90d maximum; hourly worker schedule; primary plus indexes/caches/materialized views removed within 24h after expiry. RT-06 exports expire at 24h. RT-07 backup generations have a strict 7-day rolling lifetime and must be inaccessible immediately when expired.
- Backup policy also requires expired primary data to be absent from all backups no later than 7 days after primary deletion. Therefore the operational maximum from primary expiry to backup disappearance is 8 days (24h primary purge SLA plus 7d backup window); no generation may be retained or restored beyond its own creation+7d expiry. Backups contain masked allowlisted data only.
- Deletion/hold ledger is stored separately from the backup being restored, append-only and integrity-protected by signed checkpoints. Restore starts isolated and access-denied; verify ledger signature/sequence, replay holds/releases and deletion tombstones, re-evaluate receipt-time TTL against trusted UTC, purge expired rows and derivatives, verify checkpoint chain and backup age, then run acceptance checks before enabling access.
- Process each deletion item and its receipt in one database transaction where possible. For external derivatives, use a durable per-derivative state machine (PENDING → DELETED → VERIFIED); a receipt cannot report COMPLETE until all required derivatives are VERIFIED. Partial failures produce PARTIAL/FAILED outcomes with exact counts, retryable idempotent work items and alerts; never mark a whole batch successful when any item remains unresolved. Retried work must not duplicate or contradict receipts.

### A5. Identity mapping and operational controls

- DB writer maps only to the authenticated producer/audit-writer service; reader maps only to the case-scoped investigator read service; retention-worker maps only to the retention/custodian automation; migration maps only to a deployment job with time-limited credentials. These are four technical DB identities, not human personas.
- Analyst/investigator receives a named application identity and case grant, never a DB credential. M1 approver uses a separate approval workflow and cannot grant itself access. M6 custodian operates backup/restore/retention through audited, time-bound privileged workflows and has no routine content-read permission. Dashboard viewers receive aggregates or explicitly authorized masked projections through a separate read API, never direct DB access.
- Enforce MFA for all human privileged/approval/custodian actions; service-to-service workload identity for applications; maximum investigator grant/session 24h; privileged session maximum 1h with re-authentication; grants are case/operation-scoped and revoked on expiry. These are proposed lab limits for owner confirmation.
- Break-glass requires two named approvers where practicable, reason, ticket/case, maximum 1h, alert to service owner and independent custodian, and a separate append-only access record before access. If the break-glass audit path is unavailable, protected content access remains denied; emergency disable remains available without content access.
- Migration credential is minted only for a migration window, disabled/revoked immediately after migration verification, never mounted in runtime services, and every use is audited. Rotate DB/service credentials at least every 90 days and immediately on suspected compromise; signing keys follow the KMS rotation policy in A2. Alert ownership: service owner is accountable for DB/KMS/backup/retention; named on-call delegate handles alerts, with escalation after 15 minutes unacknowledged (proposed lab target).

### A6. Availability, recovery and bounded work targets

The following are proposed acceptance objectives for the isolated, non-HA lab and require service-owner confirmation before provisioning:

| Measure | Proposed lab target | Required behavior |
|---|---:|---|
| RPO | 15 minutes maximum | Encrypted backups/checkpoint ledger must support recovery to within 15 minutes of acknowledged commits; if not achievable, report actual RPO and keep service degraded |
| RTO | 4 business hours | Restore isolated, verify ledger/checkpoints, re-purge and run acceptance checks before access |
| Volatile queue | 2 seconds maximum age; bounded capacity 1,000 events | No disk spool; reject/drop with minimized counters when full/expired |
| Drop limit | 0 silent drops | Every loss increments a bounded counter and triggers alert; any loss blocks acceptance pending reconciliation |
| Checkpoint backlog | 10 minutes or 2,000 events maximum | Beyond either threshold quarantine range and block exports |
| Retention backlog | 24 hours maximum past primary expiry | Alert at 1 hour overdue; block acceptance if any expired primary remains after 24 hours |
| Recovery acceptance | 100% sequence/checkpoint continuity; zero expired records/derivatives restored; zero unresolved deletion items | Any mismatch keeps restored service unavailable |

The single-instance design is explicitly not HA. If the proposed RPO cannot be met by the selected rolling-backup configuration, the service owner must approve a revised backup/WAL strategy and cost before implementation. A successful process restart or mocked test is not proof of these objectives.

## Review disposition and implementation gate

The independent review is recorded on Issue #83 by @jayitape at 2026-11-09 17:09:36 UTC as **APPROVE WITH AMENDMENTS / CLARIFICATIONS**. This PR incorporates the six clarification areas for reviewer verification. It does not convert that conditional review into unconditional approval. The reviewer must confirm the amended text closes the findings; the service owner must explicitly confirm the proposed numeric operating targets in A6 and the clarified controls before runtime implementation. Until both confirmations are recorded, no runtime migrations, PostgreSQL adapter, retention worker, checkpoint signer or reader service is authorized. Keep `AuditWriter` on `MemoryStore`, AP-1.0 `monitor_only`, zero active rules, and release **NOT APPROVED**.

## What already exists against this architecture

- The four-identity model is implemented and contract-tested in the
  isolated harness (`tests/integration/postgres/bootstrap.sql`,
  `test_postgres_roles.py`) — as preparation, with skip-by-design gating;
  a skip is not evidence of a running database integration.
- Retention boundary arithmetic is covered by
  `test_retention_contract.py` and the PR #136 test plan; it proves the
  policy's UTC math, not a running retention worker.
- The acceptance contracts of PR #137 guard these plans against drift.
- The volatile default is unchanged and honestly labelled everywhere it
  appears; `durable_audit` remains PENDING in `analytics.acceptance`.

## What remains after owner approval (implementation order)

1. Runtime schema + migration for the audit table, sequence, receipt
   stream and checkpoint table, owned by the migration identity.
2. A PostgreSQL-backed audit store behind the existing `AuditWriter`
   injection seam (explicit opt-in; default unchanged), with commit-
   before-acknowledge, idempotency and conflict rejection.
3. Retention worker + deletion receipts; export expiry enforcement.
4. Checkpoint signer/verifier against the external key service and the
   immutable digest export.
5. Case-scoped reader service with audited reads/exports/grants and
   fail-closed behaviour when the access-audit append is unavailable.
6. The six verification gates of the design proposal, evidenced on an
   exact commit, then implementation acceptance recorded in the approval
   record, then — and only then — `durable_audit` can move from PENDING.

## Decisions still required from humans

- **Service owner:** complete [the approval record](day20-storage-approval-record-template.md)
  — APPROVE / APPROVE WITH AMENDMENTS / REJECT, dated, against the commit
  carrying this record, covering the eight items above.
- **Independent reviewer (a different person):** complete the review
  section of the same record — threat-model and least-privilege findings,
  integrity/key-separation findings, retention/restore findings,
  objections — dated, with sanitized evidence references.

Until both are recorded: implementation of a runtime durable store is not
authorized by this record, the demo environment of issue #89 must not use
an unapproved store, issue #102's fail-closed proofs remain gated, and the
release remains **NOT APPROVED**.
