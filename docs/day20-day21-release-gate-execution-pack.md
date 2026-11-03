# Day 20–21 release-gate execution pack

**Status: preparation only.** This runbook does not claim a human demonstration, service-owner decision, independent approval, durable storage deployment, or administrator configuration has happened. Keep AP-1.0 in `monitor_only`, enforcement rules disabled, and release **NOT APPROVED** until evidence is attached.

## Gate A — approve the storage architecture before implementation

The current `analytics/store.py` is a bounded in-memory store. The existing design proposal recommends PostgreSQL plus separate writer, reader, retention, and migration identities; protected integrity checkpoints; receipt-time retention; deletion receipts; backup aging and restore-time re-purge.

A service owner must record an explicit dated decision on [Issue #83](https://github.com/madhab-tech-cyber/APIsenX/issues/83) covering:

- selected storage technology and deployment/environment;
- threat model, data classification, key/KMS ownership and rotation;
- writer/reader/retention/migration identities and least privilege;
- backup/restore, retention/deletion, holds, and operational owner;
- approved test environment and rollback/disable plan.

Do not start a production-like storage implementation or claim durability until that decision is recorded. Never put credentials, connection strings, real event payloads, personal data, or key material in GitHub evidence.

## Gate B — durable-storage acceptance (after architecture approval)

Run against an isolated, approved test database and the exact candidate commit. Use synthetic data only.

- [ ] Append acknowledgement occurs only after a committed database transaction.
- [ ] Process restart preserves accepted records; database outage fails closed with bounded, non-sensitive responses and no volatile/disk-spool fallback.
- [ ] Same opaque event reference and digest is idempotent; conflicting digest is rejected without reflecting input.
- [ ] Writer cannot read, update, delete, or run DDL; reader cannot mutate; retention worker has only its documented permissions.
- [ ] Unknown fields and secret-bearing projections are rejected before persistence.
- [ ] Receipt-time expiry boundaries and RT-03 (7 days), RT-04 (30 days), RT-05 (maximum 90 days), RT-06 (24-hour export expiry), RT-07 (rolling 7-day backups) are tested with a controlled clock or disposable fixtures.
- [ ] Deletion covers primary rows, indexes, caches, exports and derivatives; emit a minimal deletion receipt.
- [ ] Restore procedure replays deletion/hold state, rechecks expiry and verifies integrity checkpoints before access is restored.
- [ ] Case-scoped RBAC denies by default; sensitive reads, exports, grants and holds are audited; required access-audit failure denies the read/export.
- [ ] Tamper detection, outage/recovery, backup expiry and emergency disable are demonstrated.
- [ ] Capture sanitized command output, exact commit SHA, test report and CI links. Do not attach secrets or raw event data.

## Gate C — human-led integrated demonstration

A human operator and a witness/reviewer must run this against the actual approved integrated environment (sensor/collector → API → analytics/detection → durable audit store → dashboard). Unit tests and synthetic in-process demos do not satisfy this gate.

Record date/time (UTC), environment/build identifiers, operator, witness, exact commit SHA, sanitized evidence links and observed result for each scenario:

| Scenario | Required observation | Result/evidence |
|---|---|---|
| Normal event | Authenticated event flows end-to-end and is durably acknowledged only after commit | Pending |
| BOLA denial | Unauthorized object access is denied; no state mutation; no sensitive value leaks | Pending |
| BFLA denial | Unauthorized function/admin operation is denied | Pending |
| Tenant separation | Cross-tenant read/write is denied | Pending |
| Masking/leak markers | Credentials, query values, resource identifiers and raw payload markers do not appear in stored summaries/logs | Pending |
| Storage outage | Bounded generic failure; no false success, raw leak or unsafe fallback | Pending |
| Route failure/recovery | Injected route-specific failure is observable; recovery works and state remains consistent | Pending |
| Retention/deletion | Expired records and derivatives are deleted; receipt is produced | Pending |
| Restore/re-purge | Restore is isolated; deletion/hold ledger and expiry are reapplied before access | Pending |
| Emergency disable/rollback | Operator disables the affected path and verifies safe monitor-only behavior | Pending |

Use synthetic markers such as `SYNTHETIC_SECRET_MARKER` only. Do not paste raw requests, bearer tokens, customer identifiers, or production data into the issue. If any scenario cannot be run, record it as blocked—not passed.

## Gate D — independent review and service-owner decision

These are two separate decisions and must be made by the named people themselves.

- [ ] Service owner posts a dated **ACCEPT** or **REJECT** on Issue #89, references the exact tested SHA, lists evidence, limitations and rollback decision.
- [ ] Independent reviewer (not the implementer) reviews the implementation, CI, threat model and demonstration evidence; posts a separate dated **APPROVE** or **REQUEST CHANGES** with findings on the PR/issue.
- [ ] Resolve all blocking findings and rerun affected tests before a new decision.
- [ ] Release decision is explicit. Until all required gates pass, keep release **NOT APPROVED**.

## Gate E — administrator branch protection

An authorized repository administrator must configure and verify `main` in GitHub Settings → Branches (or the applicable ruleset UI/API). The current contributor connection has no admin/maintain permission, so this runbook cannot apply or independently verify the setting.

Required settings:
- [ ] Require a pull request before merging.
- [ ] Require at least one approval from an independent reviewer.
- [ ] Dismiss stale approvals when new commits are pushed.
- [ ] Require the current checks: `API Security and Quality Gates` and `Analytics Security and Quality Gates`.
- [ ] Prevent bypass for ordinary contributors; document any admin bypass policy.
- [ ] Save a sanitized screenshot/export of the effective rule and a successful test showing a direct push is rejected or the PR rules are enforced.

The administrator should record who verified the rule, UTC timestamp, repository/branch, ruleset name/ID, required check names, and evidence link on Issue #89. Do not share tokens or private settings dumps.

## Evidence record template

Copy into Issue #89 after the work is actually performed:

- **UTC date/time:**
- **Environment and build:**
- **Exact commit SHA:**
- **Operator:**
- **Independent witness/reviewer:**
- **Scenario results and evidence links:**
- **Unresolved limitations/findings:**
- **Service-owner decision (name/date/ACCEPT or REJECT):**
- **Independent reviewer decision (name/date/APPROVE or REQUEST CHANGES):**
- **Branch protection verified by admin (name/date/evidence):**
- **Release decision:** NOT APPROVED unless all required gates are evidenced.

## Safety boundary

Passing automated tests is necessary but not sufficient. Do not activate enforcement, close the release gate, or mark human/admin acceptance complete based on this runbook alone.
