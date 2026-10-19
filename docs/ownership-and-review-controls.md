# Verified Ownership and Review-Control Handoff

**Owner:** Member 1. **Identity observed:** 2026-10-18 (Asia/Calcutta).
**Control/CI status refreshed:** 2026-10-19.

## Identity evidence

| Role | Verified GitHub identity | Evidence | Repository permission |
|---|---|---|---|
| M1 | `madhab-tech-cyber` | Author of PR #18 and Member 1 branch delivery; user-specified Git identity | admin |
| M2 | `renu-stack` | Linked author/committer of `07f141022f31979c9464c2f853b982e03b4373a4` on assigned branch | write |
| M3 | `aadi3006` | Linked author/committer of `9eb26e4cd4d0cc33b92c4103a13cc90724206c31` on assigned branch | write |
| M4 | Pending | No attributable detection implementation commit in inspected scaffold branch | Not verified |
| M5 | `pappukumar96727-sketch` (Git display name Pappu kumar) | PR #19 author and workflow head commit `8f155631a5d8c878190db741143d06c28a26ef22` | write |
| M6 | `jayitape` (Git display name Jay Itape) | Linked author/committer of `39902b358ef68911795546bf22ae5faf46fbe078` | write |

Permission endpoints were read for each named identity. Attribution is evidence
of the published Git role, not a claim of personal identity verification or
acceptance of a new handoff. Full names for alias-only identities remain pending.
M1 is explicitly the interim `/analytics/` review owner until M4 is confirmed.

## CODEOWNERS semantics

The proposed [CODEOWNERS](../.github/CODEOWNERS) uses only verified accounts.
GitHub uses the last matching pattern and accepts any listed owner on that
pattern; listing two owners does not enforce both approvals. For security
changes the review record must separately contain M1 and affected-component
review, with an independent reviewer who is not the author. M1-authored policy
changes require affected-owner review; the author cannot approve their own work.
M6 is included on policy/workflow paths to permit independent evidence review.
This mapping does not activate protection by itself.

## Observed controls and repository-owner actions

On October 18, branch-list responses reported every branch `protected: false`;
the ruleset list was empty. PR #18 and #19 each had zero review submissions at
the audit. October 19 reconfirms unprotected branches and an empty ruleset list;
merged PRs #20/#22 also have zero submitted reviews. No protection, ruleset or
collaborator permission was changed here.

The corrective snapshot on October 19 additionally confirms merged PRs #24/#25
have zero submitted reviews. The project owner approved main protection, but
the connector returns HTTP 403 for protection access and CLI authentication
is rejected. Implementation/readback is BLOCKED; see the exact
[approved owner action](main-protection-owner-action.md). Authorization received
does not mean protection is enabled. Do not merge this correction without real
independent reviews simply because it fixes a prior review-control failure.

M1 (repository owner), with M6 CI support, must review and configure:

- PR-only changes into main; block direct/force pushes and branch deletion;
- at least two independent approvals, code-owner review and resolved
  conversations; dismiss stale approvals after code changes and require
  approval of the latest reviewable push by someone other than its pusher;
- no routine administrative bypass; document any exceptional bypass separately;
- required checks whose exact contexts are observed on the intended main PR
  revision, and a current branch/update policy before merge;
- actual M1 plus affected-owner review references where GitHub's any-owner
  behavior cannot express the project's two-role requirement.

These are a proposed handoff, not assertions of enabled settings. Verify through
the GitHub UI/API and a sample blocked/unblocked PR, then save the exact settings,
check contexts, revision and independently reviewed result. A required check
with no matching trigger can leave PRs permanently pending; correct triggers
and demonstrate execution before requiring it.

## CI evidence and remaining checks

| Context observed | Current evidence | Required next evidence |
|---|---|---|
| `API Security and Quality Gates` | PR #24 run 39209714300 and M5 checks on b199da1 succeed: API/contract, Ruff and dependency audit; app github-actions ID 15368; main-targeting PR trigger exists | Verify this exact context on the corrective PR head before requiring it; save protection readback and real independent reviews |
| `Repository security checks` | Member 6 push run 38860076271 succeeded: sensitive-file names and repository structure | Do not call this dashboard test coverage or a dedicated secret scan |
| Dashboard validation | Local locked installation, lint, TypeScript/production build and npm audit pass on 39902b3; no test script; successful M6 CI has no dashboard build/test job | M6 preserves the working fixture UI, adds state/privacy tests and locked install/lint/typecheck/build/test CI; M4/M6 prove backend authorization |
| Collector/sensor integration | M3 reports local Rust checks; M2 reports prerequisite/layout checks | M2/M3/M4 Linux producer/consumer, failure, loss and privacy evidence; reproducible CI where supported |

Use the current names only after testing trigger coverage. No invented future
dashboard check name is declared mandatory yet. Code, schema, documentation,
quality/security and applicable build checks need separate trustworthy evidence;
one passing job does not cover unexecuted gates.

## Checkpoint closure

Treat [#14](https://github.com/madhab-tech-cyber/APIsenX/issues/14) and
[#21](https://github.com/madhab-tech-cyber/APIsenX/issues/21) as incomplete until real
attendees/comments, owner responses, dispositions and independent sign-offs
are linked. The corrective task reopened #14 at 06:44 UTC on October 19 with
its unmet requirements retained; the owner closed it again at 06:58 UTC, still
with zero comments. That later external change is preserved; #21/#23 stay open.
The
[checkpoint register](member1-checkpoints.json) keeps Days 14/15/30 pending.
Issue state alone is not checkpoint completion. Real comments/responses and
independent sign-offs must be supplied by their actual authors.
PR approval cannot replace the missing human checkpoint. A review
added after merge cannot retroactively provide pre-merge approval. Preserve
dated evidence and distinguish artifact delivery, review and runtime acceptance.
