# Operating Guide

**Owner:** Member 6 (DevSecOps). **Reviewer:** Member 1. **Scope:** running
and verifying the APIsenX lab stack on `main`. **Release state:** NOT
APPROVED. AP-1.0 is `monitor_only` with zero active enforcement rules;
nothing in this guide changes that.

## Running the stack

The lab stack is `docker-compose.yml` (mock API + analytics + dashboard).
The Rust collector is a tested library, not a deployed daemon, and the
eBPF sensor runs on a Linux host — neither is a compose service. All
services publish on host loopback only.

```sh
export APISENTINEL_INGEST_TOKEN=<lab-only value>
export APISENTINEL_HMAC_KEY=<lab-only value>
# optional: APISENTINEL_SOURCE_ID (default lab_application),
#           APISENTINEL_KEY_VERSION (default lab-v1)
docker compose up --build
```

| Service | Host address | Notes |
|---|---|---|
| Mock API (Member 5) | `127.0.0.1:8000` | uvicorn, `docker/Dockerfile.mock-api` |
| Analytics (Member 4) | `127.0.0.1:8001` | uvicorn, `docker/Dockerfile.analytics` |
| Dashboard (Member 6) | `127.0.0.1:3000` | Vite build served by nginx, `docker/Dockerfile.dashboard` |
| Collector (Member 3) | — | build/test image only: `docker build -f docker/Dockerfile.collector .` |

No secret is baked into any image. Analytics fails to start if
`APISENTINEL_INGEST_TOKEN` or `APISENTINEL_HMAC_KEY` is unset. Never
commit lab credentials, populated `.env` files, or keys (see
`docs/data-classification-policy.md`).

Dashboard-only development (no compose):

```sh
npm --prefix dashboard ci
npm --prefix dashboard run dev
```

## Security and quality gates

Four workflows run in CI:

| Workflow | What it covers |
|---|---|
| `mock-api-tests.yml` → job **API Security and Quality Gates** | BOM guard, ruff, bandit SAST (mock-api + src), pip-audit, full Python test suite |
| `analytics-tests.yml` → job **Analytics Security and Quality Gates** | BOM guard, full test suite, frozen-candidate verification, bandit (analytics), Member 4 secret scan, pip-audit |
| `ci.yml` | repository-check (BOM guard, forbidden-sensitive-file scan, structure), python-tests, dashboard-check (eslint, vitest, build, `npm audit --audit-level=high`, dashboard SBOM generation + validation), container-security (Trivy) |
| `member3-loopback-integration.yml` → job **Rust/Python Loopback Contract** | `cargo test --locked --all-targets`, `cargo fmt --check`, clippy with `-D warnings`, then the Python loopback handoff check |

### What green does and does not mean

- The two **Quality Gates** jobs above are the required status checks for
  `main` (see branch protection below). Green means those jobs passed on
  that commit — nothing more.
- A local pass does not establish remote workflow success, branch
  protection, production readiness, or release approval.
- **The Trivy container scan is record-only.** The `container-security`
  job scans the built dashboard image for HIGH/CRITICAL vulnerabilities
  and secrets with `exit-code: '0'` and uploads the JSON report as a
  30-day artifact. A passing job is **not** proof that the image has no
  findings. Review the report and record remediation or an explicitly
  accepted risk before any release. Whether Trivy becomes a blocking
  (enforcing) check is a human decision that has not been taken.
- **Not in CI today:** IaC scanning of the Dockerfiles/compose file and
  licence scanning. A ready-to-paste proposal is saved at
  `docs/ci-scan-additions-proposed.yml`; it takes effect only when a
  human pastes it into `.github/workflows/` through the GitHub web UI
  (the Muse GitHub App cannot push workflow files).

## Branch protection (verified facts)

Classic branch protection rule **86053320** on `main`: pull request
required, 1 approval, stale approvals dismissed, required status checks =
**API Security and Quality Gates** and **Analytics Security and Quality
Gates**. Verified by Branch API readback on 2026-11-09; the readback is
recorded in `docs/member1-checkpoints.json` (`protection_observation`,
with the rule URL as `readback_reference`).

Governance bookkeeping can be checked locally at any time:

```sh
python scripts/check_member1_governance.py
```

The guard verifies internal consistency only; it does not verify human
evidence, live issue states, or protection settings.

## SBOM

`sbom.cdx.json` (repository root) is the CycloneDX 1.5 bill of materials
covering PyPI (`requirements*.txt`), crates.io (`collector/Cargo.lock`),
and npm (`dashboard/package-lock.json`). Regenerate after any lockfile
change:

```sh
python scripts/generate_sbom.py
```

The BOM guard (`scripts/check_no_bom.py`) runs inside `ci.yml` **and**
both required Quality Gates, so an out-of-sync or BOM-contaminated change
blocks merge. CI also generates and validates a dashboard-scoped SBOM per
run (uploaded as a 30-day artifact), and the analytics release candidate
carries its own lock + SBOM under `analytics/` (Member 4).

## Incidents

This project does not have a separate incident process. If secret or
prohibited data enters the repository or pipeline, follow the incident
procedure in **`docs/data-classification-policy.md` §8 (Detection and
incident response)** — stop collection, notify Member 1 through the
private security channel, rotate exposed credentials without copying them
into tickets or chat, preserve only minimal masked evidence, and record
remediation, owners, deadlines, and residual risk. Do not publicly
disclose the sensitive value while reporting or correcting the incident.

## Release posture

The release remains **NOT APPROVED**. The governance guard still lists
the Day 14, Day 15, and Day 30 human checkpoints, integrated acceptance,
and the authorized release decision as PENDING. Green CI, a merged PR, or
this guide do not substitute for those human records.
