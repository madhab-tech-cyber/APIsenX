# Member 4 Days 11–20: detection and signed lab recommendation contract

**Date:** 2026-10-21 (Asia/Calcutta). **Implementer:** `madhab-tech-cyber`.
**Baseline:** main `7efee11`; existing collector and application are unchanged.
**State:** implementation for independent review, not accepted integration.
This extends [Days 1–10](member4-ingestion-contract.md); it does not silently
change IF-04, IF-07, AP-1.0 or the zero-active-rule authorization decision.

Historical DET-1.1 baseline: [Days 21–30](member4-days21-30-evidence.md) now
uses DET-1.2, caps the instance policy snapshot at 300 seconds, validates source/
config freshness and enforces typed masking before storage. The old statements
below about unimplemented read APIs describe that earlier schedule snapshot;
current optional reads are specified in [MGT-LAB-1.0](member4-management-contract.md).

## Detection and explanations

`analytics.detection.DetectionEngine` takes an `Observation` constructed by a
trusted in-process resolver. It never accepts actor, role, tenant, owner,
permissions or object assertions from public JSON. Canonical route classification
precedes function and object checks. API authorization remains the source of
truth and is never replaced by a Sentinel recommendation.

| Rule/version | Predicate | Output boundary |
|---|---|---|
| DET-OBS-1 / DET-1.1 | Valid allowed operation, or unavailable/conflicting required context | `allow` means expected permission only; unavailable is not a finding |
| DET-SHADOW-1 / DET-1.1 | Approved OpenAPI path or method drift | `alert` / shadow candidate; does not prove a served shadow endpoint or attack |
| DET-BFLA-1 / DET-1.1 | Known active role lacks explicit function permission and authoritative response is 2xx | `deny` recommendation / BFLA candidate, independent of empty/all-owned/mixed inventory |
| DET-BOLA-1 / DET-1.1 | Function gate passes, authoritative object/tenant policy denies, response is 2xx | `deny` recommendation / BOLA candidate; same-tenant valid shares/admin reads excluded |
| DET-FLOW-1 / DET-1.1 | More than ten distinct successful, permitted status updates by one tenant/subject in 60 seconds | `alert` only, heuristic review candidate, not proof of abuse or a rate limit |

Function gates cover the current GET list/object/admin/support and PATCH object
operations. Object GET/PATCH decisions reuse M5's current `authorize` function.
The canonical decoded object ID must equal the resolver's object ID: changing
a URL without refreshing context yields unavailable, not guessed ownership.
Missing/inactive identity, unknown role/policy, missing tenant, missing object,
source outage and invalid route context cannot authorize a recommendation.
Denied 403/404 attempts are reported as `ACCESS_PREVENTED`, not successful BOLA
or BFLA. Neither object-ID changes nor volume alone can create a deny action.
List function permission does not prove every returned row was properly scoped.
Full AP-1.0 grant issuer/type and list-content acceptance remain M5/M1 review work.

Flow state uses purpose-separated HMAC over unambiguous tenant/subject namespace
encoding. Distinct event IDs count once; re-evaluating a burst event preserves
its original burst outcome. Bounded deques retain at most threshold+1 timestamps
per key; defaults are 1,000 keys and 11,000 dedup IDs. Capacity/clock rollback
returns unavailable instead of resetting a live budget. Window expiry and the
service's one-second sweeper remove idle state. The threshold is an unapproved
lab heuristic, not the M1 service rate-limit profile or a performance guarantee.

## Separate recommendation endpoint

`POST /v1/recommendations` is disabled (404) unless both runtime settings exist:
`APISENTINEL_DECISION_TOKEN` and `APISENTINEL_DECISION_KEY` (hex, >=32 decoded
bytes). They must be separate from the ingest credential and masking key.
No credential values belong in Git, logs, screenshots or chat. Existing startup
needs no new settings because this endpoint is optional and off by default.

