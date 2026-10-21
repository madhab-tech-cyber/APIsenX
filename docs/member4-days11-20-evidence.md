# Member 4 Days 11–20 delivery and acceptance evidence

**Date:** 2026-10-21 (Asia/Calcutta). **Branch:** `member4/detection`.
**Implementer:** `madhab-tech-cyber`, continuing the user-authorized takeover.
**Source:** Member 4 PDF version 1.0, pages 2–3. Days are scheduled task units,
not ten separate calendar workdays or fabricated historical commits.

## Fresh evidence before continuation

Main `7efee11` includes owner-merged PR #42 and subsequent M5 regression work.
PR #42 has **zero submitted reviews and zero comments** at this snapshot.
Issue #41 remains open with one agent-produced delivery update, not independent
reviewer feedback. Existing work is retained by normal branch synchronization;
no main push, force push, PR merge or administrative change is part of this task.

## Task/evidence mapping

| Day | Implemented engineering artifact | Acceptance state |
|---|---|---|
| 11 | Permission-aware function checks and BFLA candidates; inventory-shape regressions | Local implementation; live authoritative context and independent M5/M1 acceptance pending |
| 12 | Missing/inactive identity, changed/encoded IDs, traversal, policy/context-conflict regressions | Automated tests; no client-supplied identity trusted |
| 13 | Versioned self-labelled corpus, per-category TP/FP/TN/FN, precision/recall/FPR and explicit indeterminate counts | Engineering smoke measurement only; independent labels/holdout/acceptance absent |
| 14 | Runnable masked shadow/BOLA/BFLA and signed-recommendation demo | Automated demo executed; **human demonstration/attendees/comments/sign-offs pending** |
| 15 | Conservative context handling and flow-retry/idempotency regressions | Engineering tuning implemented; **actual external feedback and its dispositions pending** |
| 16 | Signed AP/rule/contract/source/config snapshot, deterministic reason/rule explanations | Proposed lab symmetric-MAC contract, not approved active policy |
| 17 | Explicit allow/alert/deny recommendations, always monitor_only/enforce=false | Dry-run only; cannot alter traffic or authorize an active rule |
| 18 | Separate credential, source resolver, timestamp/nonce binding, MAC/target verification and bounded anti-replay | Single-process volatile prototype; TLS/distributed restart-safe acceptance pending |
| 19 | Tenant/subject-scoped, deduplicated mutation-burst heuristic with bounds/expiry | Alert-only local heuristic; no rate limit, proven abuse or workload threshold approval |
| 20 | Minimal masked structured audit with rule IDs, server TTL and append-failure handling | Volatile prototype; durable audit/privacy/management integration pending |

See [detailed contract](member4-recommendation-contract.md) and
[human checkpoint record](member4-review-checkpoints.json). Days 14–15 cannot
be called complete without actual human evidence supplied by the participants.
This delivery does not complete Days 21–30 or approve the project for release.
[Issue #48](https://github.com/madhab-tech-cyber/APIsenX/issues/48) tracks the
actual human, protocol and label-acceptance work; it is not auto-closed by delivery.

## Repeatable commands

Use the repository virtual environment and pinned requirements/tools documented
in [analytics README](../analytics/README.md):

```bash
python -m unittest discover -s tests -v
python -m analytics.evaluate
python -m analytics.review_demo
python -m ruff check analytics tests scripts/check_analytics_secrets.py
python -m bandit -r analytics -q
python scripts/check_analytics_secrets.py
python -m pip_audit -r requirements.txt
python -m analytics.schemas
```

## Corpus results and their limits

LAB-DET-1 contains 34 self-labelled synthetic cases. None was independently
labelled or held out for external validation. The measured engineering set:

| Category | TP | FP | TN | FN | Indeterminate | Total |
|---|---|---|---|---|---|---|
| BOLA | 5 | 0 | 5 | 0 | 0 | 10 |
| BFLA | 7 | 0 | 5 | 0 | 0 | 12 |
| Discovery | 2 | 0 | 2 | 0 | 0 | 4 |
| Flow | 1 | 0 | 1 | 0 | 0 | 2 |
| Context failure | 0 | 0 | 0 | 0 | 6 | 6 |

Precision/recall on each small determinate category is 1.0 and FPR is 0.0;
context category denominators are zero and report `null`/N/A, never 100%.
These figures describe only this self-labelled corpus, **not real-world or
accepted detector accuracy**. Different/wrong-class results count as missed
and spurious findings; known-positive unavailable results count as FN plus
indeterminate. Unavailable negatives are reported separately, never as TN.
Overlapping unit/HTTP cases are not additional independent traffic samples.
All fixtures reset per case; the suite verifies the originals are not mutated.

## Executed checks

Final local checks on Python 3.12/Linux with the pinned project requirements:

- **197 unittest methods PASS** in 5.247 seconds: 81 analytics methods and 116
  existing application/policy/contract/governance methods. The 34 corpus rows and
  prior 1,000 malformed-input iterations are subcases, not extra test methods.
- **Ruff PASS**, **Bandit all-severity scan PASS**, scoped **detect-secrets zero
  candidates**, and **pip-audit no known project dependency vulnerabilities**.
  Source scan now includes the corpus and all Member 4 documents. This is not
  repository-history scanning, independent source approval or a transitive lock.
- Compile, seven schema exports, workflow YAML, JSON/checkpoint records, 29 local
  links, fenced blocks and `git diff --check`: **PASS**.
- `analytics.evaluate`: the exact counts above, zero mismatched case IDs;
  `analytics.review_demo`: owner allow, object/function deny recommendations,
  shadow alert, verified signatures and four masked volatile audit records.
  All results explicitly print monitor-only and that no human review occurred.
- Existing Starlette/httpx deprecation warning remains. Runtime TLS/key service,
  multiple-worker replay persistence, actual Rust consumer compatibility and
  live principal provenance are not exercised or accepted by these results.
- Live Uvicorn loopback boundary: health 200; unauthenticated and ingest-scoped
  recommendation calls 401; forged actor context 422; no resolver 503; replayed
  nonce 409. Synthetic secret and both generated credentials are absent from
  captured process logs. The test server was stopped after verification.

Remote CI is linked to the exact pushed head in the delivery PR after execution;
local success alone does not establish a green remote run.

## Remaining gates / coordination

- M3: accept or revise LAB-REC-1 and IF-04 transport/limits; M3 does not consume
  this new signed reply. No Linux/mTLS/Rust-to-Python integration test is claimed.
- M5: confirm trusted event/principal/object/status provenance and review function
  and object policy semantics, grant/list gaps and the self-labelled corpus.
- M6: independent CI/privacy evidence and future protected management APIs; no
  live dashboard connection or component-hiding access control is claimed.
- M1 plus independent reviewers: real Days 14/15 meeting/comments/responses and
  sign-offs, accepted rule thresholds/accuracy, privacy/performance/route-failure/
  rollback evidence. The author cannot independently approve their own work.
- Issue #41's previous dependencies remain open. No risk rating or owner closure
  is silently changed. Monitor-only, zero active rules and release hold remain.
