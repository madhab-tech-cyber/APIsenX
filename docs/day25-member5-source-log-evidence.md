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

The Day 25 regression is implemented in `tests/test_day25_source_log_alignment.py`. PR #116 added the test and evidence, and was merged to `main` at `99bc4a3a1600ef47427a5acccf65937af0d3ae17` on 2026-11-01.

The exact PR-head workflows passed:
- [API Security and Quality Gates — run 41282832329](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41282832329): PASS.
- [Analytics Security and Quality Gates — run 41282832465](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41282832465): PASS.

The exact merge-commit workflows also passed:
- [API Security and Quality Gates — run 41282903128](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41282903128): PASS.
- [Analytics Security and Quality Gates — run 41282903172](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/41282903172): PASS.

**Member 5 engineering disposition:** source-log correlation implementation, four synthetic scenarios, privacy assertions, documentation and required CI verification are complete and merged.

**Independent acceptance remains pending:** PR #116 has no submitted review. A reviewer must still confirm the scope and privacy boundary before Day 25 is described as independently accepted. This documentation closeout does not manufacture reviewer approval.

**Safety boundary:** synthetic lab only. No production credentials or real personal data. This work does not prove durable/cross-process audit, tamper evidence, production log retention, or live sensor-to-API correlation. AP-1.0 remains `monitor_only`, active enforcement rules remain zero, and release remains **NOT APPROVED**.
