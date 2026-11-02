# Member 5 — Day 28 reproducible lab, OpenAPI and attack runbook

**Purpose:** Provide a repeatable, safe local setup and explain the expected
application-side outcomes for normal, BOLA and BFLA requests.

## 1. Safety and prerequisites

- Use only this repository's synthetic users and order fixtures.
- Bind the service to `127.0.0.1`; do not expose it to a LAN or the Internet.
- Do not configure a production identity provider, external target, or real
  Sentinel destination. The optional observer is monitor-only and is not an
  authorization control.
- Use Python 3.13 and the pinned dependencies in `requirements.txt`.
- The demo bearer tokens are synthetic, process-local fixtures. Their default
  lifetime is 15 minutes.

## 2. Install and start the lab

From the repository root, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --app-dir mock-api --host 127.0.0.1 --port 8000 --no-access-log
```

Keep this terminal open. The access log is disabled so raw request paths and
query strings are not copied into Uvicorn access output. The application emits
its own allowlisted route-template observation line.

Open the runtime Swagger UI at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) or retrieve the
generated schema at [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).
The checked-in contract is [`openapi.yaml`](openapi.yaml). CI compares its
operations, operation IDs, request constraints, security and responses with
the FastAPI-generated schema.

## 3. Synthetic identities

| Identity | Bearer token | Intended use |
|---|---|---|
| Customer A | `lab-user-a-token` | Own order read; denied cross-owner/admin/mutation attempts |
| Customer B | `lab-user-b-token` | Second synthetic owner |
| Lab admin | `lab-admin-token` | Explicitly permitted lab-wide read/status update |
| Support | `lab-support-token` | Assigned, masked support list only |
| Tenant admin | `lab-tenant-admin-token` | Same-tenant read/status permissions in the single-tenant fixture |

Every authenticated request must include
`X-Policy-Version: AP-1.0`. A PATCH also requires a unique
`X-Request-Nonce` with 8–128 safe characters. Reuse inside five minutes is
rejected by process-local replay detection.

## 4. Authorization attack matrix

Run each command from a second PowerShell terminal while the API is running.
The expected result is the HTTP status; the response body should use the
documented generic error shape for denials.

### Owner read — expected 200

```powershell
curl.exe -i -H "Authorization: Bearer lab-user-a-token" -H "X-Policy-Version: AP-1.0" http://127.0.0.1:8000/orders/order-1001
```

### Cross-owner BOLA attempt — expected 404

Customer A requests Customer B's order. The response must not disclose whether
the other order exists.

```powershell
curl.exe -i -H "Authorization: Bearer lab-user-a-token" -H "X-Policy-Version: AP-1.0" http://127.0.0.1:8000/orders/order-1002
```

### BFLA attempt — expected 403

A customer cannot call the lab-admin inventory function.

```powershell
curl.exe -i -H "Authorization: Bearer lab-user-a-token" -H "X-Policy-Version: AP-1.0" http://127.0.0.1:8000/admin/orders
```

### Missing credential — expected 401

```powershell
curl.exe -i -H "X-Policy-Version: AP-1.0" http://127.0.0.1:8000/orders
```

### Missing policy version — expected 400

```powershell
curl.exe -i -H "Authorization: Bearer lab-user-a-token" http://127.0.0.1:8000/orders
```

### Assigned support view — expected 200 with only `id` and `status`

```powershell
curl.exe -i -H "Authorization: Bearer lab-support-token" -H "X-Policy-Version: AP-1.0" http://127.0.0.1:8000/support/orders
```

Inspect the JSON: support records must not include owner, total, currency,
tenant, or other full-order fields.

### Customer mutation attempt — expected 403 and no state change

```powershell
curl.exe -i -X PATCH http://127.0.0.1:8000/orders/order-1001 -H "Authorization: Bearer lab-user-a-token" -H "X-Policy-Version: AP-1.0" -H "X-Request-Nonce: day28-customer-0001" -H "Content-Type: application/json" -d "{\"status\":\"shipped\"}"
```

### Optional authorized admin mutation — expected 200

Run this last because it changes the in-memory order until the service restarts.

```powershell
curl.exe -i -X PATCH http://127.0.0.1:8000/orders/order-1001 -H "Authorization: Bearer lab-admin-token" -H "X-Policy-Version: AP-1.0" -H "X-Request-Nonce: day28-admin-0001" -H "Content-Type: application/json" -d "{\"status\":\"shipped\"}"
```

## 5. Clean reset

1. Return to the server terminal and press `Ctrl+C`.
2. Start the server again using the command in section 2.
3. Confirm `GET /orders/order-1001` returns the original fixture state.

Order mutations, token revocation and PATCH nonces exist only in process
memory. Restarting the process reloads `mock_data/orders.json` and clears
those runtime-only values. Do not edit or delete the checked-in JSON fixtures
to reset the lab. No database, durable audit store, backup or restore mechanism
is provided by this Mock API.

## 6. Validation commands

From the repository root:

```powershell
python -m unittest discover -s tests -v
python -m ruff check mock-api src tests
python -m bandit -r mock-api src -q
python -m pip_audit -r requirements.txt
git diff --check
```

The exact branch/PR head must also pass the repository's Mock API Security
Tests and required integration workflows. Record the tested SHA and actual CI
run URLs; do not infer a pass from a local command, an earlier commit, or a
documentation-only check.

## 7. Release boundary

This is a synthetic local demonstration guide, not a production deployment
runbook. The API's application-side authorization remains authoritative;
optional Sentinel telemetry cannot grant or deny access. Analytics audit
storage is still volatile, integrated failure/recovery and human acceptance
remain pending, AP-1.0 stays `monitor_only`, active rules remain zero, and the
overall release remains **NOT APPROVED**.
