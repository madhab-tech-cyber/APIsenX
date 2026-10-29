# Collector latency test plan (Member 3, Day 1)

**Status:** Test design only; no latency or throughput result has been measured.

## Measurements

- **Collector processing latency:** monotonic time from receiving a complete sensor record to enqueueing a validated normalized event. Invalid records are measured separately.
- **Forwarding latency:** monotonic time from collector receipt to authenticated analytics acknowledgement for the same event ID. Report queue time, transport time and retry time separately.
- **Enforcement lookup latency:** time spent validating and applying an already approved local decision. Measure dry-run and active paths separately only when active mode is approved.
- **Loss and recovery:** sensor drops, collector validation drops, queue overflow, retry exhaustion, duplicate acknowledgements, disconnect duration and time to healthy forwarding after restart.

Report p50, p95, p99 and maximum in microseconds, plus sample count and histogram configuration. Never combine collector-only timing with network/end-to-end timing in one claim. The schedule's “below 5 ms” statement is a review target, not an achieved result; agree its exact percentile and measurement boundary with Member 1 before using it as a gate.

## Reproducible setup

Record commit IDs for all components, host CPU/kernel, build profile, queue and batch settings, payload sizes, event rate, concurrency, network placement, clock source and test duration. Use an authorized local mock API with synthetic identities only. Run a no-collector baseline, an observe-only path and a mocked analytics path before a live integration path. Keep the same traffic mix and hardware for comparisons. Warm up, then run at least three measured trials and retain per-trial results rather than only averages.

For collector-only timings, use a monotonic clock in one process. For cross-host latency, use event ID matching plus clock-sync error bounds; do not subtract unsynchronized wall clocks. Report CPU and memory use, throughput (events/s), errors and loss alongside latency. Record 1, 10 and 100 concurrent synthetic clients or explain a host-limited alternative.

## Cases

1. Normal events at idle, steady and saturation rates.
2. Boundary-sized valid events, malformed length, unknown enums, missing string terminator, invalid route marker and unknown schema version.
3. Duplicates, delayed records, sequence wrap, out-of-order delivery and ring-buffer loss.
4. Analytics slow, unavailable and restarted; queue full and retry exhausted.
5. Emergency disable and rollback timing after an approved active-mode test.

Each run records input count, accepted count, rejected count, forwarded and acknowledged count, and drop counters. A run with unexplained loss is invalid for a performance claim. Publish a method and raw aggregate results without credentials, raw paths, IPs or user identifiers. The Day 7 baseline report must explicitly label mocked components and untested kernel/network boundaries.
