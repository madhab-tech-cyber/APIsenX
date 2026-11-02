"""Monitor-only consumer for signed analytics recommendations (issue #102).

Analytics already signs recommendations and ships an independent verifier
(analytics.decisions.DecisionVerifier), but nothing at the API boundary
consumed them — the observation adapter is telemetry-only by design and
stays that way. This consumer closes the verification loop in monitor-only
mode: it verifies a SignedReply, records a bounded structured outcome, and
NEVER changes an API response, blocks a request, or raises into the request
path. The signed schema itself pins mode=monitor_only and enforce=False;
enforcement remains unapproved and unimplemented.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics.decisions import DecisionError, DecisionVerifier  # noqa: E402

LOG = logging.getLogger("apisenx.decision_consumer")
MAX_RECORDS = 1000


class MonitorOnlyDecisionConsumer:
    """Verify signed recommendations at the boundary; log, never act."""

    def __init__(self, verifier):
        self.verifier = verifier
        self.records = []

    @classmethod
    def from_key(cls, key, contract_version, roles=None, flow_profile=None):
        return cls(
            DecisionVerifier(
                key, contract_version, roles=roles, flow_profile=flow_profile
            )
        )

    def consume(self, raw, request, target, now=None):
        """Return a bounded outcome record; never raises, never enforces."""
        now = now or datetime.now(timezone.utc)
        try:
            reply = self.verifier.verify(raw, request, target, now)
        except DecisionError:
            record = {"outcome": "rejected", "reason": "UNTRUSTED_RECOMMENDATION"}
            self._append(record)
            return record
        record = {
            "outcome": "verified_monitor_only",
            "action": reply.decision.action,
            "reason_code": reply.decision.reason_code,
            "rule_id": reply.decision.rule_id,
            "mode": reply.decision.mode,
            "enforce": reply.decision.enforce,
        }
        self._append(record)
        return record

    def _append(self, record):
        # No raw reply, signature or credential material is ever recorded.
        self.records.append(record)
        if len(self.records) > MAX_RECORDS:
            del self.records[:-MAX_RECORDS]
        LOG.info("decision_consumer outcome=%s", record["outcome"])
