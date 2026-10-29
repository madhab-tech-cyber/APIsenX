# Authorization Policy

**Decision owner:** Member 1 - Team Lead and Security Architect

**Policy identifier:** `AP-1.0`

**Last reviewed:** 2026-10-13

**Status:** Day 10 decision table approved; implementation scope recorded below

**Related decision:** [`authentication-decisions.md`](authentication-decisions.md)

## 1. Principles and decision boundary

- The API is the source of truth for identity and authorization.
- Authentication establishes a principal; it never grants access by itself.
- Decisions use only server-resolved principal, role, explicit permissions,
  tenant, resource owner, active sharing grant, route, method and policy version.
- Client-supplied subject, role, owner, tenant, permission or sharing fields are
  never trusted as authorization context.
- Ownership does not bypass tenant isolation. A grant does not bypass tenant or
  function-level restrictions. An admin label does not imply every permission.
- Missing or ambiguous required context, an unknown action/role/policy version,
  or conflicting policy data results in denial.
- A different object identifier is not proof of an attack by itself. Detection
  and severity use the separately reviewed evidence policy.
- Behavioral signals may support an alert but cannot create permission.
- Every sensitive decision produces a privacy-safe outcome without recording
  raw credentials or unnecessary object/identity values.

This policy decides application access. Route discovery classifies contract
drift and MUST NOT replace an API authorization decision.

## 2. Current and planned roles

| Role | Approved capability | Current implementation |
|---|---|---|
| `customer` | List owned objects; read an object owned by the principal; read a same-tenant object with an active read grant | Owner list/read and server-resolved, read-only, versioned, expiring/revocable grant evaluation implemented; grant storage is a lab fixture |
| `support` | Read only explicitly assigned, masked support views in the same tenant; no order mutation | Implemented on `GET /support/orders`; assigned IDs only and response exposes only ID/status |
| `tenant_admin` | Tenant-scoped read/manage only with explicit permission; no cross-tenant access | Implemented for list/read/status update with `orders:read:tenant` / `orders:manage:tenant`; global admin route denied |
| `admin` | Local-lab platform administration with explicit `orders:read:any` and `orders:manage:any` permissions | Global synthetic-order read/manage implemented; permission lookup and tenant scope are incomplete |

Customer updates, sharing administration, support access and tenant-aware roles
are not active capabilities. Their policy rows below are requirements for future
implementation, not evidence that those accesses currently work.

The mock fixture resolves `tenant_id` from server-side principal and order records and fails closed when either is missing or invalid. All shipped fixtures use one lab tenant; cross-tenant behavior is tested by mutating test fixtures, not by a deployed multi-tenant identity provider. A client cannot opt into a tenant by sending an identifier.

## 3. Decision inputs and precedence

The policy evaluator accepts:

- authenticated stable subject and active/inactive state;
- server-resolved role and explicit permission set;
- principal tenant and resource tenant where tenant scope applies;
- canonical method, normalized route and action;
- server-resolved resource owner;
- validated sharing grant where applicable; and
- exact policy identifier and decision time.

Evaluation order is deterministic:

1. deny an unauthenticated, unknown or inactive principal;
2. deny an unknown policy version, role, route or action;
3. deny missing or ambiguous required tenant/resource context;
4. enforce tenant boundary before ownership or sharing;
5. enforce route/action permission and administrative scope;
6. evaluate ownership or a validated grant where the action permits it;
7. enforce allowed field/action scope; and
8. return a stable allow/deny reason with minimised audit context.

No later step can convert an earlier denial into an allow. Resource existence
may be resolved internally, but the reviewed route response must not disclose
another tenant's or owner's object.

## 4. Ownership, sharing, tenant and admin decision table

`Allow*` means the policy decision is approved only after the capability and its
required tests exist. The present implementation state is authoritative in the
last column.

