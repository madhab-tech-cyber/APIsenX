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
