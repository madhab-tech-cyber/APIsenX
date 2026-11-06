# Day 20 — retention, deletion, restore and integrity test plan

**Status: test-plan preparation only.** This document defines acceptance cases for the approved durable audit service after the service owner records the architecture/operations decision and an independent reviewer approves the design. It does not assert that any runtime control exists or that a database has been provisioned.

## Preconditions and evidence rules

- Run only against a dedicated, disposable synthetic environment provisioned for the approved architecture.
- Use synthetic records and independently provisioned least-privilege identities. Inject credentials through the approved secret mechanism; never commit DSNs, tokens, certificates or key material.
- Use an injectable/frozen UTC clock for deterministic boundary tests. Production receipt time must be assigned by trusted server code, not accepted from the caller.
- Record the exact tested commit, schema/migration version, environment identifier (non-secret), test command, result, and sanitized logs.
- A skipped test, mocked-only test, policy arithmetic assertion, or successful CI run is not runtime acceptance evidence.
- Preserve AP-1.0 `monitor_only`, zero active enforcement rules, and release NOT APPROVED until all required approvals and acceptance gates pass.

## Retention and deletion matrix

| Class | Required policy window | Deterministic cases |
|---|---:|---|
| RT-03 masked summaries | 7 days | present just before expiry; expire exactly at boundary according to documented inclusive/exclusive rule; absent immediately after purge |
| RT-04 findings/triage | 30 days | same three boundary points; separately verify approved time-bound hold behavior |
| RT-05 protected audit/approval/access records | up to 90 days | verify 90-day maximum and earlier policy-specific expiry; reject extension beyond policy |
| RT-06 investigation exports | 24 hours | export unavailable after expiry; copied/downloaded derivatives included in deletion evidence |
| RT-07 encrypted backups | rolling 7 days | backup aging removes expired backup generations; restore cannot reintroduce expired records |

For every class, verify expiry is derived from trusted server receipt time, timezone-aware UTC is enforced, clock boundaries are deterministic, purge is idempotent, and a deletion receipt is committed only when the deletion operation commits. Verify partial batch failure rolls back or produces an explicitly documented, recoverable per-record outcome; never report a false all-success result.

## Deletion and derivative coverage

1. Insert synthetic primary record and all declared derivatives (indexes, materialized views, caches, exports and backup copies).
2. Advance the controlled clock beyond the class TTL and run the retention worker.
3. Verify primary record and every in-scope derivative are absent using the appropriate privileged verification path.
4. Verify a durable deletion receipt records record identifier/digest, class, server deletion time, reason code and operation/correlation ID without copying raw sensitive content.
5. Retry the same purge and verify idempotency (no duplicate destructive side effects and a traceable result).
6. Inject failure between primary and derivative deletion; verify retry/reconciliation completes safely and the system does not claim deletion prematurely.
7. Verify expired export links and credentials cannot retrieve an export after the 24-hour window.

## Hold and release cases

- Reject a hold lacking authenticated case-scoped authority, reason, scope, approver and expiry/review time.
- Apply an approved hold and verify only explicitly scoped records/classes are exempted; unrelated records still expire.
- Verify hold creation, change, access and release are independently audited.
- Release a hold and verify the original receipt-time expiry is honored; a hold must not silently reset or extend retention.
- Verify expired, revoked, malformed or cross-case hold grants fail closed.
- Verify hold state survives restart and restore, and is reconciled before restored data is made available.

## Restore and backup re-purge cases

1. Create synthetic records at different retention ages and a backup snapshot.
2. Advance the controlled clock so a subset expires after the snapshot.
3. Restore the snapshot into an isolated, access-denied environment.
4. Replay authoritative deletion/hold state and run re-purge before granting application or investigator access.
5. Verify expired records and derivatives remain absent, valid holds remain correctly scoped, and deletion receipts/checkpoints reconcile.
6. Inject restore interruption at each stage; keep the restored service unavailable until validation completes.
7. Verify backup generations older than the rolling seven-day policy are inaccessible and removed according to the approved backup lifecycle.
8. Capture sanitized evidence proving no pre-validation read path was available.

## Integrity checkpoint cases

Use the approved externally protected signing/anchor destination; a hash stored only beside mutable database rows is insufficient.

- Valid append sequence: verify canonical event digest, monotonic sequence and signed checkpoint.
- Payload tamper: alter a stored synthetic event and require verification failure.
- Reorder: swap adjacent events and require chain/sequence verification failure.
- Missing sequence: remove an event or checkpoint and require a detectable gap.
- Duplicate/replay: replay an event identifier or sequence and require deterministic conflict/rejection.
- Checkpoint tamper: alter signature, digest, key identifier or anchor metadata and require failure.
- Anchor outage: simulate unavailable external checkpoint destination; surface degraded state, do not claim integrity protection or silently fall back to a local mutable hash.
- Recovery: restore anchor connectivity, reconcile pending checkpoints without silently rewriting history, and verify the complete chain.
- Key rotation/revocation: verify old checkpoints remain verifiable under the approved historical key policy and revoked keys cannot sign new checkpoints.

## Authorization and access-audit cases

- Writer can append only; cannot read, update, delete or perform DDL.
- Reader access requires authenticated, case-scoped grant and cannot broaden scope by setting caller-controlled session variables.
- Retention identity can perform only policy-authorized purge and receipt operations; cannot read investigation content.
- Migration identity is separate, time-bound and unavailable to runtime services.
- Every read, export, grant, revoke, hold and administrative action produces an access audit record.
- If access-audit append fails, privileged read/export/grant operations fail closed and return no protected data.
- Cross-case, expired-grant, revoked-grant and missing-context requests are denied and audited without leaking record existence.

## Outage and recovery cases

- Append service unavailable before commit: caller receives bounded failure; no success acknowledgement and no partial mutation.
- Commit succeeds but acknowledgement is lost: retry with same idempotency key returns the original committed outcome without duplicate event.
- Conflicting payload reuses an idempotency key: deterministic conflict; original record remains unchanged.
- Storage full, timeout, permission failure and checkpoint-anchor outage each produce bounded, non-sensitive failure categories.
- No raw disk spool, unbounded queue or silent bypass is permitted.
- Recovery verifies committed state, sequence/checkpoint continuity, deletion backlog and retention backlog before normal operation resumes.
- Verify kill switch and monitor-only behavior remain effective throughout degraded and recovery states.

## Acceptance evidence checklist

- [ ] Dated service-owner architecture and operating-model decision is recorded.
- [ ] Separate independent architecture review is recorded.
- [ ] Approved service/schema and migrations are identified by immutable version.
- [ ] Every applicable test above has deterministic pass/fail evidence on the exact implementation SHA.
- [ ] Full unit/integration suite, Ruff, secret scan, SAST and dependency audit pass on that SHA.
- [ ] Sanitized restore, deletion, authorization, tamper and outage/recovery evidence is retained.
- [ ] Separate service-owner implementation acceptance and independent reviewer acceptance are recorded.

**No checkbox above is complete by virtue of this plan.** Do not switch the runtime default, deploy storage infrastructure, close Day 20, or authorize release until the required decisions and implementation evidence exist.
