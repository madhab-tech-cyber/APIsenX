import logging  # noqa: I001
import math
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import (
    Path as APIPath,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Security,
)
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from authorization import (  # noqa: E402, I001
    authorize,
    load_json,
    load_orders,
    load_users,
)


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


class TokenBucketLimiter:
    """Bounded process-local token buckets with monotonic refill and idle eviction."""

    def __init__(
        self,
        max_keys: int = 4096,
        idle_ttl: float = 60.0,
        clock=time.monotonic,
    ):
        self.max_keys = max_keys
        self.idle_ttl = idle_ttl
        self.clock = clock
        self.buckets: dict[tuple, tuple[float, float, float]] = {}
        self.lock = threading.Lock()

    def consume_many(
        self,
        requests: list[tuple[tuple, float, float, float]],
    ) -> tuple[bool, int, int]:
        """Atomically debit all gates; rejection never partially consumes tokens."""
        now = self.clock()
        with self.lock:
            expired = [
                key
                for key, (_, _, last_seen) in self.buckets.items()
                if now - last_seen >= self.idle_ttl
            ]
            for key in expired:
                self.buckets.pop(key, None)

            staged = {}
            retry_after = 1
            status_code = 429
            for key, rate, capacity, cost in requests:
                if rate <= 0 or capacity <= 0 or cost <= 0:
                    raise ValueError("rate, capacity and cost must be positive")
                if key in staged:
                    tokens, last_refill, _ = staged[key]
                elif key in self.buckets:
                    tokens, last_refill, _ = self.buckets[key]
                else:
                    tokens, last_refill = capacity, now
                    if len(self.buckets) + len(
                        set(staged) - self.buckets.keys()
                    ) >= self.max_keys:
                        return False, 1, 503

                tokens = min(
                    capacity,
                    tokens + max(0.0, now - last_refill) * rate,
                )
                if tokens < cost:
                    retry_after = max(
                        retry_after,
                        math.ceil((cost - tokens) / rate),
                    )
                    status_code = 429
                    return False, max(1, retry_after), status_code
                staged[key] = (tokens - cost, now, now)

            self.buckets.update(staged)
            return True, 0, 200

    def consume(
        self,
        key: tuple,
        rate: float,
        capacity: float,
        cost: float = 1.0,
    ) -> tuple[bool, int, int]:
        """Consume one token bucket through the atomic multi-gate path."""
        return self.consume_many([(key, rate, capacity, cost)])


SERVICE_LIMITER = TokenBucketLimiter()
SUBJECT_LIMITER = TokenBucketLimiter()
ROUTE_COST_LIMITER = TokenBucketLimiter()
SOURCE_LIMITER = TokenBucketLimiter(max_keys=4096)


def rate_limit_error(status_code: int, retry_after: int) -> JSONResponse:
    code = "RATE_LIMITED" if status_code == 429 else "SERVICE_UNAVAILABLE"
    message = (
        "Request rate limit exceeded"
        if status_code == 429
        else "Rate-limit capacity temporarily unavailable"
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response(code, message),
        headers={"Retry-After": str(max(1, retry_after))},
    )


ROUTE_BUDGETS = {
    "GET /orders": (60.0, 120.0, 5.0),
    "GET /orders/{orderId}": (80.0, 160.0, 1.0),
    "GET /admin/orders": (60.0, 120.0, 5.0),
    "GET /support/orders": (60.0, 120.0, 5.0),
    "PATCH /orders/{orderId}": (20.0, 40.0, 10.0),
}
SERVICE_COST_RATE = 400.0
SERVICE_COST_BURST = 800.0
SUBJECT_COST_RATE = 300.0
SUBJECT_COST_BURST = 600.0


def enforce_subject_rate_limit(
    actor: dict,
    route: str,
    rate: float = 80.0,
    burst: float = 160.0,
) -> None:
    """Atomically apply subject, route aggregate and weighted-cost budgets."""
    route_rate, route_burst, cost = ROUTE_BUDGETS.get(
        route, (10.0, 20.0, 10.0)
    )
    gates = [
        (("subject", actor["id"], route), rate, burst, 1.0),
        (("route", route), route_rate, route_burst, 1.0),
        (("service-cost",), SERVICE_COST_RATE, SERVICE_COST_BURST, cost),
        (
            ("subject-cost", actor["id"]),
            SUBJECT_COST_RATE,
            SUBJECT_COST_BURST,
            cost,
        ),
    ]
    allowed, retry_after, status_code = ROUTE_COST_LIMITER.consume_many(gates)
    if not allowed:
        raise HTTPException(
            status_code=status_code,
            detail=error_response(
                "RATE_LIMITED" if status_code == 429 else "SERVICE_UNAVAILABLE",
                "Request rate limit exceeded"
                if status_code == 429
                else "Rate-limit capacity temporarily unavailable",
            ),
            headers={"Retry-After": str(max(1, retry_after))},
        )


