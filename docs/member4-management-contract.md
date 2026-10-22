# Member 4 management API and masking contract — MGT-LAB-1.0

**Date:** 2026-10-22 (Asia/Calcutta). **Implementer:** `madhab-tech-cyber`.
This is a loopback lab implementation for review with M1/M6, not an accepted
shared dashboard deployment. All outputs remain monitor-only candidates.

## Backend identity and scope

The management routes are disabled (404) unless named `ReaderGrant` profiles
are configured. Each profile has its own >=32-character runtime Bearer credential,
server-defined identity, role (`viewer` or `analyst`), case and aware expiry.
At most eight profiles are supported; credentials cannot equal ingestion,
recommendation or another reader credential. No public sample credentials exist.

The service holds **one configured lab case**, `APISENTINEL_CASE_ID`, in isolated
volatile stores. Every reader grant must match that case before any read.
It is not a multi-tenant store or a general case-management service. Sending a
case/role/owner query or forwarding header cannot change the grant. A wrong-case
grant is rejected even if its token is valid. Clients cannot choose the source,
tenant or dataset by URL. Default configuration exposes no management evidence.

| Identity / action | Inventory | Alert list/detail | Append | Change/export/activate |
|---|---|---|---|---|
| Viewer, unexpired matching case | Allowed | Denied | Denied | Not implemented |
| Analyst, unexpired matching case | Allowed | Allowed | Denied | Not implemented |
| Producer / decision credential | Denied | Denied | Only its original endpoint | Not implemented |
| Missing/invalid/revoked/expired credential | Denied | Denied | Denied | Not implemented |

Lifetime is capped at 24 hours at startup, with absolute expiry checked on every
request; shorter sessions are recommended. Internal `revoke(identity)` stops
future reads. Revocation/state are not durable across restart. This is explicit
local credential provisioning, **not** OIDC/MFA, browser login or production RBAC.
Use one loopback worker; TLS/service identity and persistent sessions are still
required before shared use. Never put the reader credential in a Vite bundle,
localStorage, URL/query, screenshot, CI log or public `.env` file.

## Read endpoints

| Method / path | Filters | Result |
|---|---|---|
| GET `/v1/inventory` | limit, cursor, method, route, classification | `inventory_page` 1.0 |
| GET `/v1/alerts` | limit, cursor, method, route, finding_class | `alert_page` 1.0 |
| GET `/v1/alerts/{alert_id}` | None | `AlertDetail`, or generic 404 |

Defaults: 25 items, maximum 100 and 256 KiB response. Duplicate/unknown query
keys, non-integer/out-of-range limits, invalid enums or unregistered route filters
reject with 400. Method filters are uppercase, route filters are approved
templates or `/__unknown__`. The routes have no mutation, export, arbitrary
search, raw log, secret, session-management or activation capability.

Inventory aggregates by canonical method/template/classification/contract.
All unknown paths aggregate under `/__unknown__`, never by raw target or token.
Rows include count and last server receipt time. Empty results explicitly retain
`visibility=partial_lab_visibility`; they never claim no vulnerabilities or a
healthy sensor. Missing collector route evidence stays `visibility_unavailable`.

Alerts use server-derived opaque IDs and versioned, fixed rule explanations.
Detail exposes only method/template, rule/reason, candidate class/severity/state,
contract version, server receipt/expiry and minimal status/expected-access fields.
No raw request, query, principal, tenant, owner, event UUID, route fingerprint,
credential or arbitrary evidence text is returned. Denied attempts are not
relabeled as successful disclosure. `review_required` is not Critical severity.

Every response has `mode=monitor_only` and `data_source=volatile_lab_observations`.
These are observations retained by this local prototype, not M6 fixtures and
not proof of live sensor or authoritative context integration. The accepted
schemas are exported by `python -m analytics.schemas` (ten schemas in total).

## Cursor and error semantics

Pagination is stable over a snapshot. An HMAC-authenticated cursor binds the
reader, case, endpoint, filters, limit, offset, snapshot and <=60-second expiry.
Changing identity/filters/limit, tampering or expiry rejects. A changed snapshot
requires restarting pagination (409 `SNAPSHOT_CHANGED`); no silent offset skip.
Rows retain their server expiry even when read. Cursors are not credentials.

401 means missing/invalid/expired/revoked identity; 403 means wrong case or role;
404 is disabled/missing evidence; 400 is invalid query/cursor; 409 is changed
snapshot; 503 is store/access-audit unavailability or response/capacity failure.
Error bodies contain fixed codes, never caller values or exception text.
Successful reads use `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.
There is no cookie auth or state-changing management action. CORS is not opened
globally to make the fixture UI appear integrated; a reviewed backend/session
bridge is required for a shared browser deployment.

## Storage masking and read audit

`analytics.masking.StorageMasker` validates an explicit normalized/audit/access
projection before **every** `MemoryStore.append`. Extra or nested secret fields,
unapproved concrete routes, invalid tokens, unknown reasons/rules and malformed
schemas reject the entire append with `MASKING_REJECTED`; there is no raw-object
or regex-redaction fallback. Known IDs become templates; unknown paths use the
existing keyed normalizer. Storage snapshots deep-copy nested data so a reader
cannot mutate retained evidence. This is validation/minimization, not anonymization.

Allowed reads and authenticated role/case denials append bounded, masked access
records with a purpose-separated keyed reader reference, action and outcome.
Missing/invalid credentials produce bounded server log codes without hashing or
retaining a credential. Full access-audit/store failure returns 503 **before
returning evidence**. No HTTP endpoint exposes the audit store. All these stores
remain volatile, bounded and TTL-purged: durable/tamper-evident audit, encryption
at rest, MFA, backups, legal holds and deletion/restore acceptance are pending.

Run with Uvicorn `--no-access-log`. Do not enable raw URL/body/debug tracing in
the server, proxy or client. The tests suppress only the HTTPX test-client URL
logger when exercising synthetic sensitive query markers, never the service log.

## Member 6 handoff

The inspected M6 branch now contains real UI test files, but its endpoint/alert
data are still fixture arrays. Do not describe its repository-structure checks
as UI coverage or this API as already wired to that dashboard. M6 should validate
these schemas, loading/empty/401/403/409/503 states and safe rendering with actual
results, keeping fixture and local-observation modes visibly separate. Backend
authentication remains mandatory even if a component or button is hidden.
