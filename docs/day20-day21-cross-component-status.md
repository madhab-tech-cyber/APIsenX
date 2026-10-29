# Day 20–21 cross-component acceptance status

**Baseline:** `main` at `d2ce9ae92eb079af0c07c4c3c9dc12bc8dbe1b0e` (2026-10-28 UTC), after PRs #90 and #91.
**Purpose:** Carry forward the next two scheduled acceptance areas without
confusing a policy document or a volatile prototype with completed runtime
controls.

## Day 20 — audit retention, access and investigation

**Existing engineering evidence**

- `analytics/audit.py` emits an allowlisted, masked audit projection into the
  bounded `MemoryStore`; its module explicitly describes this as volatile, not
  a durable audit service.
- `tests/test_analytics_service.py` covers controlled-clock TTL/capacity,
  deduplication, privacy-safe errors, append failure and recovery.
- `tests/test_analytics_decisions.py` covers masked audit fields, rule/version
  metadata and failure behavior.
- `tests/test_analytics_management.py` covers case-scoped reader behavior and
  denies evidence delivery when the access-audit append fails.

**Acceptance still blocked**

- No approved durable storage technology or implemented durable append-only
  audit store.
- No accepted 90-day audit retention, deletion receipts, derivative/backup
  expiry and restore re-purge evidence.
- No independently protected tamper-evident checkpoints, full case/role RBAC,
  approved hold/export workflow or human acceptance of the storage design.

The Day 20 policy remains the specification, not proof that these controls run.
Do not add raw runtime records to Git or silently fall back to disk when the
volatile store is unavailable.

## Day 21 — route-specific failure behavior

**Existing engineering evidence**

- `docs/route-failure-policy.md` defines RF-01 through RF-05 and distinguishes
  authoritative API authorization from optional observation/enforcement.
- Existing analytics decision/hardening tests exercise stale policy, unavailable
  context, audit failure and generic rejection.
- `tests/test_rate_limits.py` covers bounded 429/503 behavior, positive
  `Retry-After`, correlation headers and rejected updates that leave fixture
  state unchanged.

**Acceptance still blocked**

- The real enforcement adapter/circuit breaker and durable-audit integration
  are not accepted runtime components.
- Route-by-route timeout, malformed/replayed decision, policy loss, full queue,
  audit failure, restart and recovery tests have not established the FAIL-LAB-1.0
  contract across the integrated system.
- Service-owner and independent-reviewer decisions and exact-head integration
  evidence remain required.

The new policy-contract tests only guard the presence of the documented route
rows and blockers. They are **documentation regression tests**, not proof that
the runtime follows the matrix and not independent approval.

## 2026-10-29 scoped follow-up — candidate, not acceptance

- The analytics append boundary now returns HTTP 409 only for the known
  `EVENT_ID_CONFLICT` condition. Other `StoreError` reasons are mapped to the
  fixed `STORE_UNAVAILABLE` response so adapter-supplied details are not echoed
  into responses or application logs.
- Runtime regressions use synthetic internal-error markers to check the event
  and batch failure paths. The batch test checks that a failed append leaves no
  partial rows and that a retry succeeds after the simulated outage is removed.
- The policy-contract test now pins the expected operation and authorization,
  optional-overlay, and audit-failure behavior for each RF-01 through RF-05 row.

This is a bounded hardening change for the existing volatile analytics store.
It does not implement durable storage, retention/deletion receipts, a real
enforcement adapter/circuit breaker, or integrated mock-API route-failure
acceptance. The local execution environment could not resolve GitHub for a
clone, so no local test run is claimed; use the candidate PR's exact-head CI
results for automated validation. Day 20 and Day 21 acceptance remain BLOCKED.

## Verification and safety boundary

The API/analytics CI results for the separate Day 19 PR #76 fix are tracked on
that PR. This branch's tests and documentation must pass their own PR checks
before being credited. No local test execution is claimed here.

Keep `monitor_only`, zero active enforcement rules and release
**NOT APPROVED**. Do not infer human sign-off from requested reviews, merged
documentation, synthetic demos or passing unit tests.