# --------------------------------------------------
# Request observation middleware
# --------------------------------------------------

@app.middleware("http")
async def observe_request(request: Request, call_next):
    """Log allowlisted request metadata without logging payloads or query values."""
    correlation_id = str(uuid.uuid4())
    started = time.perf_counter()

    # Supplementary pre-authentication abuse limits. Only the direct peer is
    # used; forwarded headers are deliberately not trusted here.
    if not request.headers.get("authorization"):
        peer = request.client.host if request.client else "unknown"
        preauth_allowed, preauth_retry, preauth_status = (
            SOURCE_LIMITER.consume_many([
                (("source", peer), 10.0, 20.0, 1.0),
                (("unauthenticated",), 20.0, 40.0, 1.0),
            ])
        )
        if not preauth_allowed:
            response = rate_limit_error(preauth_status, preauth_retry)
            response.headers["X-Correlation-ID"] = correlation_id
            logger.info(
                "observation correlation_id=%s method=%s "
                "route=unresolved status=%s outcome=rate_limited",
                correlation_id,
                request.method,
                response.status_code,
            )
            return response

    allowed, retry_after, limit_status = SERVICE_LIMITER.consume(
        ("service",),
        rate=100.0,
        capacity=200.0,
    )
    if not allowed:
        response = rate_limit_error(limit_status, retry_after)
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            "observation correlation_id=%s method=%s route=unresolved "
            "status=%s outcome=rate_limited",
            correlation_id,
            request.method,
            limit_status,
        )
        return response

    try:
        response = await call_next(request)
    except Exception:
        route = request.scope.get("route")
        route_template = getattr(route, "path", "unmatched")

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


# --------------------------------------------------
# Demo tokens and token lifecycle
# --------------------------------------------------

# Demo credentials for the local security lab only.
# Never use these tokens in production.
TOKENS = {
    "lab-user-a-token": "user-a",
    "lab-user-b-token": "user-b",
    "lab-admin-token": "admin-1",
    "lab-support-token": "support-1",
    "lab-tenant-admin-token": "tenant-admin-1",
}

TOKEN_TTL_SECONDS = int(
    os.getenv("APISENX_TOKEN_TTL_SECONDS", "900")
)

REPLAY_WINDOW_SECONDS = 300


def utc_now() -> datetime:
    """Return the current UTC time; replaceable in deterministic tests."""
    return datetime.now(timezone.utc)


TOKEN_METADATA = {
    token: {
        "subject": subject,
        "issued_at": (issued_at := utc_now()),
        "expires_at": issued_at + timedelta(seconds=TOKEN_TTL_SECONDS),
    }
    for token, subject in TOKENS.items()
}

REVOKED_TOKENS: set[str] = set()
USED_NONCES: dict[str, datetime] = {}
NONCE_LOCK = threading.Lock()

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="bearerAuth",
)


# --------------------------------------------------
# Order fixtures
# --------------------------------------------------

# Fixtures load once per process.
# Changes persist until the API process restarts.
# The original JSON fixture files are not modified.
ORDERS = load_orders()


# --------------------------------------------------
# Pydantic models
# --------------------------------------------------

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
        "RATE_LIMITED",
        "SERVICE_UNAVAILABLE",
    ]
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --------------------------------------------------
# Standardized error responses
# --------------------------------------------------

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
    """Return errors in the documented API response format."""

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
    """Return request validation failures as HTTP 400."""

    return JSONResponse(
        status_code=400,
        content=error_response(
            "INVALID_REQUEST",
            "Request validation failed",
        ),
    )


# --------------------------------------------------
# Audit logging
# --------------------------------------------------

