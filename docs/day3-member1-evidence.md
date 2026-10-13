# Day 3 Scaffold and Standards Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Date started:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 3 task: review the repository scaffolds and approve
coding and review standards without overstating the readiness of placeholder or
untested components.

## Reviewed scope

- Project governance: `README.md`, `CONTRIBUTING.md`, `SECURITY.md` and
  `docs/`.
- Authorization foundation: `src/authorization.py`, `mock_data/` and
  `tests/test_authorization.py`.
- Mock API scaffold: `mock-api/main.py`, `docs/openapi.yaml`,
  `tests/test_mock_api.py` and `docs/day3-test-note.md`.
- Component placeholders: `ebpf/`, `collector/`, `analytics/`,
  `dashboard/` and `scripts/`.
- Repository automation, manifests, lock files and workflow definitions.

## Scaffold decisions

| Area | Evidence | Decision |
|---|---|---|
| Authorization policy and fixtures | Ten policy tests cover owner/admin allow paths and BOLA/BFLA, inactive, missing and unknown denial paths | Approved as a local foundation; not production authentication |
| FastAPI mock API | Sixteen API tests cover allowed, denied, unauthenticated and malformed cases; module compilation passes | Conditionally approved for authorised local-lab testing |
| OpenAPI contract | Documents the implemented route set and security intent | Conditionally approved; runtime/contract differences D3-F01 to D3-F03 must be resolved |
| eBPF, collector, analytics and dashboard | README ownership statements only | Not approved as runnable scaffolds; interfaces and implementations remain pending |
| Scripts and automation | README placeholder; no CI workflow | Not approved as reproducible automation |
| Dependency and security tooling | Runtime packages are available in this environment, but no manifests, locks, SBOM or dedicated scanners are checked in | Not approved for reproducible or release use |

## Findings and assigned follow-up

| ID | Finding | Impact | Owner | Required action / target |
|---|---|---|---|---|
| D3-F01 | The OpenAPI scheme advertises JWT, while the mock API accepts static opaque lab tokens | Clients and reviewers may assume signature, expiry and audience validation that does not exist | M1/M5 | Describe the scheme as opaque lab bearer tokens or implement validated JWT before non-local use; Week 1 exit |
| D3-F02 | OpenAPI error schemas use `{"error": ...}`, while FastAPI currently returns `{"detail": {"error": ...}}` | Contract consumers and evidence parsers receive an undocumented shape | M5 | Align implementation and contract and add response-schema tests; Week 1 exit |
| D3-F03 | Invalid update input is documented as HTTP 400 but the implementation returns HTTP 422 | Contract drift can cause incorrect discovery/client results | M5 | Select one status contract and test it; Week 1 exit |
| D3-F04 | No dependency manifests or lock files exist for the Python application | Builds are not reproducible and dependency risk cannot be accurately scanned | M5/M6 | Add reviewed manifests/locks and record supported Python version; Week 1 exit |
| D3-F05 | Default `python -m unittest discover -v` executes zero tests | A naive CI job can pass/fail without validating behavior | M5/M6 | Configure reliable discovery or use explicit targets and assert non-zero tests; Week 1 exit |
| D3-F06 | CI, dedicated secret/static/dependency scans and SBOM automation are absent | Required security gates are not enforced | M1/M6 | Add workflows and retain passing evidence; before Day 7 exit approval |
| D3-F07 | eBPF, collector, analytics, dashboard and scripts are placeholder-only | Integrated lab, cross-boundary controls and performance claims are unverified | M1 with M2-M6 | Implement and review each owned scaffold before claiming Week 1 integration |
| D3-F08 | The test run emits a Starlette deprecation warning for the current TestClient/httpx combination | Future dependency changes may break the test harness | M5/M6 | Pin compatible dependencies and remove or formally track the warning |

These are review findings, not silent changes to another member's implementation.
They remain tracked by R-005, R-007, R-011 and R-012 in the risk register.

## Standards approved

[`coding-and-review-standards.md`](coding-and-review-standards.md) is approved as
the project baseline. It defines:

- branch, issue, staging, commit and pull-request discipline;
- shared input, authorisation, logging, bounds, TLS and enforcement rules;
- Python, Rust, eBPF, dashboard and CI expectations;
- meaningful test and evidence requirements;
- security-sensitive reviewer ownership; and
- approval states and merge/release blockers.

## Verification

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`:
  **PASS — 26 tests**.
- `python -m compileall -q src mock-api tests`: **PASS**.
- `python -m unittest discover -v`: **INVALID CHECK — 0 tests executed**.
- Dedicated secret, static, dependency and container scans: **UNRUN — tools and
  project configuration are not present**.

## Review result

The local authorization and mock-API scaffold is **conditionally approved** for
continued authorised-lab development. It is not approved for production use,
release or claims about the unimplemented pipeline. Findings D3-F01 through
D3-F08 require issue ownership and follow-up evidence.
