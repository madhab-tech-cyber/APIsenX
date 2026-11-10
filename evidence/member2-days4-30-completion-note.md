# Member 2 — Days 4–30 Completion Note (2026-11-10)

**Engineer:** Member 2 (eBPF Traffic Engineer, `renu-stack`)
**Scope:** Member 2 Individual Responsibility Plan v1.0, Days 4–30.
**Companion records:** `evidence/daily-status-updates.md` (Days 1–3, complete);
Member 2 deliverables audit of 2026-11-10 (baseline `origin/main` `7440bd0`).

**Honesty rule for this note.** This is a completion *record*, not a claim
that everything is done. Every landed item below cites a commit SHA or PR
number verified in git history on `main`. Items whose evidence requires a
running kernel (verifier logs for the current sensor, live capture/loss/
stress/performance runs, artifact checksums, the final demonstration) are
marked **PARTIAL** or **MISSING** and remain open: the Day-3 kernel evidence
was captured in an external authorized lab (Ubuntu 22.04, kernel 5.15) and
cannot be regenerated in the current environment. No kernel-level result
is claimed anywhere in this note.

## How the work landed

Member 2's daily evidence files stop at Day 3. The Days 4–30 work reached
`main` through reviewed PRs instead:

- Sensor + contract implementation: `ff99db1` (2026-10-27), merged by
  **PR #92** (merge commit `9b3fbdf`, 2026-10-29).
- Member 3 sensor-contract alignment: **PR #94** (merge `5eba141`),
  incl. `9dd1ae9`, `398c781` (2026-10-29).
- Producer corrections answering Member 3's handoff review
  (`docs/member3-sensor-handoff-review-2026-10-29.md`, 2026-10-29):
  `2aa0e1e` (complete event-record initialization + shared-sequence event
  IDs) and `fd98ec4` (sequence-wrap handling), merged by **PR #95**
  (merge `49f4efd`); CI regression follow-up **PR #96** (merge `537813c`).
- Sequence semantics + tests: `b937021`, `c2e604b`, `0c8e510`,
  `0fbac7f` (32-bit sequence wraparound test) — all 2026-10-29.
- Loader maintenance: Ruff/format passes `736dfc1`, `7342ac6` (2026-11-06).

(Days 1–3 anchors for reference: Day 1 reached main as `2cd701b`, Day 2 as
`07f1410` — the SHAs in `daily-status-updates.md` are the pre-merge branch
commits.)

## Day-by-day record, Days 4–30

