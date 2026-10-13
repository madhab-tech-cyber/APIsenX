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
| R-001 | Sensitive data or credentials are captured, logged or persisted (TB-02/TB-05; A-01/A-04/A-06) | Medium | High | High | M1/M2/M4/M6 | Capture allowlist, masking before persistence, leak tests, least-privilege access and retention/purge policy | Scope prohibits real data; runtime masking and leak tests are not implemented | High | Open / Day 23, before integration with storage |
| R-002 | Incorrect ownership or role evaluation permits BOLA/BFLA access (TB-01; A-02) | High | High | High | M1/M4/M5 | Versioned policy matrix, deny-by-default logic, labelled allow/deny fixtures and API negative tests | `authorization-policy.md`; 26 local authorization/mock-API tests pass, including cross-owner and admin denial | Medium | Mitigating / Week 2 exit |
| R-003 | False-positive enforcement or unsafe failure mode causes an outage (TB-04/TB-06; A-05/A-09) | Medium | High | High | M1/M3 | Monitor-only default, deterministic criteria, route failure matrix, circuit breaker and tested rollback | Monitor-only/fail-open foundation decision is documented; enforcement is not implemented | High | Open / Days 16-22 |
| R-004 | eBPF privilege misuse, verifier failure or malformed events affect the host (TB-03; A-04/A-09) | Medium | High | High | M1/M2/M3 | Minimum capabilities, bounded verifier-safe programs/maps, versioned event schema, validation and stress evidence | Architecture constraints only; sensor and event schema are placeholders | High | Open / Week 1 exit |
| R-005 | Vulnerable or substituted dependency/build artifact compromises the lab or release (TB-07; A-08) | Medium | High | High | M1/M6 | Manifests and lock files, provenance review, update policy, SBOM and dependency/static/secret/container scans | No manifests, lock files, CI, SBOM or dedicated scanners are checked in | High | Open / Week 1 foundation controls |
| R-006 | HTTPS observation assumptions lead to TLS weakening or missing route telemetry (TB-02; A-01/A-03/A-04) | Medium | High | High | M1/M2/M5 | Approve an application hook, controlled proxy or metadata-only source; document coverage; prohibit TLS weakening | Architecture, scope and threat model document the constraint; observation point is not selected | Medium | Mitigating / before sensor integration |
| R-007 | Static lab tokens are replayed, exposed or mistaken for production authentication (TB-01; A-01/A-02) | High | High | High | M1/M5 | Keep service lab-only, clearly label demo tokens, test missing/invalid/inactive identities, then replace with signed, expiring, audience-bound tokens | Demo tokens are labelled; negative authentication tests pass; expiry, audience, signature and replay controls are absent | High | Mitigating / before any non-local deployment |
| R-008 | Audit findings or administrative actions are altered, deleted or unattributed (TB-05/TB-06; A-06/A-07) | Medium | High | High | M1/M4/M6 | Structured correlation IDs, restricted append path, tamper evidence, retention/access policy and protected export | Mock API emits basic audit log lines; persistence, correlation and tamper evidence are absent | High | Open / Days 20-22 |
| R-009 | Dashboard privilege escalation or unsafe rendering exposes evidence (TB-06; A-01/A-06/A-07) | Medium | High | High | M1/M6 | Server-side RBAC, short sessions, output encoding, CSRF controls, role tests and masking | Dashboard is a README placeholder | High | Open / Days 23-27 |
| R-010 | Request/event floods exhaust queues or make the lab unavailable (TB-01/TB-03/TB-04; A-09) | Medium | High | High | M2/M3/M5 | Input/rate limits, bounded maps/queues/batches, timeouts, backpressure, circuit breaker and measured capacity | Input schemas exist for the mock API; no rate, queue or integrated load evidence exists | High | Open / Days 13 and 19 |
| R-011 | OpenAPI/implementation drift hides routes or produces incorrect discovery and client behavior (TB-01/TB-04; A-03) | High | Medium | High | M1/M4/M5 | Compare the checked-in contract with generated runtime OpenAPI; align authentication and error schemas; add drift tests | Routes exist in both, but the contract declares JWT while code uses opaque tokens, error envelopes differ, and invalid updates are documented as 400 but return 422 | High | Open / Week 1 exit |
| R-012 | Validation gaps allow broken or insecure changes to merge (TB-07; A-08) | High | High | High | M1/M6 | Deterministic test entry point, CI, named security checks, protected review and evidence retention | Explicit command runs 26 tests; default `unittest discover` runs zero; no CI or required security scanners exist | High | Open / Week 1 foundation controls |

## Review requirements

Update this register whenever an interface, dependency, test result, security
finding, control implementation or ownership decision changes. Each update must:

1. preserve the stable risk ID;
2. link evidence that was actually executed or reviewed;
3. distinguish planned treatment from implemented controls;
4. record residual risk, owner and target checkpoint; and
5. obtain Member 1 approval for closure or acceptance.

