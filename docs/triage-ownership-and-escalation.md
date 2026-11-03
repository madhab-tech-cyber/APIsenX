# Day 25 Triage Ownership and Escalation Workflow

**Owner:** Member 1. **Date:** 2026-10-19. **Workflow:** `TRIAGE-LAB-1.0`.

This refines the [Day 9 severity/triage policy](discovery-severity-triage-policy.md)
without inventing a running finding store. Severity is impact, confidence is
evidence quality, state is workflow progress; event volume cannot substitute
for any of them. Preserve unknown/lost telemetry as a visibility gap.

| ID / transition | Actor | Required evidence and guard |
|---|---|---|
| TR-01 `new -> validating` | Assigned analyst | Authorised lab/source, stable dedup key, owner, versions and investigation plan |
| TR-02 `validating -> confirmed` | Analyst with security review | Reproduction, policy ground truth, impact/severity/confidence and privacy-safe evidence |
| TR-03 `new/validating -> false_positive` | Analyst plus reviewer | Specific parser/version/source/label explanation and regression follow-up; not merely failed reproduction |
| TR-04 `confirmed -> remediating` | Assigned fix owner | Fix scope, target, rollback plan and acceptance case IDs |
| TR-05 `remediating -> resolved` | Fix owner | Exact merged/deployed lab version and claimed regression results; not independent verification |
| TR-06 `resolved -> verified` | Independent reviewer other than implementer | Original reproduction now safe, benign/negative regressions pass and exact build/scope evidence matches |
| TR-07 `resolved/verified -> confirmed` | Reviewer | Regression/new evidence, linked history; do not erase prior decisions |
| TR-08 `confirmed -> accepted_risk` | M1/security approver | Reason, owner, compensating control, residual rating and expiry; High/Critical still blocks release |

## Ownership and response

M4 owns detection/false-positive validation, M5 application/contract fixes, M2
sensor defects, M3 collector/enforcement failures and M6 dashboard/CI/build
issues. M1 owns severity disputes, cross-boundary coordination, risk acceptance
and release decisions. Missing M4 identity is an explicit assignment blocker,
with M1 coordinating until confirmed; never manufacture an account or response.

Critical active exploitation: notify M1 immediately and contain within 24 hours;
other Critical remediation target <= 48 hours. High: triage within one business
day, fix within seven days and before release. Medium: triage within three
business days and resolve within 30 days or record approved owner/reason/deadline.
Low: triage within five business days and schedule maintenance. Store UTC
timestamps and show local dates clearly. These targets are not permission to
probe a third-party target or retain raw sensitive evidence.

Request an owner response within 24 hours; at 48 hours without response, M1
records evidence of nonresponse and assigns a named alternate or reduces scope.
No member is declared inactive solely because their branch is old. Missed
security deadlines stay visible, trigger escalation and never silently become
accepted risk. A held rule remains inactive throughout investigation.

## Durable workflow controls

M4/M6 must implement server-side role/case authorization, append-only change
history, actor/time/reason, expected record version and idempotency keys.
Concurrent stale transitions return conflict rather than overwriting evidence.
Dedup by environment, class, method/template or unknown token/key version and
policy/contract versions; preserve original/last times and counts. Duplicates
must not close or downgrade the canonical finding.

No state-changing success is returned until required audit acknowledgement.
Invalid transition, missing context, reviewer=implementer on TR-06, unauthorized
downgrade/hold/export, stale version and backend failure must reject safely.
Mutation privileges require CSRF/session protection. Free text uses bounded
sanitized content and cannot contain raw telemetry or credentials.

M4/M6 test each transition allow/deny, concurrent conflict, duplicate request,
audit outage, escalation clock, expired acceptance and reopen behavior. Actual
owner responses and sign-offs must be linked in the tracker. Design delivery
does not complete pending human checkpoints #14/#21 or implement the workflow.