| ID | Principal and context | Requested capability | Policy decision / reason | Current state |
|---|---|---|---|---|
| PT-01 | Missing, invalid or inactive principal | Any | Deny / `IDENTITY_REQUIRED` or `IDENTITY_INACTIVE` | Implemented for current routes |
| PT-02 | Any principal; unknown role, action or policy version | Any | Deny / `POLICY_CONTEXT_INVALID` | Unknown/missing `X-Policy-Version` rejected; unknown role/action denied |
| PT-03 | Customer; same tenant; resource owner | `orders:read` | Allow / `OWNER_READ_ALLOWED` | Implemented without tenant field |
| PT-04 | Customer; same tenant; resource owner | `orders:manage` | Deny / `ADMIN_PERMISSION_REQUIRED` | Implemented |
| PT-05 | Customer; same tenant; not owner; no grant | `orders:read` | Deny / `OWNERSHIP_OR_GRANT_REQUIRED` | Cross-owner denial implemented without tenant field |
| PT-06 | Customer; same tenant; active read grant | `orders:read` | Allow / `SHARED_READ_ALLOWED` | Implemented and tested with server-resolved fixture grant |
| PT-07 | Customer; same tenant; read grant only | `orders:manage` | Deny / `GRANT_ACTION_NOT_ALLOWED` | Sharing absent; manage already denied |
| PT-08 | Customer; expired, revoked, not-yet-valid or wrong-resource grant | Any | Deny / `GRANT_INVALID` | Expired/revoked/version/tenant/resource/action constraints checked; expired and revoked denial tested |
| PT-09 | Customer; owner or grantee; tenant differs | Any | Deny / `TENANT_MISMATCH` | Tenant mismatch denied before ownership/grant; regression tests present |
| PT-10 | Customer; client asserts another owner/tenant/role | Any | Ignore assertion; decide from server context, otherwise deny | Owner is server-resolved; tenant absent |
| PT-11 | Support; same tenant; active assignment and read permission | Masked support read | Allow / `SUPPORT_READ_ALLOWED` | Implemented on dedicated masked support list; assignment and tenant scoped |
| PT-12 | Support without assignment, in another tenant or requesting mutation | Read/manage | Deny / `SUPPORT_SCOPE_REQUIRED` | Support cannot use customer order routes or mutate; only assigned same-tenant IDs returned |
| PT-13 | Tenant admin; same tenant; explicit read permission | Tenant order read/list | Allow / `TENANT_ADMIN_READ_ALLOWED` | Implemented and tested |
| PT-14 | Tenant admin; same tenant; explicit manage permission | Allowed status update | Allow / `TENANT_ADMIN_MANAGE_ALLOWED` | Implemented and tested |
| PT-15 | Tenant admin; resource belongs to another tenant | Any | Deny / `TENANT_MISMATCH` | Tenant mismatch denied; regression tests present |
| PT-16 | Lab platform admin; explicit read permission | Order read/list and `GET /admin/orders` | Allow / `ADMIN_READ_ALLOWED` | Explicit permission gate implemented and tested |
| PT-17 | Lab platform admin; explicit manage permission | Status-only order update | Allow / `ADMIN_MANAGE_ALLOWED` | Explicit permission gate implemented and tested |
| PT-18 | Admin without required permission or requesting unknown action | Any | Deny / `ADMIN_PERMISSION_REQUIRED` or `ACTION_UNKNOWN` | Unknown action tested; permissions are fixture metadata but not evaluated |
| PT-19 | Any principal; owner, tenant or grant context is conflicting/ambiguous | Any context-dependent action | Deny / `POLICY_CONTEXT_INVALID` | Partial: missing object denied; full context model absent |
| PT-20 | Any principal; cross-tenant list request | `orders:list` | Filter to authorised tenant/objects or deny; never return another tenant | Owner filtering exists; tenant filtering absent |

## 5. Route and action table

