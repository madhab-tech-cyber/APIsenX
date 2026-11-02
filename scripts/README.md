# Project scripts

Store reproducible setup, test, scanning, SBOM, demonstration, and lab-reset scripts. Scripts must fail safely and must not target systems outside the authorised lab.

`python scripts/check_member1_governance.py` validates the internal consistency
of `docs/member1-checkpoints.json`. Pending human records remain pending. Marking
one complete requires actual meeting/comment/response/independent review links;
Day 15 depends on Day 14 and the full Day 30 demo requires accepted integration.
The checker does not contact GitHub, prove a linked statement is true, enforce
branch protection or grant release/active-rule approval. Owners must inspect the
actual evidence and live settings. Tests run in the normal unittest discovery.

`python scripts/manage_main_protection.py --check` checks only the approved
main-branch settings using the authenticated GitHub CLI. The explicit `--apply`
mode creates those settings only for this repository's main branch, refuses
to overwrite an existing noncompliant rule, and requires verified readback.
It never writes on authentication/permission failure. See
[owner instructions](../docs/main-protection-owner-action.md).

`python scripts/verify_day29_lab_reset.py` verifies the reviewed Git blob SHA-1 baseline
for synthetic Mock API fixtures and proves that a fresh interpreter reloads the
fixture state and clears process-local revocations, nonces, rate-limit buckets
and subject semaphores. It does not delete fixtures or clear durable data.

