# Collector interfaces (Member 3, Day 1)

**Status:** Draft for Members 1, 2, 4 and 6; design only. No collector or enforcement implementation is claimed.

The collector owns the boundary between Member 2's Linux sensor and Member 4's analytics service. It starts in **observe-only** mode. The mock API remains the source of truth for authentication and authorization, regardless of telemetry health.

## IF-03: sensor to collector

Member 2 currently proposes an 8 MiB `api_sentinel_events` BPF ring buffer, a 192-byte `struct api_event`, and a per-CPU `STAT_RINGBUF_DROPS` counter in `api_sentinel_stats` on `member2/ebpf-capture`. These are proposals, not an accepted or running sensor. The collector must validate the actual record length before decoding, then check the method and direction enums, status range, route-marker termination and encoding, flags, and timestamp. It must never read beyond the supplied record. Unknown versions, malformed records and incomplete route markers are dropped or reduced to safe metadata with bounded counters; processing continues for later valid records.

The proposed C struct has no schema version, boot identity or stable event UUID. Its 32-bit `event_id` can wrap. IF-03 therefore needs a jointly approved versioned envelope and source identity before an implementation can claim durable deduplication. Kernel monotonic time is not UTC; the collector must record a separate receive time and clock-conversion uncertainty. Flow IPs, process IDs and UIDs are Restricted and are excluded from default forwarding, logs and metric labels.

The route marker is untrusted. A raw path can contain an object ID or secret, and TLS packet capture alone cannot reliably yield HTTP routes. Only an approved application/proxy marker that is already a route template may be forwarded. Otherwise the collector records a privacy-safe `route_unavailable` outcome. No TLS interception or raw payload capture is implied.

The current in-memory correlation table reuses a random ID for one sensor `flow_hash` within a short bounded window. This is flow-level correlation only: keep-alive requests can share a flow, and hash collisions are possible. A stable request-level ID needs an approved observation-point marker from Member 2/5 before BOLA/BFLA evidence can rely on it.

## IF-04: collector to analytics

The proposed normalized event is defined in [`schemas/collector-event.v1.schema.json`](schemas/collector-event.v1.schema.json). The collector validates against this schema, assigns a random event and correlation ID, attaches its source instance and receive timestamp, and sends bounded batches. The transport requires authenticated encryption and a named service identity; endpoint, certificate provisioning, batch limits, retry horizon and replay window require agreement with Member 4. Retries must preserve event IDs so ingestion can deduplicate. Queues and retry buffers have fixed capacity; overflow increments drop counters and never grows memory without bound. Restricted telemetry is not written to ordinary local logs.

## IF-07: analytics to enforcement adapter

The proposed decision contract is defined in [`schemas/enforcement-decision.v1.schema.json`](schemas/enforcement-decision.v1.schema.json) and explained in [`event-and-decision-contract.md`](event-and-decision-contract.md). Receipt of a decision never authorizes active blocking by itself. The adapter rejects unknown versions/actions, invalid signatures or service identity, expired/replayed decisions, ambiguous targets and missing Member 1 approval. Until approval and rollback tests exist, every `deny` or `rate_limit` decision is evaluated as a dry run and cannot alter traffic.

## IF-08: health and performance

Expose aggregate event counts, validation failures, queue depth, ring-buffer drops, analytics availability, retry outcomes, current operating mode, decision rejection reasons, rollback state and latency histograms. Use bounded, non-identifying labels only. Member 6's current dashboard branch uses static health fixtures; live metric names and the management boundary remain to be agreed. A green health view cannot imply that audit persistence succeeded unless Member 4 confirms it.

## Failure behavior and handoffs

| Failure | Required collector behavior |
|---|---|
| Malformed/oversized sensor event | Reject safely; count by bounded reason; continue |
| Ring-buffer or queue loss | Report loss and degraded visibility; preserve API authorization |
| Analytics timeout/disconnect | Bounded retry and backoff; observe-only/fail-open for this adapter |
| Invalid or stale decision | Reject; do not guess an action |
| Adapter unhealthy or emergency disable | Stop active enforcement and report rollback state |

Member 2 must confirm wire layout, versioning, flags, route provenance and drop semantics. Member 4 must accept event/decision schemas, transport, deduplication and retry semantics. Member 1 must approve classification, mode transition and active-action criteria. Member 6 must agree metric names and dashboard exposure. Contract, negative and recovery tests are needed before any interface is described as operational.
