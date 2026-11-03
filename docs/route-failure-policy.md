# Day 21 Route-Specific Failure Policy

**Owner:** Member 1. **Date:** 2026-10-19. **Policy:** `FAIL-LAB-1.0`.

**Decision:** Design behavior approved for implementation. Active enforcement
remains unapproved pending ENF-1.0 evidence and actual owner review.

## Authoritative control boundary

Fail-open applies only to optional Sentinel observation/enforcement overlays;
it never bypasses API authentication, permissions, tenant/ownership or field
validation. Missing or untrusted identity/policy context denies the API action.
Sentinel cannot infer an allow from a dropped event or failed detector.

| ID / operation | Authentication/policy dependency fails | Optional observation/detector/adapter fails | Required durable audit fails |
|---|---|---|---|
| RF-01 `GET /orders` | Fail closed: 401 for invalid identity, generic 503 for unavailable authoritative policy | Continue only after API authorization/filtering; disable active overlay and mark degraded | Owner read may continue with visible audit degradation; never claim durable audit success |
| RF-02 `GET /orders/{orderId}` | Fail closed; no object data on unknown context | Continue only if API independently authorizes; no stale Sentinel deny | Ordinary owner read may continue with degradation; privileged read fails closed if required audit cannot be appended |
| RF-03 `PATCH /orders/{orderId}` | Fail closed; no mutation | Keep API permission/field checks; disable unhealthy overlay | Fail closed with generic 503 before mutation; no unaudited privileged write |
| RF-04 `GET /admin/orders` | Fail closed independent of inventory shape | Keep API function permission gate; disable unhealthy overlay | Fail closed with generic 503 before privileged data delivery |
| RF-05 Unknown route/method or invalid path | Router/validation rejects as appropriate; never invent a permission | Privacy-safe unknown/invalid counter; drift alone cannot block | No raw path/credentials in fallback diagnostics |

Policy applies to future durable audit integration; current stdout logs do not
implement this column. Existing behavior has not been changed or newly certified.
For RF-02, owner versus privileged-read classification must be derived from the
server authorization decision, never a client flag. Unsupported context denies.
Do not leak other-owner existence through 403/404 differences; retain the pending
non-disclosure review rather than changing client status codes by guesswork.

## Circuit breaker, recovery and emergency controls

Use [ENF-1.0](enforcement-approval-and-rollback.md) clock/source/decision TTL,
resource, audit and latency triggers. Reject stale/unknown decisions; stop
active rules and expose bounded degradation/loss counters. Restart defaults to
monitor-only. Recovery does not reactivate a previous authorization.

An audit outage must not prevent emergency disablement. A privileged write must
either obtain a durable pre-action audit intent before mutation with a reliable
completion/outbox design, or be rejected. Test crashes between intent, mutation
and completion: an intent alone is not proof of success, and replay must not
duplicate a write. M4/M5 agree storage semantics before implementation approval.

M3/M4/M5/M6 must test each row with dependency timeout, malformed/replayed
decision, policy loss, full queue, audit failure, restart and safe recovery.
Prove normal authorized access, unchanged denial and no partial mutation/data
delivery; record actual statuses and durable outcomes. Per-route implementation
acceptance remains BLOCKED until these tests and independent review pass.
