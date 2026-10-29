"""Synthetic local-only demonstration; never prints credentials or raw events."""

import os
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from analytics.ownership import OwnershipEvaluator
from src.authorization import load_orders, load_users


def main():
    credential = os.environ.get("APISENTINEL_INGEST_TOKEN")
    source = os.environ.get("APISENTINEL_SOURCE_ID")
    if not credential or not source:
        print("Set the same runtime credential/source as the local analytics service")
        return 2
    event = {
        "schema_name": "application_event",
        "schema_version": "1.0",
        "event_id": str(uuid4()),
        "source_id": source,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "method": "GET",
        "request_target": "/orders/order-1001?synthetic_query=excluded",
        "status_code": 200,
    }
    try:
        # Fixed loopback endpoint; never follow redirects with the credential.
        with httpx.Client(
            base_url="http://127.0.0.1:8001", timeout=2, follow_redirects=False
        ) as client:
            response = client.post(
                "/v1/events",
                json=event,
                headers={"authorization": "Bearer " + credential},
            )
            print("Local ingestion HTTP status:", response.status_code)
            if response.status_code != 200:
                return 1
            print("Acknowledged events:", len(response.json()["accepted_event_ids"]))
    except (httpx.HTTPError, ValueError, KeyError):
        print("Local analytics unavailable or acknowledgement invalid")
        return 1
    engine = OwnershipEvaluator(load_users(), load_orders())
    for label, resource in (
        ("owned read", "order-1001"),
        ("cross-owner read", "order-1002"),
    ):
        result = engine.evaluate("user-a", resource, status_code=200)
        print(label, result.outcome, result.reason_code)
    print("Fixture demo only; no live principal correlation or enforcement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