| Day | Plan item | Status | Record |
|---|---|---|---|
| 4 | Capture approved connection metadata | DONE (code) | Sensor emits 5-tuple + method + route marker + status only, privacy boundary in-kernel — `ff99db1` / PR #92. No kernel-run proof beyond the Day-3 lab session. |
| 5 | Emit method, route marker, time, process metadata | PARTIAL | Method/route/`bpf_ktime_get_ns` emitted (`ff99db1`). Process metadata is only populated from the `api_sentinel_sessions` LRU map, which nothing in the repo populates — pid/tgid/uid are emitted as 0 in practice. |
| 6 | Bounds, map limits, unprivileged behaviour | PARTIAL | Bounds/map limits proven by layout + emulator suites (`ff99db1`). Unprivileged behaviour documented (Day-2 doc, loader checks); no recorded test of an actual unprivileged load attempt. |
| 7 | Capabilities + capture limitations doc | DONE | Day-2 privileges doc (`07f1410`) + `docs/https-safe-observation-agreement.md` (in `ff99db1`). |
| 8 | Route/process metadata for discovery | PARTIAL | Route marker: yes. Process metadata: same sessions-map gap as Day 5. |
| 9 | Capture coverage for every mock route | MISSING | No sensor route-by-route coverage matrix exists. Requires the live lab run. |
| 10 | Only approved identity/resource metadata | DONE (design+code) | Allowlist enforced by struct design; contract + privacy tests in `ff99db1` / PR #92. |
| 11 | Sensitive admin routes observed | MISSING | No evidence any admin route was exercised through the sensor. Requires the live lab run. |
| 12 | Malformed/oversized kernel events | DONE (emulated) | Emulator tests (truncated frames, IHL<5, route truncation) + contract record-size rejection — `ff99db1`. Kernel-side: none. |
| 13 | Probe cost + event loss under load | MISSING | No measurements exist. Requires the live lab run. |
| 14 | Demonstrate coverage, explain limitations | PARTIAL | `docs/day14-mid-review.md` (recorded `fb7a3ae` 2026-10-15, refreshed `f6911d4` 2026-10-17) honestly records integration BLOCKED at mid-review. The sensor merged later (PR #92), but no updated Member 2 coverage demonstration supersedes it. |
| 15 | Fix capture gaps / privilege findings | DONE | Member 3's blocking handoff findings fixed: `2aa0e1e`, `fd98ec4` via PR #95; CI follow-up PR #96. **Caveat:** no document records Member 3 *accepting* the corrected producer; that acceptance record is still owed. |
| 16 | Map enforcement hook options/constraints | PARTIAL | Options documented (Day-2 doc; `docs/enforcement-approval-and-rollback.md`). `TC_ACT_SHOT` return path exists in the design only. |
| 17 | Attach rule metadata without dropping | CLOSED BY GOVERNANCE DECISION | Not implemented. Formal disposition recorded 2026-11-10 in `docs/day1-18-evidence-completion-matrix.md`: AP-1.0 is `monitor_only`, no enforcement approved project-wide. |
| 18 | Implement approved enforcement hook | CLOSED BY GOVERNANCE DECISION | Not implemented — no enforcement was ever approved. Same disposition record as Day 17; ENF-1.0 (§5) authorizes neither a blocking rule nor a network mutation. |
| 19 | Counters for kernel-side throttling | PARTIAL | Per-CPU stats map (16 counters incl. enforcement-drop slot) in the sensor (`ff99db1`); no throttling consumer or rate-limit counters beyond event/drop/malformed totals. |
| 20 | Stable event sequence + loss counters | DONE (code) | Shared atomic sequence map + `STAT_RINGBUF_DROPS`; semantics in `docs/producer-consumer-contract.md` §5, clarified `b937021`/`c2e604b`; wraparound test `0fbac7f`. This is the fix set that closed the Day-15 findings. |
| 21 | Probe unload, map exhaustion, permission failure tests | PARTIAL | Unload/cleanup implemented + scoped (`scripts/cleanup_sensor.sh`, loader `--cleanup`, in `ff99db1`) but no recorded test run. Map exhaustion: emulator saturation only. Permission failure: no recorded test. |
| 22 | eBPF stress + privilege tests | MISSING | No stress/privilege test results recorded. Requires the live lab run. |
| 23 | Remove payload fields at capture source | DONE | Sensor never copies payload beyond the method token + bounded route marker; query values stripped in-kernel; contract privacy tests + `test_zero_credential_and_body_extraction` (`ff99db1`). |
| 24 | Safe capture-health metrics only | PARTIAL | Kernel stats map exists (16 counters). No userspace sampler/exporter for sensor health; dashboard health data is fixture-based, not sensor-fed. |
| 25 | Event-loss + observation-confidence indicators | PARTIAL | Loss: sequence + drop counter (code, Day 20). Observation-confidence indicators: not implemented for the sensor. |
| 26 | Rust advisories, lint, unsafe-code review | PARTIAL / N/A | Member 2's code is C — `cargo audit` does not apply. No recorded clang static-analysis or unsafe-review pass over `ebpf/src/api_sentinel_sensor.c`. |
| 27 | Patch eBPF findings, rerun verifier/stress | PARTIAL | Findings patched (Day 15 record). Verifier rerun after the patches: **not recorded** — the Day-3 verifier summary predates the corrected producer. Stress rerun: none exists to rerun. |
| 28 | Finalize setup, privileges, troubleshooting | PARTIAL | `ebpf/README.md`, Makefile lifecycle targets, loader `--attach/--cleanup/--status` cover setup and privileges. No dedicated sensor troubleshooting section found. |
| 29 | Build reviewed artifacts + record checksums | MISSING | No built `api_sentinel_sensor.o` artifact or checksum record in the repo. Requires the lab build. |
| 30 | Demonstrate capture health, explain kernel safety | MISSING | No Member 2 demonstration record. The project human demonstration record (`docs/final-demonstration-and-handover.md`) is itself still PENDING. |

## What remains open after this note

All remaining items need the authorized Linux lab session or another
member's signature — none can be closed with paperwork:

1. Verifier run on the current sensor with the raw log committed
   (Days 3-baseline refresh, 27).
2. One live run closing several items together: route coverage matrix
   (Day 9), admin-route observation (Day 11), event-loss measurement
   (Days 5-deliverable/13), probe-overhead measurement (Day 13), stress +
   privilege tests (Day 22), unload/exhaustion/permission-failure runs
   (Day 21).
3. Member 3's acceptance record for the corrected producer (Day 15 caveat).
4. Day-29 artifact build + SHA-256 record; Day-30 demonstration record.
5. Design-level leftovers: sessions-map population *or* a contract
   amendment stating pid/tgid/uid are unpopulated in v1 (Days 5/8);
   userspace stats sampler (Day 24); observation-confidence indicators
   (Day 25); clang static-analysis pass (Day 26); sensor troubleshooting
   section (Day 28).

Release remains **NOT APPROVED**; AP-1.0 stays `monitor_only` with zero
active enforcement rules. Nothing in this note changes that state.
