# Discovery Severity and Triage Policy

**Owner:** Member 1 - Team Lead and Security Architect

**Operational owners:** Member 4 - Detection; Member 5 - API/contract;
Member 6 - dashboard and evidence workflow

**Baseline date:** 2026-10-13

**Status:** Approved Day 9 policy baseline; discovery implementation pending

## 1. Purpose and scope

This policy defines how API-Sentinel turns a route-discovery signal into a
reviewed finding. It covers documented operations, method drift, shadow routes
and zombie routes in the authorised synthetic lab. It applies after the input
has passed the rules in
[`route-normalization-acceptance.md`](route-normalization-acceptance.md).

A discovery signal proves only that observed metadata differs from, or relates
to, an approved contract. It does not by itself prove exposure, exploitability,
an authorization bypass or malicious intent. Discovery stays monitor-only; no
severity or triage state authorizes blocking.

## 2. Discovery classes

| Class | Required meaning | Initial handling |
|---|---|---|
| `documented` | Method and route template exist in the active OpenAPI contract | Inventory only unless another detector raises a finding |
| `method_drift` | Template exists but the observed method is not declared | Open a candidate finding and validate runtime reachability |
| `shadow` | No approved template matches the privacy-safe normalized observation | Open a candidate finding without exposing the raw path |
| `zombie` | A deprecated or explicitly retired operation is still reachable or observed after its removal deadline | Open a candidate finding and verify retirement status and reachability |
| `invalid_observation` | Method/path input failed bounds, encoding, traversal or schema rules | Count the bounded reason; investigate source health or hostile input, but do not inventory it as a route |

`path_not_documented` from the normalization specification maps to `shadow`, and
`method_not_documented` maps to `method_drift`. Zombie status requires contract
or retirement metadata; it MUST NOT be inferred merely because a route looks
old. The current OpenAPI contract declares no deprecated operation, so no
current observation can be confirmed as zombie without separate approved
retirement evidence.

## 3. Severity decision

Severity measures verified business/security impact and realistic
exploitability. Confidence records the quality of evidence. Event count affects
priority and investigation context, but MUST NOT raise severity by itself.

### 3.1 Impact factors

The reviewer records all applicable factors:

- whether the operation is actually reachable at the reviewed observation
  point, rather than only present in noisy or malformed telemetry;
- authentication requirement and whether it is enforced;
- ownership, sharing, tenant and function-level authorization behavior;
- read versus state-changing or administrative capability;
- Public/Internal versus Restricted/Secret data exposure;
- internet, shared-lab or isolated-local reachability;
- contractual retirement status and whether supported clients still depend on
  the operation; and
- evidence of exploitation or repeated unauthorised access.

### 3.2 Severity levels

| Severity | Deterministic threshold | Response target |
|---|---|---|
| Critical | Confirmed reachable operation enables unauthenticated or unauthorised cross-owner/cross-tenant access to Restricted data, administrative control or material state change; or active exploitation is verified | Notify Member 1 immediately; contain active exploitation within 24 hours; block release |
| High | Confirmed reachable shadow/zombie/method-drift operation exposes Restricted data or a privileged/state-changing action, with a credible path to misuse but no verified critical impact | Triage within 1 business day; remediate within 7 days and before release; block release while residual risk remains High |
| Medium | Confirmed reachable drift is read-only or limited to synthetic/Internal data with authentication and authorization intact, or a zombie route remains reachable with its intended controls | Triage within 3 business days; remediate within 30 days or record owner, reason and deadline |
| Low | Confirmed low-impact metadata/contract hygiene issue with no sensitive data, privilege or state-change exposure and a constrained local attack surface | Triage within 5 business days; schedule maintenance |
| Informational | Inventory observation, unvalidated candidate or invalid/noisy signal with no demonstrated security impact | Validate or close as evidence permits; no vulnerability claim |

Use the highest satisfied threshold. A Critical or High rating requires
reachability plus concrete authorization, data or action evidence; an opaque
unknown-route fingerprint alone starts as Informational.

### 3.3 Confidence

| Confidence | Evidence requirement |
|---|---|
| High | Reproducible request against the authorised lab, matched contract/policy version and reviewed response/control evidence |
| Medium | Correlated observations from an authenticated source plus contract/runtime evidence, but no full reproduction |
| Low | Single source, incomplete correlation, unknown version, or evidence affected by loss/normalization ambiguity |

Severity and confidence remain separate fields. A low-confidence candidate can
be prioritised for validation without being presented as a confirmed High or
Critical vulnerability.

## 4. Triage lifecycle

Allowed states and transitions are:

`new -> validating -> confirmed -> remediating -> resolved -> verified`

`new|validating -> false_positive`

`confirmed -> accepted_risk` only through the risk-acceptance rule below.

