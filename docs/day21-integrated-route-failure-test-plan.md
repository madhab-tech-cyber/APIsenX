# Day 21 — integrated route-failure and recovery test plan

**Status: preparation only — no integrated runtime execution is claimed.** This plan turns FAIL-LAB-1.0 into a route-by-fault acceptance matrix for the approved synthetic lab. It supplements the policy in [route-failure-policy.md](route-failure-policy.md) and the Day 20 storage test plan. Track integrated acceptance on [Issue #102](https://github.com/madhab-tech-cyber/APIsenX/issues/102). It does not implement an enforcement adapter or authorize active rules.

## Preconditions

Do not run the integrated cases until all of the following are evidenced:

- [x] Service-owner architecture decision: **APPROVE**, recorded on [Issue #83](https://github.com/madhab-tech-cyber/APIsenX/issues/83) at 2026-11-09 16:29:25 UTC, isolated synthetic lab only.
- [ ] Independent-review closure: @jayitape recorded **APPROVE WITH AMENDMENTS / CLARIFICATIONS** on 2026-11-09 17:09:36 UTC; the six clarifications merged in PR #147, but reviewer closure confirmation remains pending.
- [ ] Service owner confirms or amends the remaining A6 objectives. Only 100,000 synthetic events, rolling 7-day backups and lab-hours single-instance/no-HA availability have been confirmed; RPO/RTO, queue/drop, checkpoint/retention backlog and recovery thresholds remain unapproved.
- [ ] The approved durable audit implementation and schema/migration version are deployed in a disposable, isolated synthetic environment.
- [ ] The test environment contains the actual Mock API, analytics service and approved audit backend. Add collector/dashboard only for the end-to-end demonstration; do not substitute mocks for a required live boundary.
- [ ] A separate signed-decision consumer/enforcement adapter has its own approved design and review before any such component is included. The current observer is telemetry-only.
- [ ] Exact commit SHAs, safe reset procedure, bounded fault-injection controls and rollback/disable procedure are recorded.

If any prerequisite is absent, mark the affected scenario BLOCKED. The owner decision and conditional review do not authorize runtime implementation or an integrated run while reviewer closure, remaining A6 decisions or infrastructure are missing. Never run against production, a third-party system, or a shared database. Use synthetic identities and data only; inject credentials through the approved secret mechanism.

## Common fault-injection set

Apply each fault only at the named disposable dependency boundary and record the injected component, start/end time, timeout bound and sanitized outcome.

| Fault ID | Injection | Required common invariant |
|---|---|---|
| FI-01 | Identity/policy/context provider timeout or unavailable response | Unknown or untrusted authoritative context denies the API action; no object data or mutation |
| FI-02 | Optional observer/detector timeout or exception | API authentication, ownership, tenant, function and field checks remain authoritative; optional telemetry cannot grant or deny |
| FI-03 | Malformed, stale, unknown or replayed optional decision | Reject the decision, disable the unhealthy overlay, expose bounded degraded state and remain monitor-only |
| FI-04 | Bounded queue/capacity exhausted | No unbounded queue, raw disk spool, silent bypass or false success acknowledgement |
| FI-05 | Required durable audit append timeout, permission failure or storage outage | Apply the route-specific audit rule below; never claim an uncommitted append succeeded |
| FI-06 | Process interruption between audit intent, mutation and completion | An intent alone is not success; reconcile deterministically and never duplicate a mutation |
| FI-07 | Restart followed by dependency recovery | Restart defaults to monitor-only; verify committed state and audit/checkpoint continuity before recovery; never reactivate a previous authorization |

A retry with the same idempotency key may return the original committed outcome only when the backend proves that commit occurred. A conflicting payload for the same key must be rejected without changing the original record.

## Route-by-route acceptance matrix

| Route | Required failure and recovery assertions |
|---|---|
| **RF-01 — GET /orders** | Invalid identity returns 401; unavailable authoritative policy returns bounded generic 503. Under FI-02/FI-03, return only data independently authorized and filtered by the API; mark optional observation degraded. If required audit append fails for an ordinary owner read, apply the policy's visible degradation behavior and do not claim durable audit success. |
| **RF-02 — GET /orders/{orderId}** | Unknown/untrusted context returns no object data. Cross-owner requests preserve the privacy-safe non-disclosure response. Determine owner versus privileged read from the server-side authorization result, never a client flag. An ordinary owner read may continue with visible audit degradation; a privileged read fails closed if its required audit append fails. |
| **RF-03 — PATCH /orders/{orderId}** | Keep API identity, permission, ownership and field validation authoritative during FI-02/FI-03. If required durable audit append is unavailable, return bounded generic 503 before mutation. For FI-06, prove no partial write, no false success and no duplicate mutation after retry/recovery. |
| **RF-04 — GET /admin/orders** | Keep the API admin-function permission gate authoritative during FI-02/FI-03. If required durable audit append is unavailable, return bounded generic 503 before privileged data delivery. Prove no partial response or protected data leak. |
| **RF-05 — unknown route/method or invalid path** | Router/validation rejects the request. Emit only bounded privacy-safe route/counter metadata; raw path, query values, credentials and exception text must not appear in diagnostics. Route drift alone must not block unrelated authorized API work. |

The route-specific audit behavior above follows FAIL-LAB-1.0. In particular, do not generalize RF-01/RF-02 ordinary owner-read degradation to RF-03 privileged writes or RF-04 privileged data delivery.

## Deterministic component regression — 2026-11-11

`tests/test_day21_route_failure_matrix.py::Day21OptionalSentinelFailureMatrixTests.test_invalid_and_unknown_routes_never_get_signed_recommendations` exercises an invalid path (`ROUTE_INVALID`, no route) and an undocumented path (`ROUTE_DRIFT`, synthetic `/__unknown__` route) using a resolver result bound to the request event ID. The recommendation service must reject both reason codes before audit append or signature creation and return bounded `503 CONTEXT_UNAVAILABLE`.

This is component-level regression evidence only. It does not inject failures into the integrated API/analytics/durable-audit path and does not satisfy the route-by-route acceptance matrix or its human approval gates.

The guard changes frozen analytics source, so this branch refreshes `analytics/release-candidate.json` and `docs/member4-review-checkpoints.json` to pin the new source digest. The candidate remains `monitor_only`, `release_approved=false`, and every acceptance gate remains `pending`. This is a source-freeze update only, not a human approval or release authorization.

## Execution sequence

1. Record the exact tested commit, schema/migration version, environment identifier (non-secret) and baseline fixture digest.
2. Verify normal authorized owner read, cross-owner denial, customer/admin function denial, authorized admin read and permitted synthetic PATCH before injecting faults.
3. For each RF-01–RF-05 row, execute the applicable FI-01–FI-07 cases. Record actual status, bounded error code, correlation ID and whether data was returned or mutated.
4. For RF-03, snapshot the target object before each failure. Compare it after failure and after recovery; require byte-for-byte equivalent state when the action was not committed.
5. For RF-04, use synthetic leak markers and verify no privileged response body is delivered when required audit append fails.
6. For RF-02, test both ordinary owner and privileged-read paths. Verify classification is derived from the server authorization decision.
7. For RF-05, send synthetic path/query markers and verify they are absent from response diagnostics and application logs.
8. Restart only the lab processes created for this run. Verify monitor-only defaults, committed audit sequence/checkpoint continuity, no stale authorization reuse and no duplicate mutation.
9. Reset the disposable environment using the approved procedure. Verify fixtures and test records are restored or purged as documented.

## Evidence record — fill only after a real run

- **UTC start/end:**
- **Environment ID (non-secret):**
- **API / analytics / audit service SHAs:**
- **Schema and migration version:**
- **Operator and independent witness:**
- **Fault IDs and route IDs actually executed:**
- **Observed status/error categories:**
- **No-mutation / no-data-delivery evidence:**
- **Restart and recovery evidence:**
- **Sanitized log/artifact links:**
- **Failures, skipped cases and remediation:**
- **Service-owner decision (name/date):**
- **Independent-reviewer decision (name/date):**

Never attach bearer tokens, DSNs, raw request bodies, personal data, key material or unredacted database errors.

## Acceptance boundary

Automated component tests, mocked HTTP 503 cases, the optional observer tests, policy-document checks and the Day 20 PostgreSQL preparation harness do not satisfy this integrated matrix. A skipped database test is not a pass. No route is accepted until its required cases have exact-SHA evidence from the approved integrated environment and separate owner/reviewer decisions.

Keep AP-1.0 `monitor_only`, active enforcement rules at zero, and release **NOT APPROVED**. The current observer remains telemetry-only; do not add or activate a signed-decision consumer as part of this preparation task.
