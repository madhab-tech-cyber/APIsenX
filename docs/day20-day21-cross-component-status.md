# Day 20–21 cross-component acceptance status

**Baseline:** `main` at `35967e31249a814b3c22de2b2c435d225cab299d` (2026-10-29 17:12 UTC), after PR #98.
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


## 2026-10-30 scoped Member 5 continuation — candidate, not acceptance

**Verified main baseline:** PR #98 is merged at `35967e31249a814b3c22de2b2c435d225cab299d`.
Its reviewed diff normalizes OpenAPI contract line endings, adds cross-platform
fingerprint coverage, and refreshes the frozen candidate manifest. It does not
replace `analytics/audit.py` or `analytics/store.py` with durable storage.
The current analytics health response still reports `storage: volatile`; Day 20
remains blocked pending the service-owner architecture decision in Issue #83.

**Day 21 candidate tests on `automation/day21-route-failure-matrix-20261030`:**

- `tests/test_day21_route_failure_matrix.py` exercises missing and unsupported
  policy versions for RF-01 through RF-04. It asserts bounded denial, no order
  payload, and unchanged fixture state.
- A PATCH recovery case verifies that restoring AP-1.0 allows a retry with the
  same nonce after the rejected request; the failed precondition must not
  consume the nonce or mutate the order.
- RF-05 tests cover an unknown route and unsupported method while checking that
  synthetic path/query markers are absent from the response and application
  logs.

These tests cover the mock API's authoritative policy boundary and unknown-route
diagnostic privacy only. They do not establish optional observation/enforcement
overlay failover, circuit-breaker behavior, durable-audit outage semantics,
route-specific dependency timeouts, restart-safe recovery, or integrated
sensor-to-dashboard acceptance. Exact-head CI is pending; no local test run is
claimed.

The `main` branch object reports `protected: false`; the detailed protection
read endpoint returns 403 to the current connection. Issue #89 remains open
with all administrator and human-evidence requirements unchecked. No settings
were changed and no owner/reviewer decision is inferred.


## 2026-10-31 verified-main reconciliation

**Current main:** `6b0b21752dff8bcec2bce77f459a9f9df1e50bc2` (merge of PR #106).
This section supersedes the earlier October 29/30 candidate-state descriptions
above for the Day 21 branch/PR disposition.

### Day 21 engineering work now merged

- PR [#103](https://github.com/madhab-tech-cyber/APIsenX/pull/103) adds
  deterministic analytics recommendation-boundary tests for audit failure,
  resolver outage, stale policy and replay; exact-head API run
  [41006576369](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41006576369)
  and analytics run
  [41006576407](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41006576407)
  passed.
- PR [#104](https://github.com/madhab-tech-cyber/APIsenX/pull/104) adds atomic
  store/batch, volatile-store restart and bounded request-body timeout
  regressions; exact-head API run
  [41006977674](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41006977674)
  and analytics run
  [41006977736](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41006977736)
  passed.
- PR [#105](https://github.com/madhab-tech-cyber/APIsenX/pull/105) adds an
  optional loopback-only, bounded-timeout, monitor-only observation adapter;
  exact-head analytics run
  [41007254976](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41007254976)
  and API run
  [41007255025](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41007255025)
  passed.
- PR [#106](https://github.com/madhab-tech-cyber/APIsenX/pull/106) preserves
  the API policy rejection/nonce recovery/RF-05 tests and the optional
  analytics failure matrix; exact-head API run
  [41008892369](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41008892369)
  and analytics run
  [41008892367](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41008892367)
  passed.

These PRs provide component-level regression evidence and monitor-only
observation telemetry. They do **not** implement a signed-decision enforcement
adapter, accepted route-specific circuit breaker, production transport or
durable audit backend. Issue [#102](https://github.com/madhab-tech-cyber/APIsenX/issues/102)
has been reopened with only verified engineering items checked; integrated
failure/recovery and human/independent acceptance remain unchecked.

### Day 20 and release gates remain blocked

The main analytics audit path still uses volatile `MemoryStore`. Issue
[#83](https://github.com/madhab-tech-cyber/APIsenX/issues/83) is open because
no dated service-owner approval of the PostgreSQL/KMS operating model or
durable runtime acceptance evidence is recorded. Issue
[#89](https://github.com/madhab-tech-cyber/APIsenX/issues/89) is open because
`main` reports `protected: false`, and the administrator verification,
human-led integrated demonstration, service-owner decision and independent
reviewer decision are not evidenced.

Keep AP-1.0 `monitor_only`, active rules at zero, and release
**NOT APPROVED**. Passing PR CI, synthetic tests, or requested reviews do not
close these human, administrative, durable-storage or integrated-runtime gates.
