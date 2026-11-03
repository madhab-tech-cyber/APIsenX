# Day 24 Dashboard Roles and Business-Risk Review

**Reviewer:** Member 1. **Date:** 2026-10-19. **Design:** `UI-RBAC-1.0`.

Reviewed M6 `39902b358ef68911795546bf22ae5faf46fbe078`: React fixture views
exist on the unmerged branch. Its successful repository-check job does not
prove build, UI behavior, authentication or backend authorization. No live
dashboard acceptance is granted by this document.

## Server-side permission matrix

Dashboard identities are distinct from mock API customer/admin fixtures. Every
management API read and mutation requires server-established identity, scope
and permission. Client routes, hidden buttons and local storage are not gates.
Missing role, tenant, case or policy context denies access.

| ID / action | Viewer | Analyst | Security approver | Operator / custodian |
|---|---|---|---|---|
| DV-01 Masked inventory/health in assigned scope | Read | Read | Read | Explicit assigned read only |
| DV-02 Masked case evidence | Deny by default | Read assigned cases | Read approved scope | Deny unless separately assigned |
| DV-03 Triage state/note change | Deny | Allowed transitions on assigned case | Review/disposition | Deny without analyst permission |
| DV-04 Severity downgrade/risk acceptance | Deny | Propose with evidence | Approve within policy; High risk still blocks release | Deny |
| DV-05 Export/hold/retention change | Deny | Request | Approve named scope/time | Custodian executes approved operation; no self-approval |
| DV-06 Rule activation/config change | Deny | Propose only | Record ENF authorization after gates pass | Operator executes exact authorized version; no self-authorization |
| DV-07 Emergency disable | Deny | Request | Allowed | Authorized operator always allowed, including audit outage |
| DV-08 User/role administration | Deny | Deny | Separate explicitly delegated identity administration | No implicit access from infrastructure role |

All grants are least-privilege, environment/case/tenant scoped and time bounded.
Read/export policies inherit [AUDIT-LAB-1.0](audit-retention-and-investigation.md).
Require short sessions, rotation/revocation, TLS, secure cookie attributes and
CSRF protection for state-changing browser operations. Audit allow/deny and
all mutations through protected server paths. The system must not accept a
client assertion that masking, authorization or approval has already occurred.

## Business-risk wording and fixture boundaries

- Display a persistent **Synthetic fixture data — not live security status**
  label on demo views; fixture health/latency is not measured system health.
- Label drift as **Undocumented operation observed; impact under validation**
  until authenticated source and reachability/impact evidence exist.
- Distinguish **Unauthorized attempt denied** from **Unauthorized access
  succeeded**; a 403 does not demonstrate data disclosure.
- Show severity and confidence separately, with reviewed rationale and policy/
  contract version. Do not turn a numeric anomaly into a confirmed Critical
  vulnerability or an automatic block.
- Render missing metrics as **Unavailable/Unmeasured**, never zero or Healthy.
  Preserve loading, empty, error and degraded source states; an empty result is
  not proof of no vulnerabilities.
- Encode untrusted text, validate bounded schemas and use masked projections.
  HTML escaping is not masking; evidence must not contain raw query/identity
  values or credentials even if rendered as harmless text.

## Acceptance and remaining ownership

M4/M6 agree a versioned management API contract, including fixture/live source,
data freshness, scope, errors and explicit unavailable states. M6 must provide
locked install, lint/typecheck/build and automated loading/empty/error/malformed,
safe-rendering and leak tests. M4 supplies server RBAC, direct API bypass,
cross-case/tenant, revoked session, CSRF, audit failure and export expiry tests.
M1 reviews risk wording, permission changes and actual owner sign-off.
UI-RBAC-1.0 is a design baseline; live protected dashboard approval is BLOCKED.
