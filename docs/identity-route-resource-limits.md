# Day 19 Identity, Route and Resource-Cost Limits

**Owner:** Member 1. **Implementers:** M3/M4/M5; verification M6.

**Date:** 2026-10-17 (Asia/Calcutta). **Profile:** `LIMIT-LAB-1.0`.

## 1. Scope and accounting keys

This is an initial isolated-lab design profile requiring measured tuning and
review before activation. The Day 19 Member 5 working branch adds a bounded
process-local token-bucket prototype for aggregate service traffic and
server-authenticated subject/route traffic. It does not implement every LM-01–LM-20
requirement, distributed coordination, cost weighting, pagination, response-size
caps, or production protection. It is not active on main unless merged and
validated. ENF-1.0, rule-specific authorization and Day 21 failure decisions
still apply. Never expose static lab fixtures outside the approved local environment.

Resolve identities server-side after authentication. Key authenticated buckets
by `(environment, service, server tenant scope, opaque subject, canonical
method/template, profile version)`. The current lab has a single server-defined
tenant scope; it is not supplied by the request. Tenant-aware deployment remains
blocked until AP-1.0 tenant enforcement exists. Never key by bearer value,
raw object ID, query string, unknown raw path or client role/tenant assertion.

Before authentication, use a bounded source token only as a supplementary abuse
signal; never treat IP as identity or trust forwarding headers outside an
approved proxy. Aggregate unknown routes into one bounded bucket, not one
bucket per attacker-controlled path or fingerprint.

## 2. Request and cost budgets

Token buckets refill continuously against monotonic time. Rate is tokens/second,
burst is total bucket capacity, initially full. Admission requires all applicable
buckets and concurrency gates to pass atomically. Rejection does not debit
partially admitted buckets. Request and cost budgets are separate.

| ID | Scope | Sustained / burst | Concurrent in-flight maximum |
|---|---|---|---|
| LM-01 | Entire lab service, all requests | 100 requests/s; burst 200 | 10 |
| LM-02 | Each authenticated subject, all requests | 80 requests/s; burst 160 | 5 |
| LM-03 | Each subject, status updates | 20 requests/s; burst 40 | 2 |
| LM-04 | `GET /orders/{orderId}`, service aggregate | 80 requests/s; burst 160 | Shared service/subject gates |
| LM-05 | `GET /orders`, service aggregate | 60 requests/s; burst 120 | Shared service/subject gates |
| LM-06 | `GET /admin/orders`, service aggregate | 60 requests/s; burst 120 | Shared service/subject gates |
| LM-07 | `PATCH /orders/{orderId}`, service aggregate | 20 requests/s; burst 40 | Shared service/subject gates |
| LM-08 | Unauthenticated source supplementary bucket | 10 requests/s; burst 20 | Shared service gate |
| LM-09 | All unauthenticated requests, aggregate | 20 requests/s; burst 40 | 2 |
| LM-10 | Unknown routes, service aggregate | 10 requests/s; burst 20 | 2 |
| LM-11 | Service weighted cost budget | 400 cost units/s; burst 800 | Shared service gate |
| LM-12 | Each authenticated subject cost budget | 300 cost units/s; burst 600 | Shared subject gate |

Cost weights: object read = 1, customer order list = 5, admin order list = 5,
status update = 10, other/unknown operation = 10. These are policy weights,
not CPU measurements; authorization is still evaluated separately. Lists must
be paginated to <= 100 objects and responses <= 256 KiB before this bounded
cost model can be accepted. Current unpaginated endpoints need implementation.
Increasing cardinality or payload size requires a new cost profile and rerun.

For the MRVP-1.0 40/30/20/10 request mix at 100 offered RPS, the service cost
is `40*1 + 30*5 + 20*5 + 10*10 = 390` units/s, under 400. Customer load is
70 RPS/190 cost units and admin load 30 RPS/200 units, within subject budgets.
The benchmark generator must cap per-subject in-flight requests at 5 as well
as global concurrency 10; actual benchmark compatibility is unmeasured.

