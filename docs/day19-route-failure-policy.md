# Day 19 route-failure policy decision record

**Status:** PROPOSED — requires service owner and independent reviewer approval.
**Profile:** `LIMIT-LAB-1.0`. **Enforcement:** `monitor_only`; zero active enforcement rules.

## Proposed fail behavior

| Condition | Proposed response | Rationale | Approval needed |
|---|---|---|---|
| Request rate or concurrency budget exhausted | Generic `429 RATE_LIMITED` with positive `Retry-After` | Explicit client backoff; no identity or limit details disclosed | Yes |
| Limiter state capacity exhausted for a new key | Generic `503 SERVICE_UNAVAILABLE` with positive `Retry-After` | Fail closed for the bounded lab prototype rather than grant an unmetered burst | Yes |
| Request body exceeds configured byte cap | `413` with generic `INVALID_REQUEST` body | Bound parsing/memory use | Yes |
| Response exceeds configured byte cap | Generic bounded `500` response; record sanitized metric | Avoid sending an unbounded response; application may already have done work | Yes |
| Limiter/shared coordinator unavailable in a future distributed deployment | **No deployment behavior approved**; deployment must remain blocked until owner chooses fail-closed vs explicitly scoped fail-open and tests it | This repository currently uses process-local state; distributed outage semantics cannot be inferred from it | Yes |
| Unmatched route | Shared bounded unknown-route budget; do not create a bucket per raw path | Prevent attacker-controlled cardinality | Yes |

## Guardrails

- These are proposed lab semantics, not production policy approval.
- Do not activate enforcement from this document.
- Do not trust forwarded client-IP headers unless a separately approved proxy trust configuration exists.
- Do not log bearer tokens, request bodies, query values, raw object identifiers, or raw attacker-controlled paths.
- Process-local limiters are not globally consistent across workers and reset on restart.
- Before acceptance, the owner/reviewer must approve the outage policy and review status codes, retry behavior, client compatibility, and recovery tests.

## Required evidence before sign-off

1. Normal-load, overload, and recovery probe reports from an authorized lab target.
2. Confirmation of expected 429/503/413 behavior and bounded responses.
3. Multi-worker/distributed behavior test or explicit documented exclusion for the lab.
4. Independent reviewer decision recorded in the project issue/PR.
5. Release remains **NOT APPROVED** until all required project gates are satisfied.
