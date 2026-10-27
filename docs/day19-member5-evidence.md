# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Merged implementation:** PR #69, PR #70, PR #71, and PR #72. **Current follow-up branch:** `day19-followup/streaming-response-bounds`.

## Scope delivered for review

PR #69 introduced the initial bounded limiter. PR #70 was merged at `fba1a299e9d64c36b6de693ac0ed3d387d128c7e`, adding atomic multi-gate admission, authenticated route-level budgets, and weighted service/subject cost budgets. PR #70 CI passed: Mock API Security Tests #86 and Analytics Security Tests #43. PR #71 was merged at `d55852d0d235e6a67834e45352a8c8b4b470ff91`; its Mock API Security Tests #89 and Analytics Security Tests #46 passed. PR #72 was merged at `ba6ec2a2f857d07b37a2344fbcff651972d2d6a0`; Mock API Security Tests #92 and Analytics Security Tests #49 passed. PR #73 adds bounded pagination (limit default 50, maximum 100) to list endpoints. The current follow-up builds on that branch and adds streaming request-body enforcement and a serialized response-byte cap; its CI is pending.

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
- PR #73 CI: **PENDING/NOT VERIFIED here**; its workflow lookup returned in-progress runs.
- Current follow-up branch CI: **PENDING**; no claim of passing tests or lint until its own workflows complete.
- Load/performance/recovery proof: **NOT PROVIDED**.

## Explicit limitations

This branch does not complete LM-01–LM-20. Per-subject and PATCH concurrency, multi-worker/distributed coordination, and route-specific failure decisions remain open. PR #73 adds pagination parameters (`limit` default 50, max 100; `offset` non-negative) to list endpoints. The current follow-up adds a streaming request-body cap of 16 KiB and a serialized response-byte cap of 64 KiB, both pending CI. These are process-local application middleware controls and require tests and review before acceptance. Content-Length checks alone do not prove a streaming body-size cap. The follow-up adds in-process per-route aggregate and weighted service/subject cost budgets, but does not establish full LM-01–LM-20 compliance. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.
