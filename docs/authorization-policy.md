# Authorization Policy

**Decision owner:** Member 1 - Team Lead and Security Architect

**Last reviewed:** 2026-10-13

**Related decision:** [`authentication-decisions.md`](authentication-decisions.md)

## 1. Principles

- The API is the source of truth for identity and authorization.
- Authentication establishes a principal; it never grants access by itself.
- API-Sentinel must not treat a different object ID as proof of an attack by itself.
- Decisions consider authenticated principal, role, tenant, resource owner, explicit sharing grant, route, method, and policy version.
- Behavioural signals may support an alert but must not cause automatic blocking until validated.
- Missing or ambiguous identity, role, ownership, tenant or policy context results
  in denial.
- Client-supplied subject, role, owner or tenant fields are not trusted as policy
  inputs.
- Every sensitive decision produces a privacy-safe audit outcome without storing
  the raw credential.

## 2. Foundation roles and permissions

- Customer A: may read and update Customer A's allowed resources.
- Customer B: may read and update Customer B's allowed resources.
- Support role: may access only specifically approved support functions and masked fields.
- Administrator: may access only documented administrative functions.

The current mock API implements customer read-own and administrator read/manage
permissions. Customer updates, sharing grants, support permissions and tenant
separation are policy requirements or future cases unless explicitly implemented
and tested.

## 3. Current route decisions

| Route/action | Customer | Administrator | Missing/invalid identity |
|---|---|---|---|
| `GET /orders` | Return only owned orders | Return all orders | 401 |
| `GET /orders/{orderId}` | Allow owner; deny cross-owner | Allow | 401 |
| `PATCH /orders/{orderId}` | Deny | Allow status-only update | 401 |
| `GET /admin/orders` | Deny | Allow | 401 |

Invalid or extra update fields are rejected before mutation. Cross-owner and
function-level denials use a generic client response and a privacy-safe audit
outcome.

The 403-versus-404 response for a cross-owner object must be made consistent in
the reviewed OpenAPI contract and implementation before non-local integration.

## 4. Decision context

The authorization function must receive:

- a previously authenticated stable subject;
- active/inactive state;
- server-resolved role and explicit permissions;
- requested method, normalised route and action;
- resource owner, tenant and sharing context where applicable; and
- a versioned policy identifier.

It returns an allow/deny decision, stable reason code and audit context. It must
not return raw credentials or sensitive resource content as decision evidence.

## 5. Required tests

- Owner reads own order: allow.
- User reads another user's private order: deny and alert.
- Explicitly shared object: allow and record the sharing rule.
- Ordinary user calls admin route: deny and alert.
- Expired, altered, replayed, or wrong-audience token: reject.
- Missing identity or ownership context: follow the route's documented safe failure policy.

Also test inactive identities, unknown roles, malformed credentials, invalid
actions, missing resources, extra fields, tenant mismatch and policy-version
mismatch when those capabilities exist.

## 6. Review status

The local owner/admin policy and its current negative tests are conditionally
approved for the synthetic lab. Sharing, support, tenant, signed-token and
route-specific non-disclosure behavior remain unimplemented or incomplete and
must not be claimed as verified.

