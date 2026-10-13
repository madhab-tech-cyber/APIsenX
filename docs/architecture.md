# Architecture

## Purpose

API-Sentinel observes API activity in an authorised lab, creates an endpoint inventory, detects endpoints missing from the approved OpenAPI contract, evaluates BOLA/BFLA policy, applies controlled enforcement, masks sensitive data, and presents findings on a protected dashboard.

The detailed interface register, owner handoffs, failure behavior and integration
sequence are maintained in
[`integration-data-flow.md`](integration-data-flow.md).

## Implementation status

As of 2026-10-13, the local mock API authentication, authorization, synthetic
fixture and basic audit-log path is implemented and tested. The eBPF sensor,
collector, analytics service, storage, management API, dashboard and CI/security
pipeline remain planned or placeholder components. Architecture and interface
text for those components is not implementation evidence.

## Components

1. **Mock API (Authorised Lab Target)**
   - Role: Authenticated reference e-commerce application serving as the controlled observation target.
   - Core Responsibilities:
     - Implements multi-tenant identity, customer and administrative roles, and explicit object ownership.
     - Exposes documented routes (matching the approved OpenAPI specification), deprecated routes, and intentionally undocumented (shadow) routes for detection validation.
     - Provides synthetic traffic generators and test fixtures for normal transactions and controlled attack scenarios (BOLA, BFLA, rate abuse).
   - Security Posture: Source of truth for identity and permissions; never processes production data or third-party targets.

2. **eBPF Observation Sensor (Kernel Layer)**
   - Role: Low-overhead, in-kernel telemetry sensor running on Linux.
   - Core Responsibilities:
     - Attaches approved tracepoints, socket hooks, or uprobes to capture process identity (PID/TID/cgroup), socket tuples (IP/port/proto), timestamping, and HTTP/API boundary markers.
     - Emits structured events to user space through bounded ring/perf buffers.
     - Operates under strict Linux kernel verifier constraints, ensuring finite execution, memory safety, and non-blocking operation.
   - Security & Integrity Constraints:
     - Strict data minimisation: captures only approved connection and routing metadata; avoids raw payload, secret, or token capture.
     - Never tampers with or weakens TLS/HTTPS encryption.

3. **Rust Collector and Enforcement Adapter (Host Agent)**
   - Role: High-performance, memory-safe user space daemon bridging the kernel sensor and analytics service.
   - Core Responsibilities:
     - Consumes, deserialises, and validates kernel ring-buffer events against strict size and boundary constraints.
     - Implements bounded event queues, batching, and backpressure mechanisms to prevent memory exhaustion under high traffic loads.
     - Manages secure, authenticated transport of normalised telemetry to the analytics service.
     - Hosts the local enforcement adapter for executing approved policy decisions (allow, alert, rate-limit, drop) with sub-millisecond overhead.
     - Emits health, dropped-event, and performance metrics.
   - Safety Controls: Defaults to monitor-only and fail-open mode during foundation phases; includes circuit breaker and rollback capabilities.

4. **Python Analytics and Detection Engine**
   - Role: Central analysis, policy evaluation, route discovery, and audit service.
   - Core Responsibilities:
     - Validates incoming collector batches and normalises HTTP methods and parameterized routes (e.g., `/orders/{id}`).
     - Compares observed routes against the versioned OpenAPI contract to identify shadow, deprecated, or drift endpoints.
     - Evaluates transactions against explicit BOLA (object ownership) and BFLA (function/role) authorization policies.
     - Applies privacy-preserving data masking (redacting identifiers, tokens, and PII) prior to persistence.
     - Emits structured audit events and security alerts for dashboard consumption.

5. **React Security Dashboard (Presentation Layer)**
   - Role: Protected administrative and operational web interface.
   - Core Responsibilities:
     - Renders real-time and historical API inventory, highlighting approved vs shadow routes.
     - Displays security alerts (BOLA, BFLA, rate-limit exceedance) mapped to OWASP API Security categories.
     - Presents masked evidence logs, policy triage workflows, and component health/telemetry graphs.
   - Security Controls: Enforces server-side authentication and role-based access control (RBAC); strictly avoids rendering unmasked sensitive values.

6. **Storage Layer (Data and Audit Persistence)**
   - Role: Partitioned persistence tier for telemetry, policies, and audit trails.
   - Core Responsibilities:
     - Telemetry & Event Store: Stores masked API transaction summaries, route inventory snapshots, and alert records.
     - Policy & Contract Store: Houses versioned OpenAPI contracts, authorization matrices, and rate-limiting rules.
     - Immutable Audit Log: Maintains append-only records of security findings, policy evaluations, administrative triage, and enforcement actions.
   - Security Controls: Enforces least-privilege database access, encryption at rest, data retention limits, and automatic purge schedules.

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

Both producer and consumer must approve each interface and link compatible
schema, negative, failure-recovery and integration tests before it is described
as operational.

