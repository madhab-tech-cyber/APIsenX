"""Reproducible, self-labelled lab corpus. Not independent accuracy acceptance."""

import copy
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from analytics.detection import DetectionEngine, Observation
from analytics.flow import FlowMonitor
from analytics.normalization import RouteNormalizer
from src.authorization import load_json, load_orders, load_users

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/detection_cases.json"


def execute_case(case, now=None):
    now = now or datetime.now(timezone.utc)
    users, orders = copy.deepcopy(load_users()), copy.deepcopy(load_orders())
    roles = copy.deepcopy(load_json("users.json")["roles"])
    scenario = case.get("scenario")
    grants = []
    if scenario in {"active_share", "revoked_share", "expired_share"}:
        grants = [
            {
                "grant_id": "synthetic",
                "resource_type": "order",
                "issuer": "synthetic",
                "policy_version": "AP-1.0",
                "tenant_id": "lab-tenant",
                "resource_id": "order-1002",
                "grantee_subject": "user-a",
                "actions": ["orders:read"],
                "revoked": scenario == "revoked_share",
                "expires_at": "2000-01-01T00:00:00+00:00"
                if scenario == "expired_share"
                else "2099-01-01T00:00:00+00:00",
            }
        ]
    if scenario == "other_tenant":
        orders[case["object"]]["tenant_id"] = "synthetic_other_tenant"
    elif scenario == "empty_inventory":
        orders.clear()
    elif scenario == "all_owned_inventory":
        for order in orders.values():
            order["owner_id"] = case["actor"]
    elif scenario == "missing_permission":
        roles["admin"] = []
    elif scenario == "inactive_actor":
        users[case["actor"]]["active"] = False
    elif scenario == "missing_tenant":
        users[case["actor"]].pop("tenant_id")
    normalizer = RouteNormalizer.from_file(
        ROOT / "docs/openapi.yaml", secrets.token_bytes(32), "evaluation-v1"
    )
    engine = DetectionEngine(
        normalizer,
        users,
        orders,
        roles=roles,
        flow=FlowMonitor(secrets.token_bytes(32), threshold=3),
    )
    observation = Observation(
        uuid4(),
        now,
        case["method"],
        case["target"],
        case.get("actor"),
        case.get("object"),
        case["status"],
        "unknown" if scenario == "unknown_policy" else "AP-1.0",
    )
    with patch("src.authorization.load_sharing_grants", return_value=grants):
        if scenario == "flow_burst":
            for _ in range(3):
                engine.evaluate(
                    Observation(
                        uuid4(),
                        now,
                        observation.method,
                        observation.request_target,
                        observation.actor_id,
                        observation.object_id,
                        200,
                    )
                )
        result = engine.evaluate(observation)
    return result, normalizer.contract_version


def measure(rows):
    counts = dict(
        tp=0,
        fp=0,
        tn=0,
        fn=0,
        indeterminate=0,
        label_indeterminate=0,
        unexpected_findings=0,
        total=len(rows),
    )
    for expected, observed, unavailable in rows:
        if expected == "indeterminate":
            counts["label_indeterminate"] += 1
            counts["indeterminate"] += int(unavailable)
            counts["unexpected_findings"] += int(observed is not None)
        elif unavailable:
            counts["indeterminate"] += 1
            if expected is not None:
                counts["fn"] += 1
        elif expected is None:
            counts["fp" if observed is not None else "tn"] += 1
        else:
            counts["tp" if expected == observed else "fn"] += 1
            counts["unexpected_findings"] += int(
                observed is not None and expected != observed
            )
            if observed is not None and expected != observed:
                counts["fp"] += 1

    def ratio(numerator, denominator):
        return numerator / denominator if denominator else None

    return {
        **counts,
        "precision": ratio(counts["tp"], counts["tp"] + counts["fp"]),
        "recall": ratio(counts["tp"], counts["tp"] + counts["fn"]),
        "false_positive_rate": ratio(counts["fp"], counts["fp"] + counts["tn"]),
    }


def main():
    corpus = json.loads(CORPUS.read_text())
    categories, mismatches, version = {}, [], None
    for case in corpus["cases"]:
        result, version = execute_case(case)
        unavailable = result.reason_code in {
            "ROUTE_INVALID",
            "CONTEXT_UNAVAILABLE",
            "CONTEXT_CONFLICT",
            "FLOW_STATE_UNAVAILABLE",
        }
        actual = "indeterminate" if unavailable else result.finding_class
        if actual != case["expected"]:
            mismatches.append(case["id"])
        categories.setdefault(case["category"], []).append(
            (case["expected"], result.finding_class, unavailable)
        )
    print(
        json.dumps(
            {
                "labels": corpus["label_provenance"],
                "label_version": corpus["label_version"],
                "contract_version": version,
                "case_count": len(corpus["cases"]),
                "categories": {
                    name: measure(rows) for name, rows in categories.items()
                },
                "mismatched_case_ids": mismatches,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return int(bool(mismatches))


if __name__ == "__main__":
    raise SystemExit(main())
