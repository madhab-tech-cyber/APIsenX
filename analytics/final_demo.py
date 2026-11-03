"""Day 30 automated rehearsal; no human attendance or integrated release claim."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.decisions import DecisionVerifier, RequestContext
from analytics.detection import Observation
from analytics.management import ReaderGrant


def main():
    now = datetime.now(timezone.utc)
    reader = ReaderGrant(
        "synthetic_analyst",
        secrets.token_urlsafe(32),
        "final_case",
        "analyst",
        now + timedelta(hours=1),
    )
    settings = Settings(
        secrets.token_urlsafe(32),
        "final_lab",
        secrets.token_bytes(32),
        decision_token=secrets.token_urlsafe(32),
        decision_key=secrets.token_bytes(32),
        case_id="final_case",
        readers=(reader,),
    )
    contexts = {}
    app = create_app(settings, lambda: now, resolver=contexts.get)
    verifier = DecisionVerifier(
        settings.decision_key, app.state.normalizer.contract_version
    )
    ingestion = {"authorization": "Bearer " + settings.ingest_token}
    analysis = {
        "authorization": "Bearer " + settings.decision_token,
        "content-type": "application/json",
    }
    read = {"authorization": "Bearer " + reader.token}
    with TestClient(app) as client:
        for target in (
            "/orders/order-1001",
            "/synthetic/shadow?token=SYNTHETIC_FINAL_SECRET",
        ):
            payload = {
                "schema_name": "application_event",
                "schema_version": "1.0",
                "event_id": str(uuid4()),
                "source_id": settings.source_id,
                "observed_at": now.isoformat(),
                "method": "GET",
                "request_target": target,
                "status_code": 200,
            }
            if (
                client.post("/v1/events", json=payload, headers=ingestion).status_code
                != 200
            ):
                raise RuntimeError("Synthetic ingestion demo failed")
        for label, method, target, resource in (
            ("owned", "GET", "/orders/order-1001", "order-1001"),
            ("bola", "GET", "/orders/order-1002", "order-1002"),
            ("bfla", "GET", "/admin/orders", None),
        ):
            observation = Observation(
                uuid4(), now, method, target, "user-a", resource, 200
            )
            contexts[observation.event_id] = observation
            request = RequestContext(
                event_id=observation.event_id, nonce=uuid4(), requested_at=now
            )
            response = client.post(
                "/v1/recommendations",
                content=request.model_dump_json(),
                headers=analysis,
            )
            if response.status_code != 200:
                raise RuntimeError("Synthetic analysis demo failed")
            route = app.state.normalizer.normalize(method, target).route
            decision = verifier.verify(
                response.content, request, (method, route), now
            ).decision
            print(
                label,
                decision.action,
                decision.rule_id,
                decision.mode,
                decision.enforce,
            )
        inventory = client.get("/v1/inventory?limit=1", headers=read)
        if inventory.status_code != 200 or inventory.json()["next_cursor"] is None:
            raise RuntimeError("Synthetic pagination demo failed")
        second = client.get(
            "/v1/inventory",
            params={"limit": 1, "cursor": inventory.json()["next_cursor"]},
            headers=read,
        )
        alerts = client.get("/v1/alerts", headers=read)
        if (
            second.status_code != 200
            or alerts.status_code != 200
            or len(alerts.json()["items"]) != 3
        ):
            raise RuntimeError("Synthetic management demo failed")
        detail = client.get(
            "/v1/alerts/" + alerts.json()["items"][0]["alert_id"], headers=read
        )
        output = inventory.text + second.text + alerts.text + detail.text
        for forbidden in (
            "SYNTHETIC_FINAL_SECRET",
            "user-a",
            "order-1001",
            settings.ingest_token,
            reader.token,
        ):
            if forbidden in output:
                raise RuntimeError("Synthetic response privacy check failed")
        print(
            "Protected inventory pages: 2; masked alerts:", len(alerts.json()["items"])
        )
        print("Read without credential:", client.get("/v1/alerts").status_code)
    print("Synthetic rehearsal only; human Day 30 review and release remain pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
