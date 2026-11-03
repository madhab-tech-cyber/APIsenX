# Day 2 Threat-Model and Risk Evidence

**Owner:** Member 1 - Team Lead and Security Architect

**Branch:** `member1/security-architecture`

**Date:** 2026-10-13

**Tracking issue:** Pending creation and linkage before pull request

## Objective

Complete the Member 1 Day 2 task: identify security assets, define trust
boundaries, model credible threats and establish an owned risk register with
reviewable treatment and residual-risk criteria.

## Deliverables prepared

- Expanded [`threat-model.md`](threat-model.md) with:
  - security objectives, assumptions and authorised-lab constraints;
  - nine classified assets with ownership;
  - seven trust boundaries with data, threats, required controls and verification
    ownership;
  - twelve threat scenarios mapped to stable risk IDs; and
  - explicit evidence limits and review triggers.
- Expanded [`risk-register.md`](risk-register.md) with:
  - likelihood, impact, inherent and residual ratings;
  - named treatment owners and target checkpoints;
  - distinction between planned and evidenced controls; and
  - twelve active risks covering privacy, BOLA/BFLA, enforcement, eBPF,
    dependencies, HTTPS observation, lab authentication, audit integrity,
    dashboard access, availability, contract drift and validation gaps.

## Verification evidence

- `python -m unittest tests/test_authorization.py tests/test_mock_api.py -v`
  executed 26 tests successfully.
- `python -m compileall -q src mock-api tests` completed successfully.
- The passing tests support only the current local authorization and mock-API
  controls. They do not reduce risks for unimplemented components.
- Default `python -m unittest discover -v` executed zero tests and is recorded
  as a validation gap in R-012.

## Result and remaining work

The Day 2 security baseline is prepared for issue linkage and peer review. It
does not approve any unfinished runtime control. High residual risks remain open,
and release remains blocked until their required evidence exists.
