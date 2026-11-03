# Day 23 Data Classification and Masking Field Rules

**Owner:** Member 1. **Date:** 2026-10-19. **Version:** `MASK-LAB-1.0`.

Design baseline approved for implementation. Runtime masking, leak tests and
independent affected-owner review remain pending. Apply the stricter decision
where this field policy and [classification policy](data-classification-policy.md)
overlap. Existing raw collection prohibitions remain in force.

| ID | Input field | Classification | Allowed derived output / handling |
|---|---|---|---|
| MK-01 | Authorization, cookies, passwords, keys, session/share tokens | Secret; real/unauthorized data Prohibited | Exclude at first boundary; never hash and retain a credential as telemetry |
| MK-02 | Raw target, query names/values, fragment, request/response body | Restricted synthetic only; otherwise Prohibited | Exclude from logs, metrics, persistence and dashboard; do not retain for debugging |
| MK-03 | Known method/path | Internal, Restricted when linked | Uppercase method and approved canonical template only; no concrete path values |
| MK-04 | Unknown path | Restricted | Fixed unknown-route marker and domain-separated keyed token/key version per normalization policy; no raw path display |
| MK-05 | Subject, resource, tenant and grant IDs | Restricted when correlated | Server-generated opaque reference or domain/tenant-scoped keyed pseudonym; never plain unsalted hash |
| MK-06 | IP/port, PID/UID, process/cgroup and flow tuple | Restricted | Exclude by default; separately reviewed collection purpose and short retention before any exception |
| MK-07 | Outcome, action, reason, finding class/severity/state | Internal or Restricted with finding | Versioned allowlisted enums and non-sensitive text; no caller-supplied arbitrary diagnostic |
| MK-08 | Correlation/event/finding ID and key version | Restricted | Bounded server-generated opaque values; never token/body/path-derived raw identifiers or metric labels |
| MK-09 | Time, latency, aggregate counters, health status | Internal or Restricted when linked | Bounded precision/purpose; capped cardinality, no identity/route-token labels; unmeasured value is unavailable, not healthy/zero |
| MK-10 | Evidence/export/error message | Restricted | Allowlisted masked projection, generic error and protected reference; encode display text; no raw object serialization fallback |

## Pipeline and pseudonym rules

Validate bounded schema and source before processing. Remove excluded fields
before formatting an exception, constructing a log or forwarding an event.
Construct an allowlisted output object; unknown input fields reject/quarantine
with a bounded reason without copying the raw input. Apply the same projection
on retry, dead-letter, audit/export and cache paths. No raw disk spool.

For required correlation, use a runtime-managed HMAC-SHA-256 key with at least
128 output bits. Domain-separate purpose and tenant; record only a non-secret
key version. Rotate/revoke via approved secret management; never use fixture
keys outside unit tests. Rotation may break correlation deliberately. Keys are
not evidence attachments. Pseudonyms remain Restricted; they are not anonymous
or authorization claims. Deny missing required tenant context rather than
falling back to a cross-tenant correlation namespace.

[AUDIT-LAB-1.0](audit-retention-and-investigation.md) applies to all derived
copies. A browser, screenshot, tracing SDK, exported CSV, analytics exception
and CI artifact are output boundaries too. HTML encoding prevents execution
but does not remove sensitive data. Redaction regular expressions alone do
not replace field exclusion and explicit output schemas.

## Required acceptance evidence

M2/M3/M4/M6 supply schema/field inventory and tests with unique synthetic leak
markers placed in every excluded field. Inspect success, rejection, malformed
input, exception, timeout, retry, audit failure, export and display output.
Test nested/unrecognized keys, UTF-8/percent/CRLF variants and oversized values.
No forbidden marker may appear in any forbidden output, including stderr and
tracebacks. Prove safe allowed projections remain usable and deterministic;
verify key-version rotation and tenant/domain separation.

Current mock logs and a fixture dashboard do not establish these controls.
Persistence/dashboard acceptance remains BLOCKED until negative leak and RBAC
tests plus affected-owner review are linked. R-001/R-008/R-009 remain unresolved.
