# Member 3 Day 29 — collector release build record

**Recorded:** 2026-11-10. **Source:** `main` at
`c69153a0e693d03c75f02c090ff16e71540373d9` (after PRs #150/#151 merged).
**Scope:** the Rust collector crate (`collector/`, `api-sentinel-collector`
0.1.0, edition 2021). This record documents the reproducible build inputs
and the CI verification for that source. It is **not** a release approval:
AP-1.0 remains `monitor_only` and the project release is **NOT APPROVED**.

## Reproducible build inputs

- `collector/Cargo.lock` is committed (lockfile version 4, 146 packages).
  Every CI build and test invocation uses `--locked`, so the dependency
  graph that is tested is exactly the graph in the lockfile.
- Build / verify commands (from `collector/README.md` and the loopback
  workflow):

  ```sh
  cargo test --locked --all-targets --manifest-path collector/Cargo.toml
  cargo fmt --check --manifest-path collector/Cargo.toml
  cargo clippy --locked --all-targets --manifest-path collector/Cargo.toml -- -D warnings
  cargo run --release --manifest-path collector/Cargo.toml --example baseline
  ```

- **Toolchain:** the repository carries no `rust-toolchain` pin. CI uses the
  Rust toolchain preinstalled on the `ubuntu-24.04` GitHub-hosted runner
  image (the workflow adds the `rustfmt` and `clippy` components via
  `rustup`). Member 3's own recorded local verification used Rust 1.99.1 on
  macOS arm64 (see `docs/member3-sensor-handoff-review-2026-10-29.md`).
  Pinning a toolchain in-repo remains an open improvement; it is recorded
  here, not silently assumed.

## CI evidence for this source (labelled CI evidence)

Check runs on commit `c69153a0e693d03c75f02c090ff16e71540373d9`,
2026-11-10 (GitHub Actions):

| Check | Run | Result |
|---|---|---|
| Rust/Python Loopback Contract (`member3-loopback-integration.yml`: `cargo test --locked --all-targets`, `cargo fmt --check`, strict clippy, `scripts/check_member3_loopback.py`) | [run 42771185608](https://github.com/madhab-tech-cyber/APIsenX/actions/runs/42771185608), 06:50:20–06:51:01 UTC | **SUCCESS** |
| API Security and Quality Gates | run 42771185261 | **SUCCESS** |
| Analytics Security and Quality Gates | run 42771185686 | **SUCCESS** |

## What this record does not establish

- No release-profile artifact is published or retained by CI, and **no
  artifact SHA-256 record exists**. An artifact + checksum record is still
  owed (a CI artifact step or the authorized Linux lab session).
- Bit-for-bit reproducibility across two independent builds has **not**
  been verified; the reproducibility claim is limited to the locked
  dependency graph and the recorded commands above.
- The collector remains a tested library, not a deployed daemon: no Linux
  ring-buffer consumer exists, and no live-sensor latency or recovery
  evidence is implied by this record.

## Subsequent source-package follow-up

The Member 3 final-evidence follow-up adds a CI step to package the Rust
**source crate** with `cargo package --locked`, save its SHA-256 alongside
`Cargo.lock` and the runner toolchain versions, and upload those inputs as a
30-day workflow artifact. This is pending exact-head CI verification and a
linked artifact digest; the historical limitations above remain true for the
`c69153a` source evaluated in this record. Even after CI passes, that package
is neither a full-system release artifact nor proof of bit-for-bit builds on
independent hosts.
