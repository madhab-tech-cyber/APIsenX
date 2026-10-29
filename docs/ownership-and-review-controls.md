# Verified Ownership and Review-Control Handoff

**Owner:** Member 1. **Identity observed:** 2026-10-18 (Asia/Calcutta).
**Control/CI status refreshed:** 2026-10-27 (Asia/Calcutta).
Current evidence/limits: [Member 1 closeout](member1-closeout-2026-10-27.md).

## Identity evidence

| Role | Verified GitHub identity | Evidence | Repository permission |
|---|---|---|---|
| M1 | `madhab-tech-cyber` | Author of PR #18 and Member 1 branch delivery; user-specified Git identity | admin |
| M2 | `renu-stack` | Linked author/committer of `07f141022f31979c9464c2f853b982e03b4373a4` on assigned branch | write |
| M3 | `aadi3006` | Linked author/committer of `9eb26e4cd4d0cc33b92c4103a13cc90724206c31` on assigned branch | write |
| M4 implementation takeover | `madhab-tech-cyber` | User explicitly requested M1 take over unavailable M4; merged PRs #42/#49/#53 | Existing M1 account; original unavailable M4 identity remains unverified and is not needed to attribute the takeover |
| M5 | `pappukumar96727-sketch` (Git display name Pappu kumar) | PR #19 author and workflow head commit `8f155631a5d8c878190db741143d06c28a26ef22` | write |
| M6 | `jayitape` (Git display name Jay Itape) | Linked author/committer of `39902b358ef68911795546bf22ae5faf46fbe078` | write |

Permission endpoints were read for each named identity. Attribution is evidence
of the published Git role, not a claim of personal identity verification or
acceptance of a new handoff. Full names for alias-only identities remain pending.
M1 is the `/analytics/` implementer under the authorized takeover. M3/M5/M6 are
listed affected owners for independent review; M1 cannot self-approve M4 work.

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

October 20 update: PR #28 has an independent M1 approval for `974e512`.
PRs #26/#31/#32 have no submitted reviews; the earlier approval does not extend
to the latest API or collector revisions. M5's #21/#23 handoffs are real partial
responses and are now linked in the checkpoint register. Earlier zero-response
snapshots above remain historical. Main is still unprotected; the exact
approved payload and safe owner utility are in
[the protection instructions](main-protection-owner-action.md).

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
| `API Security and Quality Gates` | PR #60 head d51e666 run 40072189001 SUCCESS: API/contract, Ruff and audit; GitHub Actions app ID 15368; main PR trigger exists | Verify corrective-head result, actual main protection/readback and independent reviews |
| `Analytics Security and Quality Gates` | PR #60 head d51e666 run 40072188985 SUCCESS: regressions/demos, frozen source candidate, lint, Bandit, scoped secrets and dependency audit | Independent detector/label/privacy acceptance, trusted live context, durable audit and shared runtime evidence |
| `Repository security checks` | M6 run 39431559242 SUCCESS: sensitive filenames and repository structure | This job is not dashboard tests or a dedicated secret scan |
| `Dashboard quality and security checks` | Same M6 run, head ec03bdf: npm ci, lint, 4 Vitest tests, TypeScript/production build and npm audit SUCCESS | Fixture UI remains unmerged; verify loading/error/malformed/sensitive-data cases and actual authenticated M4 browser contract before acceptance |
| `Rust/Python Loopback Contract` | PR #60 head d51e666 run 40072188960 SUCCESS: locked Rust tests/fmt/clippy and real Linux userspace ack/retry/negative/privacy handoff | M2/M3 live sensor envelope, provenance/correlation and shared identity/TLS acceptance; not sensor/enforcement proof |

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
with zero comments. The owner has now also closed #21/#23; those state changes
are preserved. M5 responses are credited, but actual meetings, M6 responses and
checkpoint sign-offs are not fabricated. [Issue #33](https://github.com/madhab-tech-cyber/APIsenX/issues/33)
tracks remaining owner actions. The
[checkpoint register](member1-checkpoints.json) keeps Days 14/15/30 pending.
October 27: #33/#56/#57/#58/#61 are owner-closed without completing the human
gates. Follow-up remains documented in
[#61](https://github.com/madhab-tech-cyber/APIsenX/issues/61) and the correction PR;
open #82/#83 track newer API-load human acceptance and durable-audit decisions.
Main still reports unprotected/rulesets empty; Administration GET returns 403
and the approved apply command stops at its first CLI read without a PUT.
PR #34 has no submitted review. Unsupported checkboxes in #56/#57 were corrected
without rewriting original comments or repeatedly reopening owner-closed issues.
Issue state alone is not checkpoint completion. Real comments/responses and
independent sign-offs must be supplied by their actual authors.
PR approval cannot replace the missing human checkpoint. A review
added after merge cannot retroactively provide pre-merge approval. Preserve
dated evidence and distinguish artifact delivery, review and runtime acceptance.
