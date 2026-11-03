# Member 3 Day 7 local collector baseline

**Measured:** 2026-10-17 on Apple M4, macOS arm64, Rust 1.99.1, release build.

**Command:** `cargo run --release --manifest-path collector/Cargo.toml --example baseline`

The repeatable example warms up for 10,000 records, then measures 100,000 synthetic 192-byte records per trial. One thread decodes each record, creates a privacy-minimized event, and serializes it to JSON. The route marker is an approved synthetic template. p50/p95/p99/max are per-event monotonic timings. Throughput uses wall time for the measured loop. Three trials were run sequentially on the same Mac.

| Trial | p50 (us) | p95 (us) | p99 (us) | Max (us) | Events/s |
|---|---:|---:|---:|---:|---:|
| 1 | 1.958 | 2.500 | 2.750 | 68.667 | 484,913 |
| 2 | 1.958 | 2.000 | 2.291 | 42.334 | 500,385 |
| 3 | 1.958 | 2.000 | 2.417 | 59.708 | 495,510 |

**Interpretation:** This is a local microbenchmark of the decode/normalize/serialize stage. It excludes Linux ring-buffer polling, batching, queue contention, TLS, network, Python acknowledgement, eBPF overhead, concurrency and failure recovery. The schedule's under-5-ms review target cannot be claimed from these numbers. Re-run on the approved Linux lab host after Member 2 and Member 4 interfaces are available, using the full method in `latency-test-plan.md`.
