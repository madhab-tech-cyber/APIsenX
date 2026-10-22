"""MASK-LAB-1.0 storage gate: explicit projections, never regex redaction fallback."""

import json
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError

from analytics.detection import POLICY, REASONS, RULE_VERSION, RULES
from analytics.models import Alert, StrictModel

Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Contract = Annotated[str, StringConstraints(pattern=r"^sha256:[a-f0-9]{64}$")]
CanonicalMethod = Annotated[
    str, StringConstraints(pattern=r"^[!#$%&'*+.^_`|~0-9A-Z-]{1,16}$")
]
KeyVersion = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


class NormalizedSummary(StrictModel):
    method: CanonicalMethod
    route: str | None
    classification: Literal[
        "documented",
        "method_not_documented",
        "path_not_documented",
        "visibility_unavailable",
    ]
    reason_code: Literal[
        "DOCUMENTED_OPERATION",
        "METHOD_NOT_IN_CONTRACT",
        "PATH_NOT_IN_CONTRACT",
        "ROUTE_EVIDENCE_UNAVAILABLE",
    ]
    contract_version: Contract
    unknown_route_token: Digest | None = None
    unknown_route_key_version: KeyVersion | None = None
    status_code: Annotated[int, Field(ge=100, le=599)] | None = None
    correlation_quality: Literal["unsupported", "ambiguous"] | None = None
    alert: Alert | None = None


class AuditSummary(StrictModel):
    schema_name: Literal["analytics_audit"]
    schema_version: Literal["1.0"]
    event_ref: Digest
    policy_version: Literal["AP-1.0"]
    rule_version: Literal["DET-1.2"]
    contract_version: Contract
    mode: Literal["monitor_only"]
    action: Literal["allow", "alert", "deny"]
    reason_code: str
    rule_id: str
    method: CanonicalMethod | None
    route: str | None
    finding_class: (
        Literal[
            "shadow_candidate", "bola_candidate", "bfla_candidate", "flow_candidate"
        ]
        | None
    )
    expected_access: Literal["allowed", "denied", "unavailable"]


class AccessSummary(StrictModel):
    schema_name: Literal["analytics_access"]
    schema_version: Literal["1.0"]
    reader_ref: Digest
    resource: Literal["inventory", "alerts", "alert_detail"]
    outcome: Literal["allowed", "denied"]
    mode: Literal["monitor_only"] = "monitor_only"


class MaskingError(Exception):
    pass


class StorageMasker:
    def __init__(self, routes=()):
        self.routes = frozenset(routes) | {"/__unknown__"}

    def project(self, summary):
        try:
            model = {
                "analytics_audit": AuditSummary,
                "analytics_access": AccessSummary,
            }.get(summary.get("schema_name"), NormalizedSummary)
            record = model.model_validate_json(json.dumps(summary))
            projected = record.model_dump(mode="json", exclude_unset=True)
            if "route" in projected and projected["route"] is not None:
                if projected["route"] not in self.routes:
                    raise ValueError()
            if isinstance(record, AuditSummary):
                if (
                    record.rule_id not in RULES
                    or record.reason_code not in REASONS
                    or record.rule_version != RULE_VERSION
                    or record.policy_version != POLICY
                ):
                    raise ValueError()
            if isinstance(record, NormalizedSummary):
                unknown = record.classification == "path_not_documented"
                if unknown != bool(
                    record.unknown_route_token and record.unknown_route_key_version
                ):
                    raise ValueError()
                if unknown != (record.route == "/__unknown__"):
                    raise ValueError()
                if (
                    record.route is None
                    and record.classification != "visibility_unavailable"
                ):
                    raise ValueError()
            return projected
        except (ValidationError, ValueError, TypeError, AttributeError):
            raise MaskingError("MASKING_REJECTED") from None
