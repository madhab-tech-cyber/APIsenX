# Day 21 — API/Sentinel observation adapter

## Scope and safety boundary

The mock API now has an optional outbound observation adapter. When configured,
the API sends a minimized event to the local Sentinel analytics ingestion API
after the API request has completed.

This is **monitor-only telemetry**. The adapter:
- sends only the matched route template, HTTP method, status code, timestamp,
  event ID and configured source ID;
- never sends raw URL paths, query strings, request/response bodies, bearer
  credentials, or user identity;
- uses a loopback-only HTTP endpoint and a bounded request timeout;
- does not follow redirects;
- treats Sentinel errors/timeouts as telemetry delivery failures and does not
  change the API response;
- never consumes a recommendation or authorizes, denies, or mutates API work.

The existing API authentication, authorization, tenant checks, validation and
mutation controls remain authoritative and execute independently of Sentinel.

## Local lab configuration

Configure all three variables in the API process environment:

- \`APISENTINEL_URL=http://127.0.0.1:9000\`
- \`APISENTINEL_INGEST_TOKEN=<separate runtime ingest credential>\`
- \`APISENTINEL_SOURCE_ID=mock_api\`

The configured source ID must satisfy the analytics \`SourceID\` schema and must
match the analytics service's configured \`APISENTINEL_SOURCE_ID\`. The ingest
credential must be the same secret configured for the analytics service.
Do not commit these values. If all three variables are absent, the adapter is
disabled. Partial configuration prevents the API process from starting rather
than silently operating with a broken integration.

The adapter only accepts loopback HTTP endpoints. This is a local lab
integration, not a production transport or deployment recommendation.

## Failure behavior

| Condition | Behavior |
|---|---|
| Sentinel returns accepted response | API response is unchanged |
| Sentinel connection refused | API response is unchanged; safe failure counter/log outcome |
| Sentinel times out | API response is unchanged; delivery stops within configured bound |
| Invalid route/status metadata | Event is not sent |
| Sentinel returns non-200 | API response is unchanged |

## Remaining integration acceptance

This adapter intentionally does not implement an enforcement circuit breaker.
It does not consume signed recommendations, block reads, block PATCH, or claim
durable audit. The existing analytics store is still volatile \`MemoryStore\`.
Route-specific enforcement outage semantics, durable storage, operational
monitoring, human demonstration and independent/service-owner acceptance
remain separate release blockers.

Release state remains \`monitor_only\`, zero active enforcement rules, and
\`release_approved=false\`.
