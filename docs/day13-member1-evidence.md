# Day 13 Member 1 Evidence

**Date:** 2026-10-15 (Asia/Calcutta)

**Branch:** `member1/security-architecture`, confirmed by the project owner.

**Task:** Define sample size, environment and pass/fail criteria (Member 1
responsibility plan, page 3).

**Issue:** [#11](https://github.com/madhab-tech-cyber/APIsenX/issues/11)

**Reviewed baseline:** `f566d7a6bac2466f158b88cc55d13f309c6f8f0c`

## Delivered specification

[MRVP-1.0](mid-review-validation-plan.md) defines:

- Mandatory RN/DS/AP-1.0/function regressions, including D11-F01.
- A minimum 600 distinct reviewed holdout scenarios: 100 positive and 100
  negative each for BOLA, BFLA and discovery; three reset replays.
- At least 24 separate fault/privacy scenarios with explicit safe outcomes.
- Per-family precision >= 95%, recall >= 95%, FPR <= 1%; complete accounting,
  zero required-regression misses and zero application false allows/denies.
- An isolated Linux profile, immutable run manifest and approved HTTPS-safe
  telemetry prerequisites.
- Three baseline/monitored pairs at each of concurrency 1 and 10: 120,000
  measured requests plus 6,000 warmups. Every per-stratum and combined p95
  latency delta must be < 5 ms; errors/loss/incomplete arms cannot be hidden.
- Owners, result states, evidence handling and reasons to withhold approval.

These are defined lab criteria, not measurements. Numeric targets were chosen
for MRVP-1.0; the PDF specifies the task rather than these particular numbers.
The [risk register](risk-register.md) records the handoff; all existing residual
ratings and open findings are retained.

## Source and local verification environment

The supplied responsibility PDF was read directly. Its SHA-256 is
`4379b0938dcf67499b633079d686b937a14648f7b3bc91768d8efa432c29568c`.
Source pages 3-4 establish the assignment and daily evidence/review workflow.
The delivery branch matches the PDF-assigned `member1/security-architecture`.

All 51 source files were retrieved at the reviewed GitHub SHA and verified
against their Git blob hashes in a separate local snapshot. This avoids
changing the user's Antigravity working directory or backup stash.

Actual regression environment: Windows 11 build 22631, CPython 3.12.6,
FastAPI 0.109.0, Starlette 0.35.1, Pydantic 2.5.3, HTTPX 0.27.2 and AnyIO 4.14.2.
These describe the existing test environment; they are not a reviewed dependency
lock or an assertion that those package versions have no vulnerabilities.
No dependency or executable source file was changed.

## Executed checks

From the snapshot root, using the installed CPython 3.12.6 interpreter:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Result: PASS, 26 tests (10 authorization and 16 HTTP/API). The documented fixture
subcases are part of those methods, not additional traffic samples. This explicit
`-s tests` run does not establish that default discovery or CI is configured.

The bundled CPython 3.12.14 interpreter separately passed the 10 authorization
tests. Its API-test attempt failed to import FastAPI because that dependency
was absent; the installed interpreter above then ran the complete suite. This
environment failure is recorded rather than reported as a passing test run.

Additional Day 13 checks: Python compileall; local Markdown links and trailing
whitespace; RN/DS identifier counts; holdout/performance arithmetic; and
credential-pattern inspection of the three changed documents. Results are
recorded in the draft pull request. The limited pattern inspection is not a
dedicated secret scan or a vulnerability assessment.

## Decision and remaining work

Day 13's criteria are drafted and ready for peer review. The documentation can
be reviewed without approving the unfinished runtime. Integrated accuracy,
latency, Linux/eBPF compatibility, resource and failure behavior, and dedicated
security scans are NOT RUN/BLOCKED; no accuracy, latency or zero-vulnerability
claim is made.

D11-F01 and the missing detector/pipeline, policy features, reproducible build
and scan evidence remain open under their existing owners. No risk is accepted
or closed, and no blocking action or release is authorized. M4/M5/M6 (and M2/M3
for Linux/performance handoffs) must review the applicable criteria before
merge. Day 14 should collect actual owner evidence and open risks; it must not
mark this specification as measured acceptance.
