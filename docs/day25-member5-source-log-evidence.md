# Member 5 — Day 25 source-log correlation evidence

**Scope:** Synthetic local Mock API only.  
**Implementation branch:** `member5/day25-26-log-validation-sast-20261101`.  
**Acceptance boundary:** Application response remains the authorization source of truth; logs are corroborating evidence only.

## Scenarios

| Scenario | Request | Expected API result | Required source-log evidence |
|---|---|---:|---|
| Owner read | User A reads own order | 200 | Same response correlation ID, GET route template, status 200 |
| BOLA attempt | User A reads User B's order | 404 | Same response correlation ID, parameterized route template, status 404 |
| BFLA attempt | Customer calls admin inventory | 403 | Same response correlation ID, admin route template, status 403 |
| Missing credential | Unauthenticated order read | 401 | Same response correlation ID, order-list route template, status 401 |

## Privacy assertions

The regression test requires exactly one application observation line per request and matches its correlation ID to the response's `X-Correlation-ID`. It checks that the line contains method, matched route template, response status and bounded elapsed time. It rejects raw order IDs, subject identifiers, bearer fixture tokens and synthetic query markers from the observation line.

The test captures the application logger `apisenx.audit`; it does not treat HTTP client diagnostics, reverse-proxy logs, Uvicorn access logs, or analytics telemetry as the source application record. Shared lab execution must continue to start Uvicorn with `--no-access-log` and must not enable request-body/debug tracing.

## Limitations

- The test validates source application log correlation for the controlled synthetic requests only.
- It does not prove cross-process durable audit, tamper evidence, a live sensor-to-API correlation contract, or production log retention.
- A matching log line does not make a denied request an exploit; the API response and unchanged state remain authoritative.
- No real customer data, external target or production credential is used.

## Verification

The exact-head Mock API workflow is the required execution evidence. Do not mark Day 25 accepted until the test passes on the PR head and the reviewer confirms the scope and privacy boundary.
