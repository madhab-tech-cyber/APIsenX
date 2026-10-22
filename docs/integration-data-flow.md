# Integration and Data-Flow Baseline

**Owner:** Member 1 - Team Lead and Security Architect

**Date:** 2026-10-13

**Current-status refresh:** 2026-10-20 (Asia/Calcutta); baseline main
`683a93a7f59938d6e22e8402ed617d1f8cb36101`. See
[current Member 1 closeout](member1-closeout-2026-10-20.md), the historical
[Member 1 corrective evidence](member1-governance-correction.md) and the
[checkpoint register](member1-checkpoints.json). Older dated reviews are history.

**Status:** Foundation baseline; interfaces require owner review and implementation

**Related controls:** [`architecture.md`](architecture.md),
[`threat-model.md`](threat-model.md),
[`data-classification-policy.md`](data-classification-policy.md)

## 1. Purpose and current truth

This document coordinates the intended API-Sentinel integration and defines the
minimum information that may cross each component boundary. It is a design and
handoff baseline, not evidence that the full pipeline is running.

In merged main, the local mock API request path is implemented and tested.
PR #20 repaired D11-F01; 57 API/authorization/contract methods and all nine inventory
diagnostics pass. Independent closure review is still pending; the full
tenant/sharing/support/version matrix remains incomplete:

`lab client -> FastAPI authentication -> authorization policy -> synthetic JSON fixtures -> response and basic audit log`

M2 capture remains design/headers. M3's library is merged by PR #32 at
`006bd13`, with proposed v1.1 schemas, explicit null/ambiguous correlation and
unavailable/reset loss states. Its owner reports 22 macOS tests; the successful
PR job runs Python checks, not Rust/Linux integration. M6's React fixture UI is
still unmerged. No live sensor/collector/detector/dashboard acceptance is
established. M4 analytics remains a scaffold. Main has API/contract tests plus Ruff/dependency-audit CI with a
verified main-targeting PR trigger. M6's locked install, lint, TypeScript/build
and dependency audit pass locally on `39902b3`; no UI test command exists, and
its limited repository CI does not execute these build checks. None of that
establishes live findings or server-side dashboard authorization.
Protected storage/management services and complete
integration/security evidence remain absent. Interfaces below remain
**unaccepted** until producer/consumer evidence and review are linked.

## 2. Target flows

The target runtime telemetry flow is:

`lab client -> mock API -> approved observation point -> eBPF sensor -> collector -> analytics -> storage`

The operator flow is:

`dashboard -> management API -> analytics/storage`

The controlled decision flow is:

`analytics -> signed/versioned decision -> collector enforcement adapter -> monitor, alert, rate-limit or drop`

The supply-chain flow is separate:

`reviewed source and dependencies -> CI checks -> build artifacts/SBOM -> authorised lab release`

No component may bypass a trust boundary because it shares a host or repository.
Authentication, schema validation, data minimisation and audit requirements
still apply at every crossing.

## 3. Interface register

