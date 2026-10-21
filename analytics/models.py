"""Strict, bounded wire inputs. No headers, bodies or identity assertions."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

SourceID = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,64}$", strict=True)
]
Method = Annotated[
    str, StringConstraints(pattern=r"^[!#$%&'*+.^_`|~0-9A-Za-z-]{1,16}$", strict=True)
]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, hide_input_in_errors=True
    )


class TimedModel(StrictModel):
    @field_validator("observed_at", "created_at", check_fields=False)
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTC offset required")
        return value.astimezone(timezone.utc)


class ApplicationEvent(TimedModel):
    schema_name: Literal["application_event"]
    schema_version: Literal["1.0"]
    event_id: UUID
    source_id: SourceID
    observed_at: datetime
    method: Method
    request_target: Annotated[str, StringConstraints(max_length=4096, strict=True)]
    status_code: Annotated[int, Field(ge=100, le=599)] | None


class CollectorEvent(TimedModel):
    schema_name: Literal["collector_event"]
    schema_version: Literal["1.1"]
    event_id: UUID
    correlation_id: None
    correlation_quality: Literal["unsupported", "ambiguous"]
    source_id: SourceID
    sensor_sequence: Annotated[int, Field(ge=0, le=4294967295)]
    sensor_monotonic_ns: Annotated[int, Field(ge=0, le=18446744073709551615)]
    observed_at: datetime
    direction: Literal["ingress", "egress"]
    method: Literal[
        "UNKNOWN", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
    ]
    status_code: Annotated[int, Field(ge=100, le=599)] | None
    route_template: (
        Annotated[str, StringConstraints(min_length=1, max_length=128)] | None
    )
    route_quality: Literal["approved_template", "route_unavailable"]
    data_classification: Literal["restricted"]

    @model_validator(mode="after")
    def route_consistent(self):
        if (self.route_template is not None) != (
            self.route_quality == "approved_template"
        ):
            raise ValueError("Route quality and presence conflict")
        return self


class CollectorBatch(TimedModel):
    schema_name: Literal["collector_batch"]
    schema_version: Literal["1.0"]
    batch_id: UUID
    created_at: datetime
    events: Annotated[list[CollectorEvent], Field(min_length=1, max_length=64)]


class Alert(StrictModel):
    schema_name: Literal["analytics_alert"] = "analytics_alert"
    schema_version: Literal["1.0"] = "1.0"
    finding_id: UUID
    finding_class: Literal["shadow_candidate", "bola_candidate"]
    reason_code: Literal[
        "PATH_NOT_IN_CONTRACT", "METHOD_NOT_IN_CONTRACT", "UNAUTHORIZED_SUCCESS"
    ]
    policy_version: Literal["AP-1.0"] = "AP-1.0"
    mode: Literal["monitor_only"] = "monitor_only"
    severity: Literal["review_required"] = "review_required"


def fresh(value: datetime, now: datetime):
    # LIMIT-LAB-1.0: no extension of the two-second telemetry age on retries.
    return now - timedelta(seconds=2) <= value <= now + timedelta(seconds=1)
