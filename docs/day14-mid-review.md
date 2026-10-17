# Day 14 Mid-Review Agenda and Repository Rehearsal

**Date:** 2026-10-15 (Asia/Calcutta)

**Accountable lead:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Tracking:** [Issue #14](https://github.com/madhab-tech-cyber/APIsenX/issues/14)

**Assignment:** Member 1 responsibility plan, page 3: run review agenda and
collect open risks. The Weeks 1-2 checkpoint requires demonstrable discovery,
BOLA/BFLA, performance, accuracy, GitHub and scan evidence.

**Review mode:** Repository evidence review and local rehearsal performed.
No human team meeting, attendance, mentor feedback or owner sign-off is claimed.
The timed agenda below is ready for that meeting; its timeboxes are planned,
not actual meeting durations.

## 1. Review baselines

| Scope | Pinned revision / observed evidence |
|---|---|
| Main | `f566d7a6bac2466f158b88cc55d13f309c6f8f0c` |
| Member 1 | `a2f837a5ab2df492edd1037b2d16a1dac726f06b`; Day 13 documentation and MRVP-1.0 on draft PR #13 |
| Member 2 | `07f141022f31979c9464c2f853b982e03b4373a4`; design notes, prerequisite scripts/tests and C type/map headers on its separate branch |
| Members 3, 4 and 6 | `841cde1d244a5c50e20ff580566962c5e1b22f18`; component README placeholders, no collector/detector/dashboard implementation |
| Member 5 | `fd49407fabb728b1018a30ff67ca01365bb82980`; API work merged through PR #9 and present in main |

This is a snapshot, not a live status guarantee. Branches are not merged merely
because they appear in this inventory. Member 2's reported 18 prerequisite/
layout/security tests were read as author-supplied evidence; they were not
independently executed here or accepted as Linux verifier/integration evidence.
No loadable probe or Rust workspace appears in that branch's inspected tree.

## 2. Timed agenda and executed review record

| Meeting timebox | Owner / item | Repository rehearsal result |
|---|---|---|
| 0-5 min | M1: scope, authorization and decision rules | Reviewed lab-only scope, synthetic data, preserved TLS, monitor-only boundary and required owner review |
| 5-12 min | M1/M2/M3: architecture and interfaces | Reviewed interface baseline and M2 proposals; producer/consumer acceptance and executable pipeline are absent |
| 12-22 min | M5/M6: positive/negative API demonstration | Owner read 200 and cross-owner denial 403 observed locally; two D11-F01 admin-function cases FAIL with 200 instead of 403 |
| 22-30 min | M4/M5: route discovery, BOLA/BFLA and accuracy | RN/DS/AP-1.0 requirements and Day 12 gaps reviewed; detector and 600-case holdout are absent, so accuracy is UNMEASURED |
| 30-37 min | M2/M3/M6: performance, privacy and security checks | MRVP-1.0 reviewed; Linux paired runs, privacy/failure suite, manifests/locks, dedicated scanners and CI are absent |
| 37-45 min | M1/all owners: risks, review status and next decision | Thirteen unresolved risks collected below; integrated Week 2 acceptance withheld, human feedback and owner acceptance pending |

Run the human meeting using these same artifacts and record actual attendees,
date/time, comments and decisions when it happens. An absent component should be
shown as blocked rather than demonstrated with invented output. Do not turn a
repository rehearsal into a claim that every member attended or approved.

## 3. Executed demonstration and checks

The existing explicit test suite passed 26 methods (10 unit authorization and
16 HTTP/API). Compileall also passed. These tests do not cover all required
policy contexts and do not establish detector or production security.

Four additional in-process TestClient checks were run against synthetic fixtures:

| Case | Expected / observed HTTP | Decision |
|---|---|---|
| D14-DEMO-01: customer reads its owned order | 200 / 200 | PASS: successful allowed case |
| D14-DEMO-02: customer reads another customer's order | 403 / 403 | PASS: successful security denial |
| D14-D11F01-EMPTY: customer calls admin list with empty inventory | 403 / 200 | FAIL: existing function-gate finding persists |
| D14-D11F01-OWNED: customer calls admin list with all-owned inventory | 403 / 200 | FAIL: existing function-gate finding persists |

The diagnostic deliberately exits 1 for the two violations. All four checks
left their temporary inventory unchanged; patch contexts restored original
in-memory state and no fixture files were rewritten. A passing application
suite cannot override these failures. Reproduction and environment are in
[day14-member1-evidence.md](day14-member1-evidence.md).

## 4. Readiness and governance decisions

| Gate | Decision / evidence |
|---|---|
| Local API baseline | CONDITIONAL: 26 tests and positive/negative demo pass; administrative function still violates AP-1.0 |
| Administrative-function acceptance | FAIL: D11-F01 reproduced; M5/M6 remediation and independent retest required |
| Kernel/collector integration | BLOCKED: M2 proposals are unmerged and no runnable sensor/collector integration evidence exists |
| Discovery and authorization detection | BLOCKED: no executable detector, reviewed labelled corpus or confusion counts |
| Accuracy and latency | UNMEASURED: Day 13 defines the protocol; no MRVP-1.0 integrated run occurred |
| Privacy, failure/recovery and resource bounds | NOT RUN for integrated pipeline; design constraints are not runtime proof |
| Supply chain and scanners | BLOCKED: no locked dependency/build environment, SBOM or dedicated dependency/static/secret/container evidence |
| GitHub review/CI governance | BLOCKED: PR #13 is draft, no submitted reviews; source check-run count 0 and combined status has 0 statuses; no workflows in inspected source |
| Merge protection | Branch API reports `protected: false` for main and member branches; repository ruleset list is empty |
| Reviewer ownership | CODEOWNERS still uses placeholder handles such as `@member1`; real owner identities and review enforcement remain unresolved |

Issue #3 is closed as completed, but its remaining controls still lack evidence.
Closing a tracking issue does not close R-005/R-012 or prove a scanner is enabled.
Issue #11 remains the Day 13 review item. PR #13 is the only open PR at the review
snapshot; it is documentation, not a runtime integration approval.

Do not count files named Day 1 through Day 14 as fourteen distinct working days
of commits. The calendar-based training/review requirement needs its own dated
commit audit and mentor-confirmed review window; that audit was not performed
by this task. No compliance percentage is claimed.

## 5. Collected open risks and required evidence

Residual ratings below are carried from [risk-register.md](risk-register.md):
12 High, one Medium, none accepted or closed in this review.

| Risk / residual | Accountable owner / support | Open concern and next evidence | Required checkpoint |
|---|---|---|---|
| R-001 / High | M1 / M2, M4, M6 | M2 proposes a truncated raw route marker; resolve against the no-raw-path/HMAC requirements, then prove allowlisting, pre-persistence masking and leak tests | Before observation/storage acceptance |
| R-002 / High | M5 / M1, M4, M6 | Fix D11-F01, add empty/all-owned/mixed/unknown-role regressions, then provide full AP-1.0 and separate detector evidence | Before admin approval; no later than 2026-10-21 and before release |
| R-003 / High | M3 / M1, M4 | Enforcement, failure matrix, rollback and circuit breaker lack implementation evidence | Days 16-22; no activation before approval |
| R-004 / High | M2 / M1, M3 | Headers/design do not prove supported-kernel loading, verifier safety, privilege drop, bounded allocations or parser robustness | Before sensor integration |
| R-005 / High | M6 / all component owners | Manifests/locks, provenance, SBOM and dedicated scan evidence are absent | Before next integration approval |
| R-006 / Medium | M1 / M2, M5 | HTTPS-safe observation point and actual route coverage are not approved | Before route-level sensor claims |
| R-007 / High | M5 / M1, M6 | Public opaque fixture tokens remain lab-only; production token validation/replay controls are absent | Before any non-local deployment |
| R-008 / High | M4 / M1, M6 | Basic logs do not prove protected append, correlation, tamper evidence, retention or failure handling | Days 20-22; before audit integration |
| R-009 / High | M6 / M1 | Dashboard implementation, server RBAC, session/CSRF and masking evidence are absent | Days 23-27; before dashboard acceptance |
| R-010 / High | M3 / M2, M5, M6 | No integrated load/loss/backpressure or MRVP paired latency measurements exist | Before performance/capacity claims; Day 19 limits review |
| R-011 / High | M5 / M1, M4 | Runtime validation now returns 400, but JWT-labelled contract vs opaque lab authentication remains; full drift regression is absent | Before discovery integration |
| R-012 / High | M6 / M1 | Nonzero local invocation exists; CI, real review ownership, required checks and protection remain absent | Before next integration approval |
| R-013 / High | M1 / M2, M3, M4, M6 | M2 event proposal lacks an explicit schema version; correlate/deduplicate and agree bounded producer/consumer contracts with compatibility/failure tests | Before interface acceptance |

### M2 design handoff items

At `07f1410`, `api_event` has `route_marker[128]` described as a truncated path,
and no explicit schema-version field. Its 32-bit `src_ip`/`dst_ip` fields do not
represent a full IPv6 address despite `ip_version` accepting 6. Before accepting
the interface, M2/M3/M4 must resolve privacy representation, versioning and IPv4
vs IPv6 scope against the integration and normalization specifications.

The M2 evidence note's `<15ns` hook overhead and memory/safety statements are
author claims, not accepted measurements. Layout/pattern tests alone do not
prove kernel verifier loading, total runtime allocations, absence of secrets
or zero loss. M2/M3 must supply actual build/load, resource and loss evidence
under MRVP-1.0 before these claims support a gate. The documents' assertion that
a handoff was received is not independent producer/consumer sign-off.

These are unresolved design/verification items linked to R-001/R-004/R-006/R-013,
not new claims that an unexecuted sensor exposed real data. No peer branch was
modified or merged by this review.

## 6. Review decision and next handoff

**Integrated Week 2 acceptance: NOT APPROVED.** Continue scoped foundation,
remediation and documentation work. Active enforcement and release remain
unauthorized; no residual risk was accepted or downgraded.

The next review needs M5/M6's authorization fix/regressions; M2/M3/M4's accepted
privacy-safe versioned interface and executable pipeline; M4's labelled detector
results; M3/M6's paired Linux performance results; and M6's reproducible build,
scan and governance evidence. Existing owners/targets above remain in force.
Day 15 should record actual reviewer feedback and then reassign corrective work
where needed. This review does not invent that feedback or send team messages.

**Human meeting and sign-off record:** PENDING. No attendee list, meeting time,
mentor response or component-owner approval was supplied. Record them after the
meeting and link reviewer evidence before closing the Day 14 issue. Publishing
this rehearsal is not completion of the human review checkpoint.

## 7. October 17 repository re-review

Reviewed merged `6b1a427`; previous snapshot statements above remain historical.
[Current execution evidence](member1-oct17-verification.md) now shows 40 passing
local tests, compilation and nine admin-inventory diagnostics: four policy
failures and five expected outcomes. D11-F01 remains confirmed and due
2026-10-21. New test isolation, malformed-body and missing-object checks improve
application coverage without closing the function-permission finding.

Direct requirements and mock-API CI now exist. CI's push/base-PR filters cover
`member5/mock-api`, not main-targeting integration PRs or Member 1 pushes.
Seven OpenAPI tests provide selected contract checks but omit security parity
and reverse operation-set equality. JWT-labelled contract drift persists.

Review agenda items were rechecked asynchronously: scope/policy PASS at design
level; administrative-function acceptance FAIL; executable pipeline, holdout,
paired latency, scanners, protected audit and rollback BLOCKED. All thirteen
risks remain unresolved. This refresh does not assert new live GitHub protection,
review counts or peer-branch status beyond the inspected merged source.

Integrated Week 2 acceptance remains NOT APPROVED. Human review comments and
component sign-offs are pending. Day 15 records corrective assignments using
these repository findings; it must distinguish those findings from peer feedback.