| Route/action | Customer | Support | Tenant admin | Lab platform admin | Missing/invalid identity |
|---|---|---|---|---|---|
| `GET /orders` / `orders:list` | Owned plus active same-tenant read grants* | Assigned masked records* | Same-tenant records with explicit read permission* | All synthetic lab orders with read permission | 401 |
| `GET /orders/{orderId}` / `orders:read` | Same-tenant owner or active read grant* | Assigned masked record* | Same-tenant object with read permission* | Object with read permission | 401 |
| `PATCH /orders/{orderId}` / `orders:manage` | Deny | Deny | Same-tenant status update with manage permission* | Status-only update with manage permission | 401 |
| `GET /admin/orders` / `orders:read:any` | Deny | Deny | Tenant-scoped admin view only on a separately approved route* | Allow with read permission | 401 |
| Undeclared route/action | Deny | Deny | Deny | Deny | 401 when auth applies |

An asterisk marks an approved future decision whose role, tenant or sharing
capability is not implemented. Until then, it is denied. Invalid or extra update
fields are rejected before mutation. Cross-owner and function-level denials use
a generic client response and privacy-safe audit outcome.

Object-level reads and updates use a generic 404 response for missing, cross-owner, cross-tenant, or invalid-context objects, preventing existence disclosure. Function-level permission denials remain generic 403 responses. The runtime OpenAPI schema documents the required `X-Policy-Version: AP-1.0` header.

## 6. Sharing and administrative constraints

An accepted sharing grant must be server-resolved and contain a unique grant
identifier, policy version, tenant, resource type/id, grantee subject, exact
action set, issuer, validity window and optional revocation marker. Baseline
grants are same-tenant and read-only, cannot be delegated, and never grant an
admin route or `orders:manage`. Expired, revoked, future, mismatched or malformed
grants deny. The grant itself is Restricted and must not be copied into ordinary
logs or client errors.

Administrative access requires a known role plus an explicit permission and
scope. Admin requests do not bypass validation, field restrictions, tenant
rules, audit requirements or unknown-action denial. Platform-wide tenant bypass
is not approved for a multi-tenant system by the current lab `admin` role; it
requires a separately reviewed break-glass design, reason, time bound, audit and
test evidence.

## 7. Required acceptance cases

Each `PT-*` decision-table row must become an executable labelled case. At
minimum, the suite must demonstrate:

- owner read allow and customer manage denial;
- same-tenant non-owner denial with no grant;
- active read-share allow plus wrong-action, expired and revoked grant denial;
- tenant mismatch denial even when subject and owner identifiers appear equal;
- support allow only for an assigned masked view and denial otherwise;
- tenant-admin same-tenant allow with explicit permission and cross-tenant deny;
- platform-admin allow only for known action, explicit permission and allowed
  fields;
- unknown role/action/policy version and missing/conflicting context denial;
- list filtering that never returns an unauthorised owner or tenant; and
- stable privacy-safe audit reasons for allow and deny paths.

Tests must cover direct policy evaluation and HTTP behavior. Producer/consumer
tests must prove that analytics uses the same policy version and does not label
a normal authorised share or admin operation as BOLA/BFLA.

## 8. Audit and privacy requirements

The decision result contains allow/deny, stable reason, action, normalized route,
policy version and minimal correlation references. Audit storage may use a
pseudonymized subject/resource reference only when needed. It MUST NOT contain a
raw credential, cookie, request/response body, sharing token, unmasked query or
client-supplied role/tenant assertion.

Denied cross-owner/cross-tenant responses remain generic. Detailed reasons are
restricted to protected audit evidence and bounded reason metrics; identifiers
must not become metric labels.

## 9. Approval and implementation status

`AP-1.0` approves the decision order and table for implementation. The current
mock API demonstrates only customer owner read/list, customer cross-owner and
manage denial, admin global read/manage, inactive/unknown identities,
unknown-role/action denial and update-field restriction.

As verified on October 19, merged PR #20 adds explicit admin-read/manage function
permission gates; the inventory-shape, missing-permission and denied-mutation
regressions pass. [D11-F01 patch verification](patch-verification-log.md)
records the evidence and pending independent closure review.

Sharing grant evaluation, the masked assigned-support view, tenant-admin scoped permissions, policy-version rejection and object-level non-disclosure now have implementation and regression evidence in the mock API. Grant persistence and administration are still fixture-based, not a production sharing-management service. R-002 remains mitigating until independent review, the complete labelled matrix and cross-component false-positive/false-negative evidence pass.
