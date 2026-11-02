"""Day 20 allowlisted volatile audit projections, not a durable audit service."""

import hmac
from dataclasses import asdict

from analytics.detection import REASONS, RULE_VERSION, RULES
from analytics.store import MemoryStore


class AuditWriter:
    def __init__(self, key, capacity=1000, routes=(), store=None):
        self._key = key
        # Default remains the volatile MemoryStore. A DurableStore (issue #83)
        # can be injected explicitly; the durable-audit design still requires
        # its own human acceptance before becoming any default.
        self.store = (
            store
            if store is not None
            else MemoryStore(key, capacity, retention_seconds=300, routes=routes)
        )

    def append(self, observation, detection, contract_version, now):
        if detection.reason_code not in REASONS or detection.rule_id not in RULES:
            raise ValueError("Unknown audit reason/rule")
        event_ref = hmac.new(
            self._key, b"audit-event\0" + observation.event_id.bytes, "sha256"
        ).hexdigest()
        summary = {
            "schema_name": "analytics_audit",
            "schema_version": "1.0",
            "event_ref": event_ref,
            "policy_version": "AP-1.0",
            "rule_version": RULE_VERSION,
            "contract_version": contract_version,
            "mode": "monitor_only",
            **asdict(detection),
        }
        # No target, actor, object, tenant, source credential or raw error fields.
        self.store.append(
            [
                (
                    "analytics_audit",
                    observation.event_id,
                    self.store.digest(summary),
                    summary,
                )
            ],
            now,
        )
