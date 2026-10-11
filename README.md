# API-Sentinel

API-Sentinel is an authorised lab project for runtime API inventory, shadow API discovery, BOLA/BFLA detection, controlled enforcement, rate limiting, privacy-safe telemetry, and security visualisation.

## Project status

The project is in the architecture and foundation phase. Development and testing must use the team-owned mock API or another environment with written authorisation.

## Components

- `ebpf/` - Linux eBPF observation layer.
- `collector/` - Rust event collector, enforcement adapter, and performance measurement.
- `analytics/` - Python ingestion, route discovery, BOLA/BFLA detection, masking, and audit APIs.
- `mock-api/` - Authorised e-commerce test application and OpenAPI contract.
- `dashboard/` - React endpoint inventory, alerts, investigation, and health views.
- `tests/` - Cross-component security, integration, performance, and failure tests.
- `docs/` - Architecture, threat model, policies, risks, work allocation, and review evidence.

## Team branches

- `member1/security-architecture`
- `member2/ebpf-capture`
- `member3/rust-enforcement`
- `member4/detection`
- `member5/mock-api`
- `member6/dashboard-devsecops`

All changes enter `main` through a reviewed pull request with passing checks.

## Security objective

Release only when there are no known critical or high-severity vulnerabilities, secrets are absent from the repository, required security tests pass, lower-severity risks are documented, and patch monitoring is active.

## Authorised use

Do not capture production traffic, test third-party systems, intercept real credentials, or store real personal information. See [SECURITY.md](SECURITY.md).
