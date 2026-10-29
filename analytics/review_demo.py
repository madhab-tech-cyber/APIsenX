"""Runnable Day 14 review pack with explicitly synthetic, in-process context."""

import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.decisions import DecisionVerifier, RequestContext
from analytics.detection import Observation


def main():
    now = datetime.now(timezone.utc)
    settings = Settings(
        secrets.token_urlsafe(32),
        "review_lab",
        secrets.token_bytes(32),
        decision_token=secrets.token_urlsafe(32),
        decision_key=secrets.token_bytes(32),
    )
    examples = [
        ("owner read", "GET", "/orders/order-1001", "order-1001"),
        ("cross-owner success", "GET", "/orders/order-1002", "order-1002"),
        ("function-level success", "GET", "/admin/orders", None),
        ("shadow candidate", "GET", "/synthetic/new-route?token=SYNTHETIC_QUERY", None),
    ]
    contexts = {}
    app = create_app(settings, clock=lambda: now, resolver=contexts.get)
    verifier = DecisionVerifier(
        settings.decision_key, app.state.normalizer.contract_version
    )
    with TestClient(app) as client:
        for label, method, target, object_id in examples:
            observation = Observation(
                uuid4(), now, method, target, "user-a", object_id, 200
            )
            contexts[observation.event_id] = observation
            request = RequestContext(
                event_id=observation.event_id, nonce=uuid4(), requested_at=now
            )
            response = client.post(
                "/v1/recommendations",
                content=request.model_dump_json(),
                headers={
                    "authorization": "Bearer " + settings.decision_token,
                    "content-type": "application/json",
                },
            )
            if response.status_code != 200:
                raise RuntimeError("Synthetic review recommendation failed")
            route = app.state.normalizer.normalize(method, target).route
            reply = verifier.verify(response.content, request, (method, route), now)
            decision = reply.decision
            print(
                label,
                decision.action,
                decision.rule_id,
                decision.reason_code,
                decision.mode,
            )
        rows = app.state.decisions.audit.store.snapshot(now)
        if any(
            marker in repr(rows)
            for marker in (
                "user-a",
                "order-1001",
                "SYNTHETIC_QUERY",
                settings.decision_token,
            )
        ):
            raise RuntimeError("Synthetic privacy check failed")
        print("Masked volatile audit records:", len(rows))
    print(
        "Synthetic automated demo only: no human meeting, feedback or sign-off recorded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
