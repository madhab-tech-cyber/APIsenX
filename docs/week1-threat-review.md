# Week 1 Threat Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Review date:** 2026-10-13

**Scope:** Day 6 review of the Week 1 assets, trust boundaries, threat scenarios
and unresolved risks

**Related records:** [`threat-model.md`](threat-model.md),
[`risk-register.md`](risk-register.md),
[`integration-data-flow.md`](integration-data-flow.md)

## 1. Review basis

The review compared the Week 1 threat model with:

- the implemented mock API, authorization logic, OpenAPI document and 26 tests;
- the eBPF, collector, analytics, dashboard and scripts placeholders;
- the Day 4 authentication and data-classification decisions;
- the Day 5 interface register and owner handoffs;
- repository manifests, CI, security scanners, SBOM and review configuration;
  and
- remote branches and pull-request state visible on 2026-10-13.

Architecture text and planned controls were not counted as implemented risk
treatment. A scenario remains applicable until the required control and negative
or failure evidence are linked.

## 2. Threat disposition

| Threats | Week 1 disposition | Primary unresolved evidence | Risks / accountable lead |
|---|---|---|---|
| T-01, T-12 | Open: data minimisation and TLS constraints are documented, but the observation point, capture allowlist, masking and leak tests are absent | Approved observation design, field allowlist, TLS-preservation review and leak tests | R-001 (M1), R-006 (M1) |
| T-02, T-11 | Mitigating: local invalid/inactive credential tests pass; signed, expiring, audience-bound authentication and service identity do not exist | Token validation, replay, rotation/revocation and service-authentication tests | R-007 (M5) |
| T-03 | Mitigating: local owner/admin allow and denial cases pass; tenant, sharing, support and analytics policy paths are not implemented | Versioned full policy table and cross-component negative tests | R-002 (M4) |
| T-04 | Open: monitor-only/fail-open intent is documented; no enforcement adapter, circuit breaker or rollback exists | Per-route failure matrix, deterministic decision tests, latency and rollback evidence | R-003 (M3) |
| T-05, T-10 | Open: sensor, parser, queues and integrated load path are absent | Verifier evidence, bounded schemas/maps/queues, fuzz/stress, drop, backpressure and recovery results | R-004 (M2), R-010 (M3) |
| T-06 | Open: OpenAPI/runtime authentication, error-envelope and validation-status drift remains | Generated-contract comparison and response-schema/drift tests | R-011 (M5) |
| T-07 | Open: basic process logs exist, but correlation, restricted persistence and tamper evidence do not | Structured audit schema, protected append path, retention/access and failure tests | R-008 (M4) |
| T-08 | Open: manifests, locks, CI, provenance, SBOM and dedicated scanners are absent | Reproducible dependencies/build plus retained scan and provenance evidence | R-005 (M6), R-012 (M6) |
| T-09 | Open: the dashboard and management API are placeholders | Server-side RBAC, session, CSRF, masking and safe-rendering tests | R-009 (M6) |
| T-13 | Open: interface requirements exist only as documentation and have no owner acceptance or contract tests | Machine-readable schemas, authenticated sources and producer/consumer compatibility/failure tests | R-013 (M1) |

## 3. Review conclusions

- All 13 threat scenarios remain applicable. No scenario has enough evidence to
  be closed.
- No additional scenario ID is required at this checkpoint. Day 5 threat T-13
  covers the newly documented schema/version/source-confusion exposure.
- Local mock API evidence reduces R-002 to Medium residual risk, but does not
  validate analytics or integrated BOLA/BFLA behavior.
- The documented TLS constraint reduces R-006 to Medium residual risk, but the
  risk remains until the observation point and coverage are approved.
- Eleven risks retain High residual risk. R-004, R-005, R-011, R-012 and R-013
  miss or block the Week 1 integration gate.
- Critical or High residual risk continues to block release. High risk that
  directly affects the proposed integration boundary also blocks integration
  approval until the listed evidence exists.

## 4. Immediate priority order

1. M5 aligns the OpenAPI/runtime contract and adds drift tests (R-011).
2. M6 creates deterministic non-zero CI test discovery, dependency manifests,
   lock files and dedicated security checks (R-005/R-012).
3. M1, M2 and M5 approve an HTTPS-safe observation point and capture allowlist
   before sensor integration (R-001/R-006).
4. M2 and M3 provide the bounded kernel schema, parser and failure evidence
   before an eBPF/collector pull request can be approved (R-004/R-010/R-013).
5. M3, M4 and M6 agree the authenticated batch, audit, management API and
   dashboard contracts before cross-component integration (R-003/R-008/R-009/
   R-013).

The authoritative lead, collaborator, evidence and checkpoint assignments are
recorded in the Day 6 section of [`risk-register.md`](risk-register.md).
