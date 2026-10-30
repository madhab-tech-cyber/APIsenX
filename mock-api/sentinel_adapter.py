"""Bounded monitor-only observation delivery to the local Sentinel service.

This adapter never returns an enforcement decision and never changes the API
response. API authentication and authorization remain the only access boundary.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from starlette.middleware.base import BaseHTTPMiddleware

LOG = logging.getLogger("apisenx.sentinel")


class SentinelObservationAdapter:
    def __init__(self, endpoint, token, source_id, timeout=0.25, transport=None):
        if not endpoint.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise ValueError("Sentinel endpoint must be loopback HTTP")
        if not token or len(token) < 32 or not token.isascii():
            raise ValueError("Sentinel credential must be bounded and non-default")
        if not source_id or len(source_id) > 64:
            raise ValueError("Invalid Sentinel source identity")
        if not 0 < timeout <= 1:
            raise ValueError("Sentinel timeout must be between 0 and 1 second")
        self.endpoint = endpoint.rstrip("/") + "/v1/events"
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
        event = {
            "schema_name": "application_event",
            "schema_version": "1.0",
            "event_id": str(uuid4()),
            "source_id": self.source_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "method": method,
            # Only the framework's matched route template is sent. No raw path,
            # query string, headers, identity, request body or response body.
            "request_target": route_template,
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
            return response.status_code == 200
        except Exception:
            # Do not log credentials, URLs, raw exception text or request data.
            LOG.info("sentinel_delivery outcome=unavailable")
            return False


class SentinelObservationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, adapter=None):
        super().__init__(app)
        self.adapter = adapter

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if self.adapter is not None:
            route = request.scope.get("route")
            route_template = getattr(route, "path", None)
            if route_template:
                await self.adapter.publish(
                    request.method, route_template, response.status_code
                )
        return response
