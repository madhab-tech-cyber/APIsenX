# Member 4 Day 1–10 implementation and evidence index

**Date:** 2026-10-21 (Asia/Calcutta). **Branch:** `member4/detection`.
**Implementer:** `madhab-tech-cyber` (Member 1 taking over unavailable Member 4).
**Source plan:** user-provided `API-Sentinel-Member-4-Python-Detection-Engineer.pdf`,
version 1.0, pages 2–3. The PDF is a responsibility baseline, not independent
authorization to change other components, merge a PR or activate blocking.

The following are ten scheduled **task units implemented in this session**,
not ten calendar workdays or ten fabricated historical commits. Week 1's live
integrated-lab/review acceptance is still pending. No absent member's review,
meeting attendance, consent or contribution is invented.

| Day | Delivered artifact | Executable evidence / remaining boundary |
|---|---|---|
| 1 | Separate analytics service and trust boundaries | [Contract](member4-ingestion-contract.md); mock API untouched |
| 2 | Strict application/collector/batch/alert schemas; normalized result | `python -m analytics.schemas`; unknown fields/types/versions reject |
| 3 | FastAPI app factory, required configuration, aggregate `/health` | Health/configuration tests; no secret defaults or sensitive read APIs |
| 4 | Authenticated, source-scoped event and batch ingestion | Auth before parsing; wrong source, spoofed proxy headers and duplicate auth tests |
| 5 | Bounded minimal in-memory summaries with server retention | Capacity, expiry, idempotency/conflict, atomic batch tests; no durable audit claim |
| 6 | Size/JSON/UTF-8/schema/malformed-event validation | Streaming limits, duplicate keys, NaN, nesting, bounds, time and batch rejection tests |
| 7 | Secret/PII-minimizing projection, generic errors, bounded logs | Synthetic leak-marker tests on success/rejection/backend failure; independent review still requested |
| 8 | Contract-driven route normalizer and keyed unknown tokens | All RN-* acceptance rows, byte/segment boundaries, static precedence, rotation and 1,000 deterministic malformed inputs |
| 9 | Method/template OpenAPI comparison and shadow candidates | Documented vs method drift vs path drift; invalid input excluded; no inference of live served shadow endpoints |
| 10 | Principal-to-object read evaluation using M5 policy | Owner/non-owner, tenant, grant/admin, unknown context and policy parity tests; internal callable, not a live resolver |

## Reproduce

From the repository root, use a virtual environment with `requirements.txt`:

```bash
python -m unittest discover -s tests -p 'test_analytics*.py' -v
python -m unittest discover -s tests -v
python -m ruff check analytics tests scripts/check_analytics_secrets.py
python -m bandit -r analytics -q
python scripts/check_analytics_secrets.py
python -m pip_audit -r requirements.txt
```

Tool versions: Ruff 0.17.1, Bandit 1.8.6, detect-secrets 1.5.0 and pip-audit
2.10.1. See [run instructions](../analytics/README.md) for local startup and
runtime-only secrets. No generated secret or captured runtime payload is evidence.

## Results

Clean virtual-environment installation succeeded with the pinned project
requirements on Python 3.12 / Linux. Actual results:

- Full suite: **157 methods PASS** in 3.321 seconds — 45 analytics methods plus
  112 pre-existing API/policy/contract/governance methods. Test methods contain
  additional RN subcases and 1,000 deterministic malformed-input iterations;
  those iterations are not counted as separate test methods or an accuracy
  benchmark. Existing Starlette/httpx deprecation warning remains.
- Ruff, Bandit (all severities), compile/schema export and `git diff --check`:
  **PASS**. Bandit's initial YAML-load warning was addressed by invoking the
  duplicate-checking SafeLoader directly; no warning suppression was added.
- All 53 RN acceptance IDs map to executable tests; 31 local documentation links,
  fenced blocks and workflow YAML checks pass. The contract hash is recorded in
  the service contract rather than treating an unpinned OpenAPI name as evidence.
- detect-secrets 1.5.0: **zero candidates** in the scoped Member 4 source/tests/
  evidence scan. This is a real secret scanner, not a claim of repository-wide
  history coverage. Source cannot guarantee that deployment logs are configured
  safely; the local runtime configuration was tested separately.
- pip-audit: **no known vulnerabilities found** for the resolved project
  requirements. Its first attempt could not create the read-only default cache;
  rerun with a writable `/tmp` audit cache succeeded. Requirements pin direct
  dependencies; a full transitive lock/SBOM is not added or claimed here.
- Live Uvicorn loopback: health 200 / monitor_only; unauthenticated ingestion
  401; authenticated ingestion and exact event acknowledgement 200; authenticated
  evidence read 404. Demo: owner read allowed, cross-owner 2xx yields only a
  candidate. Captured service logs exclude the synthetic query secret, concrete
  object ID and generated runtime credential. The test process was stopped.

GitHub CI results belong to the exact pushed head and will be linked on the
delivery PR after execution, not inferred from these local checks.

## Remaining review/integration gates

[Issue #41](https://github.com/madhab-tech-cyber/APIsenX/issues/41) tracks actual
reviews and integration acceptance; a merged PR alone must not complete it.

- M1 independent security/policy review cannot be self-approved by this author;
  M3/M5/M6 review is requested on the delivery PR. No review fabricated.
- M3/M4 reconcile stricter limits, clock windows, TLS/auth, retry/ack behavior
  and compiled source compatibility. Actual Rust-to-Python and Linux runs pending.
- M5/M4 accept application-hook provenance and authoritative ownership resolver;
  no raw packets, principal guessing, client role assertions or TLS weakening.
- M6/M4 agree protected inventory/alert APIs later; no live dashboard claims.
- Route failure, correctness/accuracy, performance, rollback and privacy gates
  still block active enforcement. No risk acceptance or Day 11–30 completion.
