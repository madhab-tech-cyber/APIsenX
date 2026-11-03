# Day 16 Deterministic Enforcement and Rollback Criteria

**Owner:** Member 1; implementation M3/M4, API authority M5, verification M6.

**Date:** 2026-10-17 (Asia/Calcutta). **Policy:** `ENF-1.0`.

**Decision:** Design criteria approved for implementation. Active-rule approval
requires separate evidence and a recorded authorization. Current mode is
monitor-only; collector/adapter and decision transport are absent.

## 1. Decision eligibility

Active actions are limited to a team-owned synthetic lab. The API's own
authentication/authorization remains authoritative and always runs. Observation
failure never grants API access. A shadow route, changed object ID, unknown
context, statistical anomaly or severity label alone cannot authorize denial.

Before proposing a deny/rate-limit rule, every gate must pass:

| Gate | Required evidence |
|---|---|
| EG-01 Scope | Exact lab service/environment, canonical method/template, permitted principal/resource scope and explicit exclusions |
| EG-02 Policy | Versioned AP-1.0 decision from authenticated, authoritative identity, ownership, tenant, permission and sharing context |
| EG-03 Transport | Authenticated integrity-protected decision, schema/policy version, unique decision ID, issued/expiry times and replay rejection |
| EG-04 Determinism | Pure bounded predicate; same valid inputs/versions yield the same action/reason; no heuristic-only block |
| EG-05 Correctness | Every mandatory relevant regression passes, attack/benign near-neighbors included, zero application false allows/denies and no benign enforcement blocks |
| EG-06 Quality | MRVP-1.0 per-family holdout, fault/privacy and paired latency gates pass; losses/indeterminate outcomes accounted for |
| EG-07 Recovery | Circuit breaker, explicit kill switch, timed rollback, restart and audit outage tests pass |
| EG-08 Approval | Immutable rule/config digest, owner review, M1 decision, operator identity, expiry, rollback reference and audit append confirmation |

Evidence must match the proposed build, policy, corpus, environment and config
digests. An API regression result alone cannot satisfy EG-03/06/07. A failed or
missing gate keeps the proposal monitor-only. The Day 21 per-route failure
matrix is an additional prerequisite before any active route authorization.

## 2. Bounded candidate decision envelope

Required fields: schema version, rule ID/version, decision ID, authenticated
source, lab environment/service, canonical method/template, opaque subject and
resource scope, action (`alert`, `rate_limit`, `deny`), reason code, AP/contract
versions, issue/expiry time, configuration digest and rollback reference.
No credential, raw unknown path, query, cookie or body is valid input.

Initial lab bounds: serialized decision <= 4 KiB, <= 32 simultaneously active
rules, maximum decision age 2 seconds, decision TTL <= 5 seconds, clock skew
<= 1 second. Reject unknown fields/actions/major versions, stale/replayed
decisions and scope mismatches; count bounded reasons. Expiry uses a monotonic
deadline derived at authenticated receipt, with wall-clock validation. Clock
uncertainty disables active decisions. These are implementation requirements,
not measured capabilities.

Authorization lease is distinct from decision TTL: a named rule authorization
lasts at most 30 minutes for one lab run, with no automatic renewal. Expired
authorization removes active behavior even if individual decisions are fresh.
Any build, predicate, permission model or scope change requires new approval.

## 3. Rollout and circuit breaker

Use states `draft -> monitor_only -> reviewed -> authorized_lab -> expired`.
Only M1 can authorize the named version after required peer review. The operator
may always disable a rule. Starting or restarting an adapter defaults to
monitor-only; persisted state must not silently reactivate rules.

Before authorization, replay the frozen corpus three times and perform a
ten-minute monitor-only soak at the reviewed workload. Compare candidate
actions with server policy. No hypothetical deny may target a benign case.

Immediately disable active rules if a benign request is blocked, decision
validation fails, append-only audit acknowledgment fails, clock is uncertain,
adapter crashes/restarts or source heartbeat is older than 2 seconds. For
latency, evaluate a rolling 60-second window with at least 100 requests; a
baseline-referenced p95 delta >= 5 ms trips the breaker. Fewer observations
cannot establish a latency pass; do not authorize until the soak supplied the
minimum. Resource/queue limit breach also trips the breaker. Each trip requires
fresh review before reactivation; never loop automatically between active and
inactive modes.

## 4. Rollback runbook and pass criteria

1. Operator selects the exact rule/version or all-rule kill switch. Record
   actor, time, reason, config digest and correlation reference in protected audit.
2. Stop issuing active decisions; atomically swap the adapter to monitor-only
   and remove only API-Sentinel-owned rule/map entries using recorded handles.
   Never flush host firewall rules or unrelated eBPF programs.
3. Acknowledge disablement within 2 seconds. If control delivery is lost,
   maximum 5-second decision TTL provides the fallback; verify every adapter
   is inactive by 5 seconds. Failed acknowledgment is visible and remains an
   incident, never a success status.
4. Replay authorized owner/admin reads and updates and unauthorized customer/
   cross-owner requests. Legitimate requests resume; API denials still deny.
   Confirm no unrelated network rule, fixture or object state was changed.
5. Verify resource recovery, queues/loss counters and audit trail. If audit is
   unavailable, stop new activation and use a bounded minimised emergency record;
   the kill switch must still work and cannot wait on the failed audit service.
6. Record evidence and incident disposition. Require independent review and a
   new expiring authorization before reactivation.

Required tests cover normal rollback, lost control message, expired lease,
replayed decision, stale source, restart, corrupted config, clock jump, queue
exhaustion and unavailable audit. Every test proves both application protection
and removal of active Sentinel decisions, within the deadlines above.

## 5. Current disposition

R-003 and R-013 remain High/Open. This criteria approval authorizes neither a
blocking rule nor a network mutation. Candidate dispositions and concrete lab
authorization decisions are recorded separately in Days 17 and 18.