The decision credential cannot append events, and the ingest credential cannot
obtain recommendations. Body limit is 4 KiB, with existing authentication-before-
parsing, no compression, strict JSON and concurrency/body-timeout controls.
The only request fields are UUID `event_id`, UUID `nonce` and offset-aware
`requested_at` (<=2 seconds old, <=1 second future). Additional context/target/
signature fields reject. Forwarded identity/certificate headers are not trusted.

`create_app(..., resolver=...)` is an internal integration seam. The default is
**no resolver**, even with credentials enabled: it returns 503, never loads
public claims as principal context. A resolver must supply that exact event ID,
server-resolved subject/object, method/target/status and fresh observation.
M3's null/ambiguous collector identity is insufficient. The sample review demo
injects explicitly synthetic fixtures; it is not a live provenance proof.

Server replay state claims each authenticated request nonce before resolving it;
replay returns 409, capacity returns 503. The window holds at most 4,096 live
nonces for five seconds and never evicts a live nonce to admit a new request.
After failure, retry with a new nonce and a still-fresh authoritative event.
Unknown context, source exception or audit append failure issues no signed reply.

## Proposed LAB-REC-1 envelope and MAC verification

Schemas are exported by `python -m analytics.schemas`. The response contains:

- `policy`: schema `analytics_policy` 1.0, AP-1.0, DET-1.1, exact OpenAPI digest,
  exact detection/flow/normalization/application-policy source digest, permission
  map digest, actual flow configuration, fixed lab issuer/key ID, UTC issue/expiry
  (60 seconds), mode `monitor_only`, and HMAC signature.
- `decision`: schema `analytics_recommendation` 1.0, random decision UUID,
  bound event ID/nonce, digest of the signed policy, AP/rule versions, issuer/key
  ID, UTC issue/expiry (five seconds), exact method/template, allow/alert/deny,
  allowlisted rule/reason, `mode=monitor_only`, `enforce=false`, and HMAC signature.

Canonical bytes are sorted-key, compact ASCII JSON of the typed model's JSON
projection with `signature` excluded. HMAC-SHA-256 prefixes are `policy-v1\0`
and `recommendation-v1\0`, with a separate runtime signing key. This is a
**symmetric MAC**, not public-key signing or an owner approval. Constant-time
comparison verifies both records. The consumer must pin the contract, source,
permission map and flow configuration, bind nonce/event/method/template, enforce
aware times and TTLs, reject extra/duplicate fields and oversized replies, and
consume the nonce once in its own bounded replay window. Wrong key, issuer,
version, purpose, config, target, signature or expiry rejects generically.

**LAB-REC-1 is deliberately NOT M3's `enforcement_decision` IF-07 schema.** It
contains no approval or rollback reference, and no active-mode option. A signed
deny is only a dry-run recommendation. No producer/consumer crypto contract,
M1 authorization lease or traffic-control adapter has been accepted. HMAC trust,
key rotation/distribution, TLS/mTLS and persistent replay/session state still
need joint design and actual integration tests before shared use.

Replay, audit and flow state are volatile and single-process. Restart loses
them; multiple workers do not share state. Rotate the per-session signing key
on restart and use one local worker for this prototype. Never describe this as
durable/distributed replay protection or enable enforcement from its results.
The service remains loopback-only; no public deployment/tunnel is authorized.

## Minimal structured audit (Day 20)

Before signing, append an allowlisted masked audit summary: schema/version,
purpose-keyed event reference, opaque event UUID, AP/rule/contract version,
method/template, rule ID, reason, expected-access outcome, finding class,
recommendation and explicit monitor-only mode. No raw path/query, subject,
tenant, object, credential, arbitrary diagnostic or stack trace is retained.
Failed append returns unavailable, not a success acknowledgement.

Audit uses the existing bounded volatile store (default 1,000 rows, 300-second
server receipt TTL), idempotent event semantics, capacity failure and sweeper.
It has no HTTP read/export endpoint. There is **no durable/append-only/tamper-
evident audit, encryption-at-rest, backup, legal hold or production RBAC claim**.
Those remain later hardening and integration work. Unknown-route audit uses
only `/__unknown__`; it does not retain raw values or unnecessary route tokens.
