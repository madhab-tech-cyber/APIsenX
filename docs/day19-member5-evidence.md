# Day 19 Member 5 Evidence — Bounded API Rate Limits

**Date:** 2026-10-27 (Asia/Kolkata). **Branch:** `day19/member5-bounded-rate-limits`.

## Scope delivered for review

- Added a bounded, process-local token-bucket limiter for aggregate service traffic and authenticated subject/canonical-route traffic.
- Added a lower subject limit for PATCH order updates.
- Uses monotonic time for refill, generic 429/503 errors, positive `Retry-After`, a 4,096-key ceiling, and idle-only eviction after 60 seconds. Live buckets are not evicted to grant a fresh burst.
- Added deterministic unit tests for burst exhaustion, refill, key-capacity behavior, idle eviction, and API responses.
- Restored `docs/openapi.yaml` to the canonical `main` contract after a YAML indentation error caused analytics normalization and OpenAPI parsing to fail; limiter limitations remain documented separately in `docs/identity-route-resource-limits.md`.

## Validation status

- Local test execution: **NOT RUN in this environment**.
- Ruff: **NOT RUN in this environment**.
- GitHub Actions on the pull request: **rerun pending after the OpenAPI repair commit**.
- Load/performance/recovery proof: **NOT PROVIDED**.

## Explicit limitations

This branch does not complete LM-01–LM-20. Per-route service budgets, unauthenticated source buckets, weighted-cost accounting, concurrency gates, pagination/response-size caps, multi-worker/distributed coordination, and route-specific failure decisions remain open. The limiter is volatile and process-local; restarts reset its state. This prototype is not production-ready and is not authorization to enable active enforcement.

Keep `monitor_only`, zero active enforcement rules, and the release decision **NOT APPROVED** until all required independent reviews, integration, measured load/failure evidence, and human checkpoints are complete.
