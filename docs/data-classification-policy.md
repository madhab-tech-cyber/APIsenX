# Data Classification Policy

**Policy owner:** Member 1 - Team Lead and Security Architect

**Foundation review date:** 2026-10-13

**Status:** Approved baseline; Day 20 retention/access requirements are defined
in [AUDIT-LAB-1.0](audit-retention-and-investigation.md). Runtime retention tests
and Day 23 masking implementation approval remain pending.

## 1. Purpose and principles

This policy determines what API-Sentinel may collect, process, log, persist,
display and commit. It applies to source, fixtures, traffic, telemetry, findings,
audit records, dashboards, build systems and review evidence.

Core rules:

- collect the minimum fields required for an approved test or control;
- classify data at creation or ingestion and preserve the classification through
  derived records;
- when classifications conflict, apply the more restrictive handling;
- synthetic data must be visibly synthetic and must not be copied from a real
  person, account or transaction;
- credentials and prohibited data are removed at the earliest boundary; and
- documentation is not proof that masking, access control or retention is
  implemented.

## 2. Classification levels

| Level | Definition and examples | Repository | Runtime handling |
|---|---|---|---|
| Public | Material approved for public disclosure: README files, public architecture summaries, OpenAPI contracts without sensitive examples | Allowed after review | No confidentiality requirement; integrity and provenance still apply |
| Internal | Non-sensitive project material: interface schemas, synthetic aggregate metrics, build instructions and ordinary project plans | Allowed | Team access; do not expose operational internals unnecessarily |
| Restricted | Security-relevant or linkable lab data: synthetic subject/object identifiers, raw lab telemetry, masked findings, audit events, non-public vulnerability detail and administrative actions | Only deliberately minimised test fixtures or reviewed masked evidence | Least privilege, encryption in transit/at rest, access audit, bounded retention and masked display |
| Secret | Passwords, access/refresh tokens, session cookies, private/signing keys, CI credentials and secret-store values | Prohibited | Approved secret store or injected runtime binding only; never log or persist in application data |
| Prohibited | Real production traffic, real customer/personal data, third-party captures, real credentials and data collected without written authorisation | Prohibited | Must not enter the lab; stop processing, restrict exposure and follow the incident procedure |

Synthetic data is not automatically Public. A synthetic identifier becomes
Restricted when it appears in raw telemetry or security evidence that could
reveal system behavior or be correlated across records.

## 3. Field and artifact decisions

| Data or artifact | Classification | Collection/storage decision |
|---|---|---|
| Checked-in `lab-*-token` strings | Public non-secret test fixture with high misuse impact | Allowed only for the isolated mock API; never reuse as a real credential |
| Real authorization header, token, password, cookie or private key | Secret or Prohibited | Do not collect, log, persist or commit; redact at ingress |
| Synthetic user name, role and active flag in `mock_data/` | Internal test fixture | Allowed in reviewed fixtures |
| Synthetic user/order IDs in API responses | Internal in the mock API; Restricted in telemetry/evidence | Minimise, then tokenise or pseudonymise before persistence/display |
| Synthetic order total, currency and status | Internal test fixture | Allowed for deterministic lab cases; do not substitute real transaction data |
| Method, normalised route and status code | Internal; Restricted when combined with identity or security finding | Collect only at approved observation points; avoid raw query strings |
| IP address, process/cgroup identity and socket tuple | Restricted | Collect only when required; minimise precision and retention |
| Request/response body and raw packet capture | Restricted in an explicitly approved synthetic test; otherwise Prohibited | Disabled by default; never commit; delete after the approved test window |
| Audit subject, action, resource reference and outcome | Restricted | Structured, minimised, access-controlled and tamper-evident; never include credentials |
| Vulnerability reproduction and exploit detail | Restricted | Private reporting path; public issue only after safe sanitisation |
| OpenAPI contract and public architecture | Public after review | Version-controlled and integrity-protected |
| Source, manifests, lock files and SBOM | Public or Internal according to repository visibility | Version-controlled; scan before release |
| CI logs and build artifacts | Internal, or Restricted if they contain findings | Access-controlled; scan/redact before retention or sharing |

## 4. Collection and masking rules

- Maintain an allowlist of fields at each observation boundary. Unlisted headers,
  cookies, query values and bodies are excluded.
- Remove authorization, cookie, password, secret and key material before
  telemetry, logging or error handling.
- Normalise routes without persisting sensitive path/query values.
- Replace linkable identifiers with random tokens or a keyed pseudonymisation
  method where correlation is required.
- Plain unsalted hashing is not sufficient for predictable identifiers.
- Mask before storage and before dashboard delivery; access control alone is not
  masking.
- Errors shown to clients use generic messages and stable codes. Detailed
  diagnostics remain privacy-safe and access-controlled.

The exact masking field list and verification suite require Day 23 approval.

## 5. Access, transmission and storage

- Public data may be shared after integrity and disclosure review.
- Internal data is limited to project participants and approved systems.
- Restricted data requires named service/user roles, encryption in transit and at
  rest, access logging and an approved export path.
- Secret values are available only to the runtime principal that needs them and
  must never be copied into evidence.
- Prohibited data has no approved storage location in API-Sentinel.
- Backups, derived datasets, screenshots and exported reports inherit the
  strictest source classification.

## 6. Retention and deletion baseline

The Day 20 [audit policy](audit-retention-and-investigation.md) sets maximum
periods for masked summaries, findings, audit records, exports and backups.
Its deletion/hold/restore controls require implementation before persistence
acceptance. The following collection restrictions remain in force:

- do not retain raw telemetry or captures beyond the active approved test;
- retain only minimised evidence needed to prove a result;
- do not place runtime logs, captures or restricted exports in Git;
- make deletion include derived copies and temporary exports where practical;
- keep audit evidence only in an approved restricted location; and
- record any legal, academic or review requirement before extending retention.

No team member may invent a longer retention period for convenience.

## 7. Repository and review controls

Before committing or attaching evidence:

1. inspect the exact staged files;
2. confirm all identities and transactions are visibly synthetic;
3. search for credentials, private keys, authorization headers and unexpected
   personal data;
4. remove runtime logs, captures, populated environment files and restricted
   exports;
5. document any intentionally included Restricted fixture and why it is safe; and
6. use the private reporting route for unsanitised vulnerability detail.

Dedicated secret scanning remains required; a keyword search is only a temporary
supplement.

## 8. Detection and incident response

If Secret or Prohibited data enters the repository or pipeline:

1. stop collection and prevent further access or propagation;
2. notify Member 1 through the private security channel;
3. revoke/rotate exposed credentials without copying them into tickets or chat;
4. preserve only minimal, masked incident evidence;
5. remove affected data from active systems using the approved recovery process;
6. assess whether repository history, caches, artifacts, backups or exports are
   also affected; and
7. record remediation, owners, deadlines and residual risk.

Do not publicly disclose the sensitive value while reporting or correcting the
incident.

## 9. Review and ownership

Member 1 approves classification changes. Members 2-6 classify the data created
by their components and provide evidence that the required handling is enforced.
Review this policy when a new field, data source, store, export, dashboard view or
third-party integration is proposed, and at the Day 20, Day 23 and release gates.
