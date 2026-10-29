# Member 3 review of Member 2 sensor handoff (2026-10-29)

Scope: Member 2 PR #92 at `9732fa36a652250fa743b31a4acb8c1f7b41b11c`, compared with main `d2ce9ae`. This is a local engineering review, not a joint sign-off or a Linux integration result.

## Completed locally

- Updated the existing Rust byte-slice decoder to recognize the proposed 192-byte record's version-1 high-byte flags, monitor-only bit, known low flags, IPv4/IPv6 flag consistency, and truncated-route rejection. No raw flow fields or concrete routes are forwarded. The existing null/ambiguous request correlation remains.
- Updated synthetic pipeline and microbenchmark fixtures to match the proposed flags. Pending a fixed and accepted producer, the normalized sequence is zeroed instead of forwarding uninitialized kernel bytes; egress correlation is marked unsupported because PR #92 does not initialize its flow hash. Kept the Rust library, lock file, bounded queues, loopback sender, and dry-run decision boundary.
- `cargo test --locked --all-targets --manifest-path collector/Cargo.toml`: 28 Rust tests passed on macOS arm64. `cargo fmt --check` and strict all-target Clippy passed. These are userspace compatibility checks, not Linux verifier, runtime, latency, or release evidence.
- The existing Rust/Python loopback script could not be rerun in this checkout because the local Python environment lacks `fastapi`; the temporary analytics process exited before health. No new loopback pass is claimed. The earlier PR #50 Linux CI remains separate historical evidence.

## Blocking producer/consumer findings

1. The PR #92 C producer reserves `struct api_event` but never assigns `event->event_id` in either ingress or egress. Its contract calls that field a monotonic sequence for gap/loss detection. Rust must treat this value as unverified diagnostic data; sequence gaps cannot establish loss. The trusted aggregate BPF drop counter still needs an attached sampler and reset/availability tests.
2. The egress producer does not initialize `pid`, `tgid`, `uid`, `flow.flow_hash`, the flow padding, `latency_us`, or most `route_marker` bytes before ring-buffer submit. It sets only `route_marker[0]` to NUL. This can expose stale kernel memory in the raw record and yields arbitrary flow/correlation hints. Initialize the entire reserved event before filling fields, then add a negative/privacy test on actual emitted bytes.
3. The proposed contract labels `event_id` sequential and describes a collector ring-buffer listener, boot-time UTC conversion, and Linux loss detection. Those are not implemented in the current Rust library. The contract should distinguish proposed consumer work from actual evidence. `bpf_ktime_get_ns()` is source-local monotonic time; collector `observed_at` must be UTC receive time, without inventing exact conversion.
4. A flow hash is not a request ID for keep-alive or concurrent HTTP requests. PR #92 supplies no authoritative request-level marker. Keep `correlation_id=null` and `correlation_quality=ambiguous/unsupported`; BOLA/BFLA attribution remains unavailable from this source.
5. PR #92 currently conflicts with main and its diff would remove the merged collector and analytics trees. Rebase/resolve against current main without deleting those components. Its latest CI status and Linux verifier/runtime receipts must be checked at the corrected head before acceptance.
6. The project has no authorized Linux lab attached to this task. The Rust code was tested on macOS; no real ring-buffer attach, source authentication, drop/recovery, resource, route-failure, or end-to-end latency measurement is claimed here.

## Member 4 boundary

The merged Member 4 `/v1/batches` receiver accepts the Rust **loopback-only** sender under the documented 64-event/256-KiB/4-KiB limits. PR #50's Linux userspace CI and local synthetic ack/idempotency/auth/schema/freshness tests do not connect PR #92's eBPF producer. Shared TLS/service identity, clock and retry horizon, authoritative context, durable audit, and exact producer/consumer acceptance still require owners' decisions. LAB-REC-1 is monitor-only and not IF-07 active enforcement.

Next acceptance sequence: correct and rebase the C producer; agree the exact revised wire revision with Member 2; run an unprivileged Rust ring-buffer adapter against an authorized Linux lab with real emitted records and loss counter; exercise Member 4 ingestion through the same run; record end-to-end latency/resource and fault/recovery evidence; obtain Member 1 gate decisions before considering active rules. No unrelated host rules or programs should be flushed.
