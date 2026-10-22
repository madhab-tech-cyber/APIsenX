# Day 13 — Token Lifecycle and Request Replay Acceptance

**Owner:** Member 5 — Mock API / OpenAPI  
**Implementation branch:** `member5/day13-token-replay-acceptance`  
**Status:** Code and regression additions submitted for CI; durable/distributed guarantees are explicitly out of scope.

## Acceptance coverage

The mock API's current demo-token validation rejects unknown, altered, revoked, expired, not-yet-valid, and inactive credentials with `401 UNAUTHENTICATED`. Requests also require the supported `X-Policy-Version: AP-1.0` header.

State-changing `PATCH /orders/{orderId}` requests require a unique `X-Request-Nonce` containing 8–128 characters from `[A-Za-z0-9._~-]`. The API rejects a missing or malformed nonce and rejects reuse during the five-minute replay window. Regression coverage verifies that rejected requests do not mutate the order and that an old nonce can be accepted after its replay-window entry expires.

The Day 13 tests added in this branch cover:
- a token whose `issued_at` is in the future;
- missing, too-short, whitespace-containing, invalid-character, and overlong PATCH nonces, with order immutability assertions;
- reuse of a nonce only after the configured replay window expires.

## Limitations that must remain visible

- Tokens are synthetic fixtures, not issued by a production identity provider.
- Token metadata, revocation state, and replay nonces are held in process memory. They reset on process restart and are not shared between workers/instances.
- The nonce is replay detection, not a cryptographic signature or proof of request-body integrity.
- Order updates are process-local and reset when the API restarts.
- These controls are appropriate only for the authorized local test lab. They do not establish production authentication, durable revocation, distributed replay prevention, key rotation, or deployment readiness.

Do not describe token lifecycle or replay protection as production-ready. A production design needs an agreed issuer/validation model and durable, shared revocation/replay storage before such guarantees can be claimed.

## Validation required for closeout

Run from the repository root using the project environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check mock-api tests
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
git diff --check
git status --short --branch
```

Record the exact tested commit SHA and CI run. A successful code change or partial CI run does not substitute for the complete regression suite, independent review, repository protection, or the overall release gate.

## Outstanding external gates

- Member 1: independent AP-1.0/D11-F01 review and acceptance decision at the exact candidate SHA.
- Member 6: independent privacy/logging and regression review.
- Members 1/2/4: approve the versioned observation event schema and integration contract.
- Repository owner/admin: configure and verify `main` branch protection, including required CI checks and independent PR approvals.
- Project release owners: keep release held and enforcement monitor-only until all applicable gates have evidence and a superseding decision records the result.
