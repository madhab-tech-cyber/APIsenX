# DET-1.2 rule and alert-schema freeze candidate

**Date:** 2026-10-22 (Asia/Calcutta). **Owner:** Member 4 takeover by
`madhab-tech-cyber`. **State:** unsigned source candidate, independent review
pending. Rule freezing is not release approval or an active-rule lease.

| Rule | Meaning | Candidate class | Maximum behavior |
|---|---|---|---|
| DET-OBS-1 | Expected permitted operation or missing/conflicting context | None | Allow is expected permission only; unavailable produces no signed recommendation |
| DET-SHADOW-1 | Approved contract method/path drift | shadow_candidate | Alert only; observed drift is not proof of reachable vulnerable behavior |
| DET-BOLA-1 | Function allowed, authoritative object policy denies a 2xx lab response | bola_candidate | Dry-run deny recommendation; actual enforcement false |
| DET-BFLA-1 | Active known role lacks explicit function permission but response is 2xx | bfla_candidate | Dry-run deny recommendation, independent of inventory shape |
| DET-FLOW-1 | Distinct permitted successful mutations exceed the scoped lab threshold | flow_candidate | Alert-only heuristic, never a rate limit or proof of abuse |

`DET-1.2` adds a regression fix: a non-string/blank authoritative owner is missing
context, not a cross-owner finding (F30-01). `Snapshot` now deep-copies nested
records (F30-02), and stale source/config cannot refresh its own policy lease
(F30-03). These are engineering findings and fixes, not invented reviewer feedback.
M5 application authorization code is reused and was not changed by this work.
The policy source digest now binds per-file names/hashes across core analytics
and application policy, avoiding ambiguous source-file concatenation (F30-04).

Before recommending, policy/source/config checks compare the startup code digest,
permission map (including current source), contract version and flow profile.
The instance's policy snapshot expires after 300 seconds. Expiry, backward clock,
source/config change, unavailable policy or analysis exception returns 503
without a signature. Reinitialization with explicit reviewed context is required;
recovery does not activate enforcement. Resolvers must be bounded local lookups;
remote call timeouts/worker isolation are not implemented by this prototype.

AP-1.0 authorization, LAB-REC-1 symmetric MAC envelopes, strict request/response
binding, five-second recommendation TTL and monitor_only/enforce=false remain.
Existing DET-1.1 consumers must not silently accept the new frozen code/config;
pin and review the candidate. M3's IF-07 active protocol remains separate.

`analytics.schemas` exports application/collector inputs, alert input, route
result, recommendation request/reply and inventory/alert read schemas. Wire
inputs forbid extra fields and unsafe coercion; read detail uses a masked
projection with fixed explanations. No raw input serialization fallback exists.

LAB-DET-1 remains a **34-case self-labelled engineering set**, not independent
holdout or production validation. Record TP/FP/TN/FN and six indeterminate cases
without counting repeated unit/HTTP checks as independent samples. New context,
privacy, pagination, outage and replay regressions do not enlarge that corpus
or establish real-world precision. Independent M1/M5 labels and acceptance remain.

Remaining gaps: live authoritative provenance, full grant issuer/type and list
semantics, shared TLS/key lifecycle, distributed restart-safe replay, durable
audit, tested workload thresholds, latency/loss, route failure and rollback.
All active rules remain zero; no High residual risk is accepted or closed.
