# Rust collector and enforcement

Owner: Member 3. This crate implements the user-space collector in ordered daily milestones. It defaults to observation only; active blocking is not implemented or approved.

The current source of truth for proposed interfaces is `docs/collector-interface.md` and `docs/event-and-decision-contract.md`. Run `cargo test --manifest-path collector/Cargo.toml` from the repository root. Linux sensor and Python analytics integration require their owners' handoff and separate tests.
