# APISenX — Member 3 meeting Q&A

**10 November 2026 · My role:** Rust collector, safe sensor event handling, Member 4 ingestion handoff, and preparation for future enforcement.

## 30-second answer

“I built the Rust collector that validates and normalizes proposed sensor records, sends bounded event batches, handles retries and acknowledgments, and reports safe health/loss states. I connected it to Member 4’s local Analytics receiver using synthetic traffic and updated the decoder for Member 2’s proposed 192-byte Linux record. My three PRs were merged. The work is monitor-only; I have not claimed a live Linux sensor-to-collector deployment or active blocking.”

## Questions I may be asked

### What does the Rust component do?

It is the consumer between Member 2’s proposed Linux sensor and Member 4’s Analytics service. It checks the wire record, creates a privacy-minimized versioned event, queues and batches within limits, sends with stable retry IDs, and accepts only exact matching acknowledgments. It exposes bounded processing/delivery metrics and parses decisions in dry run. It does **not** change traffic or install rules.

### Which work is yours, and which PRs contain it?

| PR | My contribution | Result |
| --- | --- | --- |
| [#32 — Rust collector foundation](https://github.com/madhab-tech-cyber/APIsenX/pull/32) | Rust crate, bounded decoder, event schema, queues/batches/retries, HTTPS/mTLS client configuration, exact acknowledgments, metrics, dry-run checks, correlation and loss safety | Merged 20 Oct |
| [#50 — Member 3/4 loopback handoff](https://github.com/madhab-tech-cyber/APIsenX/pull/50) | Local Rust sender to Member 4 `/v1/batches`, contract bounds/freshness, synthetic integration script and CI workflow | Merged 21 Oct |
| [#94 — sensor wire review](https://github.com/madhab-tech-cyber/APIsenX/pull/94) | Decoder for proposed version/flags, IPv4/IPv6 consistency, route truncation checks, safe handling of untrusted producer fields, handoff findings | Merged 29 Oct |
| [#153 — completion batch](https://github.com/madhab-tech-cyber/APIsenX/pull/153) | Day 26 decoder corpus tests, Day 28 guide, Day 29 locked build record and Days 16–22 governance disposition; authored and merged by the project owner | Merged 10 Nov |

The Day 3–10 deliverables were saved in planned order on **17 Oct**; commits were not backdated to those planned days.

### What was the hardest technical problem?

**Request correlation.** A flow hash can cover several HTTP requests on keep-alive connections and becomes ambiguous with concurrent requests. I removed the claim that it is a request ID. The event uses `correlation_id: null` and labels quality `ambiguous` or `unsupported` until the team agrees on an authoritative request marker.

### What problems did you find in Member 2’s sensor handoff?

In the PR #92 revision I reviewed, `event_id` was not assigned before ingress or egress submission, so sequence gaps could not prove loss. Several egress fields were not initialized, which could expose stale bytes and make flow hints unreliable. I kept those values out of normalized events and recorded the producer fixes needed. PR #92 was later merged; my review describes that inspected revision, not proof that every issue remains in the latest code.

### How did you integrate with Member 4?

PR #50 added a **localhost-only** sender for Member 4’s batch endpoint. It checked the 64-event / 256-KiB batch / 4-KiB event limits, source ID, freshness, and exact acknowledgments. The synthetic test used a temporary Analytics server: valid delivery and replay succeeded; bad credentials returned 401, wrong source 403, and invalid schema or stale events 422. This tests the userspace contract, not the live sensor path.

### How did you handle failures and loss reporting?

Queues, batches, timeouts and retries are bounded. Transient failures retry with stable IDs; permanent rejection or stale data stops retrying. The collector reports when sensor loss is unavailable instead of inventing a loss rate. A trusted drop-counter sampler and live recovery evidence are still needed.

### What testing can you defend?

- PR #32: **22 locked Rust tests** passed locally on macOS; formatting and strict Clippy passed.
- PR #50: **25 locked Rust tests** passed locally; synthetic Rust/Python loopback covered acknowledgments, replay, authentication, schema and freshness. Formatting and strict Clippy passed.
- PR #94: **28 locked Rust tests** passed locally; formatting and strict Clippy passed. Its corrected head passed all three GitHub Actions workflows, including the Linux Rust/Python **userspace** loopback.
- The first PR #94 CI run failed because its synthetic example had not been updated for the new wire flags. I fixed the fixture in commit `398c781`; later CI passed before merge. The old red run remains in GitHub history.
- The Day 7 macOS microbenchmark covers decode/normalize/serialize only. It is **not** measured end-to-end Linux overhead.

### Is enforcement active? Why not?

No. The Rust library checks decision shape only in dry run. Member 4 recommendations are monitor-only and are not an active Rust enforcement contract. Enabling a rule needs Member 1’s gates, approved route behavior, route-failure tests, timed rollback evidence and joint acceptance. Current state: **monitor-only, zero active rules**.

### What is still open for your part?

1. Agree the corrected wire contract and authoritative request marker with Member 2; implement/test a Rust ring-buffer listener against real emitted records.
2. Run sensor → Rust collector → Member 4 ingestion on an authorized Linux lab, including source authentication, freshness/replay, deduplication, loss/recovery and bounded health metrics.
3. Measure paired client latency and resource use under the validation plan, separate from the macOS microbenchmark.
4. Obtain Member 1/2/4/5 reviews and gates before proposing active enforcement.

For the day-by-day status and submission limits, see [the final timeline](member3-final-timeline-status-2026-11-10.md). The owner’s PR #153 is team support for Member 3 work; I should credit its authorship accurately.

**If asked whether it is deployed:** “No. The merged code and synthetic Linux CI demonstrate userspace compatibility; a live Linux sensor-to-collector pipeline and production enforcement have not been verified.”
