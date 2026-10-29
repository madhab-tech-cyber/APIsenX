# Day 20 storage design approval record

> Complete this record with the actual decision. Do not infer approval from a PR merge, CI result, or checklist checkbox. Do not put credentials, key material, production endpoints, or personal data here.

## Decision metadata

- Decision date/time (UTC):
- Service owner (GitHub handle or role):
- Independent reviewer (GitHub handle or role; must be a different person):
- Design version / commit reviewed:
- Decision: APPROVE / APPROVE WITH AMENDMENTS / REJECT
- Scope: isolated synthetic lab only

## Required service-owner decisions

For each item, record the decision, rationale, responsible role, and any limits.

- [ ] PostgreSQL hosting, ownership, isolation, capacity and availability expectations
- [ ] TLS, encryption at rest, secret-manager integration and key ownership/rotation
- [ ] Separate writer, reader, retention-worker and migration identities/permissions
- [ ] Independently protected checkpoint/signing-key service and immutable destination
- [ ] Backup schedule, rolling 7-day expiry, restore isolation and restore-time re-purge
- [ ] RT-01–RT-08 retention, deletion receipts, export expiry and hold/release workflow
- [ ] Incident response, outage behavior, emergency disable, operational ownership and costs
- [ ] Explicit confirmation that AP-1.0 stays `monitor_only`, with zero active enforcement rules

## Independent review

- Reviewer decision: APPROVE / APPROVE WITH AMENDMENTS / REJECT
- Date/time (UTC):
- Threat-model and least-privilege findings:
- Integrity/checkpoint and key-separation findings:
- Retention/deletion/restore findings:
- Required changes or objections:
- Evidence references (sanitized only):

## Implementation acceptance (complete only after runtime evidence exists)

- Candidate implementation commit:
- Isolated database integration-test run:
- Retention/deletion/restore test evidence:
- RBAC and fail-closed access-audit evidence:
- Tamper/checkpoint verification evidence:
- Secret/privacy scan and dependency/security results:
- Service-owner implementation acceptance date:
- Independent reviewer implementation acceptance date:

## Release gate

Until the decision and implementation evidence above are complete, this document is a template, not approval. Keep AP-1.0 in `monitor_only`, zero active enforcement rules, and release **NOT APPROVED**. Never store raw captures, request bodies, tokens, credentials, key material, or real personal data in Git.
