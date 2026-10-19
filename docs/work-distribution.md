# Work Distribution

| Member / verified display name | GitHub handle | Role | Branch | Primary ownership |
|---|---|---|---|---|
| 1 / madhab-tech-cyber | `@madhab-tech-cyber` | Team Lead and Security Architect | `member1/security-architecture` | Scope, architecture, threat model, policies, risks, reviews, integration and release |
| 2 / renu-stack | `@renu-stack` | eBPF Traffic Engineer | `member2/ebpf-capture` | Linux/eBPF probes, maps, privileges, kernel events and capture performance |
| 3 / aadi3006 | `@aadi3006` | Rust Enforcement and Performance Engineer | `member3/rust-enforcement` | Collector, enforcement adapter, resilience, rate limits and latency |
| 4 / identity pending | Not confirmed; M1 interim review owner | Python Detection Engineer | `member4/detection` | Ingestion, route discovery, BOLA/BFLA, masking and audit APIs |
| 5 / Pappu kumar | `@pappukumar96727-sketch` | Mock API and OpenAPI Engineer | `member5/mock-api` | Lab application, authentication, ownership, contract and attack scripts |
| 6 / Jay Itape | `@jayitape` | Dashboard, QA and DevSecOps Engineer | `member6/dashboard-devsecops` | React UI, CI, scans, containers, SBOM, tests and documentation |

Verified on 2026-10-18 from authors linked to assigned-branch commits and
repository permission reads: M1 admin; M2/M3/M5/M6 write. Display names are
published Git identities, not invented full personal names or owner sign-offs.
Member 4 has no attributable implementation commit in the inspected branch;
confirm that person's identity before adding a handle. See
[ownership controls](ownership-and-review-controls.md) for provenance, review
requirements and the distinction between CODEOWNERS and enforced protection.

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

[October 19 verification](member1-oct19-verification.md) credits the repaired API,
main-PR CI and unmerged M3 library/M6 fixture dashboard, without accepting live
integration. [Issue #14](https://github.com/madhab-tech-cyber/APIsenX/issues/14)
is reopened by the corrective task with unmet human requirements retained;
Day 15 actual feedback and owner responses remain pending in
[Issue #21](https://github.com/madhab-tech-cyber/APIsenX/issues/21).
Neither a merged document nor a green limited CI job completes those gates.
[Days 21–30](member1-days21-30-status.md) and the
[handover](final-demonstration-and-handover.md) record policy delivery and the
release hold in [#23](https://github.com/madhab-tech-cyber/APIsenX/issues/23), not
completed meetings, full-system acceptance or 30 calendar days of work.

[Member 1 correction](member1-governance-correction.md) and the
[checkpoint register](member1-checkpoints.json) are the current follow-up.
M1 owns review scheduling, actual response collection, M4 identity confirmation
and the approved-but-access-blocked protection setup. Assignments/mentions are
not owner acceptance. M5 supplies API clarification; M6 independently reviews
regressions and CI; M2/M3/M4 supply their separate interface proofs. Unknown
full names and M4's handle remain unconfirmed rather than invented.

- Mid-review: demonstrate Weeks 1-2 work and maintain commits on the required 10 days in the 14-day window.
- Final-review: demonstrate Weeks 3-4 work and maintain at least one meaningful team commit on every required day in the 20-day window.
- Confirm exact review dates with the mentor because the supplied handbook contains conflicting final-review ranges.

