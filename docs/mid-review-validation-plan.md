# Day 13 Mid-Review Validation Plan

**Owner:** Member 1 - Team Lead and Security Architect

**Date:** 2026-10-15

**Plan version:** `MRVP-1.0`

**Branch:** `member1/security-architecture`

**Reviewed source:** `f566d7a6bac2466f158b88cc55d13f309c6f8f0c`

**Status:** Criteria defined for owner review. Integrated execution is BLOCKED;
accuracy and performance are UNMEASURED. This document grants no release or
active-blocking approval.

## 1. Assignment and existing evidence

Member 1's responsibility plan, page 3, assigns Day 13: "Define sample size,
environment and pass/fail criteria." Page 4 requires reviewable work on a member
branch and review before merge. This plan completes the specification part of
that assignment; implementation, measurement and reviewer approval are separate.
The delivery uses the PDF-assigned branch `member1/security-architecture`,
confirmed by the project owner.

This plan extends [Day 12's coverage review](detection-accuracy-coverage-review.md),
[AP-1.0](authorization-policy.md), [route acceptance](route-normalization-acceptance.md),
[discovery triage](discovery-severity-triage-policy.md), and
[the interface baseline](integration-data-flow.md). Existing passing unit/HTTP
tests are application evidence only. The detector, sensor and collector remain
unimplemented in the reviewed source. D11-F01 remains an open authorization
failure in the [function review](function-level-authorization-review.md).

All numbers below are project acceptance decisions for the synthetic lab.
They are not thresholds prescribed by the PDF or measured results, and passing
them cannot establish absence of vulnerabilities or production readiness.

## 2. Authorized environment and reproducibility

Use a team-owned, isolated Linux lab VM for the eventual integrated run:

- One VM with 4 vCPUs, 8 GiB RAM and at least 20 GiB free disk; use the same
  allocation and CPU/memory limits in baseline and monitored runs. Record the
  actual CPU model, hypervisor, host/guest OS, kernel and BTF availability.
- M2/M3 must select and record an exact supported kernel, eBPF toolchain, attach
  point and least-privilege capability set before sensor execution. An unverified
  Kali or other distribution/kernel combination is not automatically supported.
- Put the load generator on a second isolated VM with at least 2 vCPUs/4 GiB;
  record its actual configuration, network topology and versions. Use no
  unrelated workload during measurements.
- Bind the API and management interfaces to loopback or the private lab network.
  Use only synthetic users, tenants, objects and public lab credential fixtures.
  Reset state before every functional case and every performance arm.
- Keep the API build, fixtures, policy/contract versions, workload, worker count,
  TLS mode and resource allocation identical across each performance pair.
  Monitoring is the only intended difference. Record any unavoidable difference.
- Preserve TLS. M1/M2/M5 must approve an application metadata hook or controlled
  proxy/termination point for method/route telemetry. Encrypted packet capture
  alone cannot establish route visibility. No payload collection or TLS bypass.
- M6 must provide manifests/locks, exact Python/Rust/library versions, dependency
  installation and launch commands, corpus/generator hashes and deterministic
  seeds. Do not resolve floating dependencies during acceptance runs.
- Capture source SHA, artifact digest, schema/policy/contract versions, config
  hash, VM settings, UTC start/end, run ID and exact commands in a run manifest.
  Use monotonic client timing. Give every input a stable synthetic case ID and
  correlate it with the processed event and finding.

The Linux profile above is a planned measurement environment. Day 13's actual
Windows/TestClient regression environment is recorded in
[day13-member1-evidence.md](day13-member1-evidence.md); it cannot prove eBPF,
network performance or Linux compatibility. A frozen run manifest and runnable
owner commands are prerequisites, not deliverables claimed to exist today.

## 3. Sample sizes and case selection

### 3.1 Mandatory deterministic regression set

M4/M5/M6 must automate all 53 `RN-*` cases, all 15 `DS-*` scenarios, all AP-1.0
Section 7 acceptance rows and the FL-01 through FL-06 matrix. Count unique IDs
and subcases explicitly; a fixture row inside one unittest is not another test
method. Not every DS scenario is a traffic sample: triage/review-state cases
remain workflow assertions. Required cases have no skipped or expected-failure
waivers in a passing acceptance run.

Include D11-F01 regressions with empty, all-owned and mixed-owner inventories,
both customer identities, unknown roles and permitted admins. Verify required
denials independently of inventory contents and confirm no state mutation.
Missing tenant, sharing or explicit-permission features are blockers to their
policy rows, not reasons to label those rows passed.

### 3.2 Frozen detection holdout: minimum 600 distinct scenarios

| Family | Finding expected | No family finding expected | Minimum total |
|---|---:|---:|---:|
| BOLA | 100 | 100 | 200 |
| BFLA | 100 | 100 | 200 |
| Discovery | 100 | 100 | 200 |
| Total | 300 | 300 | 600 |

These are distinct case IDs with meaningfully different policy/input contexts,
not 600 copies of the same request. Repeated runs, ID-only renaming, retries,
unit/HTTP overlaps and deterministic regression cases do not increase holdout
size. Keep training/tuning cases separate; freeze independently reviewed labels
and their hash before evaluating this holdout. A failed holdout may be reused
for regression, but retuning requires a fresh reviewed holdout for a new claim.

Coverage allocations within those counts are:

- BOLA positives: at least 25 cross-owner cases in each user direction, 25
  cross-tenant cases and 25 revoked/invalid-sharing cases. Negatives: at least
  40 same-tenant owner cases, 30 valid-sharing cases and 30 permitted scoped
  support/tenant-admin cases. Respect AP-1.0; future capabilities need fixtures
  and implementation first.
- BFLA positives: at least 25 customer-admin list, 25 customer update, 25
  missing/unknown permission or role, and 25 tenant/support scope violations.
  Negatives: at least 40 explicitly permitted admin reads, 30 permitted admin
  updates and 30 permitted scoped tenant/support functions. Vary empty,
  all-owned and mixed-owner inventories where relevant.
- Discovery positives: at least 40 shadow, 30 undeclared-method and 30 zombie
  scenarios with approved retirement metadata and a frozen clock after the
  deadline. Negatives: at least 40 documented operations, 30 valid encoded/query
  variants and 30 deprecated-but-supported operations before retirement. A
  synthetic contract/retirement fixture is required; the current contract alone
  cannot establish zombie detection. False-positive triage and malformed-input
  checks additionally remain mandatory in the deterministic set.

Pair every attack subtype with a benign near-neighbor. Labels must state the
expected family, reason, policy/contract version, server-resolved principal and
resource context, and expected application result. A denied attack may still
require an alert. A changed object ID alone is not ground truth for BOLA.

### 3.3 Failure and privacy cases

Execute at least 24 additional distinct scenarios: four each for malformed or
oversized input, missing/unknown context/version, duplicate/replayed events,
event loss/backpressure, downstream outage/recovery, and output privacy.
Include a boundary, failure and recovery where applicable. These cases are
separate from the 600 well-formed holdout scenarios and cannot pad its TN count.
All require explicit expected safe behavior. Replay must not multiply findings;
missing context must not authorize access; invalid data must not enter inventory.
Use synthetic leak markers and inspect success, rejection and exception output.

## 4. Accuracy and correctness pass/fail rules

M4/M6 report TP, FP, TN and FN separately for BOLA, BFLA and discovery, following
Day 12's definitions. Classification must match the expected family; an unrelated
finding cannot satisfy a TP. Report other unexpected findings separately.

- Precision = TP / (TP + FP).
- Recall = TP / (TP + FN).
- False-positive rate = FP / (FP + TN).
- Zero denominators are N/A and cannot satisfy a required gate.

| Gate | Pass condition |
|---|---|
| Required policy/route/triage regressions | Every required assertion passes, including all RN/DS rows and D11-F01 inventory regressions; no skips or silent feature omissions |
| Application authorization | Zero false allows and zero false denies against the reviewed lab policy; denied writes leave state unchanged |
| Holdout size/labels | At least 100 positive and 100 negative distinct cases per family, allocation above satisfied, frozen reviewed labels and no tuning overlap |
| Detection quality | Precision >= 95%, recall >= 95% and FPR <= 1% for EACH family; pooling families cannot hide a failed family |
| Required attack regressions | Zero misses among mandatory policy/security regression cases, regardless of aggregate holdout scores |
| Missing/late results | Every input is accounted for; no unreported drop, timeout or indeterminate outcome in the well-formed holdout |
| Failure/privacy cases | All 24+ cases pass; no sensitive field or synthetic leak marker in forbidden output; safe recovery and bounded resources demonstrated |

For exactly 100 positives and 100 negatives per family, recall requires TP >= 95
and FN <= 5; FPR permits at most one FP. Precision must still be calculated from
its own denominator. Thresholds are inclusive. Run the same frozen corpus three
times from reset state: every run must pass and corresponding deterministic
outputs must match after excluding declared timing/run-ID fields. Three runs
are repeatability evidence, not 1,800 distinct samples.

Use a one-second result deadline after receipt at the approved observation point
in normal-load correctness runs. A positive with no expected finding by the
deadline is FN, even if a late finding eventually appears. A negative is TN only
when receipt and successful processing are evidenced and no unexpected family
finding appears in the observation window. Unacknowledged negatives and unknown
context are indeterminate, never TN. Report their IDs/counts and fail the
completeness gate. Expected indeterminates in the separate fault suite must
match their predefined safe outcomes; they cannot dilute the holdout metrics.

The 600-case corpus is deliberately balanced and curated. Report exact counts
and denominators, not an overall "accuracy" percentage. These are sample pass
criteria, not a statistical guarantee about production precision, prevalence,
or unseen attacks. As a scale illustration only, zero FP in 100 independent
benign trials gives the one-sided 95% binomial upper bound
`1 - 0.05**(1/100)`, about 2.95%, not a guaranteed 1% population FPR. Curated
or correlated fixtures may not meet that independence assumption.

## 5. Performance sample and method

The Day 1 provisional p95 overhead goal becomes this lab acceptance rule:
`p95(monitored client latency) - p95(baseline client latency) < 5 ms` for each
approved workload stratum and each pair. This is a difference of p95 values,
not the p95 of paired per-request differences. Exactly 5 ms fails. The rule is
a lab goal and must be evidenced before a performance claim.

M3/M6 own the generator and repeatable runner, with M2/M4 component support:

1. Run baseline (API only) and monitored (same API plus approved monitor-only
   pipeline) at concurrency 1 and 10, capped at 100 offered requests/second
   total. The closed-loop generator honors both concurrency and rate caps;
   record achieved rate and generator saturation rather than assuming 100 RPS.
2. For each concurrency, perform three reset baseline/monitored pairs. Alternate
   order baseline-first, monitored-first, baseline-first. Before each arm send
   500 warmup requests, excluded from measurement, then 10,000 measured requests.
   Stop at five minutes per arm if completion fails and record a failed run.
3. Use the same seeded mix per arm: 40% owner `GET /orders/{orderId}`, 30% owner
   `GET /orders`, 20% permitted admin `GET /admin/orders`, 10% permitted admin
   `PATCH /orders/{orderId}`. Use synthetic fixtures and valid fixed-size
   responses/bodies. Hold fixture sizes and starting state constant; record
   actual payload sizes. Attack/fault tests run separately, outside timing arms.
4. Each arm has 4,000/3,000/2,000/1,000 requests in the four strata, respectively.
   Across both modes, three pairs and two concurrency levels there are 120,000
   measured requests and 6,000 warmups. Do not count latency requests as new
   labelled holdout scenarios.
5. Measure all request completions from the same client boundary with a
   two-second timeout. Preserve errors and timeouts in totals; never silently
   remove slow/failed requests. A timeout, unexpected response, lost request or
   incomplete arm fails that pair even if reported latency is low.
6. Compute p50/p95/p99 using nearest rank: sort N elapsed values, select the
   1-based `ceil(p*N)` element. Report per-stratum and combined percentiles,
   counts, achieved throughput, offered load and error totals for every arm.
   Per-stratum AND combined p95 overhead must be < 5 ms in every pair.
7. Under this normal-load profile require zero observed telemetry drops or
   unexplained count gaps, zero crash/restart/OOM, and monitored achieved
   throughput >= 95% of its paired baseline. Report per-component peak RSS,
   CPU, queue high-water marks, loss and recovery counters; prove configured
   queue/map/batch limits are respected. Overload is a separate failure test.

A Windows in-process TestClient run, a sensor-only microbenchmark or an absent
collector cannot satisfy this integrated rule. Do not average away a failed
pair or change thresholds after observing results. Record a new reviewed plan
version and rerun all affected cases if scope or environment changes.

## 6. Execution order, owner handoffs and result states

| Order / owner | Required handoff | State at reviewed source |
|---|---|---|
| 1 / M5, supported by M6 | Correct D11-F01; implement required AP-1.0 scopes, resolve contract drift, provide resettable synthetic fixtures | BLOCKED: known function-gate failure and missing policy features |
| 2 / M2, M3, M5 with M1 | Supported Linux profile, approved HTTPS-safe source and compatible bounded schemas/telemetry pipeline | BLOCKED: observation point and pipeline absent |
| 3 / M4 with M5, M6 | Executable RN/discovery/BOLA/BFLA engine, reviewed 600-case holdout and 24+ fault/privacy cases | BLOCKED: detector/corpus absent |
| 4 / M6 with all owners | Locked build/test commands, nonzero CI, dependency/static/secret and applicable container scans | BLOCKED: manifests/locks, CI and dedicated scan evidence absent |
| 5 / M3, M6 with M2, M4 | Three accuracy replays, paired Linux latency runs, loss/resource and privacy evidence | NOT RUN: prerequisites absent |
| 6 / M1 plus affected owners | Independently review results, open risks and evidence at Day 14 mid-review | PENDING: this plan needs peer review |

Performance and accuracy work is due before Week 2 acceptance, not an excuse to
waive missed Week 1 gates. D11-F01 retains its existing 2026-10-21 maximum
remediation deadline and must also be fixed before administrative-function
approval or any release. Other dependencies remain assigned in
[risk-register.md](risk-register.md). This plan does not send anyone a message or
claim they accepted a handoff.

Use PASS only for executed evidence meeting all conditions, FAIL for an executed
violation, BLOCKED when a prerequisite is absent, and NOT RUN when not attempted.
Overall integration acceptance requires all gates PASS and required owner review;
BLOCKED/NOT RUN is never a pass. A documentation PR may be reviewed while the
runtime remains blocked. Day 13 documentation completion and runtime readiness
must be reported separately.

## 7. Required result record and evidence handling

Every future run record must contain:

- Plan version, exact code/artifact/environment/corpus identifiers and commands.
- Required vs executed case counts; passed/failed/skipped/indeterminate/late IDs.
- Per-family TP/FP/TN/FN, denominators, precision/recall/FPR and decision.
- Application false-allow/false-deny counts and state-mutation assertions.
- All paired performance counts, latency percentiles/deltas, errors, throughput,
  resource/loss counters and failed-arm details.
- Privacy/failure/recovery results, scan-tool versions and summaries, remaining
  risk IDs, owners, target checkpoint, and reviewer decision.

Commit only privacy-reviewed aggregate results and synthetic case definitions.
Keep raw timings/logs in access-controlled lab evidence storage with documented
retention; never commit captures, credentials, keys, unrestricted paths/queries,
bodies or personal data. Store runtime HMAC keys separately. Record safe
artifact digests/references, not credentials in URLs. No row or metric in this
document claims that the future runs already happened.
