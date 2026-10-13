# Authentication Decisions

**Decision owner:** Member 1 - Team Lead and Security Architect

**Foundation review date:** 2026-10-13

**Status:** Approved requirements; current mock-API implementation is approved
only for the authorised local lab

## 1. Decision summary

Authentication proves who a caller or service is. Authorization remains a
separate server-side decision based on the authenticated subject, active state,
role, tenant, object ownership, sharing grant, requested action and policy
version.

The current static bearer-token map is an intentionally weak test fixture. Those
values are public lab fixtures, not secrets, and must never protect a shared,
Internet-accessible or production-like deployment. The service must not be
exposed beyond the authorised local lab while that mechanism is active.

Before any integrated or non-local deployment, replace the fixture mechanism
with a reviewed standards-based identity provider and validated access tokens.
Do not build custom cryptography or treat a decoded but unverified token as an
authenticated identity.

## 2. Human/API client authentication

The integrated API authentication design must:

- accept bearer access tokens only over TLS;
- validate the signature with an explicit algorithm allowlist and trusted,
  rotatable verification keys;
- validate issuer, audience, expiry and not-before claims;
- require a stable subject identifier and reject missing or ambiguous identity;
- enforce a bounded clock-skew policy;
- reject altered, expired, wrong-issuer, wrong-audience and unsupported-algorithm
  tokens;
- provide a replay-control design for sensitive or state-changing operations,
  using short lifetimes and token/session identifiers where applicable; and
- derive permissions from an authoritative server-side mapping or reviewed
  policy, not from user-controlled request fields.

The OpenAPI contract must describe the mechanism actually implemented. It must
not advertise JWT validation while the application accepts only opaque static
fixtures.

## 3. Service and dashboard authentication

- Collector-to-analytics and other service links require authenticated,
  encrypted transport using workload identity, mutual TLS or an equivalently
  reviewed mechanism. Shared static credentials in source are prohibited.
- Dashboard sessions require a server-established identity, short lifetime,
  secure rotation/revocation and cookies marked `Secure`, `HttpOnly` and an
  appropriate `SameSite` value.
- State-changing browser requests require CSRF protection in addition to
  authentication.
- Service and dashboard identities receive least-privilege permissions and must
  be distinguishable in audit records.

These are approved requirements, not claims about the current placeholder
collector, analytics or dashboard components.

## 4. Failure and response behavior

| Condition | Required result |
|---|---|
| Missing, malformed, invalid, inactive, expired or unverifiable identity | HTTP 401 or equivalent unauthenticated result; no protected data |
| Authenticated subject lacks role, ownership, tenant or action permission | HTTP 403 with a generic client message and a privacy-safe audit event |
| Resource existence would reveal another subject's data | Use the route's reviewed 403/404 non-disclosure decision consistently |
| Identity provider or key source is unavailable | Fail closed for login, authorization and administrative actions; do not accept unverified tokens |
| Observation/detection service is unavailable | Follow the separately approved route failure matrix; it must not override API authorization |

Authentication failures must not reveal whether a token, subject, tenant or
resource is otherwise valid. Rate-limit repeated failures without logging raw
credentials.

## 5. Credential and session handling

- Never log, persist, export or commit raw access tokens, passwords, private keys,
  session cookies, authorization headers or signing material.
- Redact credential-bearing headers before telemetry leaves the request boundary.
- Keep secrets in an approved secret store or injected runtime binding, not in
  source, images, command history or populated `.env` files.
- Rotate credentials and verification keys through a documented process; define
  emergency revocation before integrated deployment.
- Audit the subject identifier, action, protected resource reference, policy
  version and outcome only after applying the data-classification policy.
- Treat the checked-in `lab-*-token` values as non-secret synthetic fixtures.
  Their presence is safe only because they have no validity outside the isolated
  mock API.

## 6. Authorization handoff

After authentication, the API must pass a structured principal to authorization.
The minimum context is:

- stable subject identifier;
- active/inactive state;
- role and explicit permissions;
- tenant and sharing context when introduced;
- authentication method and assurance level;
- token/session identifier for audit correlation, never the raw token; and
- policy version used for the decision.

Missing required context results in denial. See
[`authorization-policy.md`](authorization-policy.md) for route and object
decisions.

## 7. Required verification

Current local evidence covers missing, malformed, empty, invalid and inactive
credentials plus allowed and denied role/ownership cases.

Before integrated authentication is approved, tests must also cover:

- valid token and valid session;
- altered signature and unsupported algorithm;
- expired and not-yet-valid token;
- wrong issuer and wrong audience;
- replay or revoked session behavior;
- verification-key rotation and identity-provider outage;
- disabled subject and removed role;
- CSRF protection for dashboard state changes; and
- assurance that logs, errors, telemetry and persistence contain no raw
  credentials.

## 8. Approval boundary

The local fixture mechanism is **conditionally approved** for deterministic tests
inside the authorised lab. It is **not approved** for production, shared lab,
external exposure or release claims. Member 1 and the affected component owner
must review the replacement design and evidence before that boundary changes.
