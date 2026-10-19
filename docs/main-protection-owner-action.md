# Main Protection: Approved Settings and Access Blocker

**Recorded:** 2026-10-19. **Owner:** `madhab-tech-cyber`, supported by `jayitape`.

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
PR. Use GitHub's merge-readiness state on a real PR to demonstrate the gate is
blocked without approvals and ready only after the actual required checks and
reviews. Do not test by direct-pushing to main or merging a PR in this task.

Protection does not retroactively review PRs #20/#22/#24/#25. Preserve their
zero-review history, request version-specific independent assessments and
record late reviews honestly. CODEOWNERS accepts any matching listed owner,
not all of them; the project still needs M1 coordination plus affected-owner
review, with an independent affected-owner review for M1-authored changes.