| ID | Producer -> consumer | Minimum data / contract | Classification | Security and failure requirements | Owner / status |
|---|---|---|---|---|---|
| IF-01 | Lab client -> mock API | HTTP method, documented route, bounded body and bearer credential under `openapi.yaml` | Credential is Secret in real use; current demo token is a Public lab fixture; request data is Internal or Restricted | Authenticate first, authorise server-side, validate size/type, return safe errors and never log credentials | M5 with independent review / local implementation and current operation/security contract checks pass; full AP-1.0 acceptance pending |
| IF-02 | Mock API -> approved observation point | Allowlisted method, normalised route marker, response status, timing and correlation reference | Internal; Restricted when linked to identity, object or finding | Preserve TLS; exclude raw credentials, cookies, query values and bodies by default; loss must not bypass API authentication/authorisation | M5 candidate application hook and server-generated request UUID exist and pass API/privacy tests; M1/M2/M4 joint contract/attachment acceptance pending |
| IF-03 | eBPF sensor -> collector | Versioned bounded kernel event: timestamp, process/cgroup reference, socket tuple or approved route marker, sequence and flags | Internal or Restricted | Verifier-safe bounded maps/events, type and length checks, sequence/drop counters; malformed events are rejected without crashing | M2 producer, M3 consumer / planned |
| IF-04 | Collector -> analytics | Versioned batch of normalised events plus source, batch, correlation and health metadata | Restricted | Mutually authenticated encrypted transport, replay/freshness checks, maximum batch/event sizes, bounded queues, timeout and backpressure | M3 producer, M4 consumer / planned |
| IF-05 | Analytics -> storage/audit | Masked telemetry summary, route inventory, policy version, finding and append-only audit event | Restricted; policy/contract material is Internal security-critical | Mask before write, separate least-privilege identities, encryption, idempotency, tamper evidence and approved retention/purge | M4 with M1/M6 review / storage not selected |
| IF-06 | Management API -> dashboard | Masked inventory, findings, health and triage state; bounded administrative commands | Restricted | Server-side RBAC on every request, short sessions, CSRF protection, safe rendering, pagination and audit of every change | M4 producer, M6 consumer / planned |
| IF-07 | Analytics -> collector enforcement adapter | Versioned policy/decision ID, target, action, reason, expiry and rollback reference | Internal security-critical; audit evidence is Restricted | Authenticated integrity, freshness, deterministic scope, monitor-only default, circuit breaker and tested rollback; reject unknown action/version | M4 producer, M3 consumer, M1 approval / planned |
| IF-08 | Components -> health/operations view | Availability, latency, queue depth, drop count, schema failures and build/version labels | Internal; Restricted if linked to a finding or host identity | No credentials or raw payloads; bounded labels; health failure cannot authorise traffic or hide audit failure | M2-M6 producers, M6 consumer / planned |
| IF-09 | Repository/dependency sources -> CI/release | Reviewed source, manifests, lock files, test/scan results, SBOM, provenance and artifact digest | Public/Internal; credentials and detailed findings are Secret/Restricted | Reviewed PRs, pinned dependencies, isolated credentials, deterministic tests, scans and provenance verification | M6 with M1 coordination / API main-PR CI passes; full-system locks/provenance/SBOM, dashboard/integration CI and independently verified protection remain pending |

## 4. Common event requirements

Before IF-03 through IF-08 are implemented, the producing and consuming owners
must agree on a machine-readable schema. Every event or decision type must define:

- `schema_name` and an explicit `schema_version`;
- a unique `event_id` or `decision_id` for deduplication;
- a privacy-safe `correlation_id` propagated across permitted boundaries;
- UTC event time and receive time, with a defined clock-skew tolerance;
- source component/instance identity and build version;
- data classification and an allowlisted payload;
- maximum field, event and batch sizes;
- stable outcome/error reason codes; and
- whether retry is safe and how duplicates are handled.

Unknown major versions, missing required fields, invalid sizes and invalid source
identity must be rejected or quarantined with a bounded metric. Consumers must
not silently coerce incompatible security decisions. Optional fields and
minor-version compatibility require contract tests agreed by both owners.

Raw authorization headers, cookies, passwords, keys, unrestricted query strings,
request/response bodies and real personal data are not valid telemetry fields.

## 5. Runtime sequence and control points

1. The lab client sends an authenticated request to the mock API.
2. The mock API validates identity and applies the reviewed authorization matrix.
   Observation failure never replaces or bypasses these checks.
3. An approved observation point emits only allowlisted metadata while keeping
   TLS protections intact.
4. The sensor emits a bounded, versioned event and increments loss/drop counters
   when it cannot enqueue safely.
5. The collector validates, normalises, correlates and batches events through a
   bounded queue before sending them over an authenticated encrypted link.
6. Analytics validates the batch, normalises routes, compares the approved
   OpenAPI contract, evaluates detection policy and masks sensitive fields.
7. Masked findings and audit events are written using separate least-privilege
   paths. A failed audit write is visible and cannot be reported as success.
8. The management API applies server-side RBAC before returning masked data or
   accepting an operator action from the dashboard.
9. Enforcement remains monitor-only until Member 1 approves deterministic
   criteria, per-route failure behaviour, performance evidence and rollback.

## 6. Failure and recovery baseline

