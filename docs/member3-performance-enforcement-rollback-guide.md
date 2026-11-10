# Member 3 guide — performance, enforcement adapter and rollback

**Day 28 consolidation, recorded 2026-11-10.** This guide consolidates
existing Member 3 material into one place. It introduces **no new claims**:
every statement is sourced from the collector crate, the performance docs,
or the ENF-1.0 criteria, as cited per section. AP-1.0 is `monitor_only`,
zero active enforcement rules, and the release is **NOT APPROVED**; nothing
in this guide changes that state.

## 1. What the collector is

A tested Rust library (`collector/`) that decodes Member 2's proposed
192-byte sensor record, creates privacy-minimized events, batches them
through bounded queues, retries authenticated HTTPS/mTLS delivery, exposes
aggregate counters, and parses enforcement decisions for **dry-run
validation only**. It is not a deployed daemon: no Linux ring-buffer
consumer exists. It never applies a deny or rate-limit action to traffic.
(Source: `collector/README.md`.)

## 2. Performance

### Method (Day 1)

`docs/performance/latency-test-plan.md` defines four separate measurements
— collector processing latency, forwarding latency, enforcement lookup
latency, and loss/recovery — reported as p50/p95/p99/max with sample counts.
Collector-only timing is never combined with network or end-to-end timing
in one claim, cross-host figures require event-ID matching with clock-sync
error bounds, and each run records input/accepted/rejected/forwarded/
acknowledged counts plus drop counters; a run with unexplained loss is
invalid for a performance claim.

### Evidence (Day 7) and its limits

`docs/performance/day7-baseline.md` records a local microbenchmark of the
decode/normalize/serialize stage only (Apple M4, macOS arm64, Rust 1.99.1,
release build, 100,000 synthetic records per trial, three trials):
p50 ≈ 1.96 µs per event, ≈ 485–500k events/s.

**Honest limit, in the baseline's own terms:** the measurement excludes
ring-buffer polling, batching, queue contention, TLS, network, Python
acknowledgement, eBPF overhead, concurrency and failure recovery, and
**the schedule's under-5-ms review target cannot be claimed from these
numbers**. The <5 ms figure is a review target from the plan, not a result.
No end-to-end or Linux-lab latency report exists yet; producing one
requires the authorized Linux lab session (with Member 2's running sensor
and Member 4's live ingestion) following the Day 1 method.

## 3. Enforcement adapter — design and why it is dry-run only

`collector/src/decision.rs` parses and structurally validates proposed
decisions (allow / alert / deny / rate-limit). Structural rules enforced at
parse time include:

- deny and rate-limit decisions are rejected unless both an approval
  reference and a rollback reference are present — even in dry-run
  (test: `deny_needs_approval_and_rollback_references_even_in_dry_run`);
- a rate limit is only valid with the rate-limit action;
- unknown fields, wrong schema versions and out-of-window issue/expiry
  times are rejected.

The module's own header states its boundary: *"Nothing in this module
applies a decision to traffic or verifies its cryptographic origin."*
There is no application path and no rate-limit state anywhere in the
collector.

Activation of any enforcement is governed by Member 1's ENF-1.0 criteria
(`docs/enforcement-approval-and-rollback.md`): a candidate must satisfy
gates EG-01…EG-08 (scope, policy, transport, determinism, correctness,
quality, recovery, approval) before an active rule can be authorized, and
§5 records that the criteria approval *"authorizes neither a blocking rule
nor a network mutation."* No gate evidence for an active collector rule
exists and no authorization has been recorded, so dry-run parsing is the
complete and correct implementation under current governance. The
enforcement-week plan items are formally dispositioned in
`docs/member3-days16-22-enforcement-disposition.md`.

## 4. Rollback controls

Rollback exists today in exactly two forms:

1. **As a structural precondition:** a deny or rate-limit decision cannot
   even be parsed as valid without a `rollback_id` reference (§3).
2. **As criteria:** ENF-1.0 defines the rollout state machine
   (`draft -> monitor_only -> reviewed -> authorized_lab -> expired`,
   persisted state must not silently reactivate rules), the circuit-breaker
   and kill-switch requirements (EG-07), and a rollback runbook with pass
   criteria — including that the kill switch must work even when the audit
   service is unavailable, and that rollback tests must prove both
   application protection and removal of active decisions.

**Not implemented:** no kill switch, circuit breaker or rollback mechanism
exists in the collector code. Those are EG-07 *gates* to satisfy before any
future authorization, not missing features to build under `monitor_only`:
building an application path for decisions that cannot legally be applied
would invert the governance order. If an active-mode lab exercise is ever
authorized under ENF-1.0, the runbook tests in §4 of that document are the
acceptance bar for the mechanism.

## 5. Sources

- `collector/README.md`; `collector/src/decision.rs`, `wire.rs`,
  `metrics.rs`, `transport.rs`, `pipeline.rs`, `delivery.rs`
- `docs/performance/latency-test-plan.md`;
  `docs/performance/day7-baseline.md`
- `docs/enforcement-approval-and-rollback.md` (ENF-1.0, Member 1)
- `docs/member3-day3-to-day10-evidence.md`;
  `docs/member3-sensor-handoff-review-2026-10-29.md`
- `docs/member3-days16-22-enforcement-disposition.md`;
  `docs/member3-day29-release-build-record.md`
