# Threat Model

## Assets

- Authentication tokens and test identities.
- API endpoint inventory and OpenAPI contract.
- Object ownership and role policy.
- Detection and enforcement rules.
- Masked telemetry and audit records.
- Dashboard sessions and administrative actions.
- Build artifacts, dependencies, workflow credentials, and release evidence.

## Trust boundaries

See `architecture.md`. Review each boundary whenever an interface changes.

## Initial threats and controls

| Threat | Initial control |
|---|---|
| Captured credentials or PII | Capture minimisation, masking before storage, leak tests, retention limits |
| Spoofed identity or policy decision | Authenticated services, signed/versioned policy, replay protection |
| BOLA/BFLA false negative | Explicit ownership and role matrix, negative tests, labelled attack fixtures |
| False-positive blocking outage | Detection-only mode, deterministic criteria, review, timeout, rollback |
| Parser or event memory issue | Bounded events, schema validation, fuzzing, stress and concurrency tests |
| Shadow endpoint missed | Route normalisation tests and comparison with versioned OpenAPI |
| Audit tampering | Restricted writes, correlation IDs, protected export, retention policy |
| Dependency compromise | Locked versions, provenance review, SBOM, dependency and secret scans |
| Dashboard privilege escalation | Server-side authorization, short sessions, role tests, safe errors |
| Denial of service | Bounded queues, rate limits, timeouts, circuit breaker, health monitoring |

## Review process

For each threat, record likelihood, impact, owner, mitigation, test evidence, residual risk, and status in `risk-register.md`.

