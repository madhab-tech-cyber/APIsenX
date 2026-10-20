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
