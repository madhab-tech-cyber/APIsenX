# Member 4 Days 1–10: service boundaries and proposed contracts

Implemented on 2026-10-21 (Asia/Calcutta), against main `d20e2f4`.
Implementation owner: `madhab-tech-cyber`, taking over Member 4 at the user's
request. This does not attribute work or consent to the unavailable teammate.
Contracts remain proposed for independent M1/M3/M5/M6 review. Monitor-only;
no traffic-control adapter, active rule, live sensor or release approval.

## Boundaries (Day 1)

`analytics.app:create_app` is a separate FastAPI service on loopback port 8001,
not the mock application on 8000. The only public endpoint is aggregate
`GET /health`. All other paths require one exact Bearer credential. The sole
configured producer may append only under its configured `source_id`; it cannot
read/export/change evidence. No HTTP inventory/alert/detail API is implemented
yet, so no UI hiding is used as access control. CORS and forwarded identity
headers are not trusted. Health is liveness, not proof of capture or persistence.

Runtime credentials are required, randomly generated and never fixture tokens.
This is a local lab boundary: **HTTP is permitted only on loopback**. Shared
deployment requires reviewed TLS/service identity, token provisioning, expiry,
rotation, ingress rate limits and access audit. No mTLS certificate/proxy-header
authentication or production identity-provider integration is claimed.

## Inputs and schemas (Days 2–4)

Authoritative Python models: [models.py](../analytics/models.py). Generate their
JSON schemas, including the normalized route result, with:

```bash
python -m analytics.schemas
```

All input models forbid additional fields and coercion, require offset-aware
timestamps and UUID event IDs, and reject unknown versions. Strict JSON rejects
duplicate keys, nonfinite values, malformed UTF-8 and excessive nesting. JSON
errors never echo Pydantic input values or exceptions. No headers, bodies,
cookies, IPs, principal/role/tenant/owner assertions or arbitrary diagnostics
are allowed event fields. `schema_name` separates the two observation boundaries:

| Endpoint | Schema / fields | Result |
|---|---|---|
| `POST /v1/events` | `application_event` 1.0: event_id, source_id, observed_at, method, request_target, status_code | `accepted_event_ids` only |
| `POST /v1/batches` | `collector_batch` 1.0: batch_id, created_at, events of collector_event 1.1 | Exact `batch_id`, `accepted_event_ids` acknowledgement compatible with M3's structural parser |

Application targets exist only in bounded request memory for normalization;
they are not retained, echoed or logged. This endpoint is a **candidate**
application-observation contract, not already wired to M5's logging hook.
It accepts synthetic authorized-lab traffic only.

The receiver uses M3's existing collector field names and preserves event IDs
on retries. Event correlation remains null/ambiguous/unsupported, as proposed;
it never treats a flow hint as an authenticated principal or request. Route
markers labelled `approved_template` must exactly equal a registered template;
concrete/unapproved paths reject atomically. A missing route or insufficient
operation evidence is recorded as `visibility_unavailable`, not shadow or BOLA.

### Limits and failure semantics

- 4 KiB application event and individual collector event; 64 events and 256 KiB
  per batch. These enforce the stricter M1 LIMIT-LAB-1.0 profile. M3 currently
  permits 256 events / 1 MiB: those larger batches deliberately reject here.
- At most four in-flight requests, one-second body-read timeout, no compression,
  streaming byte limit even without Content-Length. Declared/actual lengths
  must agree; authentication precedes parsing. Concurrent overload returns 503.
- Event and batch timestamps must be within two seconds old / one second future
  of receiver UTC. Retries do not extend the telemetry age. Clock alignment and
  network overhead require joint measurement; no throughput/RSS guarantee.
- Invalid auth → 401; wrong source → 403; malformed JSON → 400; oversized → 413;
  unsupported media/encoding → 415; invalid schema/time/route → 422;
  changed semantic event under an existing ID → 409; full/unavailable store → 503.
