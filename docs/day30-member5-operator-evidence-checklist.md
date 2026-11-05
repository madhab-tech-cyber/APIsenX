# Member 5 — Day 30 operator evidence checklist

**Purpose:** Capture actual operator evidence for the final synthetic API rehearsal without confusing automated CI with a human demonstration.

**Current execution status: NOT RUN IN THIS AUTOMATION.** This file is a blank evidence template, not a demonstration result, attendance record, owner decision or release approval.

## Gate 0 — prerequisites

Before any integrated demonstration, confirm all of the following with actual evidence:

- [ ] Service owner has approved the durable-audit architecture and operating model (Issue #83).
- [ ] Approved durable audit implementation is deployed in an isolated authorised lab; it is not the unapproved SQLite candidate or volatile MemoryStore.
- [ ] Independent reviewer has accepted the architecture and the exact implementation under review.
- [ ] Sensor/collector, Mock API, analytics, durable audit store and dashboard are available in the same approved test environment.
- [ ] Exact build/commit identifiers and rollback/disable procedure are recorded.
- [ ] Main-branch protection has been enabled and read back by an authorised repository administrator (Issue #89), if this is part of the release demonstration.

If any prerequisite is absent, do not represent the run as the integrated final demonstration. Record the blocker and retain the release hold.

## A. Local synthetic API rehearsal

The automated Day 30 rehearsal in `tests/test_day30_demo_runbook.py` executes the documented TestClient script in a fresh interpreter. It is a local in-process API rehearsal, not a sensor-to-dashboard demonstration. The expected statuses below are contract expectations, not observed results for this blank operator record.

| Case | Scenario | Expected result | Operator result |
|---|---|---:|---|
| DEMO-01 | Owner reads own order | 200 | NOT RUN |
| DEMO-02 | Cross-owner BOLA read; target identifiers absent | 404 | NOT RUN |
| DEMO-03 | Missing bearer identity | 401 | NOT RUN |
| DEMO-04 | Customer attempts admin inventory | 403 | NOT RUN |
| DEMO-05 | Permitted synthetic lab admin reads inventory | 200 | NOT RUN |
| DEMO-06 | Customer PATCH denied; order unchanged | 403 | NOT RUN |
| DEMO-07 | Permitted lab-admin PATCH | 200 | NOT RUN |
| DEMO-08 | Protected owner field in PATCH; order unchanged | 400 | NOT RUN |

Use the [Day 28 loopback runbook](day28-member5-lab-runbook.md) for the synthetic service setup. Keep it bound to `127.0.0.1`; use only the checked-in lab fixtures. Do not copy bearer tokens or raw payloads into the evidence record. Run the permitted admin mutation last and reset the process afterwards.

## B. Integrated demonstration scenarios

These scenarios require the approved integrated environment from Gate 0. A passing local unit test or mocked transport does not satisfy them.

| Scenario | Required observation | Operator result |
|---|---|---|
| End-to-end normal event | Authenticated event reaches API, analytics, durable audit and dashboard; acknowledgement follows durable commit | NOT RUN |
| BOLA/BFLA denial | Denied object/function requests do not mutate state or disclose protected identifiers | NOT RUN |
| Tenant separation | Cross-tenant access is denied at the server boundary | NOT RUN |
| Masking/leak markers | Synthetic secret, query, actor and resource markers are absent from persisted projections and diagnostics | NOT RUN |
| Durable-store outage | Required append failure produces bounded fail-closed behavior; no volatile/disk fallback or false success | NOT RUN |
| Route-specific recovery | Injected dependency failure is bounded and recovery does not duplicate or partially apply work | NOT RUN |
| Retention/deletion | Approved receipt-time retention, deletion receipts and derivative expiry are observed | NOT RUN |
| Restore/re-purge | Restore re-applies deletion/hold state and expiry before records become accessible | NOT RUN |
| Emergency disable/rollback | Operator disables the affected path without activating enforcement or altering unrelated host rules | NOT RUN |

## C. Actual run record — complete only after execution

- **UTC date/time:** NOT RECORDED
- **Environment/build identifier:** NOT RECORDED
- **Exact tested commit SHA:** NOT RECORDED
- **Operator:** NOT RECORDED
- **Independent witness/reviewer:** NOT RECORDED
- **Evidence links (sanitized):** NONE
- **Failed/blocked scenarios and remediation:** NOT RECORDED
- **Fixture/reset confirmation:** NOT RECORDED
- **Service-owner decision and date:** PENDING
- **Independent-reviewer decision and date:** PENDING
- **Release decision:** NOT APPROVED

After execution, attach only sanitized status/output evidence. Never attach production credentials, bearer tokens, raw customer data, database DSNs, key material or unredacted event bodies.

## Current disposition

The Day 29 reset verifier and Day 30 eight-case local rehearsal are automated engineering artifacts. They do not prove a human-run lab, live sensor/collector integration, accepted dashboard, approved durable storage, independent review or final acceptance. Keep AP-1.0 in `monitor_only`, active enforcement rules at zero, and release **NOT APPROVED** until the required evidence and separate human decisions are recorded.
