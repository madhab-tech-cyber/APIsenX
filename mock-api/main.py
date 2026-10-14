import logging
import sys
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_orders, load_users


app = FastAPI(
    title="APISenX Mock API",
    version="1.0.0",
    description=(
        "Local API-Sentinel security testing lab. "
        "Uses demo tokens and process-local order updates."
    ),
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apisenx.audit")

# Demo credentials for the local security lab only.
# Never use these tokens in production.
TOKENS = {
    "lab-user-a-token": "user-a",
    "lab-user-b-token": "user-b",
    "lab-admin-token": "admin-1",
}

bearer_scheme = HTTPBearer(auto_error=False)

# Load fixtures once.
# Changes persist across requests until this process restarts.
# The original JSON fixture files are not modified.
ORDERS = load_orders()


class OrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["processing", "shipped", "delivered"]


class Order(BaseModel):
    id: str
    owner_id: str
    status: Literal["processing", "shipped", "delivered"]
    total: float = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class OrdersResponse(BaseModel):
    orders: list[Order]


class ErrorDetail(BaseModel):
    code: Literal[
        "UNAUTHENTICATED",
        "FORBIDDEN",
        "NOT_FOUND",
        "INVALID_REQUEST",
    ]
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def error_response(code: str, message: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    # Return errors without FastAPI's default "detail" wrapper.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        body = exc.detail
    else:
        code = {
            400: "INVALID_REQUEST",
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
        }.get(exc.status_code, "INVALID_REQUEST")
        body = error_response(code, str(exc.detail))

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # All request validation failures use HTTP 400.
    return JSONResponse(
        status_code=400,
        content=error_response(
            "INVALID_REQUEST",
            "Request validation failed",
        ),
    )


def audit(
    actor: str,
    action: str,
    order_id: str,
    outcome: str,
) -> None:
    logger.info(
        "audit actor=%s action=%s order_id=%s outcome=%s",
        actor,
        action,
        order_id,
        outcome,
    )


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED",
                "Bearer token required",
            ),
        )

    actor_id = TOKENS.get(credentials.credentials)
    users = load_users()
    actor = users.get(actor_id) if actor_id else None

    if actor is None or actor.get("active") is not True:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED",
                "Invalid or inactive credentials",
            ),
        )

    return actor


def deny(
    actor_id: str,
    action: str,
    order_id: str,
    reason: str,
) -> None:
    audit(
        actor_id,
        action,
        order_id,
        f"DENY:{reason}",
    )
    raise HTTPException(
        status_code=403,
        detail=error_response(
            "FORBIDDEN",
            "Permission denied",
        ),
    )


def check_access(
    actor: dict,
    action: str,
    order_id: str,
) -> dict:
    users = load_users()

    allowed, reason = authorize(
        actor["id"],
        action,
        order_id,
        users,
        ORDERS,
    )

    if not allowed:
        if reason == "order_not_found":
            audit(
                actor["id"],
                action,
                order_id,
                "NOT_FOUND",
            )
            raise HTTPException(
                status_code=404,
                detail=error_response(
                    "NOT_FOUND",
                    "Order not found",
                ),
            )

        deny(
            actor["id"],
            action,
            order_id,
            reason,
        )

    return ORDERS[order_id]


@app.get(
    "/orders",
    response_model=OrdersResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
def list_orders(
    actor: dict = Depends(get_principal),
):
    visible = []
    users = load_users()

    for order_id, order in ORDERS.items():
        allowed, _ = authorize(
            actor["id"],
            "orders:read",
            order_id,
            users,
            ORDERS,
        )
        if allowed:
            visible.append(order)

    audit(actor["id"], "orders:list", "*", "ALLOW")
    return {"orders": visible}


@app.get(
    "/orders/{orderId}",
    response_model=Order,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def get_order(
    orderId: str,
    actor: dict = Depends(get_principal),
):
    order = check_access(actor, "orders:read", orderId)
    audit(actor["id"], "orders:read", orderId, "ALLOW")
    return order


@app.patch(
    "/orders/{orderId}",
    response_model=Order,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_order(
    orderId: str,
    update: OrderUpdate,
    actor: dict = Depends(get_principal),
):
    order = check_access(actor, "orders:manage", orderId)

    # Only status can be changed by this endpoint.
    order["status"] = update.status

    # Updates remain in memory until the API process restarts.
    audit(actor["id"], "orders:manage", orderId, "ALLOW")
    return order


@app.get(
    "/admin/orders",
    response_model=OrdersResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
def list_admin_orders(
    actor: dict = Depends(get_principal),
):
    users = load_users()

    for order_id in ORDERS:
        allowed, reason = authorize(
            actor["id"],
            "orders:read",
            order_id,
            users,
            ORDERS,
        )

        if not allowed:
            deny(
                actor["id"],
                "orders:read:any",
                order_id,
                reason,
            )

    audit(actor["id"], "orders:read:any", "*", "ALLOW")
    return {"orders": list(ORDERS.values())}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # FastAPI adds 422 automatically for request validation.
    # This API's validation handler returns 400 instead.
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                responses = operation.get("responses", {})
                responses.pop("422", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
