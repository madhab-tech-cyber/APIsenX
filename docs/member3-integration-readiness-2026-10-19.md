# Member 3 integration readiness — 2026-10-19

**State:** Reviewable collector safety correction; Linux integration blocked. This is not a deployed sensor-to-collector pipeline, a live Member 4 ingestion test, or performance acceptance.

## Checked repository inputs

- Member 2 `member2/ebpf-capture` at `07f1410` has a proposed native-endian 192-byte `api_event` header and map definitions. It has no loadable sensor or jointly accepted version/source/request-marker envelope in the inspected branch.
- Member 4 `member4/detection` at `841cde1` has an analytics placeholder and no ingestion/acknowledgment service in the inspected branch.
- This work was tested on macOS arm64. No authorized Linux lab or sensor artifact was supplied for this run.

## Implemented in this follow-up

- Removed the flow-hash correlation table. An event now has a null `correlation_id`; a nonzero flow hint is explicitly `ambiguous`, and no flow hint is `unsupported`. This prevents HTTP keep-alive or concurrent requests on one flow from appearing to share a verified request ID.
- Added a proposed normalized event schema v1.1 while retaining the original v1 proposal for review history. Member 4 must explicitly accept the new schema before live forwarding.
- Added truthful bounded sensor-loss state. Loss is unavailable until a trusted sensor counter is sampled; counter decreases are counted as resets, and disconnection returns availability to false.
- Tightened local acknowledgment parsing against extra fields and added negative tests for wrong batch IDs and incomplete, duplicate or extra event IDs.
- Kept the library in observation/dry-run mode. No kernel program, host firewall or active rule is modified.

## Handoff decisions required before integration

| Owner | Exact acceptance needed | Evidence to attach |
|---|---|
| M1 + M2 + M5 | Approve the HTTPS-safe observation point and route/request marker provenance without exposing raw paths, subjects, headers or credentials. | Written boundary/allowlist, capture demonstration and privacy test. |
| M2 producer + M3 consumer | Agree a versioned wire envelope with record length, endianness, source/boot identity, monotonic clock semantics, enum/flag meanings, request-level marker semantics and drop-counter epoch. Provide a loadable ring-buffer producer. | Header/layout checks, verifier/load logs, known-good and malformed records, drop/overflow and restart run. |
| M3 producer + M4 consumer | Accept the normalized event v1.1 and batch/ack contract, mTLS service identities, trust roots, endpoint, freshness/replay window, idempotent duplicate behavior and failure status mapping. | A live receiver with valid/invalid client tests, schema rejection, stale/duplicate replay tests, stable retry IDs, timeout and restart recovery. |
| M1 + M3 + M4 | Agree that no decision is actionable from the current unverified request correlation. Keep enforcement disabled. | Written mode gate; later route-specific failure and timed rollback evidence before any active change. |

Do not reinterpret `flow_hash`, a locally generated UUID or a bearer token as the authoritative request marker. If the source cannot assign a unique marker to each request across ingress/egress, emit null and label correlation ambiguous or unsupported. BOLA/BFLA attribution must exclude these events until the detection owner defines safe handling.

## Reproducible checks performed

On Apple M4/macOS arm64 with the locked Rust dependency graph:

```sh
cargo test --locked --manifest-path collector/Cargo.toml
cargo fmt --check --manifest-path collector/Cargo.toml
cargo clippy --locked --all-targets --manifest-path collector/Cargo.toml -- -D warnings
git diff --check
```

Results on 2026-10-19: 22 unit tests passed; formatting, strict Clippy and diff whitespace checks passed. Unit tests cover malformed proposed records, bounded queues/batches, retry ID stability, simulated timeout/recovery, exact acknowledgments, ambiguous correlation and unavailable/reset sensor-loss state. They do not prove source authentication, live receiver deduplication/freshness, Linux verifier loading or end-to-end overhead.

## Linux validation required before approval

Use the authorized 4-vCPU/8-GiB Linux lab and the existing [`mid-review-validation-plan.md`](mid-review-validation-plan.md). Record the kernel/compiler/Rust versions, frozen revisions, observation point, test commands and raw result locations. Demonstrate sensor load and ring consumption, accepted and malformed versioned events, request marker behavior with keep-alive and concurrency, sensor and collector loss under load, queue/batch limits, Member 4 mTLS identity/schema/replay/dedup tests, outage/recovery, and no active rule changes.

Measure client-visible baseline versus monitored latency using the plan's paired workload method. Report per-stratum p50/p95/p99, p95 delta, errors, timeouts, throughput and resource/loss counters. The macOS Day 7 decode/normalize/serialize microbenchmark is separate evidence and cannot establish the under-5-ms integrated goal. No Linux performance result is claimed here.

**PR decision:** Draft/blocked until M2/M4 contracts, authorized lab run and owner reviews exist. A final integration approval must contain actual Linux outputs, not only this readiness record.
