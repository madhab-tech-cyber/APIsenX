# Member 5 — Day 28 reproducible API security lab evidence

**Owner:** Member 5 — Mock API and OpenAPI Engineer  
**Scope:** Synthetic, loopback-only Mock API; no production identity, data, or target.  
**Engineering disposition:** Documentation and automated regression evidence are present.  
**Human lab execution:** Pending; no operator session, attendance, or manual response capture is claimed.

## Delivered artifacts

- [Day 28 lab runbook](day28-member5-lab-runbook.md): Python 3.13 setup, loopback-only launch, synthetic credentials, API/OpenAPI inspection, attack commands, expected outcomes, and process restart reset.
- [Mock API README](../mock-api/README.md): quick start, link to the runbook, process-local state boundary, and validation commands.
- [OpenAPI contract](openapi.yaml): operation set, operation IDs, auth, policy-version and nonce requirements, request constraints, generic error schemas, and 429/503 response references.
- [OpenAPI contract tests](../tests/test_openapi_contract.py): runtime/contract operation-set and operation-ID parity, authentication and required headers, schema constraints, response/error-code parity, tenant documentation, and process-local behavior.
- [Authorization attack regressions](../tests/test_day27_authorization_attack_matrix.py): owner allow, cross-owner BOLA generic 404, customer-to-admin BFLA 403, denied PATCH with no mutation, wrong-resource-type grant denial, and valid same-tenant read-share allow.

## Expected lab outcomes

| Scenario | Expected result | Security property |
|---|---:|---|
| Owner reads own order | 200 | Authorized owner access |
| Customer reads another owner's order | 404 | No cross-owner existence disclosure |
| Customer calls admin inventory | 403 | Function-level authorization |
| Missing bearer credential | 401 | Authentication required |
| Missing AP-1.0 policy header | 400 | Explicit policy version required |
| Assigned support list | 200 | Only the documented masked fields |
| Customer PATCH | 403 | Denied mutation leaves state unchanged |
| Authorized lab-admin PATCH | 200 | Explicit lab permission; run last because state is process-local |

Every authenticated request uses `X-Policy-Version: AP-1.0`. PATCH requests use unique `X-Request-Nonce` values. The lab must remain bound to `127.0.0.1`; synthetic tokens are not production credentials.

## Exact-head automated validation evidence

The latest complete PR-head validation available for the Day 28 implementation is PR #124 head `d43a7474caac30817851e96bfb88be59ce45e371` (2026-11-04). The Day 28 runbook, authorization regressions and OpenAPI tests were already part of the base revision used by this PR.

- [Mock API Security Tests — run 41773396282](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41773396282): PASS; 452 tests passed in 10.129s, including API/OpenAPI regression coverage; Ruff, Bandit, dependency audit, loopback and bounded load stages passed.
- [Analytics Security Tests — run 41773396244](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41773396244): PASS; 452 tests passed in 12.969s, plus detection/candidate checks, Ruff, Bandit, secret scan and dependency audit.
- [Member 3 Loopback Integration — run 41773396257](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41773396257): PASS; Rust library checks and Rust/Python loopback handoff passed.

These are exact PR-head checks, not a claim that post-merge workflows were observed on the later merge commit. The repeated 452-test counts are separate workflow executions, not 904 unique tests.

## Manual operator evidence still required

A human operator must execute the commands in sections 2–5 of the runbook against the local synthetic service and retain the actual date/time, tested commit SHA, command/response status, sanitized output, and reset confirmation. In particular:

1. Confirm the service listens only on loopback and inspect the generated `/openapi.json`.
2. Execute each owner, BOLA, BFLA, missing-auth, missing-policy, support-view and PATCH case; record the actual HTTP status and sanitized response.
3. Confirm denied PATCH does not mutate the order; execute the permitted admin PATCH last.
4. Stop and restart the service, then confirm the original fixture state is restored.
5. Attach the operator's evidence and request independent review; do not fabricate attendance or sign-off.

## Explicit limitations and release boundary

- Demo identities, order mutations, token revocation and nonce replay state are process-local. Restart resets this Mock API only; it is not durable audit deletion or a database/backup restore test.
- The synthetic fixture does not establish a grant-issuance service, trusted production issuer, distributed revocation/replay state, multi-tenant production authorization, or production identity.
- This Member 5 API lab evidence does not satisfy Member 4's separate Day 28 DET-1.2 rule/schema independent review.
- AP-1.0 remains `monitor_only`, active enforcement rules remain zero, and the overall project release remains **NOT APPROVED** until the remaining owner, independent-review, durable-audit, integration and human acceptance gates are satisfied.
