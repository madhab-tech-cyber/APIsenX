# Day 18 Proven-Lab-Case Authorization Decision

**Decision owner:** Member 1. **Date:** 2026-10-17 (Asia/Calcutta).

**Decision ID:** `LAB-AUTH-20261017-01`. **Active authorization set:** empty.

## Evidence reviewed

Reviewed [current checks](member1-oct17-verification.md),
[ENF-1.0](enforcement-approval-and-rollback.md) and the
[candidate register](blocking-rule-review-register.md). Forty application/
contract tests pass. Four customer admin-inventory policy checks fail. There is
no running collector enforcement adapter, verified decision channel, rollback
exercise, integrated accuracy/latency evidence or approved Day 21 failure matrix.

## Case decisions

| Case | Proven fact in current local API | Sentinel activation decision |
|---|---|---|
| LA-01 | Ordinary private cross-owner read returns 403 | WITHHELD: one API denial does not prove a safe adapter decision or benign-share behavior; BR-01 gates incomplete |
| LA-02 | Ordinary customer status update returns 403 | WITHHELD: missing explicit permission/version/tenant context and adapter evidence; BR-02 gates incomplete |
| LA-03 | Customer admin list returns 403 with mixed-owner fixtures, 200 with empty/all-owned fixtures | WITHHELD: D11-F01 is unresolved; repair the API function gate first |
| LA-04 | Owner and permitted admin reads/updates succeed in current tests | PROTECTED BENIGN CASES: require successful access after any future activation and rollback; never targets for denial |
| LA-05 | Shadow/zombie, tenant/share and rate-limit predicates lack executable corpus/runtime | WITHHELD: no verified lab case for active enforcement |

Application-owned authentication and authorization keep their existing behavior.
This decision issues no Sentinel deny or rate-limit capability and does not
claim a blocking demonstration occurred. It is a completed review decision
with activation withheld because the required proofs do not exist.

## Conditions for a later authorization

M3/M4 submit an implemented rule version and every EG gate with M5/M6 evidence.
M1 then records a new decision ID, exact rule/config digest, lab service,
canonical operation, approved opaque subject/resource scope, executor identity,
review reference, UTC start/expiry (<= 30 minutes), maximum decision TTL
(<= 5 seconds), kill-switch and rollback evidence references. Empty fields,
wildcard environment, replay of this decision or an expired lease never grant
permission. This document has no start/expiry because it grants no lease.

No authorization is inherited by a new commit or deployment. A new digest,
scope or policy requires re-review, even when a previous synthetic case passed.
Record revocation and expiry in protected audit. Re-test legitimate and
unauthorized API behavior after every change.

## Open dependencies and next gate

CA-01/02/03/04/05/06/10 remain prerequisites. M5 remediates D11-F01 by
2026-10-21 and before admin acceptance/release. M3/M4 supply adapter and transport,
M6 supplies reproducible evidence, and M1 reviews Day 21 failure behavior.
No High residual risk is accepted or closed. Activation stays withheld until a
new concrete authorization record satisfies these conditions.
