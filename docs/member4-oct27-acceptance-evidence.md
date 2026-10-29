# Member 4 acceptance and protected-read handoff evidence

**Date:** 2026-10-27 (Asia/Calcutta). **Implementer:** `madhab-tech-cyber`,
continuing the user-authorized takeover. **Branch:** `member4/detection`.
**Refreshed main:** `5f10593a294c68a2729f2c4072c4c4ffa5814f19`.

Engineering tasks through planned Day 30 are implemented; independent human,
shared-runtime and release acceptance are NOT complete. These are task labels,
not separate calendar workdays. This correction finishes evidence validation
and receiver-to-protected-read regressions; it does not fabricate a meeting,
labels, teammate response, durable deployment or independent reviewer decision.

## New executable acceptance boundary

```bash
python -m analytics.acceptance
python -m analytics.acceptance --require-accepted
python -m unittest tests.test_analytics_acceptance tests.test_analytics_handoff -v
```

The checker validates the frozen source and schema-v2 review register, DET-1.2,
current contract/rule-source digests, exact prepared candidate SHA, zero active
rules and monitor-only/source-candidate posture. It distinguishes five human
checkpoints (14/15/22/28/30) from seven independent integration gates. Default
exit 0 means bookkeeping consistency only. Strict exit 2 means acceptance is
still pending. CI runs consistency validation, not a forged acceptance result.

Verified gates require linked evidence and an independent exact-revision/digest
approval with timezone-aware submission time. Self/case-changed/decorated login,
requested rather than submitted approval, stale candidate/contract/source,
foreign evidence, missing gate and incomplete earlier checkpoint are rejected.
Even a synthetic all-complete validator fixture cannot enable rules or release.
This is not remote-authorship verification: a reviewer must personally post
their own record. Review the actual new PR head; update the prepared candidate
and recompute the freeze before recording any later accepted evidence. Old
delivery/base-SHA reviews cannot silently approve a later candidate.

## New receiver-to-read regressions

Four synthetic ASGI HTTP tests exercise collector_event 1.1 / collector_batch
1.0 into the actual M4 endpoints and protected management reader:

- Exact two-field Member 3-compatible ack; same-batch retry is idempotent and
  inventory counts do not inflate. Event IDs, sequence/source fields and reader
  tokens are excluded from inventory; ingestion credential cannot read evidence.
- Missing route/ambiguous correlation remains `visibility_unavailable` and
  `partial_lab_visibility`, not a documented route, healthy zero or inferred
  BOLA decision. No trusted principal/resource identity is invented.
- One unapproved concrete template rejects the complete batch before any visible
  write and does not echo the synthetic private marker.
- Conflicting event retry returns 409; retry after the two-second telemetry age
  returns 422; previously accepted observation counts remain unchanged.

These use synthetic wire envelopes and in-process HTTP, not a new Linux sensor,
Rust sender run, browser handoff or production/shared transport. Existing M3
Linux loopback CI is preserved and runs on the correction because analytics
changes match its paths. Cargo is absent locally; no local Rust result is invented.

## Existing evidence credited without overstatement

Merged PRs #42/#49/#53 supply strict ingestion/normalization, ownership/function
evaluation, the 34-case self-labelled LAB-DET-1 set, signed monitor-only
recommendations, strict pre-storage masking, volatile audit, protected paginated
inventory/alerts and deterministic source candidate. The prior registry incorrectly
called PR #49 the latest delivery; it now records owner-merged #53 with no
formal independent approval inferred. Closed #41/#48/#56/#57/#61 are historical
trackers, not completed acceptance; real M5 coordination comments stay credited.

Main's newer M5 API caps, local load CI and Day 20/21 policy-contract tests are
preserved. Documentation-contract checks are not runtime route-failure proof.
The [PostgreSQL audit design](day20-durable-audit-storage-design-proposal.md) and
[approval template](day20-storage-approval-record-template.md) require actual
service-owner hosting/key/role/checkpoint/backup decisions and independent review
before durable implementation/deployment. This work does not silently approve
those choices or add a fallback disk spool. Open #83 tracks that dependency.

## Checks and remaining gates

New acceptance/handoff suite: **16 methods**. Final full-suite, lint,
static/secret/dependency, source-freeze and exact-head CI results are recorded
on the delivery PR after execution. The source allowlist now includes the checker,
new tests and this evidence; the manifest is deliberately regenerated for review,
not treated as an independent signature. No archive/tag/release is published.

Independent labels/600-case MRVP holdout, trusted live context, shared transport,
durable restricted audit, authenticated M6 browser handoff, full-system paired
performance/route-failure/rollback, human reviews and final decision remain open.
The 34 self-labelled examples and overlapping unit tests cannot fill those gates.
Public candidate metadata uses a full commit URL and typed `sha256:` digest,
both checked against their strict formats/source. Initial entropy warnings for
two untyped public identifiers were resolved without a new scanner exclusion.
No due dates or reviewer commitments are invented. M1 implements M4 and cannot
independently approve that implementation. Monitor-only, zero active rules,
release **NOT APPROVED**.
