# Rust collector and enforcement

Owner: Member 3. This crate implements the user-space collector in ordered daily milestones. It defaults to observation only; active blocking is not implemented or approved.

The current source of truth for proposed interfaces is `docs/collector-interface.md` and `docs/event-and-decision-contract.md`. This is a tested library, not a deployed daemon. It can decode a proposed 192-byte sensor record, create privacy-minimized events, batch them through bounded queues, retry an authenticated HTTPS/mTLS analytics request, expose aggregate counters and parse decisions for dry-run validation. Flow hashes are explicitly marked ambiguous and never assigned request correlation IDs. Sensor loss is reported as unavailable until a real sensor counter is sampled. It never applies a deny or rate-limit action to traffic.

From the repository root:

```sh
cargo test --locked --manifest-path collector/Cargo.toml
cargo clippy --locked --all-targets --manifest-path collector/Cargo.toml -- -D warnings
cargo run --release --manifest-path collector/Cargo.toml --example baseline
```

The Day 3-10 implementation and evidence are recorded in `docs/member3-day3-to-day10-evidence.md`. A Linux eBPF ring-buffer consumer and live Python analytics integration require the other owners' accepted handoffs and Linux lab tests before this can be called operational.

## Member 4 loopback lab compatibility

`LoopbackAnalytics` is a separate local-only sender for Member 4's `/v1/batches`
Bearer endpoint. It accepts only an explicit `http://127.0.0.1:<port>/v1/batches`
URL, disables proxies and redirects, checks source identity and freshness, and
enforces 64 events / 256 KiB per batch and 4 KiB per event. It does not replace
`HttpsAnalytics` or authorize shared HTTP deployment. Configure the collector's
`batch_size` at 64 or less for this receiver. A rejected or stale batch is not
retried; a transient outage retains stable IDs within the short freshness window.

With the project's pinned Python dependencies installed, run the reproducible
synthetic handoff from the repository root:

```sh
python scripts/check_member3_loopback.py
```

The check creates runtime credentials in memory, starts a temporary loopback
analytics server, sends a Rust batch, verifies exact acknowledgment and an
idempotent retry, then checks bad credentials, wrong source, schema/freshness
rejection and secret-free server logs. See
`docs/member3-member4-loopback-evidence-2026-10-21.md`. This uses a synthetic
record on the local host; it does not test a Linux eBPF sensor or active rules.
