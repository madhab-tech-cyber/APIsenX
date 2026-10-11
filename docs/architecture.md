# Architecture

## Purpose

API-Sentinel observes API activity in an authorised lab, creates an endpoint inventory, detects endpoints missing from the approved OpenAPI contract, evaluates BOLA/BFLA policy, applies controlled enforcement, masks sensitive data, and presents findings on a protected dashboard.

## Components

1. **Mock API** - authenticated e-commerce test application with users, roles, orders, ownership, sharing, documented routes, deprecated routes, and intentionally undocumented routes.
2. **eBPF observation layer** - captures only approved Linux process, connection, timing, route marker, and health metadata required by the project.
3. **Rust collector and enforcement adapter** - validates kernel events, correlates and batches records, forwards them securely, applies approved decisions, and exposes performance and health metrics.
4. **Python analytics service** - validates ingestion, normalises routes, compares them with OpenAPI, evaluates ownership and role policy, masks telemetry, and creates audit events.
5. **React dashboard** - displays endpoint inventory, alerts, masked evidence, policy decisions, OWASP mapping, triage state, and component health.

## Trust boundaries

- Client to mock API: authenticate and authorise every request.
- Kernel to user space: validate event type, size, bounds, map limits, and sequence.
- Collector to analytics: use authenticated and encrypted transport.
- Analytics to storage: minimise data, encrypt sensitive records, and restrict access.
- Dashboard to management API: enforce server-side roles for every view and action.

## Important design constraint

HTTPS payloads are encrypted. eBPF does not automatically expose normal encrypted application content. The team must use an authorised observation point such as application instrumentation, a controlled reverse proxy, or metadata-only analysis. The design must never silently weaken TLS.

## Initial interfaces to approve

- Kernel event schema.
- Normalised API event schema.
- Allow, alert, and deny decision schema.
- Audit-event schema.
- Health and performance metric schema.
- OpenAPI contract versioning rule.

