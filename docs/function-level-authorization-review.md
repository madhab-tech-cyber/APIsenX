# Day 11 Function-Level Authorization Matrix Review

**Reviewer:** Member 1 - Team Lead and Security Architect

**Date:** 2026-10-14

**Policy:** `AP-1.0`, [authorization-policy.md](authorization-policy.md)

**Reviewed source baseline:** `df86811` (current merged API implementation)

## Matrix and evidence

Application function permission must be checked independently of ownership of
the objects returned by a function. Empty collections do not grant permission.
Authentication, function authorization and object authorization are separate
gates; later object checks cannot substitute for the function gate.

| ID | Function | Customer requirement | Lab admin requirement | Observed implementation / decision |
|---|---|---|---|---|
| FL-01 | `GET /orders` | List only authorized owned objects | Read permission for all lab objects | Per-object filtering exists; current customer/admin tests pass; explicit admin permissions absent |
| FL-02 | `GET /orders/{orderId}` | Owner read within approved scope | Explicit read permission | Owner/admin role evaluation exists; tests pass; tenant/share/permission/version inputs absent |
| FL-03 | `PATCH /orders/{orderId}` | Deny, including an owned object | Explicit manage permission; status-only fields | Customer role denied; admin role allowed; field tests pass; explicit permission evaluation absent |
| FL-04 | `GET /admin/orders` | Deny for every inventory shape | Explicit `orders:read:any` permission before listing | FAIL: only object-read checks run; customer allowed for empty/all-owned inventory |
| FL-05 | Unknown role or action | Deny | Unknown action denies even for admin | Unit and HTTP tests cover selected cases; unknown-role list behavior lacks full route coverage |
| FL-06 | Support and tenant-admin functions | No capability until implemented and tested | No implicit platform/tenant bypass | Roles and routes absent; design requirements only |

## Confirmed finding D11-F01

**Severity:** High. **Confidence:** High. **State:** confirmed.

`list_admin_orders()` in [main.py](../mock-api/main.py) calls `authorize()` with
`orders:read` for each object. It never checks an independent administrative
permission. With an empty inventory, the loop performs no checks. With an
all-owned inventory, every owner read succeeds. Both paths return HTTP 200 to a
customer on an administrative function that `AP-1.0` requires to deny.

Reproduction used `TestClient`, the public local-lab customer fixture, and
`patch.object(main, 'ORDERS', ...)` with an empty mapping and with the subset of
synthetic orders owned by `user-a`. Both requests to `/admin/orders` returned
200; expected 403. Patch contexts restore the in-memory inventory. No fixture
file was rewritten. No cross-owner disclosure was demonstrated in these two
cases; severity reflects the reproducible privileged-function access and the
absence of a required gate, rather than a claim of Critical impact.

The existing customer-admin test returns 403 only because the ordinary fixture
includes an order owned by another customer. This does not prove a function
permission check.

## Remediation and acceptance

| Owner | Required action | Gate |
|---|---|---|
| M5 | Add an independent admin function permission check before iteration; deny unknown roles and missing permission | Before approval of admin-route implementation |
| M5/M6 | Add empty, all-owned, mixed-owner and unknown-role inventory tests; retain admin allow cases | Regression evidence required |
| M4 | Keep BFLA expectations independent of object ownership and use the same policy version | Before integrated detection approval |
| M1 | Review corrected behavior, evidence and residual R-002 rating | Before finding closure |

High-severity remediation is due within seven days (2026-10-21) and before
release. Active blocking remains subject to the separate enforcement review.

The matrix requirements are reaffirmed, but function-level implementation
approval is **withheld** for FL-04. No API behavior was changed during this
review. Sharing, tenant, support, explicit permission and version enforcement
remain unverified requirements.
