# Dashboard User Guide

**Owner:** Member 6. **Reviewer:** Member 1. **Applies to:** the React
dashboard in `dashboard/` on `main` (ops-console layout, PRs #143/#148).
This guide describes what the dashboard shows today. It grants no live
acceptance: the dashboard is fixture-only (see "Data source" below).

## What the dashboard is

The dashboard is the security interface for the API-Sentinel lab system. It
presents endpoint inventory, alerts and triage, OWASP API Security Top 10
(2023) coverage, masked evidence, and performance/health panels. It is a
read-and-review surface: it does not change triage state, activate rules, or
talk to a live backend.

## Sections

- **Security Overview** — posture summary computed from the bundled fixture
  data: alert counts by severity, OWASP coverage, and the live-posture list.
  The rail states the real policy posture: **AP-1.0 · monitor_only** — no
  enforcement rules are active.
- **Endpoint Inventory** — discovered endpoints and their classification.
  In the fixture, inventory classification is explicitly shown as
  unavailable; the documented management contract supports `documented`,
  `method_not_documented`, `path_not_documented`, and
  `visibility_unavailable`. There is no `deprecated` classification.
- **Alerts & Triage** — fixture alert rows that can be filtered locally by
  severity and triage status, with a matching count and an empty-state
  message when a filter matches nothing. Filtering is a local view
  operation only; the dashboard never mutates triage status.
- **OWASP API Security Top 10 (2023)** — reads
  `docs/owasp-api-security-mapping.json` directly and shows each category's
  documented coverage and example result. This mapping is a traceability
  aid, **not** an assessment or certification.
- **Security Evidence** — masked evidence rendered from the bundled masked
  fixture projection only. Passwords, bearer tokens, cookies, personal
  information, and private keys must never appear in the dashboard.
- **Performance & Health** — fixture health/performance panels. Aggregate
  values that are not available are shown as `Unavailable` or
  `Unmeasured` — never as zero and never as healthy.

## Data source: fixture vs live

The dashboard renders bundled synthetic fixture data by default, and the
sections say so (fixture labels are part of the UI, not fine print). The
data-source seam is `dashboard/src/dataSource.ts`, controlled by
`VITE_DATA_SOURCE` (see `dashboard/.env.example`): `fixture` is the only
wired source today; `live` is reserved for the analytics management API and
is deliberately labelled in the header as not yet wired. Fixture numbers
must never be presented as live telemetry.

The documented `MGT-LAB-1.0` read endpoints require a case-scoped reader
Bearer grant. That credential must never be placed in a Vite bundle or
browser storage, and there is no reviewed browser session bridge, so the
dashboard stays fixture-only until one exists.

## What the dashboard is not

- It has **no** management API client, authentication/session integration,
  server-side RBAC, or case scoping. Client-side UI state is never an
  authorization boundary.
- It has no live loading/error/empty network-response handling; the alert
  filter's empty state is a local view state.
- It does not prove system health, enforcement behaviour, or release
  readiness. For who may see and do what once a live source exists, see
  `docs/dashboard-roles-and-risk-wording.md` (server-side permission
  matrix, design `UI-RBAC-1.0`).

## Using it locally

From the repository root (see `docs/operating-guide.md` for the full
stack):

```sh
npm --prefix dashboard ci
npm --prefix dashboard run dev
```

Checks:

```sh
npm --prefix dashboard run lint
npm --prefix dashboard test
npm --prefix dashboard run build
```

Responsive tables scroll horizontally on narrow screens, and the native
select controls are keyboard accessible.
