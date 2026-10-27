# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Merged implementation:** PR #69, PR #70, PR #71, PR #72, and PR #74. **Latest follow-up:** PR #76 merged at `505f0493f20c468c5b81955d6a6e939f02e77317`.

## Scope delivered for review

PR #69 introduced the initial bounded limiter. PR #70 was merged at `fba1a299e9d64c36b6de693ac0ed3d387d128c7e`, adding atomic multi-gate admission, authenticated route-level budgets, and weighted service/subject cost budgets. PR #70 CI passed: Mock API Security Tests #86 and Analytics Security Tests #43. PR #71 was merged at `d55852d0d235e6a67834e45352a8c8b4b470ff91`; its Mock API Security Tests #89 and Analytics Security Tests #46 passed. PR #72 was merged at `ba6ec2a2f857d07b37a2344fbcff651972d2d6a0`; Mock API Security Tests #92 and Analytics Security Tests #49 passed. PR #73 adds bounded pagination (limit default 50, maximum 100) to list endpoints. PR #74 was merged at `0ef5406ec4c54d39daa6a909e21ac6cb9dffbf89`; final CI passed: Mock API Security Tests #107 and Analytics Security Tests #64. PR #74 includes bounded pagination, streamed request-body enforcement (16 KiB), serialized response-byte cap (64 KiB), and bounded per-subject read/PATCH concurrency gates. PR #75 merged the reproducible load probe and proposed route-failure policy decision record. PR #76 added deterministic probe tests and fixed the Ruff import-spacing error; PR #76 is merged.

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
- PR #76 exact-head CI: **PASS** — Mock API Security Tests #116 and Analytics Security Tests #73 on `8f085437108ffc7436dee2f20405b7197086634a`.
- PR #76 merged on main at `505f0493f20c468c5b81955d6a6e939f02e77317`; merge does not substitute for independent reviewer sign-off.
- PR #78 was closed without merging because of conflicts; replacement PR #79 carries the policy-contract follow-up.
- Replacement PR #79 CI at commit `89cfbd26977a758ef2662ce272efd902ecf9848b`: **PASS** — Mock API Security Tests #124 and Analytics Security Tests #82. These validate the branch's automated suite, not live load capacity.
- Load/performance/recovery proof: **NOT PROVIDED**. The probe has not been run against an authorized lab instance in this work session.

## Explicit limitations

This work does not complete LM-01–LM-20. Per-subject read concurrency is capped at 5 and PATCH concurrency at 2 using a bounded process-local registry (4,096 keys). Pagination uses `limit` default 50, max 100, and non-negative `offset`. PR #74 adds a streaming request-body cap of 16 KiB and a serialized response-byte cap of 64 KiB. PR #75 merged at `f6b144eba0fcffc699bd92bb683a3d8ac03788c5`; Mock API Security Tests #109 and Analytics Security Tests #66 passed. PR #76 added deterministic probe tests for success, 429, connection-failure handling, and credential non-disclosure; its exact-head CI passed. Actual authorized-lab measurements and independent approval are still not claimed. Multi-worker/distributed coordination remains open. Process-local limits are not globally consistent and reset on restart. The follow-up adds in-process per-route aggregate and weighted service/subject cost budgets, but does not establish full LM-01–LM-20 compliance. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

The load probe now records observed `Retry-After` values and counts HTTP 429 responses that lack a positive integer retry delay. Regression tests cover capture of a positive delay and credential non-disclosure. The implementation and runbook changes are committed on the Day 20–21 follow-up branch; fresh CI for these latest Day 19 changes is pending.

Run the probe against an authorized lab service at normal load, overload, and recovery levels, and retain the JSON outputs as real evidence. Approve route-failure semantics with the service owner and independent reviewer. Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.


## Day 19 remaining acceptance actions (open)

1. Start the Mock API in an isolated authorized lab and verify `GET /health` and `GET /orders` with a demo bearer token and `X-Policy-Version: AP-1.0`.
2. Run and retain three separate JSON reports: normal load, overload, and recovery. Record the exact commit, endpoint, request count, concurrency, UTC timestamps, and any service restart or reset between runs. Never put bearer tokens or sensitive response bodies in evidence.
3. Verify that overload responses are bounded (expected rate-limit responses are generic 429/503 as applicable), `Retry-After` is present and positive for 429, and denied/rejected requests do not mutate order state.
4. After load stops, repeat the normal-load probe and confirm recovery. Compare status counts, transport error classes, throughput and latency percentiles; do not invent target thresholds after seeing the result.
5. Obtain service-owner and independent-reviewer acceptance of the measurements and limitations. Multi-worker/distributed coordination, restart-reset behavior, and LM-01–LM-20 gaps remain explicit limitations.

**Evidence integrity:** No live measurements are recorded here because this session did not execute the probe against a running authorized lab service. Passing CI is not load-test evidence or human sign-off.