| State | Entry requirement | Exit requirement |
|---|---|---|
| `new` | Deduplicated detector candidate created with source and versions | Assigned owner begins validation |
| `validating` | Owner, classification hypothesis and evidence plan recorded | Reproduction supports `confirmed`, or cause supports `false_positive` |
| `confirmed` | Reachability, discovery class, severity, confidence and impact evidence reviewed | Remediation starts or Member 1 records accepted risk |
| `remediating` | Fix owner, target and rollback plan recorded | Fix merged/deployed to the authorised lab and retest requested |
| `resolved` | Claimed fix or retirement completed | Independent/reviewer retest produces `verified`, or failure returns it to `confirmed` |
| `verified` | Original reproduction fails safely and regression/contract checks pass | Terminal unless regression reopens a linked finding |
| `false_positive` | Evidence identifies parser/normalizer error, stale contract selection, duplicate telemetry or another non-finding cause | Terminal with cause and regression action where applicable |
| `accepted_risk` | Member 1 records reason, compensating controls, residual severity, owner and expiry | Re-review by expiry or on scope/evidence change |

States MUST NOT skip `validating` and `confirmed` solely because a detector
assigned a severity. Day 25 may expand workflow mechanics, but it must preserve
these evidence and approval gates.

## 5. Triage procedure and ownership

1. **Ingest safely.** Accept only authenticated, versioned source metadata.
   Reject/quarantine unknown schema versions and keep raw queries, credentials,
   bodies and parameter values out of the finding.
2. **Deduplicate.** Use discovery class, canonical method/template or unknown
   route token plus its key version, environment and contract version. Query
   data never participates in the key.
3. **Assign.** Member 4 owns detection validation. Member 5 confirms contract,
   retirement and runtime behavior. Member 1 owns severity disputes and risk
   acceptance. Member 6 owns protected workflow/display evidence when present.
4. **Validate scope and source.** Confirm the target is the authorised lab, the
   observation point is approved, telemetry loss is known and the correct
   contract version was selected.
5. **Reproduce safely.** Prefer non-destructive synthetic requests. Do not probe
   third parties, weaken TLS, use real credentials or retain raw sensitive
   traffic. Any state-changing reproduction needs the component owner's
   approval and cleanup plan.
6. **Assess access and impact.** Test authentication, role, ownership, sharing,
   tenant and admin boundaries independently. A denial can still confirm route
   existence but lowers impact when the control is effective.
7. **Decide and document.** Record class, severity, confidence, evidence,
   affected versions, owner, target and relevant risk IDs. False-positive and
   false-negative counts are reported separately.
8. **Remediate and verify.** Align runtime and approved contract, retire the
   route, or restore the missing control. An owner other than the implementer
   reviews the regression evidence before `verified`.

## 6. Privacy-safe finding record

A finding may contain only:

- opaque finding and correlation identifiers;
- discovery class, canonical method/template or keyed unknown-route token;
- unknown-route key version, contract/policy/schema versions and lab
  environment identifier;
- first/last observed time, bounded count and telemetry-quality flags;
- severity, confidence, state, stable reason codes and mapped risk IDs;
- owner, response target and links to access-controlled evidence; and
- privacy-safe remediation and verification summaries.

It MUST NOT contain a raw unknown path, path parameter, query string,
authorization value, cookie, request/response body, HMAC key or real personal
data. Finding access is Restricted. Public issues and screenshots use only
sanitised summaries.

## 7. Acceptance scenarios

| ID | Scenario | Expected decision |
|---|---|---|
| DS-01 | `GET /orders/{orderId}` matches the active contract | Inventory only; no discovery finding |
| DS-02 | One unknown-route token appears without reachability evidence | `shadow`, Informational, Low confidence, `new` |
| DS-03 | Unknown route is reproduced locally, requires auth and returns only synthetic/Internal health data | `shadow`, Low or Medium according to demonstrated impact |
| DS-04 | Reachable shadow admin write accepts an ordinary customer | Critical, High confidence; immediate notification and release block |
| DS-05 | Reachable undeclared `DELETE` requires admin and performs a material state change | `method_drift`, High; release block pending remediation |
| DS-06 | Undeclared method is consistently denied before application action | `method_drift`; severity based on remaining information exposure, not automatically High |
| DS-07 | Approved deprecated route remains reachable with intended auth before its retirement deadline | Track retirement; no zombie finding solely from deprecation |
| DS-08 | Retired route remains reachable after its deadline with intact controls | `zombie`, normally Medium; raise for sensitive data/action impact |
| DS-09 | Contract version mismatch explains a candidate and correct-version comparison is documented | `false_positive`; fix version selection/regression coverage |
| DS-10 | Malformed percent encoding produces only a bounded invalid counter | `invalid_observation`; no route inventory record |
| DS-11 | Same unknown path arrives with different query secrets | One deduplicated token; queries absent from evidence |
| DS-12 | High event volume has no additional impact evidence | Priority may rise; severity remains unchanged |
| DS-13 | Cross-tenant read is reproducible on a documented route | Route stays documented; send to BOLA policy triage as Critical rather than relabeling it shadow |
| DS-14 | Fix is merged but no independent regression test exists | `resolved`, not `verified` |
| DS-15 | Reviewer proposes risk acceptance without an expiry or compensating control | Remain `confirmed`; acceptance denied |

## 8. Approval and evidence boundary

This policy approves the severity and triage decisions above. It does not prove
that discovery, retirement metadata, finding persistence, workflow RBAC or
dashboard states are implemented. R-003, R-008, R-009, R-011, R-012 and R-013
remain open or mitigating until their required runtime and test evidence exists.
