# Analytics 0.1.0-lab-candidate — release HOLD

**Date:** 2026-10-22 (Asia/Calcutta). **Implementer:** `madhab-tech-cyber`.
This is a frozen reproducible **source candidate**, not a GitHub release, package
publication, signed build attestation, production deployment or activation lease.

## Build / verify

```bash
python -m analytics.package --check
python -m analytics.package --output /tmp/api-sentinel-analytics-candidate.zip
```

The output must be outside the repository and must not already exist. The builder
never overwrites an existing artifact. It includes only an explicit source/test/
synthetic-fixture/document list; no environment files, runtime logs, captures,
keys or arbitrary untracked files. `analytics/release-candidate.json` records
each source SHA-256 and the DET-1.2 rule digest. An input change fails verification.
The manifest is source-controlled review material, not an independent signature.
The secret check first verifies all its fields/source hashes, then excludes only
this hash-only file from entropy heuristics; its 46 SHA-256 values are not
credentials. Source/tests/documents remain under the actual secret scanner.

ZIP ordering, timestamps and file modes are fixed. Two builds in the tested
environment must be byte-identical, and every archived source hash must match.
This proves archive reproducibility, not a reproducible Python dependency
environment: direct requirements are pinned, but a transitive lock/SBOM and
cross-platform build acceptance remain pending. Do not commit the generated ZIP.

Extraction is not automatic and this tool does not execute or install its output.
To exercise the repository's final synthetic rehearsal, use:

```bash
python -m analytics.evaluate
python -m analytics.final_demo
```

The demo verifies protected inventory paging, masked shadow/BOLA/BFLA detail,
signed dry-run explanations and denial of an unauthenticated read. It uses
runtime-generated credentials and an explicitly synthetic in-process resolver.
It is not a Linux sensor, shared dashboard or human final presentation.

## Actual acceptance still required

- [ ] Real Day 14 attendees/comments/sign-offs and Day 15 feedback/dispositions.
- [ ] Independent Day 22 regression and Day 28 rule/schema review.
- [ ] Independent labels/held-out accuracy and accepted authoritative event,
  principal, resource, response and policy provenance with M5/M1.
- [ ] Shared-deployment M3/M4 identity, TLS, clocks, retries and replay acceptance;
  active IF-07 remains unimplemented. Credit the new local-only Rust batch handoff.
- [ ] M6 management/browser integration, backend authorization bypass/expiry/
  cross-scope proof, fixture-vs-observation labeling and UI-state/privacy results.
- [ ] Durable restricted audit/storage, read audit, encryption, session/MFA/key
  lifecycle, deletion/restore/backup proof and incident handling acceptance.
- [ ] Rule-specific correctness, legitimate-load/performance/loss, route-failure,
  rollback and emergency-disable evidence satisfying the documented gates.
- [ ] Real Day 30 human demonstration, named reviewer responses, independent
  sign-offs and a repository-owner release decision.

Passing CI, a frozen manifest, policy MAC or merged PR does not fill these boxes.
No missing approval is inferred from a teammate reminder or absent response.
Observe-only operation, zero active rules and release held remain mandatory.
