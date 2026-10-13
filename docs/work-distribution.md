# Work Distribution

| Member | Role | Branch | Primary ownership |
|---|---|---|---|
| 1 | Team Lead and Security Architect | `member1/security-architecture` | Scope, architecture, threat model, policies, risks, reviews, integration and release |
| 2 | eBPF Traffic Engineer | `member2/ebpf-capture` | Linux/eBPF probes, maps, privileges, kernel events and capture performance |
| 3 | Rust Enforcement and Performance Engineer | `member3/rust-enforcement` | Collector, enforcement adapter, resilience, rate limits and latency |
| 4 | Python Detection Engineer | `member4/detection` | Ingestion, route discovery, BOLA/BFLA, masking and audit APIs |
| 5 | Mock API and OpenAPI Engineer | `member5/mock-api` | Lab application, authentication, ownership, contract and attack scripts |
| 6 | Dashboard, QA and DevSecOps Engineer | `member6/dashboard-devsecops` | React UI, CI, scans, containers, SBOM, tests and documentation |

## Communication

- Post a daily branch or pull-request update.
- Respond to team project messages within 24 hours.
- Report a member who is unresponsive for 48 hours and update this document.
- Do not wait for an inactive member when the schedule is at risk.

## Integration handoffs

[`integration-data-flow.md`](integration-data-flow.md) is the authoritative Day 5
interface and data-flow baseline. The immediate handoff chain is:

- M5 supplies the reviewed OpenAPI/runtime behavior, synthetic traffic and an
  HTTPS-safe candidate observation point to M1, M2 and M4.
- M2 and M3 jointly approve the bounded kernel event schema and drop behavior.
- M3 and M4 jointly approve the authenticated batch, health and decision
  contracts, including replay, backpressure and compatibility behavior.
- M4 and M6 jointly approve masked storage/management API outputs and dashboard
  RBAC expectations.
- M6 supplies deterministic CI, test, scan, SBOM and release evidence entry
  points to every component owner.
- M1 approves classification, trust-boundary controls, failure modes, residual
  risks and any transition from monitor-only to active enforcement.

No handoff is complete until producer and consumer acceptance plus passing
contract/failure evidence is linked. The Day 5 document assigns this work but
does not claim that any planned interface has been implemented or accepted.

## Review evidence

- Mid-review: demonstrate Weeks 1-2 work and maintain commits on the required 10 days in the 14-day window.
- Final-review: demonstrate Weeks 3-4 work and maintain at least one meaningful team commit on every required day in the 20-day window.
- Confirm exact review dates with the mentor because the supplied handbook contains conflicting final-review ranges.

