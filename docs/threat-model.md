# Threat Model

**Owner:** Member 1 - Team Lead and Security Architect

**Last reviewed:** 2026-10-13

**Scope:** The authorised API-Sentinel laboratory described in
[`scope-and-governance.md`](scope-and-governance.md).

Data handling follows
[`data-classification-policy.md`](data-classification-policy.md), and identity
requirements follow
[`authentication-decisions.md`](authentication-decisions.md).
The intended component interfaces and failure behavior are recorded in
[`integration-data-flow.md`](integration-data-flow.md).

## 1. Method and security objectives

This model uses asset, data-flow and trust-boundary analysis with STRIDE-style
threat prompts. Each material scenario maps to an entry in
[`risk-register.md`](risk-register.md), where likelihood, impact, mitigation,
evidence, residual risk and ownership are tracked.

The project must preserve:

- **Confidentiality:** never expose real credentials, tokens, personal data or
  sensitive captures; minimise and mask authorised lab telemetry.
- **Integrity:** identity, ownership, policy, OpenAPI contracts, findings and
  audit evidence must not be silently altered.
- **Availability:** observation and analysis failures must not create an
  uncontrolled outage; enforcement requires an approved rollback path.
- **Accountability:** every security decision and administrative action must be
  attributable through privacy-safe, tamper-evident evidence.
- **Authorisation:** all testing is limited to team-owned lab targets and every
  sensitive API path applies server-side authentication and authorisation.

## 2. Assumptions and constraints

- Only synthetic identities, orders and traffic are permitted.
- The mock API is the source of truth for identity, role and object ownership.
- The eBPF layer does not decrypt HTTPS. Route-level data must come from an
  explicitly authorised application hook, controlled proxy or TLS termination
  point; TLS must never be weakened.
- Enforcement remains monitor-only until deterministic criteria, route-specific
  failure behaviour and rollback have been reviewed and approved.
- Repository and CI credentials are infrastructure secrets and must never enter
  source files, logs, fixtures or evidence.
- Components that currently contain only README placeholders are design scope,
  not implemented or tested security controls.

## 3. Asset inventory

| ID | Asset | Classification | Required properties | Primary owner |
|---|---|---|---|---|
| A-01 | Test identities, bearer credentials and dashboard sessions | Restricted, synthetic only | Confidentiality, authenticity, expiry and replay resistance | M1/M5/M6 |
| A-02 | Object ownership, tenant, sharing and role policy | Security critical | Integrity, versioning, deny-by-default behaviour and traceability | M1/M4/M5 |
| A-03 | OpenAPI contract, route inventory and normalisation rules | Internal, security critical | Integrity, versioning and implementation consistency | M1/M4/M5 |
| A-04 | Kernel events and normalised telemetry | Restricted after collection | Minimisation, bounded size, authenticity and freshness | M2/M3/M4 |
| A-05 | Detection, rate-limit and enforcement rules | Security critical | Integrity, deterministic evaluation, approval and rollback | M1/M3/M4 |
| A-06 | Findings, masked evidence and audit records | Restricted | Integrity, retention, access control and tamper evidence | M1/M4/M6 |
| A-07 | Dashboard roles, triage state and administrative actions | Restricted | Server-side authorisation, safe rendering and accountability | M1/M6 |
| A-08 | Source, dependencies, build artifacts, CI credentials and release evidence | Restricted or internal | Provenance, integrity, reproducibility and least privilege | M1/M6 |
| A-09 | Lab service capacity, latency and recovery controls | Internal | Availability, bounded resource use and observable failure | M1/M2/M3/M4/M5/M6 |

Real production credentials, traffic and personal data are prohibited inputs,
not project assets to collect.

## 4. Data flow and trust boundaries

The intended flow is:

`lab client -> mock API -> authorised observation point -> eBPF sensor -> collector -> analytics -> storage -> management API -> dashboard`

CI and dependency sources form a separate supply-chain flow into every build.

| Boundary | Data crossing | Principal threats | Required controls | Verification owner |
|---|---|---|---|---|
| TB-01 Lab client to mock API | Credentials, route parameters and request bodies | Spoofing, replay, injection, BOLA and BFLA | Validated authentication, server-side role/ownership checks, bounded schemas, safe errors and negative tests | M1/M5 |
| TB-02 Mock API to authorised observation point | Approved route and transaction metadata | Secret/PII over-collection, TLS weakening and telemetry forgery | Explicit hook/proxy approval, allowlisted fields, masking and TLS-preservation review | M1/M2/M5 |
| TB-03 Kernel sensor to user-space collector | Process, socket and route-boundary events | Malformed events, map exhaustion, spoofing and sequence loss | Verifier-safe bounded programs, versioned schema, size/type validation, sequence and drop metrics | M2/M3 |
| TB-04 Collector to analytics | Normalised event batches and health metrics | Tampering, replay, schema confusion and queue exhaustion | Authenticated encrypted transport, batch limits, freshness/replay checks, timeouts and backpressure | M3/M4 |
| TB-05 Analytics to storage | Masked telemetry, policy, findings and audit events | Sensitive persistence, unauthorised writes, tampering and over-retention | Mask before write, least-privilege identities, encryption, append-only audit design and purge policy | M1/M4/M6 |
| TB-06 Dashboard to management API | Sessions, queries and triage/enforcement actions | Privilege escalation, unsafe rendering, CSRF and audit bypass | Server-side RBAC on every action, short sessions, output encoding, CSRF protection and audit events | M1/M6 |
| TB-07 Repository/CI to build and release | Source, dependencies, artifacts and credentials | Dependency substitution, secret theft and unreviewed release | Protected branches, reviewed PRs, pinned dependencies, provenance, SBOM and security scans | M1/M6 |

