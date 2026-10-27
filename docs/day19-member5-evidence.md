# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Merged implementation:** PR #69, PR #70, PR #71, PR #72, and PR #74. **Current follow-up branch:** `day19-followup/load-probe-tests` (PR #76).

## Scope delivered for review

PR #69 introduced the initial bounded limiter. PR #70 was merged at `fba1a299e9d64c36b6de693ac0ed3d387d128c7e`, adding atomic multi-gate admission, authenticated route-level budgets, and weighted service/subject cost budgets. PR #70 CI passed: Mock API Security Tests #86 and Analytics Security Tests #43. PR #71 was merged at `d55852d0d235e6a67834e45352a8c8b4b470ff91`; its Mock API Security Tests #89 and Analytics Security Tests #46 passed. PR #72 was merged at `ba6ec2a2f857d07b37a2344fbcff651972d2d6a0`; Mock API Security Tests #92 and Analytics Security Tests #49 passed. PR #73 adds bounded pagination (limit default 50, maximum 100) to list endpoints. PR #74 was merged at `0ef5406ec4c54d39daa6a909e21ac6cb9dffbf89`; final CI passed: Mock API Security Tests #107 and Analytics Security Tests #64. PR #74 includes bounded pagination, streamed request-body enforcement (16 KiB), serialized response-byte cap (64 KiB), and bounded per-subject read/PATCH concurrency gates. PR #75 merged the reproducible load probe and proposed route-failure policy decision record. PR #76 adds deterministic probe tests and corrects the import-spacing lint issue.

- Added a bounded, process-local token-bucket limiter for aggregate service traffic and authenticated subject/canonical-route traffic.
- Added a lower subject limit for PATCH order updates.
- Uses monotonic time for refill, generic 429/503 errors, positive `Retry-After`, a 4,096-key ceiling, and idle-only eviction after 60 seconds. Live buckets are not evicted to grant a fresh burst.
- Added deterministic unit tests for burst exhaustion, refill, key-capacity behavior, idle eviction, and API responses.
- Restored `docs/openapi.yaml` to the canonical `main` contract after a YAML indentation error caused analytics normalization and OpenAPI parsing to fail; limiter limitations remain documented separately in `docs/identity-route-resource-limits.md`.

## Validation status

- Local test execution: **NOT RUN in this environment**.
- Ruff: **NOT RUN in this environment**.
- PR #69 CI: **PASS** — Mock API Security Tests #82 and Analytics Security Tests #39.
- PR #70 CI: **PASS** — Mock API Security Tests #86 and Analytics Security Tests #43.
- PR #71 CI: **PASS** — Mock API Security Tests #89 and Analytics Security Tests #46.
- PR #72 CI: **PASS** — Mock API Security Tests #92 and Analytics Security Tests #49.
- PR #73 pagination changes are included in merged PR #74; PR #74 CI passed.
- PR #74 CI: **PASS** — Mock API Security Tests #107 and Analytics Security Tests #64.
- PR #75 CI: **PASS** — Mock API Security Tests #109 and Analytics Security Tests #66.
- PR #76 latest-head CI: **PASS** — Mock API Security Tests #116 and Analytics Security Tests #73 for `8f085437108ffc7436dee2f20405b7197086634a`.
- Load/performance/recovery proof: **NOT PROVIDED**.

## Explicit limitations

This work does not complete LM-01–LM-20. Per-subject read concurrency is capped at 5 and PATCH concurrency at 2 using a bounded process-local registry (4,096 keys). Pagination uses `limit` default 50, max 100, and non-negative `offset`. PR #74 adds a streaming request-body cap of 16 KiB and a serialized response-byte cap of 64 KiB. PR #75 merged at `f6b144eba0fcffc699bd92bb683a3d8ac03788c5`; Mock API Security Tests #109 and Analytics Security Tests #66 passed. PR #76 adds unit tests for the load probe's success, 429, and connection-failure reporting. The latest-head CI passed, but actual authorized-lab measurements and independent approval are still not claimed. Multi-worker/distributed coordination remains open. Process-local limits are not globally consistent and reset on restart. The follow-up adds in-process per-route aggregate and weighted service/subject cost budgets, but does not establish full LM-01–LM-20 compliance. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

Run the probe against an authorized lab service at normal load, overload, and recovery levels, and retain the JSON outputs as real evidence. Probe unit tests passed in PR #76 CI; they are not a substitute for actual load measurements. Approve route-failure semantics with the service owner and independent reviewer. Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.
