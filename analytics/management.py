"""Case-scoped, read-only lab management APIs. No browser-side access gates."""

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import Field, StringConstraints

from analytics.masking import CanonicalMethod, Contract
from analytics.models import StrictModel
from analytics.store import MemoryStore


@dataclass(frozen=True)
class ReaderGrant:
    identity: str
    token: str = field(repr=False)
    case_id: str
    role: str
    expires_at: datetime

    def __post_init__(self):
        if (
            not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.identity)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.case_id)
            or not self.token.isascii()
            or not 32 <= len(self.token) <= 128
            or self.role not in {"viewer", "analyst"}
            or self.expires_at.utcoffset() is None
        ):
            raise ValueError("Invalid reader grant")


class InventoryItem(StrictModel):
    method: CanonicalMethod
    route: str | None
    classification: Literal[
        "documented",
        "method_not_documented",
        "path_not_documented",
        "visibility_unavailable",
    ]
    contract_version: Contract
    observation_count: Annotated[int, Field(ge=1)]
    last_received_at: datetime


class MaskedEvidence(StrictModel):
    expected_access: Literal["allowed", "denied", "unavailable"] | None
    status_code: Annotated[int, Field(ge=100, le=599)] | None


class AlertDetail(StrictModel):
    alert_id: UUID
    finding_class: Literal[
        "shadow_candidate", "bola_candidate", "bfla_candidate", "flow_candidate"
    ]
    rule_id: Annotated[str, StringConstraints(pattern=r"^DET-[A-Z]+-1$")]
    reason_code: str
    explanation: str
    method: CanonicalMethod
    route: str | None
    contract_version: Contract
    evidence: MaskedEvidence
    received_at: datetime
    expires_at: datetime
    severity: Literal["review_required"] = "review_required"
    state: Literal["candidate"] = "candidate"
    mode: Literal["monitor_only"] = "monitor_only"
    data_source: Literal["volatile_lab_observations"] = "volatile_lab_observations"


class InventoryPage(StrictModel):
    schema_name: Literal["inventory_page"] = "inventory_page"
    schema_version: Literal["1.0"] = "1.0"
    items: list[InventoryItem]
    next_cursor: str | None
    mode: Literal["monitor_only"] = "monitor_only"
    data_source: Literal["volatile_lab_observations"] = "volatile_lab_observations"
    visibility: Literal["partial_lab_visibility"] = "partial_lab_visibility"


class AlertPage(StrictModel):
    schema_name: Literal["alert_page"] = "alert_page"
    schema_version: Literal["1.0"] = "1.0"
    items: list[AlertDetail]
    next_cursor: str | None
    mode: Literal["monitor_only"] = "monitor_only"
    data_source: Literal["volatile_lab_observations"] = "volatile_lab_observations"
    visibility: Literal["partial_lab_visibility"] = "partial_lab_visibility"


EXPLANATIONS = {
    "PATH_NOT_IN_CONTRACT": "Undocumented path observed; impact under validation.",
    "METHOD_NOT_IN_CONTRACT": "Undocumented method observed; impact under validation.",
    "ROUTE_DRIFT": "Undocumented operation observed; impact under validation.",
    "UNAUTHORIZED_OBJECT_SUCCESS": "Object policy denied a successful lab response.",
    "UNAUTHORIZED_FUNCTION_SUCCESS": "Function denied a successful lab response.",
    "BUSINESS_FLOW_BURST": "Lab burst heuristic exceeded; manual review required.",
}


