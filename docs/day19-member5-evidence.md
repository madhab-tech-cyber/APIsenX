# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Branch:** `day19/member5-bounded-rate-limits`.

## Scope delivered for review

Follow-up branch created from `main` at merge commit `48fa718c7847b357c27b33873b08026eee0105f1` after verifying PR #69 was merged. This follow-up adds atomic multi-gate admission for authenticated route-level request budgets and weighted service/subject cost budgets. The follow-up remains unmerged pending CI.

- Added a bounded, process-local token-bucket limiter for aggregate service traffic and authenticated subject/canonical-route traffic.
- Added a lower subject limit for PATCH order updates.
- Uses monotonic time for refill, generic 429/503 errors, positive `Retry-After`, a 4,096-key ceiling, and idle-only eviction after 60 seconds. Live buckets are not evicted to grant a fresh burst.
- Added deterministic unit tests for burst exhaustion, refill, key-capacity behavior, idle eviction, and API responses.
- Restored `docs/openapi.yaml` to the canonical `main` contract after a YAML indentation error caused analytics normalization and OpenAPI parsing to fail; limiter limitations remain documented separately in `docs/identity-route-resource-limits.md`.

## Validation status

- Local test execution: **NOT RUN in this environment**.
- Ruff: **NOT RUN in this environment**.
- Prior merged PR #69 CI: **PASS** — Mock API Security Tests #82 and Analytics Security Tests #39.
- Follow-up branch CI: **PENDING**; no claim of passing tests or lint until its own workflows complete.
- Load/performance/recovery proof: **NOT PROVIDED**.

## Explicit limitations

This branch does not complete LM-01–LM-20. Unauthenticated source buckets, concurrency gates, pagination/response-size caps, multi-worker/distributed coordination, and route-specific failure decisions remain open. The follow-up adds in-process per-route aggregate and weighted service/subject cost budgets, but does not establish full LM-01–LM-20 compliance. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.
