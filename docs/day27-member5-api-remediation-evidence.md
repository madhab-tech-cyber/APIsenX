# Member 5 — Day 27 API remediation and authorization attack rerun

**Task:** Patch API findings and rerun authorization attacks.  
**Baseline:** `main` at `12d6df98805e923fc52c8cb169fb3a9e487a2321`.  
**Scope:** Synthetic Mock API and its server-side authorization module only.

## Finding and correction

Code review found that `src/authorization.py` required a non-empty
`resource_type` on a sharing grant but did not require the value to be
`order`. The same `resource_id` string could therefore be interpreted as an
order reference even when a fixture described a different resource namespace.
The order authorization evaluator now rejects every non-`order` grant before
evaluating its remaining grant conditions.

The Day 26 workflow ran Bandit against `mock-api/`, while the API imports its
authorization implementation from `src/authorization.py`. The SAST gate now
scans both directories, and Ruff also checks the authorization source.

## Deterministic regression coverage

- Direct policy test: a non-order grant cannot authorize an order read.
- HTTP-level owner read remains allowed.
- HTTP-level cross-owner BOLA read remains a generic 404.
- Customer access to the admin inventory route remains a generic 403.
- Customer PATCH remains denied and leaves the order unchanged.
- A valid same-tenant order read grant remains usable; a wrong resource type
  does not.
- Day 28 contract tests now pin runtime/contract error-code parity and
  rate-limit/capacity responses.

## Validation status

The prior main-branch workflow run
[41284957296](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41284957296)
passed the then-configured Mock API, Bandit, Ruff and dependency-audit steps on
`12d6df98805e923fc52c8cb169fb3a9e487a2321`; that run did not scan `src/`.
The expanded checks and new regressions must pass on this branch's exact PR
head before this work is accepted. No local execution is claimed in this
environment.

## Remaining boundaries

The sharing-grant source remains a checked-in synthetic fixture. This change
does not create a grant-issuance service, prove issuer identity, add durable
grant/revocation state, or make the demo token mechanism production-ready.
Keep AP-1.0 in `monitor_only`, active enforcement rules at zero, and release
**NOT APPROVED**. Human and independent review remain separate gates.


## First exact-head CI attempt — 2026-11-02

PR #119 head `900bc2429170ad9c25de76f283afb9055747c587` produced these results:

- [Mock API Security Tests — run 41385158282](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41385158282): the full discovery step executed 426 tests. All six new Day 27 HTTP attack-matrix tests, the wrong-resource-type grant regression, and the new OpenAPI response/error-code parity tests passed. The overall step failed with 2 failures and 5 errors in the existing Member 4 candidate-acceptance/package checks because the frozen source and candidate digests no longer match the changed `src/authorization.py` and `docs/openapi.yaml`.
- [Analytics Security Tests — run 41385158349](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41385158349): the same frozen-candidate mismatch caused the analytics acceptance/package tests to fail.
- [Member 3 Loopback Integration — run 41385158237](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41385158237): PASS.
- Ruff, Bandit and pip-audit were skipped because the previous workflow placed them after the failing full-suite step. The workflow now runs these independent checks first; their results are still required on the new exact head.

**Cross-owner blocker:** `analytics/decisions.py` includes `src/authorization.py` in `rules_digest()`; the Member 4 source freeze also includes `src/authorization.py` and `docs/openapi.yaml`. The current `analytics/release-candidate.json` and `docs/member4-review-checkpoints.json` still pin candidate `aec622af035f825f6e1fb4a94f93469a9e98f9e3`. Member 4 must refresh the generated source manifest and candidate checkpoint to the reviewed PR head, updating the rules digest, contract version and file hashes while keeping every human gate pending, `monitor_only`, zero active rules and release unapproved. Member 5 has not modified Member 4's checkpoint or manufactured acceptance.

Do not merge or mark Days 27–28 accepted until the owner-controlled candidate refresh is complete and all required exact-head workflows pass.
