"""Bounded monitor-only observation delivery to the local Sentinel service.

This adapter never returns an enforcement decision and never changes the API
response. API authentication and authorization remain the only access boundary.
"""

import asyncio
import ipaddress
import logging
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

LOG = logging.getLogger("apisenx.sentinel")


def _validated_loopback_endpoint(endpoint):
    """Return a canonical event URL for a literal IPv4 loopback authority.

    DNS names are deliberately rejected: resolving a hostname at connection
    time would make the destination depend on mutable resolver configuration.
    """
    error = "Sentinel endpoint must be a literal IPv4 loopback HTTP URL"
    if not isinstance(endpoint, str) or not endpoint:
        raise ValueError(error)

    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError(error) from None

    try:
        address = ipaddress.ip_address(host) if host else None
    except ValueError:
        address = None

    if (
        parsed.scheme.lower() != "http"
        or address is None
        or address.version != 4
        or not address.is_loopback
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.netloc.endswith(":")
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError(error)

    authority = str(address)
    if port is not None:
        authority += f":{port}"
    return f"http://{authority}/v1/events"


class SentinelObservationAdapter:
    def __init__(self, endpoint, token, source_id, timeout=0.25, transport=None):
        self.endpoint = _validated_loopback_endpoint(endpoint)
        if not token or len(token) < 32 or not token.isascii():
            raise ValueError("Sentinel credential must be bounded and non-default")
        if not source_id or len(source_id) > 64:
            raise ValueError("Invalid Sentinel source identity")
        if not 0 < timeout <= 1:
            raise ValueError("Sentinel timeout must be between 0 and 1 second")
        self.token = token
        self.source_id = source_id
        self.timeout = timeout
        self.transport = transport

    @classmethod
    def from_env(cls):
        endpoint = os.getenv("APISENTINEL_URL")
        token = os.getenv("APISENTINEL_INGEST_TOKEN")
        source_id = os.getenv("APISENTINEL_SOURCE_ID")
        if not endpoint and not token and not source_id:
            return None
        if not endpoint or not token or not source_id:
            raise ValueError("Incomplete Sentinel observation configuration")
        return cls(endpoint, token, source_id)

    async def publish(self, method, route_template, status_code):
        """Publish a privacy-minimized event; failures are bounded and fail-open."""
        if not route_template or len(route_template) > 128:
            return False
        if not isinstance(status_code, int) or not 100 <= status_code <= 599:
            return False
        # Analytics normalizes concrete paths against OpenAPI. Replace every
        # path parameter with a fixed synthetic value before transmission so
        # no real object identifier crosses the observation boundary.
        request_target = re.sub(
            r"\{[A-Za-z][A-Za-z0-9_]*\}", "apisenx-redacted", route_template
        )
        if "{" in request_target or "}" in request_target:
            return False
        event = {
            "schema_name": "application_event",
            "schema_version": "1.0",
            "event_id": str(uuid4()),
            "source_id": self.source_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "method": method,
            # Only the framework's matched route template is sent. No raw path,
            # query string, headers, identity, request body or response body.
            "request_target": request_target,
            "status_code": status_code,
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                transport=self.transport,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await asyncio.wait_for(
                    client.post(
                        self.endpoint,
                        json=event,
                        headers={"Authorization": "Bearer " + self.token},
                    ),
                    timeout=self.timeout,
                )
            accepted = response.status_code == 200
            if os.getenv("APISENTINEL_DIAGNOSTICS") == "1":
                LOG.info(
                    "sentinel_delivery status=%s outcome=%s",
                    response.status_code,
                    "accepted" if accepted else "rejected",
                )
            return accepted
        except Exception:
            # Do not log credentials, URLs, raw exception text or request data.
            LOG.info("sentinel_delivery outcome=unavailable")
            return False


class SentinelObservationMiddleware:
    """Pure ASGI observer so the router's matched route remains in shared scope.

    BaseHTTPMiddleware runs the downstream app with a copied scope; route metadata
    attached by Starlette's router is therefore not visible to its dispatch request.
    This pure ASGI wrapper observes the original scope after the downstream app
    completes and emits only the matched route template and response status.
    """

    def __init__(self, app, adapter=None):
        self.app = app
        self.adapter = adapter

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or self.adapter is None:
            await self.app(scope, receive, send)
            return

        status_code = 500

        async def capture_response(message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, capture_response)

        route = scope.get("route")
        route_template = getattr(route, "path", None)
        method = str(scope.get("method", "")).upper()
        allowed_templates = {
            "/orders",
            "/orders/{orderId}",
            "/orders/apisenx-redacted",
            "/admin/orders",
            "/support/orders",
        }

        # Never trust a route-like string unless it is one of the contract's
        # exact templates. Some middleware/test scopes expose a redacted or raw
        # concrete path through route.path; recover only from the local allowlist.
        if route_template not in allowed_templates:
            route_template = None
            path = scope.get("path", "")
            if method == "GET" and path == "/orders":
                route_template = "/orders"
            elif method == "GET" and path == "/admin/orders":
                route_template = "/admin/orders"
            elif method == "GET" and path == "/support/orders":
                route_template = "/support/orders"
            elif method in {"GET", "PATCH"} and re.fullmatch(
                r"/orders/[A-Za-z0-9-]{1,64}", path
            ):
                route_template = "/orders/{orderId}"

        if os.getenv("APISENTINEL_DIAGNOSTICS") == "1":
            LOG.info(
                "sentinel_observation route=%s status=%s",
                route_template if isinstance(route_template, str) else "unmatched",
                status_code,
            )
        if isinstance(route_template, str) and len(route_template) <= 128:
            await self.adapter.publish(method, route_template, status_code)
