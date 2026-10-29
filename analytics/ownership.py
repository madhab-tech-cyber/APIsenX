"""Day 10 read evaluation using Member 5's authoritative lab policy, not claims."""

from dataclasses import dataclass
from uuid import uuid4

from analytics.models import Alert
from src.authorization import authorize


@dataclass(frozen=True)
class OwnershipResult:
    outcome: str
    reason_code: str
    alert: Alert | None = None


class OwnershipEvaluator:
    def __init__(self, users, orders):
        # These mappings must be server-resolved, never supplied by ingestion JSON.
        self.users = users
        self.orders = orders

    def evaluate(
        self, actor_id, object_id, *, policy_version="AP-1.0", status_code=None
    ):
        actor, resource = self.users.get(actor_id), self.orders.get(object_id)
        if not isinstance(actor, dict) or not isinstance(resource, dict):
            return OwnershipResult("unavailable", "CONTEXT_UNAVAILABLE")
        if actor is not None and actor.get("role") not in {
            "customer",
            "admin",
            "tenant_admin",
            "support",
        }:
            return OwnershipResult("unavailable", "CONTEXT_UNAVAILABLE")
        if resource is not None and (
            not isinstance(resource.get("owner_id"), str) or not resource["owner_id"]
        ):
            return OwnershipResult("unavailable", "CONTEXT_UNAVAILABLE")
        try:
            allowed, reason = authorize(
                actor_id,
                "orders:read",
                object_id,
                self.users,
                self.orders,
                policy_version,
            )
        except Exception:
            # Source/fixture outage is not proof of an access violation.
            return OwnershipResult("unavailable", "CONTEXT_UNAVAILABLE")
        unavailable = {
            "unknown_user",
            "inactive_user",
            "order_not_found",
            "policy_version_unsupported",
            "tenant_context_missing_or_invalid",
            "invalid_role_policy",
        }
        if reason in unavailable or reason not in {
            "owner_read_allowed",
            "shared_read_allowed",
            "admin_read_allowed",
            "tenant_admin_read_allowed",
            "tenant_mismatch",
            "order_ownership_required",
            "missing_orders_read_own_permission",
            "missing_orders_read_any_permission",
            "missing_tenant_read_permission",
        }:
            return OwnershipResult("unavailable", "CONTEXT_UNAVAILABLE")
        if allowed:
            return OwnershipResult("allowed", "AUTHORIZED_READ")
        # A denial (403/404) is a prevented attempt, not a confirmed BOLA finding.
        if type(status_code) is int and 200 <= status_code <= 299:
            return OwnershipResult(
                "denied",
                "UNAUTHORIZED_SUCCESS",
                Alert(
                    finding_id=uuid4(),
                    finding_class="bola_candidate",
                    reason_code="UNAUTHORIZED_SUCCESS",
                ),
            )
        return OwnershipResult("denied", "UNAUTHORIZED_READ")