- Whole-batch preflight precedes append under a lock. A rejected event cannot
  produce partial acknowledgement or mutation. Safe retries are idempotent.
  Batch IDs are acknowledgement references, not a durable replay ledger.

M3's current client authenticates with mTLS but does not attach this Bearer
credential. **No end-to-end transport compatibility is claimed.** Agree either
an authenticated mTLS termination/identity adapter or a reviewed sender change;
do not trust caller-supplied `X-Client-Cert` or weaken TLS as a workaround.

## Minimal storage and privacy (Days 5–7)

Only masked semantic summaries are stored: canonical method/template,
classification/reason, pinned contract version, optional status and minimized
candidate alert. A domain-separated keyed digest supports idempotency without
retaining original targets or queries. IDs and unknown-route tokens remain
Restricted, not anonymous. `received_at` and `expires_at` are server assigned.
No caller-specified retention override exists.

Storage is bounded **process memory**, default 1,000 summaries / 300 seconds;
hard configuration caps are 10,000 summaries / seven days. A one-second lifespan
sweeper and every read/write purge expired records. A retry does not extend
expiry; capacity rejects rather than silently evicting live evidence. Restart
loses rows and dedup state. There is no disk spool, database, backup, export,
durable audit or accepted encryption-at-rest/delete/restore mechanism. OS swap,
crash dumps and external logging must be controlled before shared use.

Logs contain fixed outcome codes only; no route, source, event ID, token or raw
exception. There is no metrics exporter/high-cardinality label set yet. Start
Uvicorn with `--no-access-log`; do not enable HTTPX/debug/body tracing in a shared
runtime. Tests use synthetic leak markers across success, validation, malformed
path, unknown path, schema failure and backend exception paths.

## Discovery and ownership (Days 8–10)

The normalizer implements [RN acceptance](route-normalization-acceptance.md),
including every RN-* row and deterministic seeded malformed-input exercises.
It compiles the **current** contract, including M5's added `/support/orders`,
and pins the exact OpenAPI bytes by SHA-256. Supported parameter schemas are
bounded strings with the reviewed ASCII ID pattern. Unsupported patterns/types,
ambiguous overlapping templates, unversioned contracts and duplicate YAML keys
fail loading. Never evaluate arbitrary contract regexes against traffic.

Tested contract SHA-256:
`f6d2ddd0e2474be18cab0ccff7c61e4ea61d4bb19024e8896c3e2e256841a48b`.

Unknown paths use domain-separated HMAC-SHA-256 plus a non-secret key version;
queries are excluded. Unknown methods and paths remain distinct classifications;
candidate drift findings do not establish a served shadow API or exploit.

`OwnershipEvaluator` performs read-only `orders:read` evaluation through M5's
existing `AP-1.0` policy and server-resolved synthetic users/orders/grants.
Ownership does not bypass tenant isolation, permissions, expiry or sharing
rules. Allowed owner/share/admin reads do not create BOLA findings; denied
403/404 responses are prevented attempts, not successful exploitation. A known
unauthorized read with authoritative 2xx evidence produces a monitor-only
`bola_candidate`, never a block. Missing/unknown/conflicting context and source
outages are unavailable, not proof of attack.

This evaluator is an **internal callable**, tested against M5 fixtures, not
connected to ingress: the accepted collector has no authenticated subject/object
context. A jointly accepted authoritative resolver and correlation contract is
required before live BOLA findings. Ingestion rejects spoofed context fields
rather than guessing owners from paths. BFLA rules, signed decisions, replay
controls for decisions, accuracy benchmarking, business-flow rules and dashboard
read APIs remain Days 11–30, not completed by this delivery.

Reusing the current application read policy avoids inventing a second permission
table; parity tests do not certify every AP-1.0 requirement or grant issuer/type
validation. The authoritative policy's remaining gaps require M5/M1 review
before live detection acceptance.
