# Project Scope and Governance

**Author:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Milestone:** Day 1 Scope Confirmation

**Repository:** `https://github.com/madhab-tech-cyber/APIsenX`

---

## 1. Project Purpose & System Boundaries

API-Sentinel is an authorized laboratory security platform designed to observe runtime API transactions, discover undocumented (shadow) and deprecated (zombie) routes against approved OpenAPI contracts, evaluate Broken Object Level Authorization (BOLA) and Broken Function Level Authorization (BFLA), apply controlled enforcement, and present findings on a protected dashboard.

### 1.1 In-Scope Components
- **Mock E-Commerce Lab Target (`mock-api/`)**: Authorized reference application serving multi-tenant customers and administrators with deterministic test identities.
- **eBPF Observation Layer (`ebpf/`)**: In-kernel socket event sensors emitting non-blocking telemetry via bounded Linux ring buffers across the kernel-to-userspace boundary.
- **Rust Collector & Enforcement Adapter (`collector/`)**: User-space daemon validating kernel events, enforcing bounded queue memory limits, measuring latency, and providing adaptive enforcement adapters across the host-to-analytics interface.
- **Python Analytics & Detection Engine (`analytics/`)**: Route parameter normalizer, OpenAPI drift engine, BOLA/BFLA policy evaluation, and privacy masking before persistence across the analytics-to-storage interface.
- **React Security Dashboard (`dashboard/`)**: Protected web interface rendering endpoint inventories, OWASP API Security alerts, and health telemetry across the management API interface.

### 1.2 Strict Out-of-Scope Constraints & Architectural Limitations
- **No Production Traffic Interception**: Prohibited from capturing, sniffing, or processing live production traffic or real user communications.
- **No Third-Party Probing**: Testing is strictly constrained to team-owned lab targets. Scanning or attacking third-party or unauthorized endpoints is prohibited.
- **No Unmasked Credential Storage**: Prohibited from logging, persisting, or exporting real passwords, cleartext secrets, bearer tokens, or sensitive personally identifiable information (PII).
- **HTTPS & Encryption Limitation**: eBPF network observation cannot normally read HTTP methods, routes or payloads inside encrypted HTTPS traffic. Route-level data must come from an explicitly authorized application hook, controlled reverse proxy, TLS termination point or another approved metadata source. The project must never weaken TLS.

---

## 2. Measurable Milestone Acceptance Criteria

Project milestone criteria covering team-owned components across the 4-week execution cycle:

### 2.1 Week 1 (Foundation & Traffic Observation)
- The assigned mock application, kernel sensor, and collector run in the integrated lab environment.
- Method, route boundary marker, timestamp, and authorized connection metadata appear in the telemetry pipeline via approved observation points.
- Threat model, asset inventory, trust boundary definitions, and risk register are reviewed and stored in GitHub.
- Dedicated automated secret scanning configured and passing without unmitigated findings.
- Foundation dependencies reviewed for known vulnerabilities.

### 2.2 Week 2 (Shadow API and BOLA/BFLA Detection)
- Parameterized route normalization maps dynamic URIs (e.g., `/orders/1001` -> `/orders/{order_id}`).
- Comparison against the approved OpenAPI contract correctly classifies documented, shadow (undocumented), and zombie (deprecated) routes.
- All agreed labelled BOLA/BFLA acceptance cases must pass in the controlled test corpus. Report false-positive and false-negative results separately.
- The `< 5 ms` p95 latency overhead goal is maintained as a provisional project target. Day 13 will define the environment, sample size, measurement method and final pass/fail criteria.

### 2.3 Week 3 (Enforcement, Rate Limiting & Resilience)
- Controlled enforcement adapter evaluates candidate actions (`allow`, `alert`, `rate_limit`, `deny`).
- Failure behavior must be selected per route and threat scenario. Availability-sensitive observation failures may fail open, while authorization and administration paths may require fail-closed behavior. Member 1 will approve the final route matrix on Day 21.
- Audit records use restricted, tamper-evident storage with documented retention and access controls. Runtime audit logs must never be committed to Git.
- Deterministic rollback mechanism verified for every blocking rule.

### 2.4 Week 4 (Privacy, Hardening & Release)
- Data protection compliance verified: sensitive fields must be removed, tokenized or pseudonymized according to the Day 23 masking policy. Plain unsalted hashing must not be treated as sufficient protection for predictable identifiers.
- React security dashboard enforces server-side authentication and role-based access control (RBAC).
- Comprehensive dependency, container, and static security scans executed with zero unresolved critical/high findings.
- Reproducible build scripts, complete SBOM, and release evidence package verified prior to final tag.

---

## 3. Meeting & Communication Routine

To maintain momentum and ensure review evidence integrity across the team:

- **Mandatory Daily Meaningful-Work Requirement**: Every member must push at least one commit representing meaningful, reviewable work every working day to their assigned branch. Meaningful work includes implementation code, tests, reviewed architecture documentation, threat-model updates, scan configurations, remediation, or measured evidence. Meaningless commits, empty commits, or artificial commits created solely to satisfy calendar metrics are strictly prohibited.
- **Communication SLA**: All members must respond to project questions and review requests within **24 hours**.
- **Escalation Protocol**: If a team member is unresponsive for **48 hours**, report to the Team Lead (Member 1), document the blocker in `docs/work-distribution.md`, and reallocate or sequence tasks to protect the delivery schedule.
- **Review Checkpoints**:
  - **Mid-Review Rehearsal**: Day 14 agenda to demonstrate Weeks 1-2 deliverables and verify daily commit distribution across the required window.
  - **Final-Review Rehearsal**: Day 28 agenda to verify end-to-end laboratory demo, evidence logs, and handover package.

---

## 4. GitHub Issue-Board Governance & Planning

### 4.1 Proposed Label Taxonomy
- **Role Assignment**: `role:member1`, `role:member2`, `role:member3`, `role:member4`, `role:member5`, `role:member6`
- **Issue Classification**: `type:docs`, `type:security`, `type:feature`, `type:test`, `type:chore`
- **Severity Classification**: `severity:critical`, `severity:high`, `severity:medium`, `severity:low` (reserved for actual security findings and vulnerabilities; not applied to ordinary project tasks)
- **Workflow State**: `status:backlog`, `status:in-progress`, `status:in-review`, `status:blocked`, `status:done`

### 4.2 Pull Request & Governance Controls
- All code and documentation enters `main` exclusively through pull requests targeting approved milestones.
- Direct commits to `main` are strictly disallowed.
- Branch protection and CODEOWNERS enforcement are currently unconfigured on GitHub and recorded as governance controls that still need configuration.
- Pull requests must include passing test evidence, clear security impact summaries, and peer review sign-offs before merge.
- Issue items proposed for Members 2-6 represent preliminary coordination items that require confirmation against their individual role specification PDFs before creation.