| Failure | Required behaviour | Evidence required before integration approval |
|---|---|---|
| Missing/invalid client identity | Fail closed with 401; do not evaluate client-supplied identity | Authentication negative tests |
| Authorization context missing or ambiguous | Fail closed for the protected API action | Route and policy negative tests |
| Observation point unavailable | Keep application authorization intact; report degraded visibility; foundation enforcement stays monitor-only/fail-open | Health signal and recovery test |
| Malformed/oversized kernel event | Reject safely, increment bounded metric and continue processing valid events | Parser boundary/fuzz tests |
| Collector queue or analytics unavailable | Apply bounded buffering/retry, expose drops and avoid unbounded memory growth | Load, backpressure and restart tests |
| Unknown schema or policy version | Reject/quarantine; never guess a security decision | Producer/consumer compatibility tests |
| Storage or audit append failure | Surface a degraded/error state; never claim the audit action was persisted | Failure-injection and recovery evidence |
| Management API/dashboard unavailable | Do not weaken runtime API controls; prevent unaudited administrative changes | RBAC/session and outage tests |
| Enforcement adapter unhealthy | Disable optional Sentinel actions and restore monitor-only; preserve application authorization and route-specific required-audit failures | FAIL-LAB-1.0 route cases, circuit-breaker, latency and rollback tests |

[Day 21's route failure matrix](route-failure-policy.md) is specified; its runtime
fault/rollback evidence is still blocked. Design delivery is not execution.

## 7. Owner handoffs and acceptance gates

| Owner | Day 5 handoff | Required consumer acceptance |
|---|---|---|
| M5 | Runtime OpenAPI output, synthetic traffic cases, identity/ownership model and candidate observation hook | M1 approves auth/data constraints; M2/M4 confirm usable minimised fields |
| M2 | Kernel event proposal, attachment point, capability list, bounds and drop semantics | M3 validates parser/queue compatibility; M1 approves privilege and TLS posture |
| M3 | Collector batch, health and decision schemas plus retry/backpressure behavior | M4 validates ingestion compatibility; M1 approves failure/rollback behavior |
| M4 | Normalisation, finding, audit, storage and management API contracts | M3 confirms source fields; M6 confirms masked dashboard contract; M1 reviews policy mapping |
| M6 | CI/test/scan entry points, dashboard contract and release evidence format | M1 approves required checks; component owners prove their commands are reproducible |
| M1 | Interface register, classification, threats, risk owners and integration gates | Each producer/consumer records review and links passing contract/integration evidence |

An interface is accepted only when both owners approve one versioned contract,
positive and negative contract tests pass, failure behavior is demonstrated,
data classification is confirmed and the relevant risk evidence is linked.

## 8. Ordered integration plan

1. M5/M1 retain passing operation/security contract checks; M1/M2/M5 select the
   authorised observation point without weakening TLS. Do not re-report the
   repaired contract drift as an outstanding defect.
2. M2 and M3 agree IF-03 and demonstrate bounded malformed/drop behavior.
3. M3 and M4 agree IF-04, then prove authentication, replay handling,
   compatibility, backpressure and restart recovery.
4. M4 and M6 agree IF-05/IF-06 after masking, storage and management API choices
   are documented.
5. M3/M4 implement IF-07 in monitor-only mode; M1 separately approves any active
   action after security, performance and rollback evidence.
6. M6 makes the agreed test, contract, scan and SBOM checks required in CI before
   release integration.

## 9. Open blockers

- A candidate HTTPS-safe application hook exists, but observation provenance,
  request-marker transport and route coverage lack joint M1/M2/M4 acceptance.
- M3's event/decision schemas and library are merged; IF-03 through IF-08
  still lack accepted live producer/consumer compatibility evidence.
- Storage technology, management API and service-identity mechanism are not
  selected.
- Direct requirements, M3/M6 language lock files and M5 quality CI exist at the
  inspected refs; API main-PR checks and local dashboard builds pass. Complete
  reproducible integrated builds, dashboard/integration CI, dedicated secret
  and applicable container checks, and SBOM evidence remain missing.
- No integrated load, failure-recovery, masking, retention, RBAC or rollback
  evidence exists.
- Producer and consumer owners have not yet recorded acceptance of these
  interface proposals.
- Human checkpoint evidence remains pending despite closed #14/#21/#23; #33
  tracks actual closeout. M5 supplied real responses; PR #28 has one M1 approval
  for its own pinned revision. PRs #26/#31/#32 lack submitted independent reviews
  at the October 20 snapshot. That approval does not cover later changes.
- Main protection was approved by the project owner but could not be applied:
  the connector's protection endpoint returns HTTP 403 and CLI authentication
  is rejected. See the [owner action](main-protection-owner-action.md); do not
  claim protection is enabled.

These blockers keep the integrated pipeline and release status **not ready**.
