# API-Sentinel

API-Sentinel is an authorised lab project for runtime API inventory, shadow API discovery, BOLA/BFLA detection, controlled enforcement, rate limiting, privacy-safe telemetry, and security visualisation.

## Project status

**Current phase:** Architecture and foundation. **Release decision:** NOT APPROVED / release held.

Development and testing must use the team-owned mock API or another environment with written authorisation. Do not capture production traffic, test third-party systems, intercept real credentials, or store real personal information.

See the [October 20 Member 1 closeout](docs/member1-closeout-2026-10-20.md) and
[final architecture/limitations](docs/final-architecture-and-presentation.md):
the mock API authorization fix, contract checks and selected quality gates are
merged. The Rust collector library is now merged through PR #32; the React
fixture dashboard remains on its peer branch. On `member4/detection`,
[Days 1–10 analytics](docs/member4-days01-10-evidence.md) now supplies authenticated
local ingestion, strict schemas, volatile masked storage, route discovery and
fixture-backed ownership evaluation. Live sensor-to-analytics
integration, detection validation and integrated acceptance remain incomplete.
These descriptions distinguish implementation progress from accepted operation.

The [Member 4 Days 11–20 extension](docs/member4-days11-20-evidence.md) adds
function-level detection, a self-labelled corpus, signed monitor-only
recommendations and volatile structured audit. It does not establish live
identity provenance, accepted accuracy or completed human review/feedback.

[Member 4 Days 21–30](docs/member4-days21-30-evidence.md) supplies stale-policy
failure tests, mandatory storage masking, protected paginated inventory/alert
APIs and a deterministic source candidate. M3 has added a local Rust/Python
Bearer batch handoff. Shared deployment, durable audit, live context, independent
reviews and the human final demonstration remain unaccepted; release is held.

Days 21–30 are Member 1 policy/review tasks, not proof of 30 calendar workdays,
completed human checkpoints or a production-ready engine. Passing reference-API
tests and documentation checks do not establish detector accuracy, integrated
performance, privacy acceptance, rollback readiness or production readiness.

**Safety restrictions:** Monitor-only operation remains mandatory. No active
enforcement rules are approved. Do not release, deploy or enable active
enforcement based on documentation completion or partial test success.

Member 1's [Days 21–30 delivery index](docs/member1-days21-30-status.md),
[release-gate decision](docs/release-gate-decision.md) and
[rehearsal/handover](docs/final-demonstration-and-handover.md) distinguish the
completed policy package from pending integration and human demonstration.
Independent review, owner acceptance, repository-protection verification and
the human-led integrated demonstration remain outstanding. See the
[October 19 verification](docs/member1-oct19-verification.md) and
[Member 1 corrective status](docs/member1-governance-correction.md) for the
dated evidence snapshots. The [current checkpoint register](docs/member1-checkpoints.json)
credits the real M5 handoffs and PR #28 approval without completing the human
checkpoints. Earlier Issues #14/#21/#23 are closed; remaining actual owner
actions are tracked in [#33](https://github.com/madhab-tech-cyber/APIsenX/issues/33).

## Intended component responsibilities

The following list describes the architecture, not a claim that every component
is implemented, merged or accepted:

- `ebpf/` - Intended Linux eBPF observation layer.
- `collector/` - Intended Rust event collector, enforcement adapter, and performance measurement.
- `analytics/` - Local monitor-only ingestion, route discovery, object/function evaluation and signed recommendations; durable audit, live context and dashboard read APIs remain pending.
- `mock-api/` - Authorised e-commerce reference application and OpenAPI contract.
- `dashboard/` - Intended React endpoint inventory, alerts, investigation, and health views; current peer-branch UI is fixture-based.
- `tests/` - Security, contract, integration, performance, and failure tests; actual coverage depends on the executed test suite.
- `docs/` - Architecture, threat model, policies, risks, work allocation, and review evidence.

See [final architecture and limitations](docs/final-architecture-and-presentation.md)
for the component-by-component implementation and acceptance status.

## Team branches

- `member1/security-architecture`
- `member2/ebpf-capture`
- `member3/rust-enforcement`
- `member4/detection`
- `member5/mock-api`
- `member6/dashboard-devsecops`

Required workflow: changes enter `main` through independently reviewed pull
requests with passing checks. **Observed status in the October 19 evidence:
branches were unprotected, the ruleset list was empty, and protection setup was
blocked by administrative access.** The required workflow is policy, not proof
that branch protection is enabled. See [ownership and review controls](docs/ownership-and-review-controls.md)
for the observed state and owner handoff.

The October 20 readback still reports main unprotected and administration access
denied. The approved settings now have a tested owner utility:
`python scripts/manage_main_protection.py --check` is read-only;
`--apply` creates only the approved main rule and verifies readback when run
with actual repository administration access. See the
[owner instructions](docs/main-protection-owner-action.md). A passing unit test
or prepared settings file does not enable protection.

## Security objective

Release only when there are no known critical or high-severity vulnerabilities,
secrets are absent from the repository, required security tests pass, lower-
severity risks are documented, and patch monitoring is active. These criteria
are necessary but do not override the release gate: unresolved high risks,
missing integration evidence, or pending required approvals keep the release
held. See the [release-gate decision](docs/release-gate-decision.md) and
[risk register](docs/risk-register.md).

## Authorised use

Do not capture production traffic, test third-party systems, intercept real
credentials, or store real personal information. Use only the team-owned mock
API or another environment with written authorisation. See [SECURITY.md](SECURITY.md)
for vulnerability reporting and response policy.
