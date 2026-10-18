# Risk Register

**Owner:** Member 1 - Team Lead and Security Architect

**Last reviewed:** 2026-10-18

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
| R-002 | Incorrect ownership or role evaluation permits BOLA/BFLA access (TB-01; A-02) | High | High | High | M1/M4/M5 | Versioned policy matrix, deny-by-default logic, labelled allow/deny fixtures and API negative tests | October 18: 40 local tests pass, but current D11-F01 diagnostic still confirms four customer admin-inventory false allows; no fix/regression closure evidence | High | Mitigating / D11-F01 due 2026-10-21 and before release; full matrix before Week 2 exit |
| R-003 | False-positive enforcement or unsafe failure mode causes an outage (TB-04/TB-06; A-05/A-09) | Medium | High | High | M1/M3 | Monitor-only default, deterministic criteria, route failure matrix, circuit breaker and tested rollback | M3 unmerged library has dry-run decision parsing and reported tests; active adapter, authenticated decision verification and rollback evidence remain absent | High | Open / Days 16-22 |
| R-004 | eBPF privilege misuse, verifier failure or malformed events affect the host (TB-03; A-04/A-09) | Medium | High | High | M1/M2/M3 | Minimum capabilities, bounded verifier-safe programs/maps, versioned event schema, validation and stress evidence | M2 design/headers/prerequisite tests and M3 parser library exist on separate branches; live Linux verifier, wire compatibility and privilege evidence remain unaccepted | High | Open / immediate: Week 1 exit missed; before sensor integration |
| R-005 | Vulnerable or substituted dependency/build artifact compromises the lab or release (TB-07; A-08) | Medium | High | High | M1/M6 | Manifests and lock files, provenance review, update policy, SBOM and dependency/static/secret/container scans | October 18 M5 run passes dependency audit/Ruff/API tests; M3 Cargo.lock and M6 package lock exist on peer branches; full build provenance, Python transitive lock, SBOM and dedicated secret/container evidence remain missing | High | Open / immediate: Week 1 foundation gate missed |
| R-006 | HTTPS observation assumptions lead to TLS weakening or missing route telemetry (TB-02; A-01/A-03/A-04) | Medium | High | High | M1/M2/M5 | Approve an application hook, controlled proxy or metadata-only source; document coverage; prohibit TLS weakening | Architecture, scope and threat model document the constraint; observation point is not selected | Medium | Mitigating / before sensor integration |
| R-007 | Static lab tokens are replayed, exposed or mistaken for production authentication (TB-01; A-01/A-02) | High | High | High | M1/M5 | Enforce `authentication-decisions.md`: keep fixtures lab-only, then replace them with validated, signed, expiring, issuer/audience-bound tokens and replay controls | Demo tokens are labelled as public fixtures; missing/malformed/invalid/inactive tests pass; signature, issuer, audience, expiry and replay controls are absent | High | Mitigating / before any non-local deployment |
| R-008 | Audit findings or administrative actions are altered, deleted or unattributed (TB-05/TB-06; A-06/A-07) | Medium | High | High | M1/M4/M6 | Structured correlation IDs, restricted append path, tamper evidence, retention/access policy and protected export | Mock API emits basic audit log lines; persistence, correlation and tamper evidence are absent | High | Open / Days 20-22 |
| R-009 | Dashboard privilege escalation or unsafe rendering exposes evidence (TB-06; A-01/A-06/A-07) | Medium | High | High | M1/M6 | Server-side RBAC, short sessions, output encoding, CSRF controls, role tests and masking | M6 unmerged React fixture dashboard exists; latest successful CI only checks repository filenames/structure; live backend RBAC, UI state/privacy tests and protected API evidence absent | High | Open / Days 23-27 |
| R-010 | Request/event floods exhaust queues or make the lab unavailable (TB-01/TB-03/TB-04; A-09) | Medium | High | High | M2/M3/M5 | Input/rate limits, bounded maps/queues/batches, timeouts, backpressure, circuit breaker and measured capacity | Input schemas exist for the mock API; no rate, queue or integrated load evidence exists | High | Open / Days 13 and 19 |
| R-011 | OpenAPI/implementation drift hides routes or produces incorrect discovery and client behavior (TB-01/TB-04; A-03) | High | Medium | High | M1/M4/M5 | Compare the checked-in contract with generated runtime OpenAPI; align authentication and error schemas; add drift tests | October 17: seven selected OpenAPI checks pass; JWT/opaque-fixture security drift persists; bidirectional operation/security equality is not tested | High | Open / immediate: Week 1 exit missed; before discovery integration |
| R-012 | Validation gaps allow broken or insecure changes to merge (TB-07; A-08) | High | High | High | M1/M6 | Deterministic test entry point, CI, named security checks, protected review and evidence retention | October 18: 40 tests pass; M5 quality CI succeeds but main PR trigger coverage absent; branches unprotected, rulesets empty, PR #18/#19 have zero reviews; verified CODEOWNERS proposed, enforcement pending | High | Open / immediate: Week 1 foundation gate missed |
| R-013 | An incompatible, unversioned or spoofed interface message causes telemetry loss, incorrect findings or an unsafe decision (TB-03/TB-04/TB-05/TB-06; A-03/A-04/A-05/A-06) | High | High | High | M1/M2/M3/M4/M6 | Machine-readable versioned schemas, authenticated sources, size/freshness/deduplication rules, reject-unknown behavior and producer/consumer compatibility/failure tests | M2/M3 interface proposals and M3 JSON schemas/library exist; compiled versioned sensor envelope, request correlation, M4 batch/ack acceptance and live compatibility/failure tests remain missing | High | Open / immediate: before each interface merge |

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

