# Day 12 False-Positive and False-Negative Coverage Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Date:** 2026-10-14

**Reviewed runtime baseline:** `df86811`

## Measurement definitions

For detection, positive means an independently labelled security finding is
expected. TP is a correctly emitted finding, FN is a missed expected finding,
FP is a finding on a labelled benign observation, and TN is a correctly quiet
benign observation. Report precision = TP/(TP+FP), recall = TP/(TP+FN), and
false-positive rate = FP/(FP+TN), with raw counts and per-category denominators.
Zero denominators are N/A, never 100 percent success.

For application authorization, false allow means unauthorized access succeeds;
false deny means authorized access fails. These are distinct from detector FN
and FP. A test asserting 403 proves application denial only. It does not prove
that a BOLA/BFLA detector emitted the right finding or that benign traffic stays
quiet. A denied malicious attempt may still legitimately trigger a finding.

Unknown context is an indeterminate outcome requiring explicit accounting; it
must not silently disappear from denominators or be counted as a TN. Ground
truth uses server policy and synthetic fixture context, not detector output.

## Existing evidence inventory

The explicit unittest command executes 10 authorization tests and 16 API tests.
`test_all_documented_cases` additionally checks seven fixture rows inside one
test; these are subcases, not seven additional independent tests. Overlapping
unit/HTTP coverage must not be reported as distinct labelled traffic samples.

| ID | Category | Evidence present | Coverage gap / owner |
|---|---|---|---|
| AC-01 | Benign owner read/list | Unit owner allow; HTTP owner read and list filtering | Detector TN/FP absent; M4 |
| AC-02 | Benign admin read/manage | Unit admin allow; HTTP admin list and update | Explicit permissions and detector TN/FP absent; M5/M4 |
| AC-03 | Cross-owner BOLA attempt | Fixture AUTH-002, unit denial, HTTP 403 | Detector TP/FN, reverse user direction and sharing cases absent; M4/M5 |
| AC-04 | Customer BFLA update | Fixture AUTH-004, unit deny, HTTP 403 | Detector TP/FN and denial-without-mutation assertion absent; M4/M5 |
| AC-05 | Admin list function gate | Customer denied with ordinary mixed-owner fixture | D11-F01: empty/all-owned inventory false allows reproduced; M5/M6 |
| AC-06 | Invalid/inactive identity | Fixture, unit and selected HTTP negatives | Per-route auth matrix and signed-token expiry/audience/replay absent; M5 |
| AC-07 | Unknown role/action | Unit negatives, selected admin HTTP negative | Every route and inventory shape; explicit permission/version failures absent; M5/M6 |
| AC-08 | Missing object and malformed update | Unit missing-object denial; HTTP update field/status/empty-body checks | HTTP missing object, no mutation, safe error/audit coverage incomplete; M5/M6 |
| AC-09 | Benign sharing/support/tenant-admin | AP-1.0 requirements | No executable cases or controls; M5 and M4 |
| AC-10 | Cross-tenant and revoked sharing | AP-1.0 denial requirements | No executable cases or controls; M5 and M4 |
| AC-11 | Route normalization/discovery | 53 RN cases and 15 DS scenarios specified | No executable normalizer/detector corpus; M4 |
| AC-12 | Loss, replay, unknown version and privacy | Interface/design requirements | Integrated failure and leak evidence absent; M3/M4/M6 |

## Confirmed blind spot and acceptance decision

The 26 passing tests coexist with customer HTTP 200 responses from an admin
function under two inventory shapes. These are application false allows against
`AP-1.0`. They are not measured detector false negatives because the repository
contains no executable detector. See
[function-level-authorization-review.md](function-level-authorization-review.md).

Detection TP, FP, TN, FN, precision, recall and false-positive rate are all
**UNMEASURED**. Application test results cannot establish a detection accuracy
percentage. The complete accuracy coverage gate is **NOT APPROVED**.

## Required corpus and execution evidence

M4 owns the labelled detection corpus; M5 supplies server-resolved policy and
runtime fixtures; M6 owns repeatable test execution; M3 supplies loss/replay
failure fixtures. Each case needs a stable ID, expected detector outcome,
category, method/template, policy/contract version, synthetic principal/resource
context, source quality and expected reason. Raw tokens, queries and unknown
paths must not enter stored evidence.

Pair every attack category with a benign near-neighbor: other-owner read versus
valid share, customer admin call versus permitted admin, cross-tenant access
versus same-tenant owner, shadow route versus encoded documented route, and
revoked grant versus active grant. Include malformed, missing-context and
failure outcomes separately.

Use isolated/reset fixtures for every case. The merged API stores order changes
in process memory; existing tests do not restore ORDERS between tests or assert
denied requests leave state unchanged. Avoid test-order dependence and verify
both action result and state before counting a case.

Report raw counts per BOLA, BFLA and discovery category, case IDs, excluded or
indeterminate cases, exact revisions, and repeatable execution command. Preserve
reviewed labels and a separate validation set when tuning heuristics. Day 13
sets final sample sizes, environment and numeric pass/fail criteria; this review
does not invent those thresholds.

## Priorities and exit gates

1. M5/M6 close D11-F01 with independent permission enforcement and inventory
   regressions by 2026-10-21 and before release.
2. M4/M5 implement and pair the missing AP-1.0/RN/DS cases before Week 2 accuracy
   approval; distinguish planned controls from passing execution evidence.
3. M6 provides nonzero deterministic CI and regression evidence before the next
   integration approval; default discovery remains an independently tracked gap.
4. M1 reviews confusion counts, indeterminate outcomes and unresolved risk before
   accepting any accuracy claim. R-002, R-011, R-012 and R-013 remain unresolved.
