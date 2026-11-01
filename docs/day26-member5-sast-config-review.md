# Member 5 — Day 26 Mock API SAST, authentication and configuration review

**Scope:** Static review and automated checks for the synthetic Mock API.  
**Implementation branch:** `member5/day25-26-log-validation-sast-20261101`.

## SAST and dependency checks

- Run Bandit recursively against `mock-api/` with the repository's pinned Python toolchain.
- Run Ruff against `mock-api/` and `tests/`.
- Run `pip-audit -r requirements.txt`.
- Run the complete unittest suite, including authentication lifecycle, role/function authorization, object ownership, replay, request validation, and OpenAPI contract regressions.

## Configuration review

| Area | Current configuration | Review disposition |
|---|---|---|
| Credentials | Demo bearer fixtures are defined in source | LAB ONLY; never production identity |
| Token lifecycle | 15-minute default TTL, expiry/revocation checks | Process-local fixture state; not distributed session management |
| PATCH replay | Five-minute nonce cache | Process-local; restart/multi-worker replay acceptance remains open |
| Policy selection | Explicit `X-Policy-Version: AP-1.0` required | Fail closed for missing/unknown version |
| Request limits | Bounded path, body, response, concurrency and rate controls | Local process limits; no distributed quota claim |
| Observation | Allowlisted route template/method/status/correlation ID | Keep access logs and body/debug tracing disabled in shared lab |
| Sentinel adapter | Optional, literal IPv4 loopback, bounded timeout, no redirects | Monitor-only telemetry; never an authorization source |
| Runtime storage | Order mutations and analytics audit are process-local/volatile | No durability, backup, or production persistence claim |
| Transport/deployment | Local lab defaults | No non-local deployment approval |

## Security boundary

Static fixtures are intentionally retained for reproducible lab attacks. They are not a production authentication mechanism. The current code does not establish signed issuer/audience-bound tokens, distributed revocation, multi-worker nonce persistence, durable audit storage, production TLS termination, or an approved production deployment configuration.

## Verification

The PR's exact-head CI must show successful Bandit, Ruff, full authentication/API tests and dependency audit. Any Bandit finding must be triaged and fixed or explicitly justified with a narrow suppression and reviewer evidence; do not suppress broad classes to force a green check.
