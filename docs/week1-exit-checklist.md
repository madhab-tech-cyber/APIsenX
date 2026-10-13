# Week 1 Exit Checklist

**Reviewer:** Member 1 - Team Lead and Security Architect

**Review date:** 2026-10-13

**Overall decision:** **NOT APPROVED — integration exit criteria are not met**

## 1. Status rules

- **PASS:** required implementation and review evidence exists.
- **CONDITIONAL:** useful evidence exists, but stated limitations remain.
- **FAIL:** a required result or control is absent, contradictory or unverified.
- **N/A:** no reviewable item exists; this is not equivalent to approval.

## 2. Foundation and governance

| Exit item | Status | Evidence / blocker |
|---|---|---|
| Authorised scope and prohibited targets/data are documented | PASS | `scope-and-governance.md`, `SECURITY.md` and the data-classification policy |
| Architecture, assets and trust boundaries are documented | PASS | `architecture.md` and `threat-model.md` |
| Authentication, authorization and data handling decisions are recorded | PASS | Day 4 decision documents; implementation remains local-lab only |
| Integration flow, interfaces and owner handoffs are documented | CONDITIONAL | `integration-data-flow.md`; IF-02 through IF-09 are not implemented or accepted by both owners |
| Week 1 threats reviewed and unresolved risks assigned | PASS | `week1-threat-review.md` and the Day 6 risk assignment table |
| Changes are linked to scoped issues | FAIL | Day 3 through Day 7 evidence still contains pending tracking-issue placeholders |
| CODEOWNERS names real GitHub reviewers | FAIL | `.github/CODEOWNERS` still contains placeholder handles such as `@member1` |
| Required peer review and protected merge controls are evidenced | FAIL | Branch protection is recorded as unconfigured; historical merges do not establish the required future review gate |

## 3. Week 1 technical criteria

| Exit item | Status | Evidence / blocker |
|---|---|---|
| Mock API and local authorization path run with positive/negative tests | CONDITIONAL | 26 focused tests pass; static opaque lab tokens and known contract drift prevent broader approval |
| Mock API, eBPF sensor and collector run in the integrated lab | FAIL | eBPF and collector directories contain README placeholders only |
| Approved method/route/timestamp/connection metadata reaches the pipeline | FAIL | Observation point is not selected and no runtime telemetry pipeline exists |
| HTTPS-safe observation point and capture allowlist are approved | FAIL | R-001/R-006 remain unresolved; TLS must not be weakened |
| Kernel and normalised event schemas are versioned and accepted | FAIL | Interface requirements are prose only; no machine-readable schemas or contract tests exist |
| OpenAPI matches runtime authentication, errors and validation status | FAIL | R-011 and findings D3-F01 through D3-F03 remain open |
| Deterministic test discovery and CI gates run non-zero tests | FAIL | Explicit tests pass, but default discovery exits 5 after running zero tests and no CI workflow exists |
| Dependency manifests, lock files and vulnerability review exist | FAIL | No manifests/locks or reproducible dependency review are checked in |
| Dedicated secret scanning is configured and passing | FAIL | No dedicated secret scanner or retained scan evidence exists |
| Static, dependency, container scans and SBOM entry points exist | FAIL | Tooling and project configuration are absent |
| High integration risks have implemented treatment evidence | FAIL | R-004, R-005, R-011, R-012 and R-013 retain High residual risk and block this gate |

## 4. Pull-request review inventory

Read-only GitHub and Git checks on 2026-10-13 found **zero open pull requests**.
Therefore, no integration pull request was available to approve, request changes
on or merge.

| Item | State | Day 7 decision |
|---|---|---|
| PR #4, `member5/mock-api` | Already merged into `main` | Cannot be retroactively approved; its local mock API evidence remains conditionally accepted with D3/R-011 follow-up |
| PR #5, `member1/security-architecture` | Already merged into `main` | Cannot be retroactively approved; it contains the Day 2–3 documentation baseline |
| Commit `65e3d0f` on `member1/security-architecture` | Pushed after PR #5 merged; not in `main` and no open PR exists | Not reviewed or approved for merge; requires a linked issue, draft PR, passing checks and a reviewer other than its sole author |
| Member 2/3/4/6 integration branches | Remote tips still point to the shared documentation commit `841cde1`; no open PR exists | N/A — no component implementation or reviewable integration change exists |

This review does not claim approval merely because work was previously merged.
No GitHub approval, merge or review-state mutation was performed.

## 5. Exit decision and re-entry criteria

The project may continue foundation work and local mock API testing, but it has
**not passed the Week 1 integrated-lab exit**. No release or end-to-end detection,
enforcement, performance, masking or dashboard claim is approved.

Re-run this checklist only after:

1. scoped issues and real reviewers are linked;
2. M5 resolves OpenAPI/runtime drift;
3. M6 adds reproducible dependency/test/scan/SBOM gates;
4. M1/M2/M5 approve the observation point and capture allowlist;
5. M2/M3 provide a bounded, tested sensor-to-collector contract;
6. affected producer/consumer owners approve machine-readable interface schemas
   with compatibility and failure tests; and
7. an open integration pull request contains the required evidence and independent
   reviewer approval.
