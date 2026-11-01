# Member 5 — Day 23 and Day 24 hardening evidence

**Date:** 2026-11-01. **Role:** Mock API and OpenAPI Engineer.
**Base:** main commit `a6f9937c6d12a04545ae85ce3f1a96393d945b6b`.

## Day 23 — synthetic sensitive-field test data

Added `tests/fixtures/day23_sensitive_fields.json` with four explicitly
non-operational markers:
- an email under the reserved `.invalid` domain;
- a telephone number in the fictional 555-01xx range;
- an all-zero, invalid card-number placeholder; and
- an API-key-shaped field whose value explicitly says it is not a credential.

The new regression tests submit each field as an unapproved extra property on
the order PATCH schema. They require a generic 400 response, unchanged order
state, and no echo of the supplied marker. A middleware test also confirms that
the rejected request's monitor-only Sentinel event contains only the route
template/status metadata and none of the four values.

No real personal data, payment card, API credential, or populated secret is
included in the fixture.

## Day 24 — OWASP API Security mapping and examples

Added `docs/owasp-api-security-mapping.json`, a machine-readable mapping of
all ten OWASP API Security Top 10 (2023) categories to the mock API routes,
relevant test files, and a concrete synthetic scenario/expected outcome.
`tests/test_day24_owasp_mapping.py` checks category completeness, route
references against `docs/openapi.yaml`, evidence-file existence, and
conservative coverage labels.

API6 is explicitly `not_assessed` because the current lab has no checkout,
payment, promotion, or transfer business-flow endpoint. API4, API7, API8,
API9 and API10 remain `partial`: the SSRF change hardens a fixed environment-
configured observer destination, while API10 transport tests cover internal
monitor-only telemetry rather than third-party API consumption. Contract/runtime
route parity is not a complete inventory of deployed hidden or rogue routes.
The mapping is a traceability aid, not a full OWASP assessment or certification.

## Additional Day 24 security correction — observer SSRF boundary

Review of `mock-api/sentinel_adapter.py` found that a string-prefix check for
`http://127.0.0.1:` / `http://localhost:` did not parse the URL authority.
That could accept a crafted user-info/authority string whose actual destination
was not loopback.

The adapter now parses the URL, accepts only literal IPv4 loopback addresses
in `127.0.0.0/8`, rejects DNS names and user-info, rejects non-root URL
components and invalid ports, and constructs a canonical `/v1/events` URL.
The change removes DNS resolution from this configurable outbound destination.
It does not add any new telemetry fields or change the monitor-only failure
behavior.

## Validation and release boundary

The new deterministic tests are intended for the existing Mock API Security
workflow. No local test run is claimed in this execution environment; report
only exact-head GitHub Actions results after the PR workflows finish.

This work does not implement signed-decision enforcement, a production
circuit breaker, durable audit storage, retention/deletion, or human acceptance.
Keep AP-1.0 `monitor_only`, active enforcement rules at zero, and release
**NOT APPROVED**.
