# Risk Register

**Owner:** Member 1 - Team Lead and Security Architect

**Last reviewed:** 2026-10-27 (Asia/Calcutta)

Current evidence: [Member 1 closeout](member1-closeout-2026-10-27.md), baseline
`5f10593a294c68a2729f2c4072c4c4ffa5814f19`. New implementation and passing
component checks are credited below without accepting integrated operation.
All residual ratings remain unchanged: 12 High, R-006 Medium. The historical
October 21 D11 independent-review deadline is overdue, not silently extended.
Remaining owner actions: the correction PR, owner-closed [#61](https://github.com/madhab-tech-cyber/APIsenX/issues/61)
and open #82/#83. Closing a tracker does not accept its unresolved risk.

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
| R-001 | Sensitive data or credentials are captured, logged or persisted (TB-02/TB-05; A-01/A-04/A-06) | Medium | High | High | M1/M2/M4/M6 | Enforce the data-classification policy, capture allowlists, masking before persistence, leak tests, least-privilege access and retention/purge rules | M5 privacy/exception regressions and M4 strict pre-storage masking, bounded volatile retention, protected reads and leak tests exist; Linux userspace loopback log privacy passes. Durable restricted storage, backup/export and full cross-layer privacy acceptance remain missing | High | Mitigating / before storage integration |
| R-002 | Incorrect ownership or role evaluation permits BOLA/BFLA access (TB-01; A-02) | High | High | High | M1/M4/M5 | Versioned policy matrix, deny-by-default logic, labelled allow/deny fixtures and API negative tests | D11-F01 regressions pass; M5 tenant/permission/share validation and DET-1.2 self-labelled BOLA/BFLA tests are implemented. Historical PR #28 approval is revision-scoped; current independent closure, complete endpoint-specific AP-1.0 and held-out detector acceptance remain pending; documented admin-inventory limitations persist | High | Mitigating / latest independent D11 review due 2026-10-21 and before release; full matrix before integration acceptance |
| R-003 | False-positive enforcement or unsafe failure mode causes an outage (TB-04/TB-06; A-05/A-09) | Medium | High | High | M1/M3 | Monitor-only default, deterministic criteria, route failure matrix, circuit breaker and tested rollback | Merged M3 library/Linux userspace loopback and M4 signed monitor-only/stale-source/lease/outage tests exist. LAB-REC-1 is not accepted IF-07; no active adapter, approved rule or timed full-system rollback evidence | High | Mitigating / before active enforcement |
| R-004 | eBPF privilege misuse, verifier failure or malformed events affect the host (TB-03; A-04/A-09) | Medium | High | High | M1/M2/M3 | Minimum capabilities, bounded verifier-safe programs/maps, versioned event schema, validation and stress evidence | M2 remains design/headers at 07f1410; M3 parser and Linux userspace handoff CI exist. No loadable sensor, verifier/load/capability/stress or accepted M2/M3 wire/provenance evidence | High | Open / immediate: before sensor integration |
| R-005 | Vulnerable or substituted dependency/build artifact compromises the lab or release (TB-07; A-08) | Medium | High | High | M1/M6 | Manifests and lock files, provenance review, update policy, SBOM and dependency/static/secret/container scans | Python API/analytics dependency, lint, scoped secret and static CI plus M6 locked install/build/test/npm audit pass on pinned component heads. M4 frozen source candidate exists, not a full-system release; Python transitive lock, provenance/SBOM and applicable container evidence remain pending | High | Mitigating / before release build acceptance |
| R-006 | HTTPS observation assumptions lead to TLS weakening or missing route telemetry (TB-02; A-01/A-03/A-04) | Medium | High | High | M1/M2/M5 | Approve an application hook, controlled proxy or metadata-only source; document coverage; prohibit TLS weakening | M5 candidate observation hook emits matched templates and server request UUIDs with privacy regressions. Joint M1/M2/M4 schema/provenance, TLS coverage and live capture acceptance remain pending; loopback transport does not establish them | Medium | Mitigating / before sensor integration |
| R-007 | Static lab tokens are replayed, exposed or mistaken for production authentication (TB-01; A-01/A-02) | High | High | High | M1/M5 | Enforce `authentication-decisions.md`: keep fixtures lab-only, then replace them with validated, signed, expiring, issuer/audience-bound tokens and replay controls | Merged PRs #52/#54 implement 15-minute lab token lifecycle, revoke/future-token rejection and five-minute process-local PATCH nonce checks with regressions. Public fixture identity, no cryptographic issuer/audience binding and restart/multi-worker replay limits still block non-local deployment | High | Mitigating / before any non-local deployment |
| R-008 | Audit findings or administrative actions are altered, deleted or unattributed (TB-05/TB-06; A-06/A-07) | Medium | High | High | M1/M4/M6 | Structured correlation IDs, restricted append path, tamper evidence, retention/access policy and protected export | API request UUIDs, sanitized logs and M4 structured masked volatile decision/access audit with expiry and fail-closed read tests exist. Durable protected append, cross-layer attribution, tamper evidence, export/hold and independent acceptance remain pending | High | Mitigating / before audit integration |
| R-009 | Dashboard privilege escalation or unsafe rendering exposes evidence (TB-06; A-01/A-06/A-07) | Medium | High | High | M1/M6 | Server-side RBAC, short sessions, output encoding, CSRF controls, role tests and masking | M6 ec03bdf has observed npm ci/lint/4 Vitest tests/TypeScript-production-build/audit CI; M4 backend case/role/expiry/revocation authorization and masked detail tests exist. Fixture UI remains unmerged and unconnected; browser state/privacy coverage and authenticated live contract acceptance remain pending | High | Open / before dashboard integration |
| R-010 | Request/event floods exhaust queues or make the lab unavailable (TB-01/TB-03/TB-04; A-09) | Medium | High | High | M2/M3/M5 | Input/rate limits, bounded maps/queues/batches, timeouts, backpressure, circuit breaker and measured capacity | API input/nonce bounds, merged M3 bounded queue/batch/retry/loopback and M4 ingestion/store/query/cursor bounds exist. No accepted integrated load/capacity, Linux sensor loss/recovery, paired latency or rollback evidence | High | Mitigating / before capacity claims |
| R-011 | OpenAPI/implementation drift hides routes or produces incorrect discovery and client behavior (TB-01/TB-04; A-03) | High | Medium | High | M1/M4/M5 | Compare the checked-in contract with generated runtime OpenAPI; align authentication and error schemas; add drift tests | Current API/OpenAPI parity regressions and M4 strict normalization/discovery/self-labelled corpus exist; old JWT drift is repaired. Admin endpoint limitations, schema/provenance handoffs and independent full-system discovery/accuracy acceptance remain pending | High | Mitigating / before discovery integration |
| R-012 | Validation gaps allow broken or insecure changes to merge (TB-07; A-08) | High | High | High | M1/M6 | Deterministic test entry point, CI, named security checks, protected review and evidence retention | API/analytics/Linux-loopback CI and M6 peer-branch UI CI pass on their recorded heads. PR #34 has no formal reviews; main protected=false/rulesets empty. October 27 approved apply stops at initial access read, connector GET403; no admin change or independent human sign-off | High | Mitigating / immediate: before next integration approval |
| R-013 | An incompatible, unversioned or spoofed interface message causes telemetry loss, incorrect findings or an unsafe decision (TB-03/TB-04/TB-05/TB-06; A-03/A-04/A-05/A-06) | High | High | High | M1/M2/M3/M4/M6 | Machine-readable versioned schemas, authenticated sources, size/freshness/deduplication rules, reject-unknown behavior and producer/consumer compatibility/failure tests | M3/M4 exact batch/ack/freshness/negative/retry compatibility now runs in Linux userspace CI; masked volatile audit, signed LAB-REC-1 and protected MGT-LAB-1.0 prototypes exist. Accepted sensor envelope, shared TLS/identity, trusted live correlation, M6 browser handoff and IF-07 consumer remain pending | High | Mitigating / immediate: before interface acceptance |

## Day 6 unresolved-risk assignments

The Week 1 review in [`week1-threat-review.md`](week1-threat-review.md) confirms
that no risk is ready for acceptance or closure. The lead is accountable for
coordinating the named collaborators and linking the required evidence.

| Risk | Accountable lead / collaborators | Next required evidence | Target checkpoint |
|---|---|---|---|
| R-001 | M1 / M2, M4, M6 | Capture allowlist, pre-persistence masking, leak tests, access and purge evidence | Before storage integration; Days 20/23 final review |
| R-002 | M5 / M1, M4, M6 | Independently review merged D11-F01 fix and passing inventory regressions; M4 coordinates full `AP-1.0` detection matrix | D11-F01 review: 2026-10-21 and before release; complete matrix: before integration acceptance |
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

### October 27 current closeout

[Current reconciliation](member1-closeout-2026-10-27.md) supersedes current-state
claims in the older dated sections below. M4's merged detection/masking/protected
read work, M5 tenant/share/token/nonce regressions, M3 Linux userspace loopback
and M6 real UI-test/build CI are credited. None closes the human, administrative
or full runtime acceptance gates. No risk rating, waiver or deadline changes.

### October 20 historical closeout

[Current evidence](member1-closeout-2026-10-20.md) supersedes later/current-state
claims in the dated snapshots below. M3's library is merged; M5's real handoffs,
candidate observation hook, privacy/startup/permission fixes and the pinned
PR #28 approval are credited. That approval does not approve PR #31 or release.
#14/#21/#23 are now closed without completing their human gates. Follow-up #33
and the [register](member1-checkpoints.json) retain the unmet requirements.
The owner utility's unit tests and prepared payload are not enabled protection;
actual Administration access/readback remains blocked. No rating is reduced,
no risk accepted/closed and no active rule/release authorized.

### October 19 / Day 27 patch verification

[Patch log](patch-verification-log.md) and [executed baseline](member1-oct19-verification.md)
supersede the current-state claims in older dated reviews. D11-F01 is repaired
and regression-tested, not independently closed. Contract/security drift and
the missing main-PR trigger were corrected by M5; do not re-report them as
current defects. No detector, live transport, protected dashboard, durable audit,
integrated latency or rollback acceptance is inferred from those improvements.

The October 18 paragraph above records a historical reopening. Issue #14 was
subsequently closed without human evidence, then reopened by the October 19
corrective task. #21/#23 stay open; neither human checkpoint is complete.
The owner closed #14 again at 06:58 UTC on October 19 with no comments. Preserve
that later issue-state change without treating its unmet human gate as complete.
[Issue #23](https://github.com/madhab-tech-cyber/APIsenX/issues/23)
tracks the release hold. Days 21–26 add route failure, masking, dashboard and
triage specifications, not runtime proof. All 13 risks remain unresolved,
with 12 High and R-006 Medium; no waiver or rating reduction is made.

[Member 1 corrective evidence](member1-governance-correction.md) supersedes
current coordination/status claims. [Checkpoint bookkeeping](member1-checkpoints.json)
is pending for Days 14/15/30. Main protection was explicitly approved by the
owner but remains blocked by HTTP 403/CLI authentication rejection; only actual
settings readback can establish enabled protection. No self-sign-off, false
calendar completion, active rule or release approval is introduced.

### Required update record

Update this register whenever an interface, dependency, test result, security
finding, control implementation or ownership decision changes. Each update must:

1. preserve the stable risk ID;
2. link evidence that was actually executed or reviewed;
3. distinguish planned treatment from implemented controls;
4. record residual risk, owner and target checkpoint; and
5. obtain Member 1 approval for closure or acceptance.

