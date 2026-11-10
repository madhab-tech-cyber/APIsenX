# Day 20 storage design approval record

> This record captures the service owner's explicit architecture decision. It is not an independent review, runtime implementation acceptance, deployment authorization, or release approval. Do not put credentials, key material, production endpoints, or personal data here.

## Decision metadata

- Decision date/time (UTC): 2026-11-09 16:29:25 UTC
- Service owner (GitHub handle or role): pappukumar96727-sketch — service owner, as designated by repository owner in Issue #83
- Independent reviewer (GitHub handle or role; must be a different person): @jayitape — review posted 2026-11-09 17:09:36 UTC on Issue #83; outcome APPROVE WITH AMENDMENTS / CLARIFICATIONS (not unconditional approval)
- Design version / commit reviewed: `docs/day20-durable-audit-architecture-decision.md`, merged on main by PR #138; architecture decision commit `c36a4b2e8ad1619c55c09177d0aa10cc807cfecc`
- Decision: APPROVE / APPROVE WITH AMENDMENTS / REJECT — **recorded decision: APPROVE**
- Decision source: Explicit service-owner confirmation in the project conversation at 2026-11-09 16:29:25 UTC; recorded in the repository at the service owner's request.
- Scope: **Isolated synthetic lab only.** No production data, no production deployment, and no enforcement activation.
- Limits: Approval adopts the PostgreSQL architecture as written. It does not claim that infrastructure, credentials, KMS, backups, immutable destination, or runtime controls have been provisioned or tested.

## Required service-owner decisions

The service owner approves the eight architecture positions below as written in the decision record. These checkboxes document the owner's decision, not implementation evidence.

- [x] **PostgreSQL hosting, ownership, isolation, capacity and availability.** Approve a dedicated PostgreSQL instance for the isolated lab, operationally owned by the service owner and reachable only from the analytics host over a private network. Scope capacity to masked, allowlisted event projections and bounded lab volume; lab-hours availability, not HA. Provisioning and capacity evidence remain pending.
- [x] **TLS, encryption at rest, secret-manager integration and key ownership/rotation.** Require TLS for connections and encryption for database storage and backups. Keep checkpoint-signing keys in an external KMS or equivalent protected key service, separate from the database and repository. Key generation, custody, rotation runbook and secret-manager setup remain to be implemented and evidenced.
- [x] **Separate writer, reader, retention-worker and migration identities/permissions.** Approve four distinct identities with least privilege: INSERT-only writer; case-scoped reader; retention worker limited to expiry deletion and deletion receipts; migration identity for deployment-time DDL only. Runtime authorization and cross-case denial still require tests.
- [x] **Independently protected checkpoint/signing-key service and immutable destination.** Approve a canonical ordered hash chain, externally signed checkpoints, and periodic digest export to a separately administered append-only destination. Checkpoint failure must quarantine affected evidence and block investigation export; no silent re-signing.
- [x] **Backup schedule, rolling 7-day expiry, restore isolation and restore-time re-purge.** Approve rolling seven-day backups of masked data only. Restore into isolation, replay deletion/hold state, re-check expiry, verify checkpoints and run integrity/retention tests before access. Backup expiry must be separately verified.
- [x] **RT-01–RT-08 retention, deletion receipts, export expiry and hold/release workflow.** Approve AUDIT-LAB-1.0 classes, including RT-03 7 days, RT-04 30 days, RT-05 maximum 90 days, RT-06 exports 24 hours and RT-07 rolling 7-day backups. Calculate expiry from server receipt time; run retention at least hourly and remove expired primary data within 24 hours, including derivatives, with minimal protected deletion receipts. Holds require named approval, case scope and expiry no later than 30 days, reviewed weekly.
- [x] **Incident response, outage behavior, emergency disable, operational ownership and costs.** Approve bounded failure on writer/database outage, no disk/stdout durable fallback and no unbounded memory queue. Keep emergency disable available. The service owner accepts operational responsibility for the lab PostgreSQL instance, backups, key service and retention worker, and the architecture's stated single-instance plus backup-storage cost model. Actual provisioning, cost estimate and operating runbook remain pending.
- [x] **Explicit confirmation that AP-1.0 stays `monitor_only`, with zero active enforcement rules.** Approved. This architecture decision does not activate enforcement or change authoritative API authorization.

