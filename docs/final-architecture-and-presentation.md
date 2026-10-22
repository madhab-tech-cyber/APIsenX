# Day 28 Final Architecture, Limitations and Presentation

> Historical October 19 narrative. [Current October 20 closeout](member1-closeout-2026-10-20.md)
> records the now-merged M3 library and later M5 changes. No accepted live
> pipeline, completed human demonstration or release is inferred.

**Recorded:** 2026-10-19. **Owner:** M1. **Main baseline:** `c165964`.

This finalizes the Member 1 architecture narrative for the current evidence
snapshot; it does not assert that the planned engine is implemented. Exact
branch revisions and executed checks are in the [baseline](member1-oct19-verification.md).
Future revisions require a new evidence/release decision, not silent reuse of
this document's conclusions.

## Actual delivery versus intended design

| Boundary | Actual evidence | Acceptance still needed / lead |
|---|---|---|
| Client -> reference API | Main has synthetic customers/admin, opaque public lab tokens, owner checks, explicit admin function gates, field restrictions and matching OpenAPI tests | Full AP-1.0 tenant/share/support/version cases and production-grade identity; M5/M4 |
| API/host -> sensor | M2 design/headers and prerequisite tests only | Approved HTTPS-safe observation point, supported Linux/kernel profile, verifier/capability/bounded event evidence; M2 with M5/M1 |
| Sensor -> collector | Unmerged M3 Rust library, JSON schemas, lock and reported unit/fmt/Clippy/microbenchmark results | Loadable producer and consumer agreement, bounded versioned envelope, request correlation, real receipt/loss/failure results; M2/M3 |
| Collector -> analytics | Proposed flow and M3 batch structures; M4 branch remains scaffold | Authenticated transport, batch/ack/retry/size/version acceptance, executable ingestion and privacy rejection; M3/M4 |
| Analytics -> decisions/storage | Policy specifications and corpus plan | Detector implementation, labelled results, safe normalization, durable masking/audit/retention/triage; M4 |
| Management API -> dashboard | Unmerged M6 React/TypeScript fixture UI and package lock | Agreed M4 contract, server-side authentication/authorization, live-versus-fixture label, UI state/privacy tests and meaningful build CI; M4/M6 |
| Control -> enforcement adapter | ENF/FAIL policies and zero approved active rules | Rule-specific correctness, authenticated fresh decisions, latency/loss, route failures, breaker and rollback demonstration; M3/M4/M6/M1 |

The intended sequence is target observation -> bounded validated event ->
collector -> authenticated analytics ingestion -> normalized inventory and
policy classification -> masked persistence -> authorized management views.
An independently approved, time-limited control path may later return decisions
to an adapter. It is not a synchronous replacement for application authorization.

The [integration register](integration-data-flow.md) is the interface handoff
authority; neither producer-only schemas nor local library tests establish
consumer acceptance. Flow hashes are not yet an accepted per-request correlation
mechanism. Transport/schema mismatches, missing tenants/versions and rejected
events must remain visible as loss/unknown, never healthy zero findings.

## Security and operational boundaries

- Preserve TLS; eBPF does not automatically expose encrypted HTTP paths. Do not
  choose packet decryption or weaker TLS to make the architecture appear live.
- [AP-1.0](authorization-policy.md) defines object/function policy; the lab has
  no approved multi-tenant production authentication. Public fixture tokens
  must stay local and synthetic. Denied requests must not mutate orders.
- [Route normalization](route-normalization-acceptance.md),
  [MASK-LAB-1.0](masking-field-policy.md) and
  [AUDIT-LAB-1.0](audit-retention-and-investigation.md) minimize data before
  output/persistence and require server-side access, expiry and protected audit.
- [LIMIT-LAB-1.0](identity-route-resource-limits.md) defines bounded resource
  budgets; [ENF-1.0](enforcement-approval-and-rollback.md) defines decisions,
  circuit breakers and rollback. These remain unmeasured design limits.
- [FAIL-LAB-1.0](route-failure-policy.md) preserves application authentication
  and authorization on optional monitoring failure. Privileged audit-dependent
  delivery/mutation fails closed; emergency disable must remain possible.
- [UI-RBAC-1.0](dashboard-roles-and-risk-wording.md) separates fixture data,
  unavailable telemetry, suspected findings and confirmed unauthorized access.
  Hiding a React component is not backend access control.

All 13 [risk-register](risk-register.md) entries remain unresolved: 12 High,
one Medium. No independent source/integration approval is supplied by this
documentation. Day 14 attendees/comments and Day 15 responses/sign-offs remain
missing, even though Issue #14 was closed. Branch protection is not enabled in
the observed snapshot. No calendar attendance/compliance claim is made.

## Presentation outline and truthful claims

1. **Problem/scope:** authorized runtime BOLA and shadow API detection is the
   goal; no third-party traffic or production credentials are in scope.
2. **Architecture:** show the table above; distinguish implemented main,
   unmerged libraries/fixtures and missing runtime components.
3. **Available rehearsal:** demonstrate API owner allow/cross-owner denial,
   D11-F01 empty/all-owned/mixed denial, admin allow and unchanged denied writes.
   State clearly that these are reference-API results, not detector alerts.
4. **Policies:** explain route normalization, minimization, route-specific
   failures and monitor-only/zero-rule safety boundaries.
5. **Evidence/limitations:** report 53 test methods and nine diagnostics PASS;
   do not translate these into detection precision, overhead, protected
   dashboard coverage or successful rollback. Show actual CI scope.
6. **Decision/handover:** show unresolved owner assignments and the release
   hold; collect real reviewer questions, owner responses and independent
   sign-offs before claiming a completed human/integrated demonstration.

No mentor/team attendees, presentation date, recording or audience approval are
invented. The final review date and conflicting handbook calendar requirements
still need mentor confirmation. [Issue #23](https://github.com/madhab-tech-cyber/APIsenX/issues/23)
is the coordination record, not a completed-demo certificate.
