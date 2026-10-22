"""Signed, nonce-bound lab recommendations. This is NOT the IF-07 active protocol."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import Field, StringConstraints, field_validator

from analytics.audit import AuditWriter
from analytics.detection import POLICY, REASONS, RULE_VERSION, RULES, Observation
from analytics.models import StrictModel, fresh
from src.authorization import load_json

Name = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Contract = Annotated[str, StringConstraints(pattern=r"^sha256:[a-f0-9]{64}$")]


def canonical_bytes(path: Path) -> bytes:
    """Normalize text line endings before calculating source digests."""
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def rules_digest():
    directory = Path(__file__).resolve().parent
    names = (
        "app.py",
        "audit.py",
        "decisions.py",
        "detection.py",
        "flow.py",
        "management.py",
        "masking.py",
        "models.py",
        "normalization.py",
        "store.py",
    )
    sources = {
        name: hashlib.sha256(canonical_bytes(directory / name)).hexdigest()
        for name in names
    }
    sources["src/authorization.py"] = hashlib.sha256(
        canonical_bytes(directory.parent / "src/authorization.py")
    ).hexdigest()
    # Bind file names and boundaries, not an ambiguous concatenation of sources.
    return hashlib.sha256(canonical(sources)).hexdigest()


def permission_digest(roles):
    return hashlib.sha256(canonical(roles)).hexdigest()


class FlowProfile(StrictModel):
    threshold: Annotated[int, Field(ge=1, le=100)]
    window_seconds: Annotated[int, Field(ge=1, le=60)]
    capacity: Annotated[int, Field(ge=1, le=4096)]


class DecisionError(Exception):
    pass


class RequestContext(StrictModel):
    event_id: UUID
    nonce: UUID
    requested_at: datetime

    @field_validator("requested_at")
    @classmethod
    def aware(cls, value):
        if value.utcoffset() is None:
            raise ValueError("Offset required")
        return value.astimezone(timezone.utc)


class SignedPolicy(StrictModel):
    schema_name: Literal["analytics_policy"] = "analytics_policy"
    schema_version: Literal["1.0"] = "1.0"
    policy_version: Literal["AP-1.0"] = POLICY
    rule_version: Literal["DET-1.2"] = RULE_VERSION
    contract_version: Contract
    rules_digest: Digest
    permission_digest: Digest
    flow_profile: FlowProfile | None
    mode: Literal["monitor_only"] = "monitor_only"
    issuer: Name
    key_id: Name
    issued_at: datetime
    expires_at: datetime
    signature: Digest


class SignedDecision(StrictModel):
    schema_name: Literal["analytics_recommendation"] = "analytics_recommendation"
    schema_version: Literal["1.0"] = "1.0"
    decision_id: UUID
    event_id: UUID
    nonce: UUID
    policy_digest: Digest
    policy_version: Literal["AP-1.0"] = POLICY
    rule_version: Literal["DET-1.2"] = RULE_VERSION
    issuer: Name
    key_id: Name
    issued_at: datetime
    expires_at: datetime
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    route: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    action: Literal["allow", "alert", "deny"]
    reason_code: Annotated[str, StringConstraints(pattern=r"^[A-Z0-9_]{1,64}$")]
    rule_id: Annotated[str, StringConstraints(pattern=r"^DET-[A-Z]+-1$")]
    mode: Literal["monitor_only"] = "monitor_only"
    enforce: Literal[False] = False
    signature: Digest


class SignedReply(StrictModel):
    policy: SignedPolicy
    decision: SignedDecision


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def mac(key, purpose, value):
    unsigned = {name: item for name, item in value.items() if name != "signature"}
    return hmac.new(key, purpose + b"\0" + canonical(unsigned), "sha256").hexdigest()


class ReplayWindow:
    def __init__(self, capacity=4096):
        self.capacity, self._seen, self._lock = capacity, {}, RLock()

    def claim(self, identifier, now, expires):
        with self._lock:
            self._seen = {
                key: expiry for key, expiry in self._seen.items() if expiry > now
            }
            if identifier in self._seen:
                raise DecisionError("REPLAY_REJECTED")
            if len(self._seen) >= self.capacity:
                raise DecisionError("REPLAY_CAPACITY")
            self._seen[identifier] = expires


class DecisionService:
    def __init__(self, engine, resolver, key, audit_key, clock):
        if len(key) < 32 or key == audit_key:
            raise ValueError("A separate runtime decision key is required")
        self.engine, self.resolver, self.clock = engine, resolver, clock
        self._key = key
        self.rules_digest = rules_digest()
        self.permission_digest = permission_digest(engine.roles)
        self.contract_version = engine.normalizer.contract_version
        self.loaded_at = clock()
        self.policy_expires_at = self.loaded_at + timedelta(seconds=300)
        self.flow_profile = (
            engine.flow.threshold,
            engine.flow.window,
            engine.flow.capacity,
        )
        self.replays = ReplayWindow()
        self.audit = AuditWriter(
            audit_key, routes=[item.route for item in engine.normalizer.templates]
        )

    def check_policy(self, now):
        try:
            current_permissions = permission_digest(load_json("users.json")["roles"])
            current_rules = rules_digest()
        except Exception:
            raise DecisionError("POLICY_UNAVAILABLE") from None
        if (
            not self.loaded_at <= now < self.policy_expires_at
            or current_rules != self.rules_digest
            or current_permissions != self.permission_digest
            or permission_digest(self.engine.roles) != self.permission_digest
            or self.engine.normalizer.contract_version != self.contract_version
            or (
                self.engine.flow.threshold,
                self.engine.flow.window,
                self.engine.flow.capacity,
            )
            != self.flow_profile
        ):
            raise DecisionError("POLICY_STALE")

    def issue(self, request):
        now = self.clock()
        if not fresh(request.requested_at, now):
            raise DecisionError("REQUEST_TIME_INVALID")
        self.replays.claim(request.nonce, now, now + timedelta(seconds=5))
        self.check_policy(now)
        if self.resolver is None:
            raise DecisionError("CONTEXT_UNAVAILABLE")
        try:
            observation = self.resolver(request.event_id)
        except Exception:
            raise DecisionError("CONTEXT_UNAVAILABLE") from None
        if (
            not isinstance(observation, Observation)
            or observation.event_id != request.event_id
            or observation.observed_at.utcoffset() is None
            or not fresh(observation.observed_at, now)
        ):
            raise DecisionError("CONTEXT_UNAVAILABLE")
        try:
            result = self.engine.evaluate(observation)
        except Exception:
            raise DecisionError("ANALYSIS_UNAVAILABLE") from None
        if permission_digest(self.engine.roles) != self.permission_digest:
            raise DecisionError("CONTEXT_UNAVAILABLE")
        if (
            result.method
            not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"}
            or result.route is None
            or result.reason_code
            in {"CONTEXT_UNAVAILABLE", "CONTEXT_CONFLICT", "FLOW_STATE_UNAVAILABLE"}
        ):
            raise DecisionError("CONTEXT_UNAVAILABLE")
        # Fail before signing when audit append is unavailable; no raw exception output.
        self.audit.append(
            observation, result, self.engine.normalizer.contract_version, now
        )
        policy = SignedPolicy(
            contract_version=self.engine.normalizer.contract_version,
            rules_digest=self.rules_digest,
            permission_digest=self.permission_digest,
            flow_profile=(
                FlowProfile(
                    threshold=self.engine.flow.threshold,
                    window_seconds=int(self.engine.flow.window.total_seconds()),
                    capacity=self.engine.flow.capacity,
                )
                if self.engine.flow
                else None
            ),
            issuer="lab_analytics",
            key_id="decision_v1",
            issued_at=now,
            expires_at=now + timedelta(seconds=60),
            signature="0" * 64,
        )
        policy = policy.model_copy(
            update={
                "signature": mac(
                    self._key, b"policy-v1", policy.model_dump(mode="json")
                )
            }
        )
        decision = SignedDecision(
            decision_id=uuid4(),
            event_id=request.event_id,
            nonce=request.nonce,
            policy_digest=hashlib.sha256(
                canonical(policy.model_dump(mode="json"))
            ).hexdigest(),
            issuer=policy.issuer,
            key_id=policy.key_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=5),
            method=result.method,
            route=result.route,
            action=result.action,
            reason_code=result.reason_code,
            rule_id=result.rule_id,
            signature="0" * 64,
        )
        decision = decision.model_copy(
            update={
                "signature": mac(
                    self._key, b"recommendation-v1", decision.model_dump(mode="json")
                )
            }
        )
        reply = SignedReply(policy=policy, decision=decision)
        if len(reply.model_dump_json().encode()) > 4096:
            raise DecisionError("REPLY_BOUNDS")
        return reply


class DecisionVerifier:
    """Independent consumer verifier; returns a dry-run proposal, never an action."""

    def __init__(self, key, contract_version, roles=None, flow_profile=None):
        if len(key) < 32:
            raise ValueError("Runtime decision key required")
        self._key, self.contract_version = key, contract_version
        self.rules_digest = rules_digest()
        self.permission_digest = permission_digest(
            roles if roles is not None else load_json("users.json")["roles"]
        )
        self.flow_profile = flow_profile or {
            "threshold": 10,
            "window_seconds": 60,
            "capacity": 1000,
        }
        self.replays = ReplayWindow()

    def verify(self, raw, request, target, now):
        try:
            if len(raw) > 4096:
                raise ValueError()

            def unique(pairs):
                result = {}
                for name, value in pairs:
                    if name in result:
                        raise ValueError()
                    result[name] = value
                return result

            json.loads(raw, object_pairs_hook=unique)
            reply = SignedReply.model_validate_json(raw)
            policy, decision = reply.policy, reply.decision
            for record, purpose, ttl in (
                (policy, b"policy-v1", 60),
                (decision, b"recommendation-v1", 5),
            ):
                if record.issuer != "lab_analytics" or record.key_id != "decision_v1":
                    raise ValueError()
                if not hmac.compare_digest(
                    record.signature,
                    mac(self._key, purpose, record.model_dump(mode="json")),
                ):
                    raise ValueError()
                if (
                    record.issued_at.utcoffset() is None
                    or record.expires_at.utcoffset() is None
                ):
                    raise ValueError()
                if not record.issued_at <= now < record.expires_at:
                    raise ValueError()
                if (
                    not timedelta(0)
                    < record.expires_at - record.issued_at
                    <= timedelta(seconds=ttl)
                ):
                    raise ValueError()
            if (
                policy.contract_version != self.contract_version
                or policy.rules_digest != self.rules_digest
                or policy.permission_digest != self.permission_digest
                or policy.flow_profile is None
                or policy.flow_profile.model_dump() != self.flow_profile
                or decision.policy_digest
                != hashlib.sha256(canonical(policy.model_dump(mode="json"))).hexdigest()
                or decision.nonce != request.nonce
                or decision.event_id != request.event_id
                or (decision.method, decision.route) != target
                or decision.reason_code not in REASONS
                or decision.rule_id not in RULES
            ):
                raise ValueError()
            self.replays.claim(decision.nonce, now, decision.expires_at)
            return reply
        except (ValueError, TypeError, RecursionError, DecisionError):
            raise DecisionError("UNTRUSTED_RECOMMENDATION") from None
