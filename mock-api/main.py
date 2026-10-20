
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Security,
)
from fastapi import (
    Path as APIPath,
)
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import authorize, load_json, load_orders, load_users

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


@app.middleware("http")
async def observe_request(request: Request, call_next):
    """Emit allowlisted request metadata; never inspect payloads or query values."""
    correlation_id = str(uuid.uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        route = request.scope.get("route")
        route_template = getattr(route, "path", "unmatched")
        # Never emit exception text or traceback in routine telemetry: either
        # may contain request-derived or otherwise sensitive values.
        logger.error(
            "observation correlation_id=%s method=%s route=%s status=500 "
            "outcome=unhandled_exception",
            correlation_id,
            request.method,
            route_template,
        )
        raise

    route = request.scope.get("route")
    route_template = getattr(route, "path", "unmatched")
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "observation correlation_id=%s method=%s route=%s status=%s elapsed_ms=%s",
        correlation_id,
        request.method,
        route_template,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Demo credentials for the local security lab only.
# Never use these tokens in production.
TOKENS = {
    "lab-user-a-token": "user-a",
    "lab-user-b-token": "user-b",
    "lab-admin-token": "admin-1",
    "lab-support-token": "support-1",
    "lab-tenant-admin-token": "tenant-admin-1",
}

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")

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


class SupportOrder(BaseModel):
    id: str
    status: Literal["processing", "shipped", "delivered"]


class SupportOrdersResponse(BaseModel):
    orders: list[SupportOrder]


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
    # Preserve the documented error response structure.
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
    # This API consistently reports request validation errors as 400.
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
    # Do not put raw subject/resource identifiers into routine logs. The
    # identifiers remain server-side inputs to the decision, not telemetry.
    logger.info(
        "audit action=%s outcome=%s actor_ref_present=%s resource_ref_present=%s",
        action,
        outcome,
        bool(actor),
        bool(order_id and order_id != "*"),
    )


def get_principal(
    request: Request,
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

    # A caller must explicitly select the policy contract; unknown or missing
    # versions fail closed before any protected operation is evaluated.
    if request.headers.get("x-policy-version") != "AP-1.0":
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "INVALID_REQUEST",
                "Unsupported or missing policy version",
            ),
        )

    return actor


def has_permission(actor: dict, permission: str) -> bool:
    """Resolve permissions from the server-side role policy, never request data."""
    role = actor.get("role")
    role_permissions = load_json("users.json").get("roles", {})
    permissions = role_permissions.get(role, [])
    return isinstance(permissions, list) and permission in permissions


def require_permission(actor: dict, permission: str, action: str) -> None:
    if not has_permission(actor, permission):
        deny(actor["id"], action, "*", f"missing_permission:{permission}")


def require_read_permission(actor: dict, action: str) -> None:
    permission_by_role = {
        "customer": "orders:read:own",
        "admin": "orders:read:any",
        "tenant_admin": "orders:read:tenant",
    }
    permission = permission_by_role.get(actor.get("role"))
    if permission is None:
        deny(actor["id"], action, "*", "unknown_role")
    require_permission(actor, permission, action)


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
        # Do not reveal whether an inaccessible order exists. Missing,
        # cross-owner, cross-tenant and invalid-context objects share one reply.
        audit(actor["id"], action, order_id, "NOT_FOUND_OR_NOT_DISCLOSED")
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "NOT_FOUND",
                "Order not found",
            ),
        )

    return ORDERS[order_id]


@app.get(
    "/orders",
    operation_id="listOrders",
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
    require_read_permission(actor, "orders:list")
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
    operation_id="getOrder",
    response_model=Order,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def get_order(
    orderId: str = APIPath(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
    actor: dict = Depends(get_principal),
):
    require_read_permission(actor, "orders:read")
    order = check_access(actor, "orders:read", orderId)

    audit(actor["id"], "orders:read", orderId, "ALLOW")

    return order


@app.patch(
    "/orders/{orderId}",
    operation_id="updateOrder",
    response_model=Order,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_order(
    update: OrderUpdate,
    orderId: str = APIPath(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
    actor: dict = Depends(get_principal),
):
    # Function-level permission is checked independently of object ownership.
    manage_permission = {
        "admin": "orders:manage:any",
        "tenant_admin": "orders:manage:tenant",
    }.get(actor.get("role"))
    if manage_permission is None:
        deny(actor["id"], "orders:manage", orderId, "role_not_permitted")
    require_permission(actor, manage_permission, "orders:manage")
    order = check_access(actor, "orders:manage", orderId)

    # Only status can be changed by this endpoint.
    order["status"] = update.status

    # Updates remain in memory until the API process restarts.
    audit(actor["id"], "orders:manage", orderId, "ALLOW")

    return order


@app.get(
    "/admin/orders",
    operation_id="listAdminOrders",
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
    # Must run before inventory iteration, including when inventory is empty.
    require_permission(actor, "orders:read:any", "orders:read:any")
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



@app.get(
    "/support/orders",
    operation_id="listSupportOrders",
    response_model=SupportOrdersResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
def list_support_orders(actor: dict = Depends(get_principal)):
    # Support receives only explicitly assigned records and only masked fields.
    if actor.get("role") != "support" or not has_permission(actor, "orders:read:assigned"):
        deny(actor["id"], "support:orders:read", "*", "support_permission_required")
    assigned = actor.get("assigned_order_ids")
    if not isinstance(assigned, list):
        deny(actor["id"], "support:orders:read", "*", "support_assignment_missing")
    visible = []
    for order_id in assigned:
        order = ORDERS.get(order_id)
        if order is None:
            continue
        if not actor.get("tenant_id") or order.get("tenant_id") != actor.get("tenant_id"):
            continue
        visible.append({"id": order["id"], "status": order["status"]})
    audit(actor["id"], "support:orders:read", "*", "ALLOW")
    return {"orders": visible}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Validation errors are converted to HTTP 400 by the custom handler.
    # Remove FastAPI's default 422 response from every operation.
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                responses = operation.get("responses", {})
                responses.pop("422", None)

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi
