# Day 11 — AP-1.0 Boundary, Observation Hook, and Local Startup

**Project:** API-Sentinel / APIsenX mock API  
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

## Observation hook and logging boundary

`mock-api/main.py` exposes a FastAPI middleware observation hook. It emits an allowlisted event with a server-generated correlation ID, HTTP method, matched route template (for example, `/orders/{orderId}`), response status and elapsed milliseconds. The correlation ID is returned as `X-Correlation-ID`. Routine audit messages avoid raw subject/resource identifiers.

The middleware does not inspect request bodies, authorization headers, cookies, or query values. **That alone does not guarantee privacy across every logging layer.** Uvicorn's default access logger may record the request target, which can include a query string. For local runs, use `--no-access-log` so the application allowlist is the only request-level log emitted by this server. Any reverse proxy, gateway, hosting platform or other access logger used outside the local lab must independently be configured and tested to omit credentials, bodies, and query values. Do not disable TLS to solve a logging issue.

This is a candidate application-side observation hook for M1/M2/M4 to approve, not an accepted sensor interface or proof of end-to-end telemetry. Tenant ID, sharing grant, support assignment, explicit effective permissions and policy version are not all authoritative fields in the current model and therefore are not fabricated or emitted. M1/M2/M4 must agree the versioned schema and permitted identity/resource correlation before cross-component integration. Observation failure must never bypass authentication or authorization.

## Clean local startup (PowerShell)

Run from the repository root, not from `mock-api/`. Use the Python executable available on your machine; the Windows `py` launcher is optional.

```powershell
python --version
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m pip install ruff==0.17.1 pip-audit==2.10.1
.\\.venv\\Scripts\\python.exe -m uvicorn main:app --app-dir mock-api --host 127.0.0.1 --port 8000 --no-access-log
```

If the `python` command is not found, install Python 3.13 and ensure it is on PATH, then open a new PowerShell terminal. If venv activation is preferred and permitted, run `.\\.venv\\Scripts\\Activate.ps1` and then use `python -m ...`. The explicit `.venv\\Scripts\\python.exe` commands above avoid dependence on shell activation policy.

Open `http://127.0.0.1:8000/docs` for the interactive Swagger API page, or `http://127.0.0.1:8000/openapi.json` for the generated schema. The root path `/` is not defined; a 404 there is expected and does not mean the server failed to start. Keep the server terminal running; press Ctrl+C to stop it.

Synthetic tokens are public, lab-only fixtures: `lab-user-a-token`, `lab-user-b-token`, and `lab-admin-token`. Never use them as real credentials or outside the authorised local lab. No non-local deployment is approved until real authentication, secret management, transport, identity lifecycle and the remaining authorization controls have been reviewed and implemented.

## Reproducible validation commands

Run from the repository root in a second terminal:

```powershell
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v
.\\.venv\\Scripts\\python.exe -m ruff check mock-api tests
.\\.venv\\Scripts\\python.exe -m pip_audit -r requirements.txt
git diff --check
git status --short --branch
```

CI remains responsible for the API/security/OpenAPI suite, Ruff and dependency audit. Report results against the exact tested SHA; do not infer passing results from a successful server startup.

## Independent review and follow-up

- **Member 1:** independently review the D11-F01 evidence at the pinned source revision and confirm the AP-1.0 denial boundary, audit fields and policy-context requirements. Do not close D11-F01 solely from merged status.
- **Member 6:** independently inspect the privacy regression and CI evidence, confirm no existing D11-F01/OpenAPI regressions were removed, and record positive/negative results against the exact tested SHA.
- **Members 1/2/4:** approve or revise the observation schema before integration. Keep TLS, exclude credentials/bodies/query values, and do not infer absent tenant/grant/version context.
- **AP-1.0 extensions:** tenant boundaries, sharing/revocation, scoped support/admin and policy-version rejection remain unimplemented until the authoritative model and test cases are agreed with Member 1. Their acceptance cases are not claimed as passed.

D11-F01 closure and AP-1.0 completion remain separate decisions.
