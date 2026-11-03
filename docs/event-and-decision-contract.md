# Event and enforcement decision contract (Member 3, Day 2)

**Status:** Proposed IF-03/04/07 contract, pending Members 1, 2 and 4 acceptance. No active blocking is authorized.

## Sensor record (IF-03)

Member 2's current `api_event` is a 192-byte C record with `timestamp_ns` (monotonic), 32-bit sequence-like `event_id`, process/flow metadata, method, direction, status, size, latency, flags and a 128-byte route marker. Validate exact layout and endianness against the compiled sensor on Linux before decoding. Require an outer major schema version, source instance/boot ID and record length in the handoff; the current C definition lacks them. Do not infer UTC from `timestamp_ns` or infer a complete request from a packet. `event_id` alone is not globally unique and wraps.

The collector forwards only allowlisted, privacy-safe fields. A route marker must come from an approved plaintext observation point, be a bounded UTF-8 template without query/fragment or concrete object/subject values, and pass explicit normalization rules. Otherwise omit it and set `route_unavailable`. Do not forward raw IPs, PID/UID, headers, cookies or bodies. Member 2 and Member 1 must approve route provenance and schema changes before this is an implemented contract.

## Normalized event (IF-04)

[`schemas/collector-event.v1.1.schema.json`](schemas/collector-event.v1.1.schema.json) is the current proposed event schema. `event_id` is a collector-generated random UUID, preserved on retries. `sensor_sequence` is diagnostic only. `correlation_id` is null until a reviewed, authenticated request-level marker exists; `correlation_quality` explicitly says `ambiguous` for a flow-only hint or `unsupported` without one. `observed_at` is collector UTC receive time, while `sensor_monotonic_ns` is source-local monotonic time. `route_template` may be absent. `data_classification` is `restricted` because combined telemetry can be linkable even in the synthetic lab. The earlier v1 proposal is retained as historical design material and must not be accepted for request-level attribution.

Batching needs a separate versioned envelope with `batch_id`, source/build version, creation time, event count and bounded total bytes; those limits remain a Member 4 handoff. Analytics acknowledges batch and event IDs. Retrying a batch keeps all IDs unchanged. Unknown major versions, extra fields, invalid sizes or invalid source identity are rejected and counted, never silently coerced. No event should be persisted locally before masking and retention are approved.

## Decision (IF-07)

[`schemas/enforcement-decision.v1.schema.json`](schemas/enforcement-decision.v1.schema.json) defines one decision for one exact method and normalized route template. Actions are `allow`, `alert`, `deny` and `rate_limit`. A decision includes a unique ID, correlation reference, policy version, issuer/key ID, UTC issue/expiry, reason code, target, and integrity signature. Active actions also require Member 1's approval reference and rollback reference. The schema checks structure, not cryptographic validity or whether an approval is genuine.

The Day 10 Rust parser checks structure for `allow`, `alert` and `deny` in dry-run form. `rate_limit` is reserved for Day 19. A structurally valid decision is still untrusted: signature verification, issuer authentication, replay state and real Member 1 approval are not implemented, so no parsed decision can change traffic.

Before any action, the adapter checks authenticated service identity, canonical signed bytes and key, accepted policy version, bounded clock skew, expiry, deduplication/replay window, target equality, current operating mode and emergency-disable state. Signature algorithm, canonicalization, approval registry, maximum TTL, skew limit and per-route failure matrix require joint design approval; until then the adapter cannot activate `deny` or `rate_limit`. A malformed, unknown, delayed or duplicate decision cannot broaden an earlier decision.

Operating modes are `observe_only` (default), `dry_run` (record proposed outcomes) and `active` (only after Member 1's separate approval and passing safety/rollback evidence). Analytics outage, audit failure, circuit breaker, timeout or emergency disable returns this adapter to its approved monitor-only/fail-open behavior. The mock API's own authentication and authorization continue to fail closed for invalid access. Re-enabling active mode requires a new explicit approved transition; recovery alone cannot re-enable it.

## Contract acceptance cases

- Positive: valid event and acknowledged retry preserve IDs; valid `alert` produces no traffic change.
- Negative event: wrong length/version, enum, route provenance, UTF-8, oversized marker and sequence wrap do not crash or leak raw data.
- Negative decision: unknown action/version, bad signature, expired/future timestamp, replay, wrong route/method, missing approval and emergency disable produce no block.
- Recovery: analytics restart, full queue, dropped sensor record and adapter restart expose counters and return to observe-only.

Record producer/consumer sign-off and executable test evidence before labeling IF-03, IF-04 or IF-07 accepted.