class ManagementError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class ManagementService:
    def __init__(self, store, audit, key, readers, case_id, routes, clock):
        self.store, self.audit, self._key = store, audit, key
        self.readers, self.case_id, self.clock = readers, case_id, clock
        self.routes = frozenset(routes) | {"/__unknown__"}
        self.revoked = set()
        self.access = MemoryStore(key, capacity=1000, retention_seconds=300)
        now = clock()
        if any(grant.expires_at > now + timedelta(hours=24) for grant in readers):
            raise ValueError("Reader grant exceeds maximum session lifetime")

    def revoke(self, identity):
        if identity not in {grant.identity for grant in self.readers}:
            raise ValueError("Unknown reader identity")
        self.revoked.add(identity)

    def record(self, reader, resource, outcome):
        reference = hmac.new(
            self._key,
            b"reader-ref\0" + encoded([reader.case_id, reader.identity]),
            "sha256",
        ).hexdigest()
        summary = {
            "schema_name": "analytics_access",
            "schema_version": "1.0",
            "reader_ref": reference,
            "resource": resource,
            "outcome": outcome,
            "mode": "monitor_only",
        }
        self.access.append(
            [("access", uuid4(), self.access.digest(summary), summary)], self.clock()
        )

    def authorize(self, headers, resource):
        if len(headers) != 1 or len(headers[0]) > 256:
            raise ManagementError(401, "AUTHENTICATION_REQUIRED")
        reader = next(
            (
                grant
                for grant in self.readers
                if hmac.compare_digest(
                    headers[0].encode("utf-8"),
                    ("Bearer " + grant.token).encode("ascii"),
                )
            ),
            None,
        )
        if (
            reader is None
            or self.clock() >= reader.expires_at
            or reader.identity in self.revoked
        ):
            raise ManagementError(401, "AUTHENTICATION_REQUIRED")
        if reader.case_id != self.case_id or (
            resource != "inventory" and reader.role != "analyst"
        ):
            self.record(reader, resource, "denied")
            raise ManagementError(403, "FORBIDDEN")
        return reader

    def query(self, parameters, alerts=False):
        values = {}
        allowed = {
            "limit",
            "cursor",
            "method",
            "route",
            "finding_class" if alerts else "classification",
        }
        if len(str(parameters).encode()) > 4096:
            raise ManagementError(400, "INVALID_QUERY")
        for name, value in parameters.multi_items():
            if name not in allowed or name in values or len(value) > 2048:
                raise ManagementError(400, "INVALID_QUERY")
            values[name] = value
        limit = values.pop("limit", "25")
        if not limit.isascii() or not limit.isdigit() or not 1 <= int(limit) <= 100:
            raise ManagementError(400, "INVALID_QUERY")
        cursor = values.pop("cursor", None)
        if "method" in values and not re.fullmatch(r"[A-Z]{1,16}", values["method"]):
            raise ManagementError(400, "INVALID_QUERY")
        if "route" in values and values["route"] not in self.routes:
            raise ManagementError(400, "INVALID_QUERY")
        for name, choices in (
            (
                "classification",
                {
                    "documented",
                    "method_not_documented",
                    "path_not_documented",
                    "visibility_unavailable",
                },
            ),
            (
                "finding_class",
                {
                    "shadow_candidate",
                    "bola_candidate",
                    "bfla_candidate",
                    "flow_candidate",
                },
            ),
        ):
            if name in values and values[name] not in choices:
                raise ManagementError(400, "INVALID_QUERY")
        return int(limit), cursor, values

    def paginate(self, items, reader, parameters, kind):
        limit, cursor, filters = self.query(parameters, kind == "alerts")
        selected = [
            item
            for item in items
            if all(item.get(name) == value for name, value in filters.items())
        ]
        snapshot = hashlib.sha256(encoded(selected)).hexdigest()
        binding = hmac.new(
            self._key,
            b"cursor-binding\0"
            + encoded([reader.identity, reader.case_id, kind, filters, limit]),
            "sha256",
        ).hexdigest()
        offset = 0
        if cursor is not None:
            try:
                if len(cursor) > 1024:
                    raise ValueError()
                raw, signature = cursor.split(".")
                payload = base64.b64decode(
                    raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True
                )
                expected = hmac.new(
                    self._key, b"page-cursor\0" + payload, "sha256"
                ).hexdigest()
                if not hmac.compare_digest(signature, expected):
                    raise ValueError()
                parsed = json.loads(payload)
                if (
                    set(parsed) != {"snapshot", "binding", "offset", "expires"}
                    or parsed["binding"] != binding
                    or self.clock().timestamp() >= parsed["expires"]
                    or type(parsed["offset"]) is not int
                    or not 0 <= parsed["offset"] <= len(selected)
                ):
                    raise ValueError()
                if parsed["snapshot"] != snapshot:
                    raise ManagementError(409, "SNAPSHOT_CHANGED")
                offset = parsed["offset"]
            except (ValueError, KeyError, TypeError):
                raise ManagementError(400, "CURSOR_INVALID") from None
        page = selected[offset : offset + limit]
        next_cursor = None
        if offset + limit < len(selected):
            payload = encoded(
                {
                    "snapshot": snapshot,
                    "binding": binding,
                    "offset": offset + limit,
                    "expires": int(self.clock().timestamp()) + 60,
                }
            )
            raw = base64.urlsafe_b64encode(payload).decode().rstrip("=")
            signature = hmac.new(
                self._key, b"page-cursor\0" + payload, "sha256"
            ).hexdigest()
            next_cursor = raw + "." + signature
        model = AlertPage if kind == "alerts" else InventoryPage
        response = model.model_validate_json(
            json.dumps({"items": page, "next_cursor": next_cursor})
        ).model_dump(mode="json")
        if len(encoded(response)) > 262144:
            raise ManagementError(503, "RESPONSE_BOUNDS")
        return response

    def inventory(self, reader, parameters):
        grouped = {}
        for row in self.store.snapshot(self.clock()):
            key = (
                row["method"],
                row["route"],
                row["classification"],
                row["contract_version"],
            )
            if key not in grouped:
                grouped[key] = {
                    "method": key[0],
                    "route": key[1],
                    "classification": key[2],
                    "contract_version": key[3],
                    "observation_count": 0,
                    "last_received_at": row["received_at"],
                }
            grouped[key]["observation_count"] += 1
            grouped[key]["last_received_at"] = max(
                grouped[key]["last_received_at"], row["received_at"]
            )
        items = [
            InventoryItem(**row).model_dump(mode="json") for row in grouped.values()
        ]
        items.sort(
            key=lambda row: (row["method"], row["route"] or "", row["classification"])
        )
        return self.paginate(items, reader, parameters, "inventory")

    def alert_items(self):
        rows = self.store.snapshot(self.clock())
        if self.audit is not None:
            rows += self.audit.store.snapshot(self.clock())
        items = []
        for row in rows:
            alert = row.get("alert")
            finding = alert["finding_class"] if alert else row.get("finding_class")
            if finding is None:
                continue
            reason = alert["reason_code"] if alert else row["reason_code"]
            if reason not in EXPLANATIONS:
                raise ManagementError(503, "EVIDENCE_UNAVAILABLE")
            identifier = UUID(
                bytes=hmac.new(
                    self._key,
                    b"finding-id\0"
                    + encoded(
                        [
                            self.case_id,
                            row.get("schema_name", "normalized_observation"),
                            row["event_id"],
                            row.get("rule_id", "DET-SHADOW-1"),
                            reason,
                        ]
                    ),
                    "sha256",
                ).digest()[:16],
                version=4,
            )
            item = AlertDetail(
                alert_id=identifier,
                finding_class=finding,
                rule_id=row.get("rule_id", "DET-SHADOW-1"),
                reason_code=reason,
                explanation=EXPLANATIONS[reason],
                method=row["method"],
                route=row["route"],
                contract_version=row["contract_version"],
                evidence=MaskedEvidence(
                    expected_access=row.get("expected_access"),
                    status_code=row.get("status_code"),
                ),
                received_at=row["received_at"],
                expires_at=row["expires_at"],
            )
            items.append(item.model_dump(mode="json"))
        return sorted(items, key=lambda item: item["alert_id"])

    def alerts(self, reader, parameters):
        return self.paginate(self.alert_items(), reader, parameters, "alerts")

    def detail(self, identifier):
        try:
            identifier = str(UUID(identifier))
        except (ValueError, AttributeError):
            raise ManagementError(404, "NOT_FOUND") from None
        for item in self.alert_items():
            if item["alert_id"] == identifier:
                return item
        raise ManagementError(404, "NOT_FOUND")
