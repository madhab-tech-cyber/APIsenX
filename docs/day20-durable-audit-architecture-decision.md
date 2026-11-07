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
