
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "mock_data"


def load_json(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_users() -> dict[str, dict[str, Any]]:
    data = load_json("users.json")
    return {user["id"]: user for user in data["users"]}


def load_orders() -> dict[str, dict[str, Any]]:
    data = load_json("orders.json")
    return {order["id"]: order for order in data["orders"]}


def authorize(
    actor_id: str,
    action: str,
    order_id: str,
    users: dict[str, dict[str, Any]],
    orders: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    """Evaluate authorization with tenant isolation before permissions."""
    actor = users.get(actor_id)

    if actor is None:
        return False, "unknown_user"

    if actor.get("active") is not True:
        return False, "inactive_user"

    if action not in {"orders:read", "orders:manage"}:
        return False, "unknown_action"

    order = orders.get(order_id)
    if order is None:
        return False, "order_not_found"

    # Fail closed when authoritative tenant context is missing or invalid.
    actor_tenant = actor.get("tenant_id")
    resource_tenant = order.get("tenant_id")

    if (
        not isinstance(actor_tenant, str)
        or not actor_tenant.strip()
        or not isinstance(resource_tenant, str)
        or not resource_tenant.strip()
    ):
        return False, "tenant_context_missing_or_invalid"

    # Tenant isolation takes precedence over role permissions and ownership.
    if actor_tenant != resource_tenant:
        return False, "tenant_mismatch"

    role = actor.get("role")
    role_permissions = load_json("users.json").get("roles", {})
    permissions = role_permissions.get(role, [])

    if not isinstance(permissions, list):
        return False, "invalid_role_policy"

    # Enforce function-level permissions independently of API route checks.
    if action == "orders:manage":
        if role != "admin":
            return False, "admin_role_required"

        if "orders:manage:any" not in permissions:
            return False, "missing_orders_manage_permission"

        return True, "admin_management_allowed"

    if action == "orders:read":
        if role == "admin":
            if "orders:read:any" not in permissions:
                return False, "missing_orders_read_any_permission"

            return True, "admin_read_allowed"

        if role == "customer":
            if "orders:read:own" not in permissions:
                return False, "missing_orders_read_own_permission"

            if order.get("owner_id") == actor_id:
                return True, "owner_read_allowed"

        return False, "order_ownership_required"

    return False, "access_denied"


def main() -> None:
    users = load_users()
    orders = load_orders()

    print("API-Sentinel Authorization Demo")
    print("-------------------------------------")

    for actor, action, order_id in [
        ("user-a", "orders:read", "order-1001"),
        ("user-a", "orders:read", "order-1002"),
        ("admin-1", "orders:manage", "order-1002"),
    ]:
        allowed, reason = authorize(
            actor, action, order_id, users, orders
        )
        result = "ALLOW" if allowed else "DENY"
        print(f"{actor} | {action} | {order_id} | {result} | {reason}")


if __name__ == "__main__":
    main()
