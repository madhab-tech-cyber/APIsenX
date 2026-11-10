# Member 3 individual-plan Days 16–22 — formal disposition (2026-11-10)

**This is a disposition record, not an implementation record.** It closes
the enforcement-week items from Member 3's (Rust Enforcement &
Performance) individual 30-day plan, mirroring the Member 2 Days 17–18
disposition recorded in `docs/day1-18-evidence-completion-matrix.md`
(PR #150). Items that were genuinely completed are recorded as completed;
only the parts that require applying decisions to traffic are closed by
governance decision.

| Member 3 plan day | Plan item | Disposition |
|---|---|---|
| 16 | Design detection-only, monitor and blocking modes | **COMPLETED as design** — ENF-1.0 criteria (`docs/enforcement-approval-and-rollback.md`), gates EG-01…EG-08 and the rollout state machine. No implementation was required for the design item. |
| 17 | Implement dry-run decision application and metrics | **COMPLETED at dry-run level** — `collector/src/decision.rs` parses/validates decisions; `collector/src/metrics.rs` exposes aggregate counters. Applying a parsed decision to traffic is dispositioned with Day 18. |
| 18 | Apply deny decision with timeout and emergency disable | **CLOSED BY GOVERNANCE DECISION** — not implemented, none approved |
| 19 | Implement bounded rate-limit state and safe responses | **CLOSED BY GOVERNANCE DECISION** — rate-limit contract is parsed and validated (`RateLimit{requests, per_seconds}`, approval + rollback references required); no rate-limit state is implemented or applied |
| 20 | Add correlation IDs and tamper-evident export metadata | **COMPLETED as contract, with a recorded design limit** — flow correlation is deliberately marked ambiguous/`null` (no authoritative request marker exists; see `collector/README.md` and `docs/collector-interface.md`). Tamper-evident checkpoint/export metadata belongs to the #83-gated audit design, not the collector, and is **held under the same governance** — not implemented in the collector |
| 21 | Add timeouts, circuit breaker and emergency disable | **CLOSED BY GOVERNANCE DECISION** — circuit breaker and kill switch exist as ENF-1.0 EG-07 criteria; no mechanism is implemented, because there is no approved active mode for it to protect |
| 22 | Run blocking, rollback and recovery tests | **PARTIALLY COMPLETED; remainder CLOSED BY GOVERNANCE DECISION** — observe-path failure/recovery is covered by userspace resilience tests and the loopback CI contract. Blocking and rollback tests have nothing approved to run against; live-path recovery evidence remains owed by the authorized Linux lab session, not by this disposition |

**Basis for the disposition:**

- AP-1.0 is `monitor_only` project-wide with zero active enforcement
  rules, and the release is **NOT APPROVED**. No enforcement action of any
  kind has been authorized for any member's plan.
- `docs/enforcement-approval-and-rollback.md` (policy ENF-1.0, Day 16)
  approves enforcement *design criteria* only. Its §1 gates (EG-01…EG-08)
  must all be satisfied before an active rule can be authorized, and its
  §5 disposition states that the criteria approval "authorizes neither a
  blocking rule nor a network mutation." No such authorization exists in
  the repository.
- The collector code is consistent with monitor-only operation:
  `collector/src/decision.rs` states "Nothing in this module applies a
  decision to traffic or verifies its cryptographic origin," and no
  application path or rate-limit state exists anywhere in the crate.

**Effect:** Member 3 plan Days 16–22 require no enforcement implementation
and no further enforcement evidence while this governance state holds. They
may only be reopened by a recorded authorization under ENF-1.0 naming the
rule, scope and expiry — not by a PR, a CI result, or this record. This
disposition does not approve enforcement, deployment, or release.
