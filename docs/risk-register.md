# Risk Register

**Owner:** Member 1 - Team Lead and Security Architect

**Last reviewed:** 2026-10-13

**Related model:** [`threat-model.md`](threat-model.md)

## Rating and status rules

Likelihood and impact use **Low**, **Medium**, **High** and **Critical**. The
inherent rating describes exposure before planned controls; residual risk is the
current rating after evidenced controls only. Planned or documented controls do
not reduce residual risk until implementation evidence is linked.

Statuses are:

- **Open:** treatment is incomplete or lacks evidence.
- **Mitigating:** at least one control is evidenced, but required treatment
  remains.
- **Accepted:** Member 1 has recorded a reason, owner and deadline.
- **Closed:** required controls and tests are complete and reviewed.

Critical or high residual risk blocks release. Accepted risk does not bypass that
release rule.

## Active risks

| ID | Risk and affected boundary/assets | Likelihood | Impact | Inherent | Owner | Required treatment | Current evidence | Residual | Status / target |
|---|---|---|---|---|---|---|---|---|---|
| R-001 | Sensitive data or credentials are captured, logged or persisted (TB-02/TB-05; A-01/A-04/A-06) | Medium | High | High | M1/M2/M4/M6 | Enforce the data-classification policy, capture allowlists, masking before persistence, leak tests, least-privilege access and retention/purge rules | `data-classification-policy.md` defines handling and prohibits real data; runtime masking, retention and leak-test evidence are absent | High | Mitigating / Days 20 and 23, before storage integration |
| R-002 | Incorrect ownership or role evaluation permits BOLA/BFLA access (TB-01; A-02) | High | High | High | M1/M4/M5 | Versioned policy matrix, deny-by-default logic, labelled allow/deny fixtures and API negative tests | `AP-1.0` design exists; Day 11 D11-F01 confirms customer access to `/admin/orders` with empty/all-owned inventory despite 26 passing tests; sharing, tenant and explicit-permission evidence absent | High | Mitigating / D11-F01 due 2026-10-21 and before release; full matrix before Week 2 exit |
| R-003 | False-positive enforcement or unsafe failure mode causes an outage (TB-04/TB-06; A-05/A-09) | Medium | High | High | M1/M3 | Monitor-only default, deterministic criteria, route failure matrix, circuit breaker and tested rollback | Monitor-only/fail-open foundation decision is documented; enforcement is not implemented | High | Open / Days 16-22 |
| R-004 | eBPF privilege misuse, verifier failure or malformed events affect the host (TB-03; A-04/A-09) | Medium | High | High | M1/M2/M3 | Minimum capabilities, bounded verifier-safe programs/maps, versioned event schema, validation and stress evidence | Architecture constraints only; sensor and event schema are placeholders | High | Open / immediate: Week 1 exit missed; before sensor integration |
| R-005 | Vulnerable or substituted dependency/build artifact compromises the lab or release (TB-07; A-08) | Medium | High | High | M1/M6 | Manifests and lock files, provenance review, update policy, SBOM and dependency/static/secret/container scans | No manifests, lock files, CI, SBOM or dedicated scanners are checked in | High | Open / immediate: Week 1 foundation gate missed |
| R-006 | HTTPS observation assumptions lead to TLS weakening or missing route telemetry (TB-02; A-01/A-03/A-04) | Medium | High | High | M1/M2/M5 | Approve an application hook, controlled proxy or metadata-only source; document coverage; prohibit TLS weakening | Architecture, scope and threat model document the constraint; observation point is not selected | Medium | Mitigating / before sensor integration |
| R-007 | Static lab tokens are replayed, exposed or mistaken for production authentication (TB-01; A-01/A-02) | High | High | High | M1/M5 | Enforce `authentication-decisions.md`: keep fixtures lab-only, then replace them with validated, signed, expiring, issuer/audience-bound tokens and replay controls | Demo tokens are labelled as public fixtures; missing/malformed/invalid/inactive tests pass; signature, issuer, audience, expiry and replay controls are absent | High | Mitigating / before any non-local deployment |
| R-008 | Audit findings or administrative actions are altered, deleted or unattributed (TB-05/TB-06; A-06/A-07) | Medium | High | High | M1/M4/M6 | Structured correlation IDs, restricted append path, tamper evidence, retention/access policy and protected export | Mock API emits basic audit log lines; persistence, correlation and tamper evidence are absent | High | Open / Days 20-22 |
| R-009 | Dashboard privilege escalation or unsafe rendering exposes evidence (TB-06; A-01/A-06/A-07) | Medium | High | High | M1/M6 | Server-side RBAC, short sessions, output encoding, CSRF controls, role tests and masking | Dashboard is a README placeholder | High | Open / Days 23-27 |
| R-010 | Request/event floods exhaust queues or make the lab unavailable (TB-01/TB-03/TB-04; A-09) | Medium | High | High | M2/M3/M5 | Input/rate limits, bounded maps/queues/batches, timeouts, backpressure, circuit breaker and measured capacity | Input schemas exist for the mock API; no rate, queue or integrated load evidence exists | High | Open / Days 13 and 19 |
| R-011 | OpenAPI/implementation drift hides routes or produces incorrect discovery and client behavior (TB-01/TB-04; A-03) | High | Medium | High | M1/M4/M5 | Compare the checked-in contract with generated runtime OpenAPI; align authentication and error schemas; add drift tests | Day 4 review reconfirmed that the contract declares JWT while code uses opaque fixtures, error envelopes differ, and invalid updates are documented as 400 but return 422 | High | Open / immediate: Week 1 exit missed; before discovery integration |
| R-012 | Validation gaps allow broken or insecure changes to merge (TB-07; A-08) | High | High | High | M1/M6 | Deterministic test entry point, CI, named security checks, protected review and evidence retention | Explicit command runs 26 tests; default `unittest discover` runs zero; no CI or required security scanners exist | High | Open / immediate: Week 1 foundation gate missed |
| R-013 | An incompatible, unversioned or spoofed interface message causes telemetry loss, incorrect findings or an unsafe decision (TB-03/TB-04/TB-05/TB-06; A-03/A-04/A-05/A-06) | High | High | High | M1/M2/M3/M4/M6 | Machine-readable versioned schemas, authenticated sources, size/freshness/deduplication rules, reject-unknown behavior and producer/consumer compatibility/failure tests | `integration-data-flow.md` defines the interface and acceptance baseline; planned component schemas, owner acceptance and integration tests are absent | High | Open / immediate: before each interface merge |

