"""DET-1.2: explainable lab recommendations from authoritative in-process context."""

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import unquote_to_bytes
from uuid import UUID

from src.authorization import authorize, load_json

POLICY = "AP-1.0"
RULE_VERSION = "DET-1.2"
RULES = {"DET-OBS-1", "DET-SHADOW-1", "DET-BOLA-1", "DET-BFLA-1", "DET-FLOW-1"}
REASONS = {
    "CONTEXT_UNAVAILABLE",
    "CONTEXT_CONFLICT",
    "ROUTE_INVALID",
    "ROUTE_DRIFT",
    "AUTHORIZED_OPERATION",
    "ACCESS_PREVENTED",
    "UNAUTHORIZED_OBJECT_SUCCESS",
    "UNAUTHORIZED_FUNCTION_SUCCESS",
    "BUSINESS_FLOW_BURST",
    "FLOW_STATE_UNAVAILABLE",
}


@dataclass(frozen=True)
class Observation:
    """Only a trusted resolver may construct this; never bind it to request JSON."""

    event_id: UUID
    observed_at: datetime
    method: str
    request_target: str = field(repr=False)
    actor_id: str | None = field(default=None, repr=False)
    object_id: str | None = field(default=None, repr=False)
    status_code: int | None = None
    policy_version: str = POLICY


@dataclass(frozen=True)
class Detection:
    action: str
    reason_code: str
    rule_id: str
    method: str | None
    route: str | None
    finding_class: str | None = None
    expected_access: str = "unavailable"


class DetectionEngine:
    def __init__(self, normalizer, users, orders, roles=None, flow=None):
        self.normalizer, self.users, self.orders = normalizer, users, orders
        self.roles = roles if roles is not None else load_json("users.json")["roles"]
        self.flow = flow

    def evaluate(self, observation):
        route = self.normalizer.normalize(
            observation.method, observation.request_target
        )

        def result(
            reason, rule="DET-OBS-1", action="alert", finding=None, access="unavailable"
        ):
            return Detection(
                action, reason, rule, route.method, route.route, finding, access
            )

        if route.classification == "invalid":
            return result("ROUTE_INVALID")
        if route.classification != "documented":
            return result("ROUTE_DRIFT", "DET-SHADOW-1", finding="shadow_candidate")
        actor = self.users.get(observation.actor_id)
        if (
            observation.policy_version != POLICY
            or not isinstance(actor, dict)
            or actor.get("active") is not True
        ):
            return result("CONTEXT_UNAVAILABLE")
        role = actor.get("role")
        if role not in {"customer", "admin", "tenant_admin", "support"}:
            return result("CONTEXT_UNAVAILABLE")
        tenant = actor.get("tenant_id")
        permissions = self.roles.get(role)
        if (
            not isinstance(tenant, str)
            or not tenant.strip()
            or not isinstance(permissions, list)
            or not all(isinstance(value, str) for value in permissions)
        ):
            return result("CONTEXT_UNAVAILABLE")
        operation = (route.method, route.route)
        required = {
            ("GET", "/admin/orders"): {"admin": "orders:read:any"},
            ("GET", "/support/orders"): {"support": "orders:read:assigned"},
            ("GET", "/orders"): {
                "customer": "orders:read:own",
                "admin": "orders:read:any",
                "tenant_admin": "orders:read:tenant",
            },
            ("GET", "/orders/{orderId}"): {
                "customer": "orders:read:own",
                "admin": "orders:read:any",
                "tenant_admin": "orders:read:tenant",
            },
            ("PATCH", "/orders/{orderId}"): {
                "admin": "orders:manage:any",
                "tenant_admin": "orders:manage:tenant",
            },
        }.get(operation)
        if required is None:
            return result("CONTEXT_UNAVAILABLE")
        succeeded = (
            type(observation.status_code) is int
            and 200 <= observation.status_code <= 299
        )
        if required.get(role) not in permissions:
            if succeeded:
                return result(
                    "UNAUTHORIZED_FUNCTION_SUCCESS",
                    "DET-BFLA-1",
                    "deny",
                    "bfla_candidate",
                    "denied",
                )
            return result("ACCESS_PREVENTED", "DET-BFLA-1", access="denied")
        if route.route == "/orders/{orderId}":
            resource = self.orders.get(observation.object_id)
            if (
                not isinstance(resource, dict)
                or not isinstance(resource.get("owner_id"), str)
                or not resource["owner_id"].strip()
            ):
                return result("CONTEXT_UNAVAILABLE")
            # Changed IDs need changed authoritative context; never guess an owner.
            observed_id = (
                unquote_to_bytes(observation.request_target.split("?", 1)[0])
                .decode()
                .split("/")[-1]
            )
            if observed_id != observation.object_id:
                return result("CONTEXT_CONFLICT")
            try:
                allowed, reason = authorize(
                    observation.actor_id,
                    "orders:read" if route.method == "GET" else "orders:manage",
                    observation.object_id,
                    self.users,
                    self.orders,
                    observation.policy_version,
                )
            except Exception:
                return result("CONTEXT_UNAVAILABLE")
            if reason in {
                "tenant_context_missing_or_invalid",
                "invalid_role_policy",
                "order_not_found",
                "unknown_user",
                "inactive_user",
            }:
                return result("CONTEXT_UNAVAILABLE")
            if not allowed:
                if succeeded:
                    return result(
                        "UNAUTHORIZED_OBJECT_SUCCESS",
                        "DET-BOLA-1",
                        "deny",
                        "bola_candidate",
                        "denied",
                    )
                return result("ACCESS_PREVENTED", "DET-BOLA-1", access="denied")
        if (
            self.flow is not None
            and operation == ("PATCH", "/orders/{orderId}")
            and succeeded
        ):
            state = self.flow.observe(observation, tenant)
            if state == "unavailable":
                return result("FLOW_STATE_UNAVAILABLE")
            if state == "burst":
                return result(
                    "BUSINESS_FLOW_BURST",
                    "DET-FLOW-1",
                    finding="flow_candidate",
                    access="allowed",
                )
        return result("AUTHORIZED_OPERATION", action="allow", access="allowed")