## Day 13 validation handoff

[MRVP-1.0](mid-review-validation-plan.md) now defines sample sizes, environment,
measurement and pass/fail rules for the Week 2 review. The plan is a specification
for peer review; no new runtime risk is accepted, downgraded or closed.

| Risk | Accountable lead / support | Day 13 evidence required | Gate |
|---|---|---|---|
| R-002 | M5 / M4, M6, M1 review | D11-F01 inventory regressions, full AP-1.0 application cases and separate detector confusion counts | Before authorization/detection approval; existing 2026-10-21 maximum finding deadline and before release remain |
| R-004, R-006, R-013 | M2/M3 / M5, M4, M1 review | Exact supported Linux/kernel profile, approved HTTPS-safe observation point, bounded compatible schemas and receipt/loss evidence | Before integrated correctness or latency runs |
| R-005, R-012 | M6 / all component owners | Locked dependency environment, nonzero repeatable checks, dependency/static/secret and applicable container scan evidence | Before next integration approval; currently absent |
| R-010 | M3 / M2, M5, M6 | Three paired latency runs at each of two concurrency levels, bounded resource and loss/backpressure evidence | Before capacity/performance claims; Day 19 limits decision still separate |
| R-001, R-011 | M4/M5 / M6, M1 review | Versioned contract/corpus, no forbidden output and all privacy/route/discovery assertions | Before discovery acceptance or evidence persistence |

