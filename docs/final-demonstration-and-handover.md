# Day 30 Demonstration Rehearsal and Handover

> Historical rehearsal/handover snapshot. Use the [October 27 current closeout](member1-closeout-2026-10-27.md)
> for later merged analytics, M3 loopback and M6 UI-test CI evidence, M1's
> authorized M4 takeover and actual remaining actions in #61. The required
> human integrated demonstration below is still pending, not replaced by tests.

**Prepared/executed:** 2026-10-19. **Owner:** M1.

**Status:** Local reference-API rehearsal and handover package prepared.
The human-led, integrated final demonstration is PENDING, not completed.
There is no detector or accepted end-to-end pipeline to demonstrate, and no
actual attendees, mentor comments, recording, owner responses or independent
signatures are recorded. [RG-LAB-20261019-01](release-gate-decision.md) holds
release and all active enforcement. Day labels do not establish calendar work.

## Reproducible local rehearsal

Run from the repository root in an already provisioned lab Python environment.
This uses only public synthetic fixtures and in-process FastAPI TestClient;
it opens no listening socket, captures no host traffic and does not test the
real network, detector, audit service or dashboard. Audit logging is suppressed
for compact fixture-only output, not tested or claimed as passing. The original
inventory and every JSON fixture digest are checked after the temporary patch.
The managed strict sandbox initially stalled the TestClient harness; the
recorded PASS used sandbox network permission as documented in the
[verification caveat](member1-oct19-verification.md). No remote target is used.

```python
import hashlib
import logging
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

root = Path.cwd()
assert (root / "mock-api/main.py").is_file(), "Run from repository root"
fixture_paths = sorted((root / "mock_data").glob("*.json"))
assert fixture_paths, "Synthetic fixtures are required"
digests = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture_paths}
sys.path.insert(0, str(root / "mock-api"))
import main

logging.disable(logging.CRITICAL)
original_inventory = main.ORDERS
saved_inventory = deepcopy(original_inventory)
customer = {"Authorization": "Bearer lab-user-a-token"}
admin = {"Authorization": "Bearer lab-admin-token"}

def expect(case_id, response, expected):
    assert response.status_code == expected, (case_id, response.status_code, expected)
    print(f"{case_id}: expected={expected} actual={response.status_code} PASS")

with patch.object(main, "ORDERS", deepcopy(saved_inventory)):
    with TestClient(main.app) as client:
        expect("DEMO-01 owner read", client.get("/orders/order-1001", headers=customer), 200)
        expect("DEMO-02 cross-owner read", client.get("/orders/order-1002", headers=customer), 403)
        expect("DEMO-03 missing identity", client.get("/orders"), 401)
        expect("DEMO-04 customer admin list", client.get("/admin/orders", headers=customer), 403)
        expect("DEMO-05 permitted admin list", client.get("/admin/orders", headers=admin), 200)
        before_denied = deepcopy(main.ORDERS)
        denied = client.patch("/orders/order-1001", headers=customer, json={"status": "shipped"})
        expect("DEMO-06 customer patch", denied, 403)
        assert main.ORDERS == before_denied, "Denied patch mutated inventory"
        allowed = client.patch("/orders/order-1001", headers=admin, json={"status": "shipped"})
        expect("DEMO-07 admin patch", allowed, 200)
        assert main.ORDERS["order-1001"]["status"] == "shipped"
        before_invalid = deepcopy(main.ORDERS)
        invalid = client.patch("/orders/order-1001", headers=admin,
                               json={"status": "shipped", "owner_id": "user-b"})
        expect("DEMO-08 protected field", invalid, 400)
        assert main.ORDERS == before_invalid, "Invalid update mutated inventory"

assert main.ORDERS is original_inventory and main.ORDERS == saved_inventory
assert digests == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture_paths}
print("Inventory restored; all JSON fixture digests unchanged: PASS")
```

