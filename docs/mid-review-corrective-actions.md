# Day 15 Review Feedback and Corrective Assignments

**Owner:** Member 1 — Team Lead and Security Architect

**Recorded:** 2026-10-17 (Asia/Calcutta), against merged `6b1a427`.

## Feedback provenance

The October 15 [rehearsal](day14-mid-review.md) and October 17
[verification](member1-oct17-verification.md) supply repository findings.
No human reviewer comments, meeting minutes or mentor sign-off were supplied
for this task. The peer-feedback slot remains PENDING. Items below are Member 1
repository-review dispositions and assigned next work, not invented quotations,
proof of delivery to a person or accepted owner handoffs.

## Corrective register

| ID | Review finding / disposition | Accountable owner / support | Concrete closure evidence | Target / status |
|---|---|---|---|---|
| CA-01 | D11-F01 still permits customer admin access with empty/all-owned inventories | M5 / M6, M1 | Independent permission gate; both customers denied across inventory shapes, admin allowed; missing permission/unknown role and no-mutation assertions | 2026-10-21 and before admin acceptance/release; OPEN |
| CA-02 | AP-1.0 tenant/sharing/explicit permission/version rows lack implementation | M5 / M4 | Reviewed schemas, deny-by-default decisions and every PT row paired with benign/attack tests | Before Week 2 re-entry; BLOCKED |
| CA-03 | M4 detector and executable RN/DS/holdout corpus absent | M4 / M5, M6 | RN/DS regressions, frozen 600-case holdout, 24+ fault cases, three replays with per-family counts | Before accuracy approval; BLOCKED |
| CA-04 | Sensor source, supported Linux profile and event compatibility unaccepted | M2 / M3, M4, M5, M1 | Approved HTTPS-safe metadata source, versioned bounded schemas, privacy/IPv6 scope resolution and Linux build/load/loss evidence | Before interface integration; BLOCKED |
| CA-05 | Collector/enforcement and rollback absent | M3 / M4, M1 | Monitor-only adapter, authenticated decisions, circuit breaker and rollback fault tests under Day 16 criteria | Before any activation review; BLOCKED |
| CA-06 | No integrated latency/resource measurements | M3 / M2, M4, M6 | MRVP-1.0 paired runs and Day 19 bounds with raw denominators and safe evidence digests | Before capacity claim; BLOCKED |
| CA-07 | CI exists but member5 base filter excludes PRs into main | M6 / M5, M1 | Main-targeting PR and relevant branch triggers, nonzero jobs on reviewed revision and required-check evidence | Before next integration approval; OPEN |
| CA-08 | Direct pins exist; locks/SBOM/dedicated scans and real review ownership missing | M6 / all owners | Transitive lock/provenance, SBOM, dependency/static/secret and applicable container scans; actual CODEOWNERS and protection verification | Before next integration approval; OPEN |
| CA-09 | Contract checks are partial; JWT/fixture security drift remains | M5 / M4 | Security parity and bidirectional operation comparison, resolved permission vocabulary, error/schema assertions | Before discovery acceptance; OPEN |
| CA-10 | Audit storage and investigation controls absent | M4 / M6, M1 | Day 20 retention/RBAC/tamper/deletion tests, append-failure and export evidence | Before audit integration; BLOCKED |
| CA-11 | Peer feedback and owner acceptance unavailable | M1 / affected owners | Dated reviewer comment reference, disposition, actual owner response and unresolved objection list | Before checkpoint sign-off; PENDING |

## Assignment changes and escalation

M5 remains the accountable D11-F01 remediation owner; M6 explicitly takes CI
integration trigger correction and regression execution, with M5 support.
M4 owns the combined policy/detection corpus and M3 owns adapter/performance
evidence. These are responsibility assignments in Git, not changes to external
issue assignees or messages to teammates. Existing ownership in the risk
register remains applicable; no person is declared inactive without evidence.

M1 checks dependencies at the next review. Missed targets keep the relevant
gate blocked and require a recorded new plan; do not extend the D11-F01
deadline silently. Release stays blocked by High residual risks. Human feedback
must be linked and dispositioned before Day 15's feedback obligation is complete.

## Re-entry order

Close CA-01 and align contract/CI first; accept observation schemas and build
the monitor-only pipeline next; execute policy/accuracy/failure/performance
cases; then submit concrete candidate rules for independent approval. A merged
documentation artifact alone does not advance an activation state.
