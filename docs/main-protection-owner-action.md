# Main Protection: Approved Settings and Access Blocker

**Refreshed:** 2026-10-27 (Asia/Calcutta). **Owner:** `madhab-tech-cyber`, supported by `jayitape`.

The project owner explicitly approved protecting `main` during the Member 1
corrective task. Authorization is received; implementation is BLOCKED, not done.
No administrative setting was changed.

## Actual access and check evidence

The branch list reports `main` unprotected; rulesets are empty. The connector's
`GET /repos/madhab-tech-cyber/APIsenX/branches/main/protection` returns 403
`Resource not accessible by integration`. The configured CLI token is rejected
by `gh auth status --hostname github.com`; its protection read also fails.
No token value was read, printed, replaced or requested in chat. Do not bypass
the proxy or silently use another credential.

The GitHub plugin is already connected/enabled. ChatGPT plugin approval
preferences are not GitHub OAuth Administration scopes and were not changed.
The same Administration/CLI failure was rechecked on October 27. The approved
apply stopped at its initial CLI read (exit 2); no PUT/settings change occurred.
Main reports `protected: false` and rulesets are empty. Active owner follow-up
is the correction PR and [#61](https://github.com/madhab-tech-cyber/APIsenX/issues/61);
#23/#33/#61 are now owner-closed historical trackers, not evidence of completion.

## Tested owner command (default is read-only)

The approved REST settings are stored in
[main-protection-settings.json](main-protection-settings.json). From this
repository checkout, on a machine whose GitHub CLI is authenticated as the
repository owner/admin:

```bash
python scripts/manage_main_protection.py --check
python scripts/manage_main_protection.py --apply
python scripts/manage_main_protection.py --check
```

Only `--apply` can write. It targets exactly `madhab-tech-cyber/APIsenX:main`,
requires an authenticated admin, creates the approved legacy rule only if none
exists, then verifies protection and branch readback. It preserves an already
compliant/stronger rule and refuses to overwrite other existing protection.
403/authentication failure stops before any PUT. It never edits rulesets,
permissions, collaborators, source branches or credentials. Exit 0 means the
settings readback matched; exit 1 means unmet settings; exit 2 means blocked.
Do not interpret mocked unit-test success as a real administrative change.

Before applying, verify the corrective PR's observed API check is passing;
after applying, retain the JSON readback and actual PR merge-readiness evidence.
Do not merge a PR or direct-push to main just to test the gate. If authenticated
Administration access is unavailable, use the owner UI below. Never paste a
token into a tracker, terminal transcript or chat.

Observed required-check candidate: `API Security and Quality Gates`, app
`github-actions` (ID `15368`). On `b199da1` checks `117921636188` and
`117920785321` succeeded; PR #24 run
[39209714300](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/39209714300)
also succeeded. The workflow runs for PRs targeting main. The final corrective
PR must demonstrate that exact check on its own head before it is required.

## Repository owner UI action

In [repository branch settings](https://github.com/madhab-tech-cyber/APIsenX/settings/branches),
create/verify a protection rule targeting exactly `main`:

- Require pull requests and at least two approving reviewers; author approval
  is not an independent approval.
- Require code-owner review, dismiss stale approvals and require approval of
  the latest push by someone other than its pusher.
- Require resolved review conversations.
- Require `API Security and Quality Gates` from GitHub Actions and require the
  branch to be up to date before merging. Do not require invented/unrun jobs.
- Apply the rule to administrators/no routine bypass, with an empty bypass
  list for this baseline.
- Keep force pushes and branch deletion disabled.

These settings enforce only the observed API gate. They do not imply dashboard
tests, full-system acceptance, secret scanning or SBOM coverage. Add future
checks only after M6 proves their actual names and trigger behavior.

## Verification required before marking done

Save a settings readback or owner-provided screenshot with date, exact pattern,
review count, code-owner/stale/latest-push rules, strict check context and app,
admin/bypass and force/deletion settings. Link it in Issue #23 and the corrective
PR and [Issue #33](https://github.com/madhab-tech-cyber/APIsenX/issues/33).
Earlier #23 is closed without satisfying the underlying release hold.
Use GitHub's merge-readiness state on a real PR to demonstrate the gate is
blocked without approvals and ready only after the actual required checks and
reviews. Do not test by direct-pushing to main or merging a PR in this task.

Protection does not retroactively review PRs #20/#22/#24/#25. Preserve their
zero-review history, request version-specific independent assessments and
record late reviews honestly. CODEOWNERS accepts any matching listed owner,
not all of them; the project still needs M1 coordination plus affected-owner
review, with an independent affected-owner review for M1-authored changes.