Recorded result on this branch: DEMO-01 through DEMO-08 PASS; denial/invalid-write
state assertions PASS; original inventory and fixture digests unchanged PASS.
These eight overlapping API checks are a rehearsal, not eight new independent
detector cases or additions to the 53 test-method count. The nine-inventory
D11-F01 diagnostic in [the baseline](member1-oct19-verification.md) separately
passes; its administrator-owned subset is empty in the synthetic dataset.

## Handover owners and next executable evidence

Assignments below are requests, not claimed owner acceptance. Verified handles
come from [ownership controls](ownership-and-review-controls.md). M1 coordinates
M4 until that member's actual identity is confirmed; no username is invented.

| Role / contact | Delivered reference | Required next evidence / acceptance dependency |
|---|---|---|
| M1 `madhab-tech-cyber` | Policies, risks, release hold and this handover on `member1/security-architecture` | Request independent review; reconcile #14/#21; confirm M4 identity; owner verifies branch protection/checks; schedule real mentor/team demo |
| M2 `renu-stack` | Capture design at `07f1410` | Supported Linux/attach point/privileges, approved HTTPS-safe observation, bounded versioned producer, verifier and loss/privacy results accepted by M3 |
| M3 `aadi3006` | Unmerged library/schemas at `9eb26e4` | Live M2/M4 compatibility and request correlation, authenticated transport, queue/load and timed rule/route rollback evidence |
| M4 identity PENDING | Scaffold `841cde1`; M1 interim review contact | Confirm owner, implement ingestion/discovery/BOLA/BFLA/masking/audit, agree M3/M6 contracts, execute AP/RN/DS/MRVP corpus and privacy evidence |
| M5 `pappukumar96727-sketch` | Merged API/D11/contract repair `1ab289a`; 53 tests PASS | Independent D11 review with M6, full tenant/share/support/version policy coverage, candidate observation hook and signed-token work before non-local use |
| M6 `jayitape` | Unmerged fixture dashboard `39902b3`; limited repository CI | Preserve UI, label fixtures, locked install/lint/typecheck/build/UI tests, M4-backed server RBAC/evidence, actual scans/SBOM and CI/protection verification with M1 |

Review each [TF item](release-findings-triage.md) against exact new commits,
schema/config/corpus versions and artifacts. Preserve original finding IDs and
owner responses; follow [TRIAGE-LAB-1.0](triage-ownership-and-escalation.md) for
independent verification and escalation. Do not count an old branch as proof
of nonresponse; start response/escalation timestamps from an actual request.

## Required human demonstration record — all fields PENDING

Record the actual date/time, authorized lab/run manifest, candidate artifact
digests, attendees/roles and recording or approved minimal notes. Each reviewer
must supply actual questions/comments; each owner supplies their response,
disposition, next commit/evidence or deadline. Record independent sign-offs
against the exact version, conflicts/remaining blockers and the explicit final
decision. M1 cannot self-approve M1-authored policies.

Present [Day 28's outline](final-architecture-and-presentation.md), show actual
API results separately from fixture UI/library artifacts, and demonstrate the
integrated engine only after its prerequisites exist. If incomplete, record
the limitation and hold rather than substituting replayed fixtures for live
findings. No signature/approval/meeting entry is filled on another person's
behalf. #14 being closed does not satisfy its unchecked requirements.

## Operational stop and restart criteria

Keep the lab loopback/private, synthetic and monitor-only. Never weaken TLS or
run privileged sensor/enforcement commands on an unapproved host. No active
network rules exist in this task and no host cleanup is required. If later
authorized operation fails, use the bounded [ENF rollback](enforcement-approval-and-rollback.md)
without flushing unrelated rules; application authorization must continue.

Handover does not remove the release hold. Collect the missing evidence in
[#23](https://github.com/madhab-tech-cyber/APIsenX/issues/23), retain actual human
reviews and rerun the full release gate on a new frozen candidate before any
release decision. Future work begins with these prerequisites, not another
day label declaring them complete.
