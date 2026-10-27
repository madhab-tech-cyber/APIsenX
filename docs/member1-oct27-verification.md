# Member 1 repository correction verification

**Date:** 2026-10-27 (Asia/Calcutta). **Implementer:** `madhab-tech-cyber`.
**Main baseline:** `5f10593a294c68a2729f2c4072c4c4ffa5814f19`.
The interrupted October 24 draft was saved in a local Git stash, main was
fast-forwarded normally, and the draft reapplied without losing newer CI,
rate-limit, load-probe or storage-proposal work. The backup is retained.

## Engineering changes

- Pin human candidates separately from current main; retain historical tracker
  IDs and real M5 responses. Closed trackers never complete a human checkpoint.
- Reject self/decorated-login approvals, wrong-revision meeting/sign-offs,
  timezone-naive sign-offs, Day 30 bypass of Days 14/15, evidence-free integration
  acceptance and release with pending human gates/unverified protection.
- Default checker returns consistency only and prints pending gates;
  `--require-complete` returns exit 2 while blocked. Add checker and tooling lint
  to CI without pretending it authenticates human evidence or remote settings.
- Refresh architecture, risk, ownership and README with merged M4, real M6
  four-test/build CI, M3 Linux userspace loopback, new M5 API caps/load CI and
  the still-unapproved PostgreSQL audit proposal. Preserve all residual ratings.
- Correct four pre-existing Ruff findings in the load helper with line wrapping
  and equivalent result collection; do not change its workload or result policy.

## Actual checks

Fresh Linux/Python 3.12 virtual environment; existing project requirements,
Ruff 0.17.1, Bandit 1.8.6, pip-audit 2.10.1 and detect-secrets 1.5.0.
The preserved/refreshed draft passed 272 test methods before the last additional
login regression. Final correction counts/results and exact-head remote jobs
are recorded on the delivery PR after execution, not inferred from this note.

Final local correction: **273 test methods PASS** in 6.577 s; repository-wide
Ruff, runtime Python Bandit, scoped M4 secret scan, dependency audit, source
freeze, changed Python/JSON/YAML/Markdown checks and 128 local links PASS.
Strict completion returns the expected exit 2 and six pending gates. The M1
patch leaves analytics/collector/mock-API/authorization/requirements/OpenAPI
byte content unchanged; only the load-probe helper receives lint-only cleanup.

```bash
python -m unittest discover -s tests -q
python -m ruff check .
python scripts/check_member1_governance.py
python scripts/check_member1_governance.py --require-complete
python -m bandit -r src mock-api analytics -q
python scripts/check_analytics_secrets.py
python -m pip_audit -r requirements.txt
python -m analytics.package --check
```

The strict completion command is expected to return 2, not green acceptance.
The static scan above covers runtime Python, not every helper: the October 26
expanded scan reported eight low subprocess and two medium urllib heuristics
in existing helper scripts; those require scoped triage, not invented exploit
claims or blanket suppressions. The secret check is scoped M4 source/test/docs,
not complete repository-history scanning. No local Rust result is claimed;
Cargo is unavailable. The local TestClient suite needs sandbox network permission.

## Live external evidence / blockers

Exact baseline-main API run 40455842509 and analytics run 40455842618 succeeded;
API steps include bounded Day 19 normal/overload/recovery probes and denied
cross-owner write non-mutation. This is isolated mock-API evidence, not the
full-system paired MRVP latency gate or human sign-off.

Main still reports unprotected, rulesets empty; connector protection GET returns
HTTP403. The already-approved `manage_main_protection.py --apply` was retried
and stopped at its first CLI read (exit 2), before a PUT. No settings changed.
Actual human meetings/reviews and durable-store infrastructure/design approval
remain missing in the retrieved records. No personal names, due dates, owner
responses or independent sign-offs are manufactured. No source approval,
release, deployment, force push or PR merge is performed by this correction.