Boundary controls are requirements until their implementation and tests are
linked in the risk register. Architecture text alone is not control evidence.

## 5. Threat scenarios

| ID | Boundary/assets | Scenario and impact | Required treatment | Risk |
|---|---|---|---|---|
| T-01 | TB-02/TB-05; A-01/A-04/A-06 | Credentials or personal data are captured, logged or persisted, causing disclosure | Minimise at source, mask before persistence, leak tests, access control and retention limits | R-001 |
| T-02 | TB-01/TB-04; A-01/A-02 | A caller, service or replayed event is accepted as a trusted identity or policy decision | Validated credentials, authenticated service links, expiry/audience/replay checks and versioned policy | R-007 |
| T-03 | TB-01; A-02 | Incorrect ownership or role evaluation permits BOLA/BFLA access | Explicit policy matrix, deny-by-default logic, labelled allow/deny fixtures and negative tests | R-002 |
| T-04 | TB-04/TB-06; A-05/A-09 | A false positive or unsafe failure mode blocks legitimate lab traffic | Monitor-only default, deterministic criteria, route failure matrix, circuit breaker and tested rollback | R-003 |
| T-05 | TB-03/TB-04; A-04/A-09 | Malformed or excessive events exhaust kernel/user-space memory or crash parsers | Bounded maps/queues/events, strict schema validation, fuzzing, stress tests and drop metrics | R-004/R-010 |
| T-06 | TB-01/TB-04; A-03 | Contract or normalisation drift hides a shadow route or misclassifies a documented route | Versioned contract, implementation comparison, parameterisation cases and drift tests | R-011 |
| T-07 | TB-05/TB-06; A-06/A-07 | A finding or administrative action is altered, deleted or performed without attribution | Restricted append path, correlation IDs, tamper evidence, retention and protected export | R-008 |
| T-08 | TB-07; A-08 | A vulnerable or substituted dependency/build artifact compromises the lab or release | Locked versions, provenance review, SBOM, dependency/static/secret/container scans | R-005 |
| T-09 | TB-06; A-01/A-06/A-07 | A dashboard user gains another role or views unmasked evidence | Server-side RBAC, short sessions, role tests, safe rendering and masked responses | R-009 |
| T-10 | TB-01/TB-03/TB-04; A-09 | Traffic, event or request floods make the pipeline unavailable | Rate limits, bounded queues, timeouts, circuit breakers, health metrics and capacity evidence | R-010 |
| T-11 | TB-01; A-01/A-09 | The deliberately weak lab token model is exposed or mistaken for production authentication | Bind to the authorised lab, label demo credentials, block production deployment and replace with validated tokens before release | R-007 |
| T-12 | TB-02; A-01/A-04 | The team attempts to observe HTTPS by disabling or bypassing transport security | Use only an approved observation point, document metadata-only limits and reject TLS-weakening designs | R-006 |
| T-13 | TB-03/TB-04/TB-05/TB-06; A-03/A-04/A-05/A-06 | An unversioned, incompatible or spoofed event/decision is silently accepted, causing telemetry loss, incorrect findings or unsafe enforcement | Versioned schemas, authenticated sources, bounds, freshness/deduplication, reject-unknown behavior and producer/consumer contract tests | R-013 |

## 6. Current evidence and known gaps

- The authorization and mock-API suites exercise owner/admin allow cases,
  cross-owner and function-level denial, missing/invalid credentials, malformed
  inputs, inactive identities and unknown roles.
- The current evidence applies only to the local mock API and synthetic fixtures.
  It does not validate the eBPF, collector, analytics, storage, dashboard or
  integrated trust boundaries.
- The lab currently uses static opaque demo tokens. Expiry, audience, signature
  and replay controls are not implemented. The fixture mechanism is conditionally
  approved only for the isolated local lab.
- A foundation data-classification policy now defines Public, Internal,
  Restricted, Secret and Prohibited handling. Runtime masking, retention,
  access-control and leak-test evidence is still absent.
- Dependency manifests, lock files, CI, SBOM generation and dedicated secret,
  static, dependency and container scans are not yet present.
- The checked-in OpenAPI contract and FastAPI behavior have known differences
  tracked in the Day 3 scaffold review and R-011.
- The Day 5 interface register assigns producer/consumer handoffs, but IF-02
  through IF-09 lack recorded owner acceptance and integrated contract/failure
  evidence. Schema-confusion risk is tracked in R-013.
- The Day 6 [`week1-threat-review.md`](week1-threat-review.md) re-evaluates all
  13 scenarios against current evidence. Every scenario remains applicable and
  none is closed; accountable follow-up is recorded in the risk register.

## 7. Review and acceptance process

Review this model whenever an interface, asset, data field, privilege, dependency,
enforcement action or deployment boundary changes, and at the Week 1, mid-review,
enforcement and release checkpoints.

A threat is not closed by documentation alone. Closure requires linked test or
operational evidence, an owner-approved residual rating and any accepted-risk
reason/deadline recorded in the risk register. Critical or high residual risk
blocks release.

