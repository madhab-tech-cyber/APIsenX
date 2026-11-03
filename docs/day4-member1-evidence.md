# Day 4 Authentication and Data-Classification Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Date started:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 4 task: review authentication and data-classification
decisions, approve safe foundation requirements and distinguish current local-lab
evidence from controls that remain unimplemented.

## Reviewed inputs

- `mock-api/main.py` authentication and audit behavior;
- `src/authorization.py` and the synthetic user/order fixtures;
- `tests/test_authorization.py` and `tests/test_mock_api.py`;
- `docs/openapi.yaml`, `docs/authorization-policy.md` and the Day 3 findings;
- architecture, threat model, risk register, scope and security policy; and
- repository contents for credentials, personal data, runtime logs and captures.

## Authentication decisions

[`authentication-decisions.md`](authentication-decisions.md) now establishes:

- strict separation of authentication from server-side authorization;
- conditional approval of static opaque tokens only as public local-lab fixtures;
- signed-token validation requirements for issuer, audience, expiry, not-before,
  algorithm, subject and replay controls before non-local integration;
- workload identity or mutual TLS requirements for service links;
- secure dashboard session and CSRF requirements;
- 401/403/404 failure rules and fail-closed identity behavior; and
- credential redaction, rotation, revocation and audit-context requirements.

[`authorization-policy.md`](authorization-policy.md) now records the current
route matrix, required decision context, missing-context denial and the boundary
between verified local policy and future sharing/tenant/support behavior.

## Data-classification decisions

[`data-classification-policy.md`](data-classification-policy.md) defines:

- Public, Internal, Restricted, Secret and Prohibited levels;
- field-level decisions for tokens, fixtures, identifiers, telemetry, captures,
  audit events, vulnerability details, build output and contracts;
- collection allowlists, ingress redaction and pseudonymisation requirements;
- access, transport, storage, retention and repository rules; and
- stop/notify/rotate/remove steps when Secret or Prohibited data is detected.

The baseline intentionally leaves component-specific retention and the final
masking field list for the scheduled Day 20 and Day 23 approvals.

## Review findings

| ID | Finding | Decision / owner |
|---|---|---|
| D4-F01 | Static `lab-*-token` values have no signature, issuer, audience, expiry or replay protection | Treat them as public test fixtures and keep the service isolated; M5 implements the approved replacement before non-local use |
| D4-F02 | OpenAPI advertises JWT while code accepts opaque static fixtures | Remains an R-011 contract blocker; M5 must align contract and implementation |
| D4-F03 | Missing, malformed, invalid and inactive identities are rejected, and owner/admin denials are tested | Conditionally approved as local foundation evidence only |
| D4-F04 | Audit logs contain actor and order identifiers | Safe only because current fixtures are synthetic; M4/M6 must apply Restricted handling, masking and retention before persistence/display |
| D4-F05 | Service-to-service and dashboard authentication do not exist | Requirements approved; M3/M4/M6 provide implementations and tests before integration claims |
| D4-F06 | No runtime secret store, rotation/revocation procedure or identity-provider outage evidence exists | M5/M6 must implement and demonstrate these controls before non-local deployment |
| D4-F07 | Repository-wide discovery still executes zero tests and dedicated security scanners are absent | R-012 remains High; explicit tests are required until CI is corrected |

## Verification evidence

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`:
  **PASS — 26 tests**.
- `python -m compileall -q src mock-api tests`: **PASS**.
- Missing, malformed, empty, invalid and inactive credential cases are present.
- Owner/admin allow cases and BOLA/BFLA denial cases are present.
- Expiry, issuer, audience, signature, replay, key rotation, revocation, CSRF and
  service-identity tests are **UNRUN/ABSENT** because those controls are not
  implemented.
- Dedicated secret, static, dependency and container scans remain
  **UNRUN — tooling and project configuration are absent**.

## Result

Authentication and data-classification requirements are approved as a foundation
baseline. The current mock authentication remains **conditionally approved only
for the isolated authorised lab**. It is not approved for production, shared
deployment or release, and high residual risks R-001, R-007, R-011 and R-012
remain open or mitigating.