def audit(
    actor: str,
    action: str,
    order_id: str,
    outcome: str,
) -> None:
    """Log action metadata without exposing raw actor or resource identifiers."""

    logger.info(
        "audit action=%s outcome=%s actor_ref_present=%s resource_ref_present=%s",
        action,
        outcome,
        bool(actor),
        bool(order_id and order_id != "*"),
    )


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def get_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
) -> dict:
    """Authenticate the demo bearer token and validate its lifecycle."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED",
                "Bearer token required",
            ),
        )

    token = credentials.credentials
    metadata = TOKEN_METADATA.get(token)
    now = utc_now()

    if (
        metadata is None
        or token in REVOKED_TOKENS
        or now >= metadata["expires_at"]
        or now < metadata["issued_at"]
    ):
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED",
                "Invalid, expired, or revoked credentials",
            ),
        )

    actor_id = metadata["subject"]
    users = load_users()
    actor = users.get(actor_id)

    if actor is None or actor.get("active") is not True:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                "UNAUTHENTICATED",
                "Invalid or inactive credentials",
            ),
        )

    # Fail closed when the caller does not select the supported
    # authorization policy contract.
    if request.headers.get("x-policy-version") != "AP-1.0":
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "INVALID_REQUEST",
                "Unsupported or missing policy version",
            ),
        )

    return actor


# --------------------------------------------------
# PATCH replay protection
# --------------------------------------------------

def require_fresh_nonce(nonce: str | None) -> None:
    """Require a unique request nonce within the replay-protection window."""

    if nonce is None or not re.fullmatch(
        r"[A-Za-z0-9._~-]{8,128}",
        nonce,
    ):
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "INVALID_REQUEST",
                "A valid X-Request-Nonce header is required",
            ),
        )

    now = utc_now()
    cutoff = now - timedelta(seconds=REPLAY_WINDOW_SECONDS)

    with NONCE_LOCK:
        # Remove entries older than the replay-protection window.
        for key, seen_at in list(USED_NONCES.items()):
            if seen_at < cutoff:
                USED_NONCES.pop(key, None)

        # Reject a nonce that has already been used within the window.
        if nonce in USED_NONCES:
            raise HTTPException(
                status_code=400,
                detail=error_response(
                    "INVALID_REQUEST",
                    "Duplicate request nonce",
                ),
            )

        USED_NONCES[nonce] = now


# --------------------------------------------------
# Authorization helpers
# --------------------------------------------------

def has_permission(actor: dict, permission: str) -> bool:
    """Resolve permissions from server-side role definitions."""

    role = actor.get("role")
    role_permissions = load_json("users.json").get("roles", {})
    permissions = role_permissions.get(role, [])

    return (
        isinstance(permissions, list)
        and permission in permissions
    )


def require_permission(
    actor: dict,
    permission: str,
    action: str,
) -> None:
    if not has_permission(actor, permission):
        deny(
            actor["id"],
            action,
            "*",
            f"missing_permission:{permission}",
        )


def require_read_permission(
    actor: dict,
    action: str,
) -> None:
    permission_by_role = {
        "customer": "orders:read:own",
        "admin": "orders:read:any",
        "tenant_admin": "orders:read:tenant",
    }

    permission = permission_by_role.get(actor.get("role"))

    if permission is None:
        deny(
            actor["id"],
            action,
            "*",
            "unknown_role",
        )

    require_permission(actor, permission, action)


def deny(
    actor_id: str,
    action: str,
    order_id: str,
    reason: str,
) -> None:
    """Record a denial and return a standardized forbidden response."""

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
    """Apply object-level authorization without disclosing inaccessible orders."""

    users = load_users()

    allowed, reason = authorize(
        actor["id"],
        action,
        order_id,
        users,
        ORDERS,
    )

    if not allowed:
        # Missing, cross-owner, cross-tenant and inaccessible objects
        # receive the same response to avoid disclosing their existence.
        audit(
            actor["id"],
            action,
            order_id,
            "NOT_FOUND_OR_NOT_DISCLOSED",
        )

        raise HTTPException(
            status_code=404,
            detail=error_response(
                "NOT_FOUND",
                "Order not found",
            ),
        )

    return ORDERS[order_id]


# --------------------------------------------------
# GET /orders
# --------------------------------------------------

@app.get(
    "/orders",
    operation_id="listOrders",
    response_model=OrdersResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def list_orders(
    actor: dict = Depends(get_principal),
):
    enforce_subject_rate_limit(actor, "GET /orders")
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

    audit(
        actor["id"],
        "orders:list",
        "*",
        "ALLOW",
    )

    return {"orders": visible}


# --------------------------------------------------
# GET /orders/{orderId}
# --------------------------------------------------

@app.get(
    "/orders/{orderId}",
    operation_id="getOrder",
    response_model=Order,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
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
    enforce_subject_rate_limit(actor, "GET /orders/{orderId}")
    require_read_permission(actor, "orders:read")

    order = check_access(
        actor,
        "orders:read",
        orderId,
    )

    audit(
        actor["id"],
        "orders:read",
        orderId,
        "ALLOW",
    )

    return order


# --------------------------------------------------
# PATCH /orders/{orderId}
# --------------------------------------------------

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
    nonce: str | None = Header(None, alias="X-Request-Nonce"),
    orderId: str = APIPath(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
    actor: dict = Depends(get_principal),
):
    enforce_subject_rate_limit(
        actor,
        "PATCH /orders/{orderId}",
        rate=20.0,
        burst=40.0,
    )
    # Enforce role-specific function-level permissions.
    # Customer and support roles cannot update orders.
    manage_permission = {
        "admin": "orders:manage:any",
        "tenant_admin": "orders:manage:tenant",
    }.get(actor.get("role"))

    if manage_permission is None:
        deny(
            actor["id"],
            "orders:manage",
            orderId,
            "role_not_permitted",
        )

    require_permission(
        actor,
        manage_permission,
        "orders:manage",
    )

    # Enforce object-level authorization before replay validation so
    # unauthorized callers receive the documented authorization response.
    order = check_access(
        actor,
        "orders:manage",
        orderId,
    )

    # Reject missing, malformed, or previously used nonces before mutation.
    require_fresh_nonce(nonce)

    # Only the status field is mutable through this endpoint.
    order["status"] = update.status

    # Changes are process-local and reset when the API restarts.
    audit(
        actor["id"],
        "orders:manage",
        orderId,
        "ALLOW",
    )

    return order


# --------------------------------------------------
# GET /admin/orders
# --------------------------------------------------

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
    enforce_subject_rate_limit(actor, "GET /admin/orders")
    # Check function-level permission even when inventory is empty.
    require_permission(
        actor,
        "orders:read:any",
        "orders:read:any",
    )

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

    audit(
        actor["id"],
        "orders:read:any",
        "*",
        "ALLOW",
    )

    return {"orders": list(ORDERS.values())}


# --------------------------------------------------
# GET /support/orders
# --------------------------------------------------

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
def list_support_orders(
    actor: dict = Depends(get_principal),
):
    enforce_subject_rate_limit(actor, "GET /support/orders")
    # Support receives only explicitly assigned orders and masked fields.
    if (
        actor.get("role") != "support"
        or not has_permission(actor, "orders:read:assigned")
    ):
        deny(
            actor["id"],
            "support:orders:read",
            "*",
            "support_permission_required",
        )

    assigned = actor.get("assigned_order_ids")

    if not isinstance(assigned, list):
        deny(
            actor["id"],
            "support:orders:read",
            "*",
            "support_assignment_missing",
        )

    visible = []

    for order_id in assigned:
        order = ORDERS.get(order_id)

        if order is None:
            continue

        if (
            not actor.get("tenant_id")
            or order.get("tenant_id") != actor.get("tenant_id")
        ):
            continue

        visible.append({
            "id": order["id"],
            "status": order["status"],
        })

    audit(
        actor["id"],
        "support:orders:read",
        "*",
        "ALLOW",
    )

    return {"orders": visible}


# --------------------------------------------------
# OpenAPI customization
# --------------------------------------------------

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Request validation errors are returned as HTTP 400.
    # Document the policy-version header and remove default 422 responses.
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            responses = operation.get("responses", {})
            responses.pop("422", None)

            parameters = operation.setdefault("parameters", [])

            # Nonce validation is performed in the endpoint so authorization
            # failures retain their documented status codes. Document it as
            # required even though the framework-level default is optional.
            if operation.get("operationId") == "updateOrder":
                for parameter in parameters:
                    if (
                        parameter.get("name") == "X-Request-Nonce"
                        and parameter.get("in") == "header"
                    ):
                        parameter["required"] = True

            if not any(
                parameter.get("name") == "X-Policy-Version"
                and parameter.get("in") == "header"
                for parameter in parameters
            ):
                parameters.append({
                    "name": "X-Policy-Version",
                    "in": "header",
                    "required": True,
                    "description": (
                        "Authorization policy contract version; "
                        "only AP-1.0 is accepted."
                    ),
                    "schema": {
                        "type": "string",
                        "enum": ["AP-1.0"],
                    },
                })

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi