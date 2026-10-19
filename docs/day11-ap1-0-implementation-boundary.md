# Day 11 — AP-1.0 Boundary, Observation Hook, and Local Startup

**Project:** API-Sentinel / APIsenX mock API  
**Branch:** `member5/day11-ap1-boundary`  
**Owner:** Member 5  
**Status:** Implementation handoff; independent review and AP-1.0 extensions pending

## Security baseline preserved

This change is additive to the D11-F01 repair on `member5/mock-api` (reviewed source baseline `1ab289aeab0ea072e731c18615cbea8c29f6d5d5`; merged PR #20 at `67677d4e5440c6a2e40ab40eb88bf2877e165ddc`). Keep the independent `orders:read:any` gate before admin inventory iteration, `orders:manage:any` before PATCH object authorization/mutation, inventory-shape tests, denied-write immutability checks, protected-field checks, fixture reset, OpenAPI parity, Ruff and pip-audit gates unchanged.

The repaired D11-F01 finding is **not** proof that all AP-1.0 authorization rows are implemented. No claim is made here that the tenant/sharing/support/version acceptance matrix passes.

## Current implementation versus AP-1.0

The current fixture has no tenant attribute, share-grant store, support assignment, tenant-admin role, or policy-version negotiation. The current principal is resolved server-side from a synthetic lab bearer token and the user fixture; order ownership is resolved from the order fixture. The current role permissions come from the server-side role table.

Until Member 1 approves the data model and Member 5 implements the matching tests, the required outcomes are:

| Capability | Current status | Required behavior until implemented |
|---|---|---|
| Tenant boundary enforcement | Unsupported: no authoritative tenant on principal/resource | Deny tenant-dependent actions; never trust client-supplied tenant/owner/role |
| Sharing and revocation | Unsupported: no authoritative grant store/lifecycle | Cross-owner access remains denied; no client-provided grant may create access |
| Scoped support/admin | Support and tenant-admin scopes absent; current admin is lab-global | Unknown role or missing scope/permission is denied; no implicit tenant bypass |
| Policy-version rejection | No request/decision policy-version field yet | Version-dependent decisions must not be accepted by downstream consumers; integration remains blocked until exact version semantics are agreed and tested |

These are documented limits and denial requirements, not passing acceptance cases. Do not add arbitrary headers or client fields as substitutes for authoritative policy context.

## Observation hook for M2/M4 review

`mock-api/main.py` now exposes a FastAPI middleware observation hook. It emits an allowlisted event with:

- a server-generated correlation ID;
- HTTP method;
- matched route template (for example, `/orders/{orderId}`, not the concrete object ID);
- response status; and
- elapsed milliseconds.

The correlation ID is returned as `X-Correlation-ID`. Routine audit messages no longer include raw subject or resource identifiers; they retain action/outcome and booleans indicating whether internal references were present. The hook does not read request bodies, authorization headers, cookies, or query values and does not alter transport/TLS configuration. The API must still be reached over HTTPS wherever TLS is required by the environment; the local HTTP URL is only for loopback lab use.

**Review boundary:** this is a candidate application-side observation hook for M1/M2/M4 to approve, not an accepted sensor interface or proof of end-to-end telemetry. Tenant ID, sharing grant, support assignment, explicit effective permissions and policy version are not all authoritative fields in the current model and therefore are not fabricated or emitted. M1/M2/M4 must agree the versioned schema and permitted identity/resource correlation before cross-component integration. Observation failure must never bypass API authentication or authorization.

## Clean local startup (PowerShell)

Run from the repository root, not from `mock-api/`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install ruff==0.17.1 pip-audit==2.10.1
python -m uvicorn main:app --app-dir mock-api --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive Swagger API page, or `http://127.0.0.1:8000/openapi.json` for the generated schema. The root path `/` is not defined; a 404 there is expected and does not mean the server failed to start.

Synthetic tokens are public, lab-only fixtures: `lab-user-a-token`, `lab-user-b-token`, and `lab-admin-token`. Never use them as real credentials or outside the authorised local lab. No non-local deployment is approved until real authentication, secret management, transport, identity lifecycle and the remaining authorization controls have been reviewed and implemented.

## Reproducible validation commands

Run from the repository root:

```powershell
python -m unittest discover -s tests -v
python -m ruff check mock-api tests
python -m pip_audit -r requirements.txt
git diff --check
git status --short --branch
```

CI remains responsible for the API/security/OpenAPI suite, Ruff and dependency audit. A repository edit is not a test result: report the exact CI run and commit SHA after GitHub Actions completes.

## Independent review requested

- **Member 1:** review the D11-F01 evidence at the pinned source revision and confirm the AP-1.0 denial boundary, audit fields and policy-context requirements. Do not close D11-F01 solely from merged status.
- **Member 6:** independently inspect the new privacy regression and CI run, confirm no existing D11-F01/OpenAPI regressions were removed, and record positive/negative results against the exact tested SHA.
- **Members 1/2/4:** approve or revise the observation schema before integration. Keep TLS, exclude credentials/bodies/query values, and do not infer absent tenant/grant/version context.

D11-F01 closure and AP-1.0 completion remain separate decisions.