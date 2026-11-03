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


## 2026-11-03 verified-main reconciliation and scoped hardening

**Verified baseline:** `main` at `b522952927290d7cd0621fa0bde43a26d8d88dad`.
The latest exact-main workflows observed before this branch were all green:
[Mock API Security Tests #41502130599](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41502130599),
[Analytics Security Tests #41502130655](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41502130655),
and [Member 3 Loopback Integration #41502130586](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41502130586).
These runs validate the repository at that main SHA; they do not supply human approval or prove the outstanding Day 20/21 gates.

### Day 20 — candidate storage is not acceptance

PR [#121](https://github.com/madhab-tech-cyber/APIsenX/pull/121) added
`analytics/durable_store.py` and `tests/test_durable_store.py`. The implementation
is an opt-in local SQLite candidate. `AuditWriter` still defaults to
`MemoryStore`; a caller must explicitly inject the candidate. Its current
retention bound is at most seven days, so it cannot satisfy RT-05's 90-day
maximum as written, and it does not implement per-class retention, authenticated
database roles, deletion receipts, export/backup expiry, restore-time re-purge,
case-scoped RBAC, audited reads/exports, or protected integrity checkpoints.
SQLite is not the proposed PostgreSQL/KMS architecture and is not treated as
service-owner approval.

This branch hardens only the candidate's local contract: it rejects SQLite
in-memory/URI paths, requires timezone-aware clocks, normalizes timestamps to
UTC before expiry comparisons, and explicitly requests SQLite FULL synchronous
commit behavior. These changes do not turn the candidate into an accepted
audit service or make it the runtime default.

### Day 21 — optional observer isolation

The Mock API's optional monitor-only observer is not an authorization boundary.
This branch catches unexpected observer exceptions at the API middleware
boundary, logs only a fixed outcome, and preserves the already-produced API
response. A deterministic regression injects a synthetic failing observer and
checks successful API behavior, unchanged order state, and absence of exception
text from diagnostics.

The observer still sends telemetry only. No signed-decision consumer,
enforcement adapter, route-specific enforcement circuit breaker, or active
rule is introduced. Integrated failure/recovery, durable-audit outage,
restart-safe behavior and human-led acceptance remain pending.

### Governance correction and release safety

Issues [#83](https://github.com/madhab-tech-cyber/APIsenX/issues/83),
[#102](https://github.com/madhab-tech-cyber/APIsenX/issues/102) and
[#89](https://github.com/madhab-tech-cyber/APIsenX/issues/89) were found closed
by the repository owner on 2026-11-02 even though the approval record remains
blank and their own evidence bodies retain outstanding requirements. They are
being reopened with corrected, evidence-based status; closure state alone is
not evidence of implementation, administrator action or human acceptance.

Keep AP-1.0 in `monitor_only`, active enforcement rules at zero, and release
**NOT APPROVED**. No production deployment, branch-protection change, human
sign-off or enforcement activation is claimed.


### Member 5 Day 20/21 log and outage follow-up — 2026-11-03 branch candidate

The API request correlation UUID is now passed as the optional observation event
UUID. This lets the application audit line's `correlation_id` be joined to the
Sentinel event's `event_id` without adding user identity, raw URL, query, body
or credentials to the event. The adapter validates a caller-supplied UUID and
continues to generate one when used independently. A deterministic API test
uses a synthetic analytics HTTP 503 and checks that the event UUID matches the
response correlation header and application log, while the API still returns
its successful result and order state remains unchanged.

This is a mocked service-unavailable test, not a live database outage. The
analytics service currently uses volatile storage by default; no production
database is configured in this lab. Existing analytics audit-append failure
tests exercise the bounded 503 path at the analytics component boundary. A
real approved database outage/recovery demonstration remains pending.

### Additional 2026-11-03 route-authority regression

The same candidate branch extends the observer-outage regression across RF-01
through RF-04 API operations. A synthetic observer exception is injected after
the API has produced its response. The test checks that owner reads and
authorized admin reads still succeed, cross-owner and unauthorized admin reads
remain denied, and an authorized PATCH completes without being rolled back by
optional telemetry failure. Correlation IDs remain present and exception text
is not exposed. This is a deterministic mock-only test; it does not simulate a
live analytics/database outage or implement signed-decision enforcement.

The Day 20 candidate test suite now also injects a deterministic SQLite trigger
failure on the second row of a batch and verifies that the first row is rolled
back. This checks the candidate's transaction atomicity under a mid-write
storage error only; it does not supply the missing retention, authorization,
backup/restore, checkpoint or human-approval controls.

### Exact candidate validation — 2026-11-03

PR [#123](https://github.com/madhab-tech-cyber/APIsenX/pull/123) candidate
head `7c391ece7d31ac30992abd4d29d63a116a39fca4` passed all three exact-head
workflows:

- [Mock API Security Tests #41574896563](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41574896563):
  451 tests, Ruff, Bandit, dependency audit, loopback integration and bounded
  Day 19 load stages passed.
- [Analytics Security Tests #41574896521](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41574896521):
  451 tests, detection corpus/review demo, frozen candidate verification/build,
  Ruff, Bandit, secret scan and dependency audit passed.
- [Member 3 Loopback Integration #41574896577](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41574896577):
  Rust library checks and real loopback Rust/Python batch handoff passed.

The candidate includes the observer-outage RF-01–RF-04 API authority matrix and
the SQLite mid-batch rollback regression. These are synthetic/component-level
tests, not live database outage or production acceptance. PR review is
requested but no review decision is recorded. Service-owner architecture
approval and independent approval remain absent. Day 20/21 and release gates
remain BLOCKED; AP-1.0 stays `monitor_only`, active rules stay zero, and
release remains **NOT APPROVED**.


## 2026-11-03 post-merge verification — main at b0e4c704da7d3eeaa2beb0724150d6b10cadb6a9

This section supersedes earlier candidate/pending-PR descriptions above where
they conflict with the verified post-merge state.

### Exact-main CI

All three workflows completed successfully on the exact current main SHA:

- Mock API Security and Quality Gates:
  https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41629873808
  Steps passed: Ruff, Bandit, dependency audit, loopback integration, API and
  OpenAPI tests, and bounded Day 19 load stages.
- Analytics Security and Quality Gates:
  https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41629873988
  Steps passed: API/contract/analytics regressions, detection corpus and review
  demo, frozen candidate verification/build, Ruff, Bandit, secret scan and
  dependency audit.
- Rust/Python Loopback Contract:
  https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41629873851
  Steps passed: locked Rust library checks and real loopback Rust/Python batch
  handoff.

### Day 20 — what changed and what remains blocked

PR #123 is merged. The opt-in SQLite candidate now rejects in-memory/URI paths,
requires timezone-aware clocks, normalizes timestamps to UTC, requests FULL
synchronous commits, and has a mid-batch SQLite failure rollback regression.
It remains opt-in; `AuditWriter` still defaults to volatile `MemoryStore`.

Still missing: service-owner approval of storage architecture and key ownership;
independent architecture review; authenticated role separation; RT-01–RT-08
runtime retention (including RT-05 90-day maximum); deletion receipts and
derivative/export/backup expiry; restore-time re-purge; case-scoped RBAC and
audited reads/exports; protected integrity checkpoints; and approved runtime
integration tests. Issue #83 remains OPEN.

### Day 21 — what changed and what remains blocked

PR #123 is merged. The optional monitor-only observer is now isolated from API
responses when it raises unexpectedly; diagnostics use a fixed failure outcome.
The API correlation UUID is reused as the Sentinel event UUID, and tests cover
mocked analytics HTTP 503, observer exceptions, and RF-01–RF-04 API authority
under observer failure.

These tests do not simulate a live durable-database outage. The observer remains
telemetry-only: no signed-decision consumer, enforcement adapter, or active
enforcement rule exists. Integrated route-specific dependency failure,
durable-audit append failure, restart-safe recovery, approved-environment
evidence and separate dated owner/independent decisions remain pending. Issue
#102 remains OPEN.

### Release and governance

Issue #89 remains OPEN. The branch object previously reported
`protected: false`; the detailed protection endpoint returns HTTP 403 to this
connection, so effective protection cannot be verified or changed here. No
administrator action, human-led demonstration, service-owner approval or
independent-reviewer approval is claimed.

Keep AP-1.0 `monitor_only`, active enforcement rules at zero, and release
**NOT APPROVED**. Passing CI validates the tested code at this SHA; it does not
satisfy the outstanding architecture, operational, administrative or human
acceptance gates.