## Day 6 unresolved-risk assignments

The Week 1 review in [`week1-threat-review.md`](week1-threat-review.md) confirms
that no risk is ready for acceptance or closure. The lead is accountable for
coordinating the named collaborators and linking the required evidence.

| Risk | Accountable lead / collaborators | Next required evidence | Target checkpoint |
|---|---|---|---|
| R-001 | M1 / M2, M4, M6 | Capture allowlist, pre-persistence masking, leak tests, access and purge evidence | Before storage integration; Days 20/23 final review |
| R-002 | M5 / M1, M4, M6 | Fix D11-F01 independent admin permission gate; add inventory-shape regression cases; M4 coordinates full `AP-1.0` detection matrix | D11-F01: 2026-10-21 and before release; complete matrix: Week 2 exit |
| R-003 | M3 / M1, M4 | Route failure matrix, circuit breaker, latency and rollback tests | Days 16-22; before active enforcement |
| R-004 | M2 / M1, M3 | Capability/attach-point review, bounded schema/maps, verifier, parser and stress results | Immediate; before any sensor integration PR |
| R-005 | M6 / M1 and component owners | Manifests/locks, provenance, SBOM and passing dependency/static/secret/container scans | Immediate; before the next integration merge |
| R-006 | M1 / M2, M5 | Approved observation point, coverage statement and TLS-preservation evidence | Before sensor integration |
| R-007 | M5 / M1, M6 | Signed-token validation, replay, rotation/revocation and service-identity tests | Before any non-local deployment |
| R-008 | M4 / M1, M6 | Correlated audit schema, protected append path, tamper, retention/access and failure evidence | Days 20-22; before audit integration |
| R-009 | M6 / M1 | Server-side RBAC, session/CSRF, masking and safe-rendering tests | Days 23-27; before dashboard integration |
| R-010 | M3 / M2, M5 | Bounded queue/batch/rate controls plus load, drop, backpressure and recovery measurements | Days 13/19; before capacity claims |
| R-011 | M5 / M1, M4 | Runtime-contract comparison and authentication/error/status drift tests | Immediate; before discovery integration |
| R-012 | M6 / M1 | Non-zero deterministic CI entry point, required review gate and retained check results | Immediate; before the next integration merge |
| R-013 | M1 / M2, M3, M4, M6 | Machine-readable schemas, owner acceptance and producer/consumer compatibility/failure tests | Before each interface PR is approved |

## Review requirements

Update this register whenever an interface, dependency, test result, security
finding, control implementation or ownership decision changes. Each update must:

1. preserve the stable risk ID;
2. link evidence that was actually executed or reviewed;
3. distinguish planned treatment from implemented controls;
4. record residual risk, owner and target checkpoint; and
5. obtain Member 1 approval for closure or acceptance.

