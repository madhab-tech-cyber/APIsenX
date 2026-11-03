# Day 20 Audit Retention, Access and Investigation Policy

**Owner:** Member 1. **Implementation:** M4; storage/RBAC/backup verification M6.

**Date:** 2026-10-17 (Asia/Calcutta). **Policy:** `AUDIT-LAB-1.0`.

**Decision:** Retention and investigation requirements approved for the
synthetic lab; no audit store or access-control implementation is accepted.
The current mock API's stdout logging is not this protected audit service.

## 1. Minimum audit record

Allowlist: schema/policy version, opaque event/correlation ID, event/receipt UTC
times, authenticated source/build, opaque actor and resource references,
canonical action/method/template, outcome/reason, rule/config version, relevant
approval/rollback reference and evidence digest. Use server-assigned identifiers
or keyed pseudonyms when correlation is necessary; keys remain outside logs
and Git. Record append acknowledgement and deduplicate event IDs.

Exclude raw bearer/session/sharing tokens, cookies, bodies, query names/values,
unknown paths, real personal data and unneeded socket/process metadata. Mask
before append and export. Access controls do not replace masking. Schema/log
injection, oversized records and unknown sources are rejected with bounded
reason counters; never echo rejected content.

## 2. Retention schedule

Retention starts at server receipt, never an untrusted caller timestamp.
An older event timestamp does not authorize extra retention. Deletion work runs
at least hourly and removes expired primary data within 24 hours. Indexes,
caches, materialized views and temporary files follow the source expiry.

| ID | Data class/artifact | Maximum active retention | Purpose and expiry behavior |
|---|---|---|---|
| RT-01 | Raw paths, queries, headers, bodies and captures | No routine persistence | Excluded at ingress; synthetic exceptional capture needs separate written scope/window and deletion, never Git |
| RT-02 | Volatile normalized event queue | 2 seconds, bounded by LIMIT-LAB-1.0 | Transport only; no disk spool; drop with minimised count on expiry |
| RT-03 | Masked transaction summaries | 7 days | Short investigation correlation; remove identifying links and all derived copies on expiry |
| RT-04 | Masked findings and triage records | 30 days | Reproduction/remediation tracking; extend only by a separately recorded hold |
| RT-05 | Protected audit/approval/rollback and audit-access records | 90 days | Security accountability; append-only during retention and controlled expiry afterward |
| RT-06 | Investigation exports | 24 hours | Named recipient and purpose; encrypted private location, automatic expiry and deletion receipt |
| RT-07 | Encrypted backups of approved masked data | Rolling 7 days | No raw capture/secret inclusion; expired records may survive at most 7 additional days after primary deletion |
| RT-08 | Sanitised aggregate review documents and source-controlled policy | Repository lifecycle after disclosure review | No raw/runtime records; public summaries contain no linkable subject/object references |

For example, a 90-day audit record expires from primary storage within 24 hours
and from backups no later than seven days after that primary deletion. Retention
is not an instruction to create backups or collect a field otherwise prohibited.
The policy approves no indefinite Restricted archive. Day 23 finalizes masking
field implementations; until leak tests pass, persistence stays blocked.

## 3. Holds, deletion and restore

M1 may approve a minimised investigation hold for <= 30 days with case ID,
specific opaque record IDs, reason, custodian, access list and expiry. No blanket
collection hold or automatic extension. Review every seven days; renewal needs
a new approval before expiry. Hold records are isolated, encrypted and excluded
from routine exports/backups where practical. Record hold creation/release in
protected audit. A hold cannot authorize Secret/Prohibited collection.

Release/expiry triggers the normal deletion deadline. Deletion verifies primary,
indexes, caches, exports and backup aging and retains only a non-sensitive
deletion receipt. Backups must not silently reintroduce expired records: restore
into an isolated area, replay deletion/hold state and verify TTLs before service
access. Cryptographic deletion counts only when all relevant key copies and
restorable derivatives are accounted for. Do not claim deletion from a row
count alone. This policy performs no deletion of the user's existing files.

## 4. Access and integrity

| Role/service | Permitted access | Explicit restriction |
|---|---|---|
| API/collector producer | Append validated minimised events through authenticated endpoint | No read, export, update, deletion or retention override |
| Audit writer (M4 service) | Schema validation, masking, idempotent append acknowledgement | Separate credential from readers and dashboard |
| Analyst/investigator | Case-scoped masked read, bounded queries, no public export | Cannot change audit history or grant self access |
| M1 security approver | Approve case scope, time-bound holds, exports and retention changes | No silent record rewrite or bypass of access audit |
| M6 storage custodian | Backup/restore/deletion execution under approved policy | No routine investigation content access; exceptional access time-bound and logged |
| Dashboard ordinary viewer | Reviewed aggregate or explicitly authorized masked findings | No raw audit store or unrestricted bulk download |

Use named least-privilege identities, authenticated encrypted transport,
encryption at rest, bounded sessions and server-side authorization on every
read/export/change. Investigators require MFA in a shared deployment. No shared
fixture token may secure the audit store. Reader authorization is case-scoped
and expires after <= 24 hours unless M1 renews it explicitly.

Audit every read, failed read, export, policy change, hold, deletion and restore
without recursively auditing the audit writer's own append. Store access events
on a separate restricted append path and monitor gaps. Use append-only storage
plus sequence/previous-record digests and externally anchored signed checkpoints
or equivalent independently protected integrity evidence. A hash chain stored
beside mutable logs alone does not prevent history rewriting. Separate signing
keys and trusted checkpoint storage; verify tampering and missing sequences.

## 5. Investigation process

1. Intake a finding/case ID and classify urgency using discovery triage policy.
   M1 appoints a case owner; immediate suspected disclosure uses private handling.
2. Confirm authorised synthetic scope and grant the minimum case access for
   <= 24 hours. Use metadata references first; do not gather extra raw traffic.
3. Preserve relevant masked records by explicit hold if needed. Verify source,
   versions, timestamps, sequence, digests and chain of custody before analysis.
4. Correlate policy decisions with findings, source quality and application
   outcomes. Track hypotheses, confirmed impact and false-positive explanations
   separately. Do not infer malicious intent from changed identifiers alone.
5. M1 approves a named-recipient export only when case-scoped read is insufficient.
   Record recipient, purpose, exact fields/IDs, digest, encryption and 24-hour
   expiry. No public ticket, screenshot or repository attachment of raw evidence.
6. Assign remediation and re-test, record decisions in append-only history,
   revoke case access and release holds. Confirm export expiry and deletion
   receipts. Keep only reviewed sanitized outcomes in version control.

## 6. Failure and acceptance evidence

Audit append failure is a visible degraded state, not success. Stop new rule
activation and administrative policy mutations needing audit acknowledgment.
Trigger ENF-1.0 deactivation when active-rule audit fails; the emergency kill
switch always remains available. Existing API authentication/authorization
continues. A bounded volatile emergency queue may use only the 2-second event
TTL and resource caps, with visible loss counts. No silent raw disk fallback.
Final protected-route write behavior is resolved by Day 21 failure review.

Required M4/M6 tests: allowlisted-field and synthetic leak markers across
success/error/export; reader/writer/analyst/viewer negative RBAC; append failure
and duplicate handling; deleted/rewritten/reordered sequence detection; clock
skew and malicious timestamp; every RT expiry with a controlled clock; hold
approval/renewal/release; export expiration; full derivative deletion and restore
re-purge. Test zero-data, normal, outage and recovery paths. Retain safe aggregate
results and artifact digests, not raw test logs. R-001/R-008/R-009 remain High
until these controls and independent evidence exist.
