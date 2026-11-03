"""Issue #102: monitor-only signed-decision consumer at the API boundary.

The consumer must verify real signed replies and reject tampered, stale,
replayed and wrong-key replies — while never raising and never enforcing.
"""

import secrets
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

from analytics.app import Settings, create_app  # noqa: E402
from analytics.decisions import RequestContext  # noqa: E402
from analytics.detection import Observation  # noqa: E402
from decision_consumer import MonitorOnlyDecisionConsumer  # noqa: E402

TARGET = ("GET", "/orders/{orderId}")


class DecisionConsumerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic",
            secrets.token_bytes(32),
            **{
                "decision_" + "token": secrets.token_urlsafe(32),
                "decision_" + "key": secrets.token_bytes(32),
            },
        )
        self.observation = Observation(
            uuid4(), self.now, "GET", "/orders/order-1001", "user-a", "order-1001", 200
        )
        self.app = create_app(
            self.settings, lambda: self.now, resolver=lambda _: self.observation
        )
        self.client = TestClient(self.app)
        self.request = RequestContext(
            event_id=self.observation.event_id, nonce=uuid4(), requested_at=self.now
        )
        self.consumer = MonitorOnlyDecisionConsumer.from_key(
            self.settings.decision_key, self.app.state.normalizer.contract_version
        )

    def signed_reply(self):
        response = self.client.post(
            "/v1/recommendations",
            content=self.request.model_dump_json(),
            headers={
                "authorization": "Bearer " + self.settings.decision_token,
                "content-type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.content

    def test_valid_reply_verified_monitor_only(self):
        record = self.consumer.consume(
            self.signed_reply(), self.request, TARGET, self.now
        )
        self.assertEqual(record["outcome"], "verified_monitor_only")
        self.assertEqual(record["action"], "allow")
        self.assertEqual(record["mode"], "monitor_only")
        self.assertFalse(record["enforce"])

    def test_tampered_reply_rejected(self):
        raw = self.signed_reply().replace(b'"allow"', b'"alert"', 1)
        record = self.consumer.consume(raw, self.request, TARGET, self.now)
        self.assertEqual(record["outcome"], "rejected")

    def test_stale_reply_rejected(self):
        raw = self.signed_reply()
        record = self.consumer.consume(
            raw, self.request, TARGET, self.now + timedelta(seconds=6)
        )
        self.assertEqual(record["outcome"], "rejected")

    def test_replayed_reply_rejected(self):
        raw = self.signed_reply()
        first = self.consumer.consume(raw, self.request, TARGET, self.now)
        second = self.consumer.consume(raw, self.request, TARGET, self.now)
        self.assertEqual(first["outcome"], "verified_monitor_only")
        self.assertEqual(second["outcome"], "rejected")

    def test_wrong_key_rejected(self):
        other = MonitorOnlyDecisionConsumer.from_key(
            secrets.token_bytes(32), self.app.state.normalizer.contract_version
        )
        record = other.consume(self.signed_reply(), self.request, TARGET, self.now)
        self.assertEqual(record["outcome"], "rejected")

    def test_garbage_input_rejected_without_raising(self):
        record = self.consumer.consume(b"not json", self.request, TARGET, self.now)
        self.assertEqual(record["outcome"], "rejected")


if __name__ == "__main__":
    unittest.main()
