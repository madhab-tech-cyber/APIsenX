# Member 1 Verification Snapshot — October 17

**Date:** 2026-10-17 (Asia/Calcutta)

**Source:** `6b1a427`, merged main fast-forwarded into
`member1/security-architecture`; clean working tree before this work.

## Environment and executed checks

Linux 6.18.55 x86_64, CPython 3.12.14, FastAPI 0.141.1, Starlette 1.6.0,
Pydantic 2.13.4, HTTPX 0.28.1 and PyYAML 6.0.3. This preinstalled environment
differs from requirements.txt; results do not establish a locked build or
the GitHub Actions Python 3.13 environment.

```bash
python -m unittest discover -s tests -v
python -m compileall -q src mock-api tests
```

PASS: 40 methods (10 authorization, 23 HTTP/API, seven OpenAPI). PASS:
compilation. A Starlette deprecation warning recommends an updated test-client
dependency. No package or runtime source was changed for this review.

## Administrative-function diagnostic

Run from the repository root; this command reports every case and exits 1
when a policy violation exists. It changes only temporary in-process fixtures.

```python
import copy
import logging
import sys
from unittest.mock import patch

sys.path.insert(0, 'mock-api')
from fastapi.testclient import TestClient
import main

logging.disable(logging.CRITICAL)
original = copy.deepcopy(main.ORDERS)
violations = 0
with TestClient(main.app) as client:
    for actor in ('user-a', 'user-b', 'admin'):
        subject = 'admin-1' if actor == 'admin' else actor
        for shape in ('empty', 'all-owned', 'mixed'):
            inventory = {} if shape == 'empty' else (
                {k: v for k, v in original.items() if v['owner_id'] == subject}
                if shape == 'all-owned' else original
            )
            with patch.object(main, 'ORDERS', copy.deepcopy(inventory)):
                response = client.get('/admin/orders', headers={
                    'Authorization': 'Bearer lab-' + actor + '-token'
                })
                assert main.ORDERS == inventory
            expected = 200 if actor == 'admin' else 403
            violations += response.status_code != expected
            print(actor, shape, expected, response.status_code)
assert main.ORDERS == original
raise SystemExit(1 if violations else 0)
```

Observed: four FAIL (each customer's empty and all-owned inventory), five PASS
(two mixed customer denials and three admin allows). The admin-owned subset is
empty in current fixtures; the full mixed fixture supplies the populated admin
allow case. No fixture file was rewritten. The initial executed diagnostic
printed these results without a failing exit; the command above adds the exit
gate for reproducible acceptance use. Passing application tests do not override
the four policy failures, all tracked as D11-F01 under R-002.

## Source inspection

- The API, seven OpenAPI tests, pinned direct requirements and a GitHub Actions
  workflow now exist. The workflow targets member5 pushes and pull requests
  whose base is `member5/mock-api`; a PR into main does not match that filter.
- Transitive dependency locks, SBOM and dedicated dependency/static/secret
  scan evidence remain absent from this source.
- OpenAPI tests check documented subsets/selected fields; they do not prove
  reverse operation equality, full security parity or absence of shadow routes.
  The checked-in bearer format still says JWT while runtime uses lab fixtures.
- Collector, detector, enforcement and dashboard remain README placeholders on
  this branch. Peer branches have not been approved by this snapshot.
- Integrated accuracy, latency, rollback, resource and audit controls are
  BLOCKED/UNMEASURED. No external peer feedback or meeting attendance is implied.

## Documentation validation

For the Days 13–20 changes, verify local Markdown targets, balanced code fences,
unique acceptance IDs and no trailing whitespace; run `git diff --check` and
inspect staged content for credentials. Limited credential-pattern inspection
supplements review and is not a dedicated security scanner. The daily evidence
notes refer to this common execution snapshot rather than implying eight
separate runtime runs or eight calendar days of work.