Owners are handoff assignments, not claims that they accepted or executed work.
The 26 application tests pass in the Day 13 local regression environment;
detector accuracy and integrated performance remain UNMEASURED. Missing detector,
pipeline, locked environment and dedicated scans keep those acceptance gates
BLOCKED. See [Day 13 evidence](day13-member1-evidence.md) and
[Issue #11](https://github.com/madhab-tech-cyber/APIsenX/issues/11).

## Day 14 mid-review collection

[Day 14 review](day14-mid-review.md) collects all thirteen unresolved risks:
12 High and one Medium. Local owner-read and cross-owner-denial demos pass,
but D11-F01 again returns 200 instead of 403 with empty/all-owned admin
inventories. The existing 26 application tests pass without covering those
failures. M5/M6 retain remediation/regression ownership and the existing deadline.

M2's unmerged `07f1410` design and header proposals add useful foundation work,
but raw/truncated route markers, missing event schema version, IPv6 scope and
unmeasured performance/resource claims need producer/consumer review under
R-001/R-004/R-006/R-013. No live sensor or collector result was demonstrated.

PR #13 remains draft; no submitted reviews or CI checks were present at the
audit snapshot. Rulesets, branch protection, real CODEOWNERS identities and
dedicated scan/build evidence remain unresolved under M1/M6 coordination.
Closing Issue #3 did not provide evidence that those controls were completed.

Integrated Week 2 acceptance is NOT APPROVED. No residual rating, existing owner
or remediation deadline is reduced, and no risk is accepted or closed. The
repository rehearsal is recorded in [Day 14 evidence](day14-member1-evidence.md);
the human meeting, actual feedback and owner sign-off remain pending in
[Issue #14](https://github.com/madhab-tech-cyber/APIsenX/issues/14).

## October 17 corrective review

[Current verification](member1-oct17-verification.md) passes 40 application/
contract tests. D11-F01 still has four failing customer inventory checks.
Direct requirements, selected OpenAPI checks and member5-filtered CI now exist;
earlier absence statements above describe historical review snapshots. These
improvements do not close R-005/R-011/R-012: transitive locks, dedicated scans,
full security parity and main-targeting integration checks remain absent.

[Day 15 actions](mid-review-corrective-actions.md) supersede the immediate
follow-up queue: CA-01/02 map to R-002; CA-03/09 to R-011; CA-04 to
R-001/004/006/013; CA-05 to R-003; CA-06 to R-010; CA-07/08 to R-005/012;
CA-10 to R-001/008/009; CA-11 to R-012/013. M5 retains D11-F01 remediation,
M6 owns CI trigger correction, M4 owns detector/corpus and M3 owns adapter/
performance evidence. No residual rating or deadline is reduced.

## Days 16–20 control decisions

[ENF-1.0](enforcement-approval-and-rollback.md) supplies R-003/R-013 design gates,
bounded decision leases and rollback deadlines. The
[rule review](blocking-rule-review-register.md) and
[lab authorization decision](lab-blocking-authorization.md) approve zero active
rules. [LIMIT-LAB-1.0](identity-route-resource-limits.md) supplies R-010 identity,
route, cost, queue and retry requirements; no limiter/load proof exists.
[AUDIT-LAB-1.0](audit-retention-and-investigation.md) supplies R-001/R-008/R-009
retention, RBAC, integrity, deletion and investigation requirements; no runtime
store/control evidence exists. These are policy progress only: every risk
remains unresolved and residual ratings are unchanged. Per-day disposition and
pending human reviews are in [delivery status](member1-days13-20-status.md).

## October 18 evidence and checkpoint correction

[Re-audit](member1-oct18-integration-review.md) pins all six branch revisions,
credits M3/M6 unmerged implementations and M5 quality CI, and reconfirms D11-F01
against current main. Documentation/contract assessment and automated regression
results do not constitute independent source or integration approval.
[Ownership controls](ownership-and-review-controls.md) replace placeholder handles
with verified identities while keeping M4 unconfirmed and protection unchanged.

Day 14 [#14](https://github.com/madhab-tech-cyber/APIsenX/issues/14) is reopened;
Day 15 [#21](https://github.com/madhab-tech-cyber/APIsenX/issues/21) explicitly
tracks real feedback/owner acceptance. M1 owns checkpoint and protection
coordination; M2/M3/M4 own interface proofs, M5/M6 D11-F01 evidence, M4 detector
results and M6 dashboard/CI evidence. All risk ratings and the October 21
D11-F01 deadline are unchanged. Monitor-only and zero active authorization
remain in force. No calendar-day compliance or completed meeting is inferred.

## Review requirements (current)

Update this register whenever an interface, dependency, test result, security
finding, control implementation or ownership decision changes. Each update must:

1. preserve the stable risk ID;
2. link evidence that was actually executed or reviewed;
3. distinguish planned treatment from implemented controls;
4. record residual risk, owner and target checkpoint; and
5. obtain Member 1 approval for closure or acceptance.

