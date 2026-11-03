# Day 17 Proposed Blocking-Rule Review Register

**Reviewer:** Member 1. **Date:** 2026-10-17 (Asia/Calcutta).

**Scope:** Merged source `6b1a427` plus ENF-1.0 requirements.

No executable enforcement rule, adapter configuration or signed owner proposal
exists in the inspected collector/analytics directories. The rows below make
design candidates explicit for review; they do not imply a teammate submitted
code. Every candidate has been assessed against
[ENF-1.0](enforcement-approval-and-rollback.md). No wildcard activation is allowed.

## Candidate register

| ID/version | Exact candidate predicate and scope | Proposed action | Review result / missing evidence |
|---|---|---|---|
| BR-01/1 | Authenticated customer reads another owner's private `GET /orders/{orderId}`, with complete AP-1.0 tenant/grant context proving denial | `deny` in named lab only | HOLD: API currently denies ordinary cross-owner access, but tenant/share context, authenticated decision path and rollback are absent |
| BR-02/1 | Authenticated customer calls `GET /admin/orders` or `PATCH /orders/{orderId}`, with server-resolved function permission denied | `deny` in named lab only | HOLD: admin-list D11-F01 still permits some customer cases; no adapter or rule-specific false-positive/rollback proof |
| BR-03/1 | Normalized method/template missing from approved OpenAPI, or retired after a verified deadline | `alert` | MONITOR DESIGN ONLY: drift alone is insufficient for blocking; normalizer, retirement registry and authenticated source absent |
| BR-04/1 | Subject/method/route bucket or cost budget exhausted under the versioned Day 19 policy | `rate_limit` | HOLD: implementation, atomic multi-bucket accounting, legitimate workload and fairness evidence absent |
| BR-05/1 | A subject changes object IDs, request volume rises, or a model assigns high anomaly/severity | proposed `deny` | REJECT: insufficient deterministic authorization evidence; investigate or alert only |
| BR-06/1 | Raw unversioned kernel path or incomplete identity suggests a policy breach | proposed `deny` | REJECT: privacy/source/context gates fail; reject the decision and retain bounded health reasons |

M3 owns adapter implementations for BR-01/02/04, M4 owns predicates and source
contracts, M5 supplies server-policy truth and D11-F01 remediation, M6 supplies
regression/performance evidence, and M1 owns final decisions. HOLD and MONITOR
DESIGN ONLY allow design/replay development, not active behavior.

## Required resubmission record

For each version provide immutable code/config hashes, exact service/environment,
canonical method/template and opaque subject/resource scope, rule owner,
predicate/action/reason, AP/contract/schema versions, benign exclusions, evidence
for EG-01 through EG-08, kill-switch handle, rollback results, review references,
requested start/expiry and lease duration. No missing gate defaults to pass.

Changes to any predicate, digest, scope, action, permission model or expiry
require a new version and review. Retire the previous authorization; reject
conflicting versions. Operator rollback authority cannot be removed by a rule.

## Per-rule review checklist

Review malicious and benign cases together: owners, active shares, valid scoped
admins, missing/revoked permissions, empty/all-owned/mixed inventories, unknown
versions, duplicate/out-of-order decisions and downstream failure. Prove no
state mutation on deny and no raw identifier/query leakage. Review response
status with M5 and failure mode under Day 21 before activation.

For BR-04, test N-1/N/N+1 budget boundaries, simultaneous workers, bucket expiry,
rotation, retry/refill and cardinality exhaustion. For BR-01/02, independently
validate the API's original authorization rather than treating Sentinel as its
replacement. For BR-03, a legitimate new endpoint or encoded documented path
must not become a deny merely because it appears novel.

## Decision

Active rules approved: **0**. Active deny/rate-limit deployments: **0**.
Four candidates remain held/monitor design; two blocking rationales are rejected.
No existing firewall, kernel map or API route was changed by this review.
