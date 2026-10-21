# Member 3 ↔ Member 4 loopback handoff — 2026-10-21

**Baseline:** Member 4 PR #49 merged into main at `d2984a4`; Member 3 PR #32
was also merged. This follow-up joins their *lab batch endpoint* to the Rust
collector in a separate local-only mode. It does not establish accepted IF-04
for shared deployment, a Linux sensor, request-level attribution or IF-07.

## Contract reconciliation

| Boundary | Member 4 receiver | Member 3 follow-up |
|---|---|---|
| Transport | HTTP only on 127.0.0.1 with a runtime Bearer credential | New `LoopbackAnalytics` accepts only an explicit 127.0.0.1 batch URL, with no proxy/redirect; existing HTTPS/mTLS client remains separate |
| Identity | Exact Bearer token and configured `source_id`; no certificate trust | Runtime token and source ID required; wrong token/source rejected in live lab check |
| Event | `collector_event` 1.1 with null request correlation | Existing v1.1 emitter matches; no flow hash is promoted to request identity |
| Bounds | 64 events, 256 KiB batch, 4 KiB event | Sender checks these before network; caller must set collector `batch_size` <=64 |
| Freshness | created/observed time from 2 seconds old to 1 second future | Sender checks at each attempt; stale batches stop retrying |
| Ack/dedup | Exact batch ID and event IDs; volatile event idempotency | Existing exact ack parser; same batch replayed and acknowledged twice in live check |
| Errors | 4xx rejection; 408/503 transient | Permanent rejection is not retried; timeout/server failure uses bounded existing retry behavior |

The loopback Bearer mode is restricted to a single local lab host. No TLS,
certificate identity, key rotation, distributed replay persistence or durable
audit is claimed. Member 4's separate LAB-REC-1 recommendation is **not** M3's
IF-07 decision; the Rust library does not consume it or enforce its results.

## Reproducible checks and observed result

On Apple M4/macOS arm64 with Rust 1.99.1 and Python 3.12 in a temporary virtual
environment containing `requirements.txt`:

```sh
cargo test --locked --all-targets --manifest-path collector/Cargo.toml
cargo fmt --check --manifest-path collector/Cargo.toml
cargo clippy --locked --all-targets --manifest-path collector/Cargo.toml -- -D warnings
python scripts/check_member3_loopback.py
git diff --check
```

**Observed locally:** 25 Rust unit tests passed; format and strict Clippy
passed. The loopback script started Member 4 Uvicorn on a random 127.0.0.1 port,
received a Rust-generated synthetic collector batch with an exact ack, replayed
the same batch ID/event ID successfully, observed 401 for a bad credential and
403 for a wrong source, observed 422 for invalid schema and stale event,
and found no generated runtime credential in captured server logs. The script
stopped the server. The Linux GitHub Actions check is proposed in this branch;
its result must be linked after the branch is pushed.

## Remaining acceptance gates

- M2/M3/M5/M1 still need an approved HTTPS-safe source, versioned Linux wire
  contract, runnable sensor and authoritative request marker. No sensor path was
  used in this check.
- M3/M4/M1 must choose the shared-deployment identity/TLS arrangement, confirm
  source and clock ownership, retry/replay horizon, key handling and whether
  the 2-second freshness budget is practical under measured load.
- Use `docs/mid-review-validation-plan.md` on the authorized Linux profile for
  verifier/load, loss/recovery, paired client latency and resource evidence. A
  GitHub Linux runner can verify userspace compatibility but is not that lab.
- Active enforcement remains disabled. No host rules or programs are installed,
  removed or flushed.