## Independent review

- Reviewer: **@jayitape** (separate from the service owner and Member 1 architecture author)
- Review date/time (UTC): **2026-11-09 17:09:36 UTC**
- Reviewer decision: **APPROVE WITH AMENDMENTS / CLARIFICATIONS** for the isolated synthetic-lab architecture only.
- Findings: six clarifications covering trusted case authorization/database boundaries; checkpoint ordering, canonicalization and recovery; deletion-receipt privacy; retention/backup and partial-batch semantics; identity/operational controls; and availability/recovery objectives.
- Amendment evidence: incorporated in the architecture decision and retention/restore/integrity plan through [PR #147](https://github.com/madhab-tech-cyber/APIsenX/pull/147), merged on 2026-11-09 at `5e0bc4c970b2fadc3aa5d704e201b5fddcdbe1ec`.
- **Reviewer closure of all six findings: PENDING.** A separate dated confirmation against the merged amendments has been requested; the conditional review is not unconditional approval.
- Evidence references: [Issue #83](https://github.com/madhab-tech-cyber/APIsenX/issues/83) and [PR #147](https://github.com/madhab-tech-cyber/APIsenX/pull/147).

This review is independent of the service-owner decision. A conditional architecture review does not constitute runtime implementation acceptance, deployment authorization or release approval.

## A6 operating-target confirmation — 2026-11-10

The service owner explicitly confirmed the following three targets on Issue #83:

- [x] Capacity: up to **100,000 synthetic audit events**.
- [x] Backup retention: **rolling 7 days**.
- [x] Availability: **lab-hours only, single instance, no HA**.

The following proposed A6 objectives remain **UNAPPROVED** and must be explicitly confirmed or amended before they are relied on for provisioning or acceptance:

- [ ] RPO: 15 minutes maximum.
- [ ] RTO: 4 business hours.
- [ ] Volatile queue: 2 seconds maximum age; capacity 1,000 events.
- [ ] Zero silent drops, with bounded loss counters and alerts.
- [ ] Checkpoint backlog: 10 minutes or 2,000 events maximum.
- [ ] Retention backlog: 24 hours maximum past primary expiry; alert at 1 hour overdue.
- [ ] Recovery: 100% sequence/checkpoint continuity, zero expired records/derivatives restored, and zero unresolved deletion items.

These checkboxes record only the service-owner confirmation already posted; they do not represent infrastructure, runtime or test evidence.

## Implementation acceptance

## Implementation acceptance (complete only after runtime evidence exists)

- Candidate implementation commit: PENDING — no approved PostgreSQL runtime implementation yet
- Isolated database integration-test run: PENDING — disposable database and four role credentials/environment are not yet provisioned
- Retention/deletion/restore test evidence: PENDING
- RBAC and fail-closed access-audit evidence: PENDING
- Tamper/checkpoint verification evidence: PENDING
- Secret/privacy scan and dependency/security results: PENDING
- Service-owner implementation acceptance date: PENDING
- Independent reviewer implementation acceptance date: PENDING

## Release gate

**Architecture decision: APPROVED by service owner on 2026-11-09 16:29:25 UTC. Independent architecture review: APPROVE WITH AMENDMENTS / CLARIFICATIONS (2026-11-09 17:09:36 UTC); PR #147 merged the six clarifications, but reviewer closure remains PENDING. Service owner confirmed only 100,000 synthetic events, rolling 7-day backups and lab-hours single-instance/no-HA availability on 2026-11-10; all remaining A6 targets remain UNAPPROVED. Runtime implementation and acceptance: PENDING.**

Keep AP-1.0 in `monitor_only`, active enforcement rules at zero, and release **NOT APPROVED**. The architecture approval authorizes review and documentation refinement only. Runtime implementation remains gated until the independent reviewer confirms the six clarifications are closed, the service owner confirms or amends the remaining A6 operating targets, and the required isolated infrastructure is provisioned. It does not authorize production deployment, live production data, enforcement activation, or release approval. Never store raw captures, request bodies, tokens, credentials, key material, or real personal data in Git.
