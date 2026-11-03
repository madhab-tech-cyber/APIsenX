# Day 10 Authorization Policy-Table Approval

**Reviewer:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Review date:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 10 schedule task by approving a versioned ownership,
sharing, tenant and administrative authorization decision table.

## Work completed

[`authorization-policy.md`](authorization-policy.md) now records `AP-1.0` with:

- trusted decision inputs and deny-first evaluation precedence;
- current and planned role boundaries;
- 20 labelled `PT-*` ownership, sharing, tenant and admin decisions;
- route/action outcomes for customers, support, tenant administrators and the
  local lab platform administrator;
- same-tenant, read-only baseline sharing constraints;
- explicit administrative permission, scope and field restrictions;
- executable acceptance, cross-component consistency and privacy requirements;
  and
- a row-by-row distinction between approved design and current implementation.

[`risk-register.md`](risk-register.md) now links `AP-1.0` to R-002 while keeping
the risk in Mitigating state because the complete matrix is not implemented.

## Current behavior reviewed

The current synthetic mock API supports customer owner read/list, cross-owner
denial, customer manage denial, global lab-admin read/manage, inactive/unknown
identity denial, unknown role/action denial and status-only update validation.

It has no tenant attributes, sharing grants, support role, tenant-admin role,
policy-version input or explicit permission evaluation. Those decisions remain
deny-by-default and are not represented as passing implementation evidence.

## Verification

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`:
  **PASS - 26 tests** for the current owner/admin implementation boundary.
- `python -m compileall -q src mock-api tests`: **PASS**.
- `git diff --check`: **PASS - no whitespace errors**.
- Documentation link, policy-ID/table-ID uniqueness, required-section,
  trailing-whitespace and credential-pattern checks: **PASS - no findings**.

## Decision and evidence boundary

The `AP-1.0` decision table is approved for implementation and test handoff.
R-002 is not closed: Member 4 and Member 5 must add the labelled sharing,
tenant, permission/version and cross-component BOLA/BFLA cases before Week 2
exit approval.
