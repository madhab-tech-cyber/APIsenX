
import logging
import sys
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_orders, load_users

app = FastAPI(
    title="APIsenX Mock API",
    version="1.0.0",
    description="Local API-Sentinel security testing lab",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apisenx.audit")

# Local lab tokens only. Never use these as production credentials.
TOKENS = {
    "lab-user-a-token": "user-a",
    "lab-user-b-token": "user-b",
    "lab-admin-token": "admin-1",
}

bearer_scheme = HTTPBearer(auto_error=False)


class OrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["processing", "shipped", "delivered"]


def error_response(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def audit(actor: str, action: str, order_id: str, outcome: str) -> None:
    logger.info(
        "audit actor=%s action=%s order_id=%s outcome=%s",
        actor, action, order_id, outcome
    )


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED", "Bearer token required"
            ),
        )

    actor_id = TOKENS.get(credentials.credentials)
    users = load_users()
    actor = users.get(actor_id) if actor_id else None

    if actor is None or actor.get("active") is not True:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED", "Invalid or inactive credentials"
            ),
        )

    return actor


def deny(actor_id: str, action: str, order_id: str, reason: str) -> None:
    audit(actor_id, action, order_id, f"DENY:{reason}")
    raise HTTPException(
        status_code=403,
        detail=error_response("FORBIDDEN", "Permission denied"),
    )


def check_access(actor: dict, action: str, order_id: str) -> dict:
    users = load_users()
    orders = load_orders()

    allowed, reason = authorize(
        actor["id"], action, order_id, users, orders
    )

    if not allowed:
        if reason == "order_not_found":
            audit(actor["id"], action, order_id, "NOT_FOUND")
            raise HTTPException(
                status_code=404,
                detail=error_response("NOT_FOUND", "Order not found"),
            )
        deny(actor["id"], action, order_id, reason)

    return orders[order_id]


@app.get("/orders")
def list_orders(actor: dict = Depends(get_principal)):
    orders = load_orders()
    visible = []

    for order_id in orders:
        allowed, _ = authorize(
            actor["id"], "orders:read", order_id,
            load_users(), orders
        )
        if allowed:
            visible.append(orders[order_id])

    audit(actor["id"], "orders:list", "*", "ALLOW")
    return {"orders": visible}


@app.get("/orders/{orderId}")
def get_order(
    orderId: str,
    actor: dict = Depends(get_principal),
):
    order = check_access(actor, "orders:read", orderId)
    audit(actor["id"], "orders:read", orderId, "ALLOW")
    return order


@app.patch("/orders/{orderId}")
def update_order(
    orderId: str,
    update: OrderUpdate,
    actor: dict = Depends(get_principal),
):
    order = check_access(actor, "orders:manage", orderId)

    # Modify only the allowed field.
    order["status"] = update.status

    # Persist this mock update for the running process only.
    # The JSON fixture is deliberately not rewritten.
    audit(actor["id"], "orders:manage", orderId, "ALLOW")
    return order


@app.get("/admin/orders")
def list_admin_orders(actor: dict = Depends(get_principal)):
    orders = load_orders()

    for order_id in orders:
        allowed, reason = authorize(
            actor["id"], "orders:read", order_id,
            load_users(), orders
        )
        if not allowed:
            deny(actor["id"], "orders:read:any", order_id, reason)

    audit(actor["id"], "orders:read:any", "*", "ALLOW")
    return {"orders": list(orders.values())}
