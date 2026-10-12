# Authorization Policy

## Principles

- The API is the source of truth for identity and authorization.
- API-Sentinel must not treat a different object ID as proof of an attack by itself.
- Decisions consider authenticated principal, role, tenant, resource owner, explicit sharing grant, route, method, and policy version.
- Behavioural signals may support an alert but must not cause automatic blocking until validated.

## Initial test roles

- Customer A: may read and update Customer A's allowed resources.
- Customer B: may read and update Customer B's allowed resources.
- Support role: may access only specifically approved support functions and masked fields.
- Administrator: may access only documented administrative functions.

## Required tests

- Owner reads own order: allow.
- User reads another user's private order: deny and alert.
- Explicitly shared object: allow and record the sharing rule.
- Ordinary user calls admin route: deny and alert.
- Expired, altered, replayed, or wrong-audience token: reject.
- Missing identity or ownership context: follow the route's documented safe failure policy.

