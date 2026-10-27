# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Merged implementation:** PR #69 and PR #70. **Current follow-up branch:** `day19-followup/unauth-input-bounds`.

## Scope delivered for review

PR #69 introduced the initial bounded limiter. PR #70 was merged at `fba1a299e9d64c36b6de693ac0ed3d387d128c7e`, adding atomic multi-gate admission, authenticated route-level budgets, and weighted service/subject cost budgets. PR #70 CI passed: Mock API Security Tests #86 and Analytics Security Tests #43. The current follow-up branch adds pre-authentication source and aggregate unauthenticated budgets; its CI is pending.

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
- Current follow-up branch CI: **PENDING**; no claim of passing tests or lint until its own workflows complete.
- Load/performance/recovery proof: **NOT PROVIDED**.

## Explicit limitations

This branch does not complete LM-01–LM-20. Concurrency gates, pagination/response-size caps, multi-worker/distributed coordination, and route-specific failure decisions remain open. The current follow-up adds bounded pre-authentication source buckets and an aggregate unauthenticated bucket, pending CI. The follow-up adds in-process per-route aggregate and weighted service/subject cost budgets, but does not establish full LM-01–LM-20 compliance. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.
