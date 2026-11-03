# Day 6 Week 1 Threat and Risk Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Date started:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 6 schedule task: review Week 1 threats, assign every
unresolved risk and preserve an evidence note without treating planned controls
as implemented.

## Work completed

- Re-evaluated assets A-01 through A-09 and trust boundaries TB-01 through TB-07
  against the repository's current implementation.
- Reviewed all threat scenarios T-01 through T-13 and their mapped risk entries.
- Confirmed that all scenarios remain applicable and none meets closure rules.
- Assigned a single accountable lead, required collaborators, next evidence and
  target checkpoint for R-001 through R-013.
- Identified R-004, R-005, R-011, R-012 and R-013 as missed or blocking Week 1
  integration risks.
- Preserved Medium residual ratings only where actual local evidence or an
  enforced design constraint supports them (R-002 and R-006).

The full disposition is in
[`week1-threat-review.md`](week1-threat-review.md), with assignments in
[`risk-register.md`](risk-register.md).

## Evidence boundary

The mock API and authorization tests support only TB-01 and synthetic local
fixtures. They do not validate eBPF capture, collector parsing, authenticated
transport, analytics, storage, dashboard, CI or enforcement boundaries.

Documentation of a control does not lower residual risk without implementation
and negative/failure evidence. No unresolved risk was accepted or closed during
this review.

## Verification

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`:
  **PASS — 26 tests**. The existing Starlette warning recommends moving from
  `httpx` to `httpx2`.
- `python -m compileall -q src mock-api tests`: **PASS**.
- `python -m unittest discover -v`: **FAIL/INVALID — exit 5, zero tests**.
- `git diff --check` and documentation local-link, trailing-whitespace and
  credential-pattern checks: **PASS — no findings**.
- Integrated/failure/security scan evidence: **UNRUN/ABSENT** because the
  relevant components and tooling are not present.

## Result

The Week 1 threat review and accountable risk assignments are prepared. Risk
ownership is explicit, but the risk posture remains unsuitable for integration
or release approval until the blocking evidence is delivered.
