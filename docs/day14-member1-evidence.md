# Day 14 Member 1 Evidence

**Date:** 2026-10-15 (Asia/Calcutta)

**Branch:** `member1/security-architecture`

**Issue:** [#14](https://github.com/madhab-tech-cyber/APIsenX/issues/14)

**Task:** Run review agenda and collect open risks (Member 1 plan, page 3).

**Result:** Repository review/rehearsal and open-risk collection performed;
human meeting, feedback and owner sign-off remain pending. Integrated Week 2
acceptance is NOT APPROVED.

## Reviewed evidence

[day14-mid-review.md](day14-mid-review.md) contains the timed meeting agenda,
executed asynchronous review record, component status, diagnostic results,
thirteen unresolved risks and required owner handoffs. It extends
[MRVP-1.0](mid-review-validation-plan.md), without claiming its future runs passed.

The supplied PDF SHA-256 remains
`4379b0938dcf67499b633079d686b937a14648f7b3bc91768d8efa432c29568c`.
Its pages 3-4 define the assignment, evidence and member-branch/review workflow.
No new PDF or replacement schedule was created.

Pinned source: `a2f837a5ab2df492edd1037b2d16a1dac726f06b`.
All 53 files were fetched into a separate local snapshot and verified against
Git blob hashes. Main was `f566d7a`; Member 1 was two commits ahead and zero
behind at audit time. Member 2's `07f1410` tree and selected design/header/evidence
files were also read; its reported tests were not independently executed here.
Members 3/4/6 remained at `841cde1`; Member 5 was `fd49407`.

GitHub evidence at audit time: PR #13 open/draft with zero submitted reviews;
zero source check runs and zero combined statuses; empty repository ruleset
list; branch endpoints report unprotected; CODEOWNERS has placeholder handles.
No approval is inferred from the absence of a failing check.

## Executed local checks

Windows 11 build 22631, CPython 3.12.6, FastAPI 0.109.0, Starlette 0.35.1,
Pydantic 2.5.3, HTTPX 0.27.2 and AnyIO 4.14.2 were used. This records the test
environment, not an approved dependency lock or vulnerability-free package set.

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q src mock-api tests
```

Results: 26 application tests passed; compileall passed. This explicit invocation
does not establish default discovery or CI. Four separate TestClient diagnostics
gave two PASS and two FAIL results: owner read 200, cross-owner read 403, empty
admin inventory 200 and all-owned admin inventory 200. The last two require 403
under AP-1.0 and reconfirm D11-F01. Diagnostic exit status was 1; it is not a
passing acceptance test. Original fixture files and global inventory were
preserved. The 26 methods and four diagnostics are reported separately.

### Reproducible admin diagnostic

Run the following from the pinned repository root in the recorded environment.
It uses only public synthetic lab fixtures and temporary in-process patches:

```python
import copy
import sys
from unittest.mock import patch

sys.path.insert(0, 'mock-api')
from fastapi.testclient import TestClient
import main

original = copy.deepcopy(main.ORDERS)
all_owned = {k: v for k, v in original.items() if v['owner_id'] == 'user-a'}
violations = 0
with TestClient(main.app) as client:
    for name, inventory in [('empty', {}), ('all-owned', all_owned)]:
        with patch.object(main, 'ORDERS', copy.deepcopy(inventory)):
            response = client.get(
                '/admin/orders',
                headers={'Authorization': 'Bearer lab-user-a-token'},
            )
            print(name, 'expected=403', 'actual=', response.status_code)
            assert main.ORDERS == inventory
            violations += response.status_code != 403
assert main.ORDERS == original
raise SystemExit(1 if violations else 0)
```

Expected current-baseline output: both actual statuses are 200, exit 1. After
remediation both must be 403 with independent allowed/denied/unknown-role and
inventory-shape regressions before finding closure. The two ordinary demo cases
are reproducible through the existing owner and cross-user HTTP tests.

Documentation local links, fenced-block balance, whitespace and a limited
credential-pattern check were run on the scoped documents. Detailed results
are recorded in draft PR #13. A pattern check is not dedicated secret scanning.
No dependency/static/container scan, Linux verifier run, integrated detector
accuracy test, paired latency measurement or human meeting was performed.

## Scope and remaining work

Only this review record, this evidence note and the risk-register update are
delivered. No runtime source, dependency, peer branch, reviewer approval or
security setting is changed. The current R-011 note now recognizes the API's
400 validation responses while retaining its unresolved authentication/contract
drift; no risk rating is reduced. Human meeting and component review are pending,
so Issue #14 stays open and the PR remains draft.
