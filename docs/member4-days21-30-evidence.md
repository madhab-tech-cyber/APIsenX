# Member 4 Days 21–30 engineering handoff

**Date:** 2026-10-22 (Asia/Calcutta). **Branch:** `member4/detection`.
**Implementer:** `madhab-tech-cyber`, continuing the authorized Member 4 takeover.
**Plan:** user-provided Member 4 PDF v1.0, pages 2–3. This completes engineering
task coverage through the planned Day 30, not 30 calendar days, human checkpoint
completion, integration approval or a released security engine.

## Refreshed baseline and credit

Main `71f95f1` includes owner-merged PR #49 and M3 PR #50. PR #49 still has no
submitted review or conversation comment at this snapshot. Issue #48 contains
a real coordination request from `pappukumar96727-sketch`:
[source comment](https://github.com/madhab-tech-cyber/APIsenX/issues/48#issuecomment-6335628520).
That reminder requests named owners, dates and actual evidence; it is credited,
not treated as label/crypto approval, attendance or a completed feedback session.

M3 now implements an explicit local-only Bearer batch client using M4's stricter
64-event/256-KiB bounds, exact ack, freshness and permanent/transient error rules.
[M3 evidence](member3-member4-loopback-evidence-2026-10-21.md) reports 25 Rust tests
and a macOS userspace loopback run. Cargo is unavailable locally in this audit
workspace, so that run is owner-reported here; exact-head GitHub Linux userspace
results are linked on the delivery PR after execution. It is not TLS/shared
acceptance, a Linux sensor or a LAB-REC-1 consumer. Existing M3 CI is preserved.

## Scheduled task mapping

| Day | Engineering delivery | Acceptance boundary |
|---|---|---|
| 21 | Analysis/policy outage and stale lease/config/source/clock tests; no signed fallback allow | Local prototype; no active enforcement or remote resolver timeout claim |
| 22 | Full detection/audit regression, previous corpus and privacy tests | Automated evidence; independent human regression review pending |
| 23 | Explicit typed masking gate before every store append; immutable nested snapshots | Volatile lab stores, not accepted durable restricted persistence |
| 24 | Server-authenticated, case-scoped filtered inventory with bounded signed pagination | M6 schema/browser handoff pending; no live sensor/dashboard claim |
| 25 | Analyst-only alert list/detail, masked evidence and fixed explanations | Viewer denial, expiry/revocation/case checks on backend; not component hiding |
| 26 | Python lint/SAST, real secret scan, dependency audit, API and failure regressions | Actual scoped results below/PR; not repository-history or full supply-chain approval |
| 27 | F30-01 invalid owner context, F30-02 nested snapshot mutation and F30-03 stale lease fixes | Regression evidence; original application policy/list/grant gaps stay explicit |
| 28 | DET-1.2 rule catalog and versioned read/alert schemas | Docs/code ready; independent rule/schema review pending |
| 29 | Frozen, allowlisted deterministic source candidate and hash checks | NOT APPROVED release; no tag, publishing, deployment or secret-bearing artifact |
| 30 | Runnable signed shadow/BOLA/BFLA/audit + protected-read rehearsal and handoff | Automated synthetic demo only; actual human final review/sign-offs pending |

See [management/masking contract](member4-management-contract.md),
[rule catalog](member4-rule-catalog.md), [release checklist](member4-release-checklist.md)
and [review checkpoint record](member4-review-checkpoints.json).

## Repeatable checks

```bash
python -m unittest discover -s tests -v
python -m analytics.evaluate
python -m analytics.review_demo
python -m analytics.final_demo
python -m ruff check analytics tests scripts/check_analytics_secrets.py
python -m bandit -r analytics -q
python scripts/check_analytics_secrets.py
python -m pip_audit -r requirements.txt
python -m analytics.package --check
python -m analytics.package --output /tmp/api-sentinel-analytics-candidate.zip
```

Use a fresh virtual environment and the existing pinned requirements/tools.
Runtime secrets never belong in evidence. The candidate builder uses exclusive
creation: choose a new output filename for each build.

## Actual results

Final checks use a clean Python 3.12/Linux virtual environment with the existing
pinned requirements and Ruff 0.17.1, Bandit 1.8.6, pip-audit 2.10.1 and
detect-secrets 1.5.0. The exact final test/build/scan results and candidate archive
SHA-256 are recorded on the delivery PR, not inferred from a day label.

- New direct API tests exercise missing/wrong-scope/expired/revoked readers,
  viewer denial, wrong case, forged scope filters, bounded paging, signed cursor
  tampering/binding/expiry/snapshot changes and no-store masked detail.
- Hardening tests cover analysis/policy outage, stale source/config/lease, clock
  rollback, malformed owner context, file-boundary digest binding, extra/nested
  secret rejection, deterministic projection and immutable nested snapshots.
- Candidate tests verify the source freeze, byte-identical builds, every packaged
  source hash, exclusive output creation and explicit non-secret input list.
- Automated final rehearsal shows protected inventory paging, three masked
  shadow/BOLA/BFLA candidates, verified dry-run explanations, reader denial and
  explicit monitor-only/release-pending output. It is not a human presentation.
- Initial secret scan flagged only 46 SHA-256 values in the generated hash-only
  manifest. The check now validates every manifest field/hash before excluding
  that exact file from entropy heuristics; source/test/doc scanning remains on.
- Ruff and all-severity Bandit pass. Existing Starlette/httpx deprecation warning
  remains. Python dependency, final source/archive and remote CI results are
  linked after execution; no Rust run is invented on this Cargo-less host.

Final local suite: **230 methods PASS** (114 analytics, 116 pre-existing), with
the previous 34-case corpus unchanged. Ruff, all-severity Bandit, compile/ten
schema exports, JSON/YAML/fences, 41 local links, frozen-source checks and scoped
secret scan pass; project pip-audit reports no known vulnerabilities. Two source
archives are verified byte-identical and their entries match the frozen hashes.
The delivery PR records the final archive checksum and exact-head remote jobs.

LAB-DET-1's 34 self-labelled cases retain TP/TN counts BOLA 5/5, BFLA 7/5,
discovery 2/2 and flow 1/1, with zero FP/FN on this small set and six indeterminate
context cases. It is not held-out, independently labelled or production accuracy.
New unit/HTTP regressions and overlapping demos are not additional traffic samples.

## Remaining ownership and release gate

M1 coordinates real review records and risk gates; the implementer cannot approve
their own work. M5 reviews labels, trusted context and source policy semantics.
M3 jointly accepts shared transport, clocks/replay and future active contracts.
M6 reviews protected management/UI integration and independent privacy/CI proof.
Ask actual owners for dates and responses; a mention or requested review is not
their acceptance. Prior Issues #41/#48 remain dependencies, not auto-closed by
this delivery. No original teammate identity/consent or human review is invented.

Full runtime acceptance, real Days 14/15/22/28/30 reviews, durable privacy/audit,
shared identity/TLS, independent accuracy and performance/route-failure/rollback
evidence remain open. All recommendations are monitor_only/enforce=false;
active rules are zero and release remains held.


## 2026-10-31 Day 22–23 runtime-hardening follow-up (candidate)

**Baseline:** `main` at `6b0b21752dff8bcec2bce77f459a9f9df1e50bc2`. **Source candidate commit:** `aec622af035f825f6e1fb4a94f93469a9e98f9e3`.
This follow-up adds focused regression coverage to the existing Day 22/23
engineering work; it does not replace the historical October 22 test snapshot.

- **Day 22 audit projection:** a deterministic test supplies synthetic raw
  target, query, actor and resource markers to the observation object and
  verifies that the retained audit projection contains none of them.
- **Day 23 typed masking:** recursive JSON serialization failures are now
  converted to the same fixed `MASKING_REJECTED` boundary as other invalid
  projections. A batch regression verifies that a valid first item is not
  partially appended when a later deeply nested item is rejected.
- **Day 23 immutability:** a caller-owned nested alert is mutated after append;
  the stored projection must remain unchanged. The existing snapshot-mutation
  regression remains in place as a separate direction of isolation.

These are deterministic synthetic tests around the existing volatile
`MemoryStore`. They do not establish durable persistence, 90-day retention,
deletion/restore behavior, independent leak review, or integrated sensor-to-
dashboard acceptance. The exact-head PR CI is the validation source for this
candidate; no local test run is claimed.
