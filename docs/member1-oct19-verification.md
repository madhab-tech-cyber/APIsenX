# Member 1 October 19 Verification Baseline

**Execution date:** 2026-10-19 (Asia/Calcutta).

**Reviewed main:** `c16596428d241fd2f61a97e62f8a50bf6c0768d6`.

This snapshot supports the Days 21–30 policy/review package. Day numbers are
schedule tasks, not ten calendar workdays. No human meeting, mentor feedback,
owner sign-off, integrated demo or production release is implied.

## Executed checks

Linux 6.18.55 x86_64, CPython 3.12.14, preinstalled dependencies. The environment
is not a clean requirements installation or an approved Linux sensor profile.

```bash
python -m unittest discover -s tests -q
python -m compileall -q src mock-api tests
```

PASS: 53 test methods; compilation PASS. The Starlette test-client dependency
warning remains. Tests do not establish detector accuracy or integrated latency.

The reproducible diagnostic in
[October 17 verification](member1-oct17-verification.md) was re-executed against
current main: all nine outcomes PASS, exit 0. Both customers get 403 for empty,
all-owned and mixed inventories; admin gets 200. The admin-owned subset is empty
in these fixtures. Temporary patches restore in-memory state; disk fixtures are
unchanged. D11-F01 behavior is fixed by merged
[PR #20](https://github.com/madhab-tech-cyber/APIsenX/pull/20), at
`1ab289aeab0ea072e731c18615cbea8c29f6d5d5`. Closure still needs independent review;
the broader tenant/sharing/version authorization risk is not resolved.

## Live repository evidence

| Scope | Pinned head | Evidence boundary |
|---|---|---|
| Main | `c165964` | M5 fix and M1 governance corrections merged |
| M1 | `a76374f` before this package | Policy/ownership corrections; merged PR #22 has zero submitted reviews |
| M2 | `07f1410` | Capture design/headers/prerequisite tests; no new sensor evidence |
| M3 | `9eb26e4` | Unmerged Rust collector library, schemas and reported local tests; no live Linux/analytics integration |
| M4 | `841cde1` | Scaffold; no detector, ingestion or labelled results |
| M5 | `1ab289a` | Authorization fix and new regressions; PR CI success |
| M6 | `39902b3` | Unmerged fixture React UI; limited repository-check CI |

GitHub Actions run 39103365610 reports successful API/contract tests, Ruff and
dependency audit on the M5 PR head; the main-targeting PR trigger now exists.
This is stronger than earlier branch-only CI but not full integration evidence.
Main and member branches report unprotected; ruleset list is empty. PRs #20/#22
have zero submitted reviews. Issue #14 is closed again with no comments and
unchecked human requirements; Issue #21 remains open with no actual feedback.
No administrative setting or peer branch is changed by this verification.

## Evidence status vocabulary

PASS means executed evidence met the stated condition. FAIL means an executed
condition violated its expectation. BLOCKED means missing prerequisites;
NOT RUN means not attempted; PENDING means an actual review/response is needed.
A design approval does not mark runtime controls PASS. An open risk cannot be
silently accepted by preparing a day-numbered file.
