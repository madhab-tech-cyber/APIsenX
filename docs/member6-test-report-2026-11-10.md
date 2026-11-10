# Member 6 Consolidated Test Report — 2026-11-10

**Owner:** Member 6 (QA / DevSecOps). **Baseline:** `main`
`c69153a0e693d03c75f02c090ff16e71540373d9` ("Merge pull request #150 from
madhab-tech-cyber/member2/evidence-completion").
**Method:** every number below was either run locally on 2026-11-10
against this exact tree (marked **ran locally**) or is a GitHub Actions
result for this exact SHA (marked **CI evidence**). Nothing else is
claimed. **Release state:** NOT APPROVED; AP-1.0 `monitor_only`.

## Results summary

| Suite | Result | Source |
|---|---|---|
| Python full suite (pytest) | **492 passed, 5 skipped, 492 subtests passed** (19.4 s) | ran locally |
| Dashboard suite (vitest) | **12 passed, 5 test files**; production build succeeds; ESLint clean | ran locally |
| Rust collector (cargo test, fmt, clippy) | job **SUCCESS** on this SHA | CI evidence |
| Ruff (repo-wide) | clean | ran locally |
| Member 1 governance guard | **PASS** (exit 0); 5 human items PENDING (below) | ran locally |

## Python suite — ran locally

```sh
python3 -m venv /tmp/auditenv  # + requirements.txt, pytest 9.2.0, ruff, pyyaml
PYTHONPATH=$PWD /tmp/auditenv/bin/pytest -q
# 492 passed, 5 skipped, 1 warning, 492 subtests passed in 19.36s
```

The 5 skips are all in `tests/integration/postgres/test_postgres_roles.py`.
They require psycopg, a disposable PostgreSQL database, and the four
role DSNs of the approved audit-store environment, which is gated on
Issue #83's implementation authorization. They are skipped by design in
this environment, not failing.

## Dashboard suite — ran locally

Run in a layout-faithful scratch copy (`dashboard/` + `docs/` siblings,
because the app imports `docs/owasp-api-security-mapping.json` via a
relative path):

```sh
npm ci && npm test        # Test Files 5 passed (5); Tests 12 passed (12)
npm run build             # succeeds
npx eslint .              # clean
```

## CI evidence for this exact SHA

Check runs recorded for the push to `c69153a` (2026-11-10 06:50–06:51 UTC),
all **completed / success**:

- **API Security and Quality Gates** (`mock-api-tests.yml`)
- **Analytics Security and Quality Gates** (`analytics-tests.yml`)
- **Rust/Python Loopback Contract** (`member3-loopback-integration.yml`) —
  this is the Rust evidence for this SHA: `cargo test --locked
  --all-targets`, `cargo fmt --check`, clippy with `-D warnings`, plus
  the Python loopback handoff check. Rust was not compiled locally for
  this report (no cargo toolchain in the local environment).

## Governance guard — ran locally

```sh
python scripts/check_member1_governance.py
# PASS: Member 1 checkpoint bookkeeping is internally consistent.
# PENDING: Day 14 human checkpoint
# PENDING: Day 15 human checkpoint
# PENDING: Day 30 human checkpoint
# PENDING: integrated acceptance
# PENDING: authorized release decision
```

The guard verifies bookkeeping consistency only; the PENDING lines are
human records, not test failures.

## Scans inventory (what CI runs today)

From the four workflow files on this baseline:

- **BOM guard** — `scripts/check_no_bom.py` in `ci.yml` and both required
  Quality Gates.
- **Forbidden sensitive-file scan** — `.env*`, `*.pem`, `*.key`, `*.p12`,
  `*.pfx` rejected in `ci.yml` repository-check.
- **SAST** — bandit over `mock-api` + `src` (API gates) and over
  `analytics` (Analytics gates).
- **Dependency audit** — `pip-audit -r requirements.txt` in both Quality
  Gates; `npm audit --audit-level=high` for the dashboard.
- **Secret scan (analytics scope)** — `scripts/check_analytics_secrets.py`
  in the Analytics gates.
- **SBOM** — repository SBOM validated by regeneration
  (`scripts/generate_sbom.py`, CycloneDX, 406 components); dashboard
  SBOM generated and format-validated per CI run.
- **Container scan** — Trivy over the built dashboard image (HIGH/CRITICAL
  vulnerabilities and secrets), **record-only**: the job uses
  `exit-code: '0'` and uploads the JSON report as a 30-day artifact.
  A green container-security job is **not** proof of a clean image.

**Absent from CI today:** IaC scanning (Dockerfiles / compose) and
licence scanning — the plan's Day 26 items. A ready-to-paste workflow
adding both is saved at `docs/ci-scan-additions-proposed.yml`. It is a
proposal only: the GitHub App cannot push files under
`.github/workflows/`, so it takes effect only when a human pastes it
into `.github/workflows/` through the GitHub web UI. Making the Trivy
container scan *enforcing* (fail on findings) is a separate human
decision and is not part of that proposal.

## Not covered by this report

- The live team demonstration (Issue #89) has not been run; its human
  record remains PENDING.
- Day 19 load-probe measurements were never collected
  (`docs/day19-load-probe-runbook.md`).
- The release evidence bundle does not exist yet; it is gated on the
  Issue #102 integrated evidence and the authorized release decision.
