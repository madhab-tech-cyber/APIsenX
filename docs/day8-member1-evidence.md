# Day 8 Route-Normalization Acceptance Evidence

**Reviewer:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Review date:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 8 schedule task by defining deterministic,
privacy-safe route-normalization acceptance cases for the Week 2 discovery
handoff.

## Work completed

[`route-normalization-acceptance.md`](route-normalization-acceptance.md) now
defines:

- the current OpenAPI method/template registry and normalized output contract;
- exact method canonicalization and method-drift behavior;
- structural exclusion of query names and values;
- safe classification and keyed aggregation of unknown routes;
- single-pass percent decoding, strict UTF-8 and ambiguous-separator rejection;
- literal, encoded and double-encoded traversal defenses;
- OpenAPI parameter constraints plus raw path, method and segment bounds;
- privacy rules for outputs, logs, metrics and unknown-route fingerprints; and
- 53 unique labelled `RN-*` cases for later conversion into executable
  acceptance tests.

The specification distinguishes invalid observations from undocumented paths
and undocumented methods. It prohibits heuristic template invention and
requires ambiguous contract templates to fail loading deterministically.

## Security and privacy review

The output does not include raw request targets, decoded parameters or query
data. Unknown-route aggregation uses a versioned keyed fingerprint rather than
plain hashing, preventing routine dictionary recovery of predictable paths. Raw
authorization headers, cookies and bodies remain outside the accepted telemetry
schema.

The synthetic strings in the acceptance table are test vectors, not real
identities, credentials or traffic. The document contains no fingerprint key or
runtime evidence.

## Verification

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`:
  **PASS - 26 tests**. These tests protect the existing mock API baseline; they
  do not implement route normalization.
- `python -m compileall -q src mock-api tests`: **PASS**.
- `git diff --check`: **PASS - no whitespace errors**.
- Documentation local-link, required-section, acceptance-ID uniqueness,
  trailing-whitespace and credential-pattern checks: **PASS - no findings**.

## Evidence boundary and result

The Day 8 design acceptance baseline is complete. Route-normalizer code, an
executable `RN-*` corpus, keyed runtime configuration, fuzz/property tests and
producer/consumer acceptance are still pending. Therefore this evidence does
not claim implementation acceptance, integrated discovery, risk closure or
release readiness.
