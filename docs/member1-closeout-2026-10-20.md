# Member 1 Evidence Reconciliation and Protection Closeout

**Observed:** 2026-10-20 (Asia/Calcutta).
**Baseline main:** `683a93a7f59938d6e22e8402ed617d1f8cb36101`.
**Branch:** `member1/security-architecture`.

> Historical October 20 snapshot. The [October 27 closeout](member1-closeout-2026-10-27.md)
> supersedes current-state claims below, credits later M3/M4/M5/M6 work and
> tracks remaining actual acceptance in Issue #61. Earlier observations stay dated.

This was the October 20 Member 1 coordination record. It superseded current-status
claims in older dated documents without rewriting historical observations.
Day labels do not establish calendar attendance, human review or release.

## Facts now reconciled

| Scope | Actual evidence | Acceptance boundary |
|---|---|---|
| M5 API/privacy/startup | PRs #28–#31 merged; clean requirements install, 57 API/authorization/contract methods, lint, dependency audit, nine D11 diagnostics and eight overlapping rehearsal cases pass | Tenant/share/support/version policy remains unsupported; observation hook is a candidate, not an accepted live sensor contract |
| M5 owner response | One real #21 handoff and two #23 evidence updates by `pappukumar96727-sketch` are linked in the register | Partial owner responses; not a human meeting, all-owner acceptance or independent M1 checkpoint sign-off |
| Component review | M1 approved PR #28 at `974e5129116380ed10ab17c12695c911fb8b6ee3` | That approval covers its pinned revision only, not later PR #31, M1-authored policies or release |
| M3 collector | PR #32 is merged; v1.1/null correlation, explicit ambiguity and loss availability/reset states; owner reports 22 macOS Rust tests | No Linux/live acceptance. Its green Actions run 39289716416 runs Python API checks, not Rust tests |
| M2/M4/M6 | M2 still headers/design; M4 scaffold; M6 fixture UI has passing local install/lint/TypeScript-build/npm audit but no test command | No live detector, protected management backend, UI test coverage or accepted pipeline |
| Governance | #14/#21/#23 are closed; checkpoint statuses remain pending. #33 tracks the actual remaining owner actions | Closure and merged documents cannot supply missing attendees/comments, responses or independent approvals |

The structured [checkpoint register](member1-checkpoints.json) now credits those
specific source references. Component approvals are deliberately separate from
M1 human sign-offs. Case-changed usernames cannot bypass self-sign-off checks.
An issue-state snapshot is dated evidence, not a driver that marks a human task
complete. No author response, attendance record or personal full name is invented.

## Protection: implementation ready, actual access blocked

The owner previously approved exact main protection. The connected GitHub app
still receives Administration HTTP403, and configured CLI authentication fails.
Plugin approval preferences cannot grant GitHub OAuth scopes; no preferences
or injected credentials were changed. No administrative setting is claimed
enabled without readback.

The [approved payload](main-protection-settings.json) and
[owner utility](../scripts/manage_main_protection.py) replace a vague handoff
with reproducible operations:

```bash
python scripts/manage_main_protection.py --check
python scripts/manage_main_protection.py --apply
```

Default mode is read-only. Apply can target only this repository's main, requires
an authenticated owner/admin, refuses to overwrite existing partial/stronger
settings, and checks exact context/app, review controls, admin enforcement,
conversation resolution, force/deletion settings and branch readback. It does
not merge, push, change collaborators/rulesets or grant release. Already compliant
stronger settings remain unchanged. A failed read stops before PUT; failed
post-write verification is explicitly reported as submitted-but-unverified.
See [complete owner instructions](main-protection-owner-action.md).

## Actual remaining owner actions

[Issue #33](https://github.com/madhab-tech-cyber/APIsenX/issues/33) is the focused
closeout tracker. Preserve prior owner closures rather than repeatedly reopening
them or declaring their human gates satisfied.

- Repository owner: run the approved apply command with real Administration
  access or use GitHub settings, then attach readback and real PR gate evidence.
- M5/M6: independently review the new M1 correction revision and provide actual
  responses. M1 cannot approve M1-authored policy work.
- M1/M6: assess the latest PR #31 revision independently; keep historical PR #28
  approval separate. Automated regression evidence alone is not source approval.
- M1: confirm the actual M4 identity, coordinate the real review/demo date and
  retain actual attendees, comments, dispositions and independent sign-offs.
- M2/M3/M4/M6: mutually accept exact producer/consumer contracts and provide
  live correctness, privacy, latency/loss, route-failure and rollback evidence.

Source-review tooling was unavailable in the audit (CodeRabbit installer
HTTP403); no manual-source-review substitute or approval is invented. Rust
checks remain owner-reported because Cargo is unavailable in this workspace.
The current API byte content at PR #31 matches the tested baseline for
`mock-api/`, `src/`, `tests/` and requirements; that comparison is not independent
source approval. This patch changes governance tooling/documents, not API rules
or collector code.

All 13 risk entries remain unresolved (12 High, R-006 Medium). Monitor-only,
zero active rules and release hold remain. No completed meeting, production
readiness, enabled protection or retroactive pre-merge review is claimed.

## Executed correction checks

On October 20, using the audit virtual environment and pinned project requirements:

- `python -m unittest discover -s tests -q`: **81 methods PASS** — 57 API/auth/contract,
  12 checkpoint-bookkeeping and 12 mocked protection-utility methods. Network
  permission was needed for the local TestClient transport; the restricted run
  stalled and was stopped, then the permission-enabled run completed in 0.160 s.
  Starlette's existing httpx deprecation warning remains.
- `python -m ruff check .`, `python scripts/check_member1_governance.py`,
  Python AST/compile checks and `git diff --check`: **PASS**.
- All 274 local Markdown links resolve; fences and JSON parse checks pass.
  All 13 primary risk rows retain their prior residual ratings.
- Live `python scripts/manage_main_protection.py --apply`: **BLOCKED**, exit 2,
  at its initial access read (`HTTP unknown` from the failing CLI). No PUT was
  reached. The connector independently returns Administration HTTP403.

These are automated verification results, not human checkpoint acceptance,
source-review approval, live integration or proof of enabled protection.