On rate/cost/concurrency exhaustion, return generic 429 with integer
`Retry-After` >= 1 second, computed from the slowest exhausted refill gate
(or 1 for a concurrency gate). Do not create findings solely from a 429. Bucket
cardinality exhaustion uses a generic 503 and bounded health signal; do not
evict a live bucket to grant a fresh burst. Limit failure mode under dependency
outage must be finalized per route at Day 21 before activation.

## 3. Bounded state and pipeline resources

| ID | Resource | Required maximum / failure behavior |
|---|---|---|
| LM-13 | Limiter keys | 4,096 active keys and 8 MiB total limiter state, whichever first; idle eviction only after 60 seconds; expired entries lose no active debt |
| LM-14 | API input | Target <= 4,096 bytes, path <= 2,048 raw bytes/32 segments, decoded segment <= 128 bytes; JSON body <= 16 KiB; enforce before parsing |
| LM-15 | Collector event and batch | <= 4 KiB/event, <= 64 events and <= 256 KiB/batch; reject incompatible/oversized input |
| LM-16 | Collector queue | <= 10,000 events and <= 16 MiB allocated queue state, whichever first; event age <= 2 seconds, bounded loss counters on drop |
| LM-17 | Analytics ingestion | <= 4 in-flight batches, <= 32 MiB ingestion buffer allocation; reject/backpressure at limit, no unbounded retry |
| LM-18 | Collector retry | <= 3 attempts, each timeout <= 500 ms, backoffs 100 then 200 ms with <= 50 ms jitter; total event age <= 2 seconds always overrides retries |
| LM-19 | Observation hot path | Never wait for analytics/storage; no application-thread body capture; bounded enqueue or counted drop |
| LM-20 | Adapter rules/decisions | ENF-1.0: <= 32 active rules, <= 4 KiB/decision, decision TTL <= 5 seconds; reject overflow/version mismatch |

Count allocation and metadata overhead toward byte limits, not payload bytes
alone. A 4 KiB event therefore cannot yield 10,000 queued events within 16 MiB;
the lower byte ceiling takes precedence. Collection loss disables active
decisions under ENF-1.0 while the API's own controls remain intact. No raw
rejected payload is persisted for debugging. The 2-second queue limit concerns
telemetry; the 5-second TTL concerns active decisions and is not an extension
of telemetry retention.

## 4. Acceptance tests and owner evidence

M3/M5 demonstrate boundary N-1/N/N+1, refill, bursts, concurrent workers and
atomic multi-bucket debit. Test subject isolation, forwarded-IP spoofing,
unknown-path floods, key-cap exhaustion, idle eviction, restart and clock jump.
Restart must not provide repeated fresh bursts without the approved mitigation.
Use bounded durable counters or a reviewed cold-start restrictive mode; record
that choice before activation.

M3/M4 demonstrate event/byte/age caps, metadata overhead, batch overflow,
duplicate replay, retry deadline, downstream outage and recovery. Record peak
RSS separately from queue allocation: these caps do not prove a process RSS
ceiling. M6 runs the legitimate MRVP mix without unintended 429/503, then a
separate overload workload that proves bounds and recovery. Report fairness,
tail latency, achieved throughput, drops and counters without high-cardinality
identity/path metric labels. M1 reviews a versioned profile before any tuning
or BR-04 activation. R-010 remains High/Open until evidence passes.


## Day 19 implementation candidate — Member 5

The working branch `day19/member5-bounded-rate-limits` introduces:
- A process-wide token bucket (100 requests/s, burst 200) applied before route dispatch.
- Authenticated subject/canonical-route buckets (80 requests/s, burst 160), with PATCH limited to 20 requests/s, burst 40.
- Monotonic-time refill, positive `Retry-After`, a 4,096-key ceiling, 60-second idle eviction, and fail-closed 503 when all buckets remain live.
- Generic rate-limit errors and OpenAPI response documentation for 429/503.

This is partial implementation evidence only. Per-route service budgets, unauthenticated supplementary buckets, weighted-cost budgets, concurrency gates, pagination/response-byte caps, load tests, multi-worker/distributed behavior, and route-specific outage policy remain incomplete. No performance or capacity claim is accepted until CI and measured load/recovery evidence are reviewed. Keep monitor-only and zero active enforcement.
