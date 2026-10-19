# Member 1 Corrective Evidence and Remaining Gates

**Date:** 2026-10-19. **Branch:** `member1/security-architecture`.
**Reviewed main:** `596b592f6c5a5bd60e3037746cf2c0ee1071777e`.

The project owner requested fixes for Member 1 after the project audit. This
task corrects coordination/status defects; it does not implement teammates'
runtime components, forge meetings or approve a release. Existing work and
dated historical findings are preserved. No PR is merged or force-pushed here.

## Corrective dispositions

| ID | Finding | Action / current disposition |
|---|---|---|
| M1-C01 | Authoritative integration baseline repeats repaired D11-F01, contract drift and main-PR-trigger blockers | Corrected IF-01/IF-09, ordered plan and current blockers; link pinned evidence and distinguish API, local UI build and integrated acceptance |
| M1-C02 | Day 14 tracker closed without human evidence; Day 15/30 incomplete | Reopened #14 preserving unchecked requirements; #21/#23 retain the human gates; machine-readable checkpoint statuses remain pending |
| M1-C03 | Security/policy PRs merged without independent recorded reviews | PRs #20/#22/#24/#25 have zero review submissions; request actual M5/M6 assessment on the corrective PR and preserve history; approval is still pending |
| M1-C04 | Main unprotected, no rulesets | Owner approved exact protections, but connector protection access returns 403 and CLI authentication is rejected; no settings changed; exact settings/readback handoff documented |
| M1-C05 | Ownership and response coordination incomplete | Keep five verified handles; M1 interim M4 contact; request actual owner responses and M4 identity through #23 without inventing acceptance or names |
| M1-C06 | Risk/status statements lag newer work | Credit repaired API, main-PR CI and locally passing dashboard install/lint/TypeScript/build/audit; no dashboard tests or live backend acceptance inferred |

## Refreshed implementation evidence

Main now includes PR #24's policy/handover and PR #25's M5 Day 10 validation
note. M5 `b199da1` adds evidence only, not another runtime fix. The source of the
D11-F01 behavior repair remains `1ab289a`/PR #20. M2 `07f1410` has design/headers,
M3 `9eb26e4` is an unmerged library, M4 `841cde1` is scaffold and M6 `39902b3`
is an unmerged fixture dashboard. No live producer/consumer acceptance is added.

The preceding read-only audit ran isolated archives of main `721a14e` and M6:

- Main: 53 API/contract methods, nine D11 diagnostic cases, eight overlapping
  rehearsal scenarios and compilation PASS. The admin-owned diagnostic subset
  is empty in the fixtures; no output is counted twice as unique detector data.
- M6: locked install (`npm ci --ignore-scripts` with a writable temporary cache),
  lint, `tsc -b && vite build`, and npm audit PASS (zero known vulnerabilities
  reported). `npm test -- --run` fails with missing test script. The first install
  failed because the managed home cache was unwritable; using a temporary cache
  resolved the harness issue. No project lock was regenerated or UI rewritten.
- M6's successful run 38860076271 only checks forbidden filenames/structure.
  Local build success is not UI test coverage, live findings or backend RBAC.
- M3 Rust tests were not rerun because Cargo is unavailable. Reported 18 local
  tests/macOS microbenchmark are credited as owner evidence, not Linux acceptance.

This corrective branch reruns the API suite plus the new bookkeeping tests,
compilation, lint and documentation checks before push. Its actual command
results are recorded below. No clean full-system build,
detector accuracy, integrated performance or rollback is claimed.

## Executed corrective checks

Linux/Python 3.12.14 with preinstalled application dependencies:

| Check | Actual result |
|---|---|
| `python -m unittest discover -s tests` | PASS, 61 methods: 53 API/contract and eight separate governance bookkeeping methods |
| `python scripts/check_member1_governance.py` | PASS; Days 14/15/30 remain pending, integration blocked and release held |
| Existing nine-case D11-F01 diagnostic | PASS, every expected customer 403/admin 200 |
| Documented eight-case local rehearsal | PASS; denied/invalid writes unchanged, original inventory restored and JSON fixture hashes unchanged |
| `python -m compileall -q src mock-api tests scripts/check_member1_governance.py` | PASS |
| Ruff 0.17.1: `ruff check mock-api tests scripts/check_member1_governance.py` | PASS; tool installed only in an isolated temporary directory |
| Documentation and risk consistency | PASS: 14 changed files, ten Markdown files, 93 local links, code fences/JSON/Python syntax; all 13 risks unresolved (12 High, R-006 Medium); `git diff --check` PASS |

The dependency deprecation warning remains. These are not detector/dashboard
tests, a locked full-system environment, human evidence verification or enabled
protection. The eight governance methods test missing evidence, self-sign-off,
revision/source constraints, checkpoint dependencies, invalid bookkeeping and
reintroduction of the specific stale integration claims.

## Checkpoint and owner response procedure

[member1-checkpoints.json](member1-checkpoints.json) is the current structured
register for Day 14/#14, Day 15/#21 and Day 30/#23. All remain pending with empty
actual human evidence. Run:

```bash
python scripts/check_member1_governance.py
python -m unittest discover -s tests -v
```

The checker validates bookkeeping only. It cannot verify that a meeting or
linked comment happened, whether a sign-off is adequate, live issue state or
repository protection. Review the original sources independently. Completed
records need actual dated meeting/attendees where applicable, reviewer comments,
affected-owner responses and independent sign-offs pinned to a full revision.
Day 15 needs the real Day 14 feedback; the full Day 30 demo additionally needs
accepted integration and a reproducible run manifest. A completed meeting does
not itself approve integration or release. Never populate fields for someone
else; unit-test examples are explicitly synthetic and are not evidence.

M1 coordinates scheduling and supplies the real mentor/team review date. M5
reviews API/contract/failure claims; M6 independently assesses regression,
dashboard and CI/protection evidence. M2/M3/M4 must accept their own contracts;
M4's actual identity is still required. Track requests and actual responses in
#14/#21/#23, allow 24 hours for response and escalate at 48 hours with evidence
of nonresponse per TRIAGE-LAB-1.0. Branch age is not proof of inactivity.

The project owner approved main protection in chat, but access is blocked as
documented in [the exact owner handoff](main-protection-owner-action.md). After
owner UI action or restored administration access, save readback and actual
merge-readiness evidence before claiming it enabled. Do not bypass controls,
request credential values in chat or retroactively manufacture pre-merge review.

## Remaining acceptance decision

All 13 risks remain unresolved, with 12 High and R-006 Medium. Release stays
held, monitor-only with zero approved active rules. Required runtime correctness,
privacy, performance, route failures and rollback gates are unchanged. Human
reviews, independent D11 closure, M4 identity and enabled protection cannot be
completed by this agent's documentation or passing consistency tests.
