"""Loopback lab analytics. Configure runtime secrets; run with --no-access-log."""

import asyncio
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from analytics.decisions import DecisionError, DecisionService, RequestContext
from analytics.detection import DetectionEngine
from analytics.flow import FlowMonitor
from analytics.models import Alert, ApplicationEvent, CollectorBatch, fresh
from analytics.normalization import RouteNormalizer
from analytics.store import MemoryStore, StoreError
from src.authorization import load_orders, load_users

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("apisenx.analytics")


@dataclass(frozen=True)
class Settings:
    ingest_token: str = field(repr=False)
    source_id: str
    hmac_key: bytes = field(repr=False)
    key_version: str = "lab-v1"
    contract: Path = ROOT / "docs/openapi.yaml"
    capacity: int = 1000
    retention_seconds: int = 300
    decision_token: str | None = field(default=None, repr=False)
    decision_key: bytes | None = field(default=None, repr=False)

    def __post_init__(self):
        if not self.ingest_token.isascii() or not 32 <= len(self.ingest_token) <= 128:
            raise ValueError("A bounded, non-default runtime credential is required")
        # Use the wire type's constraints for the configured identity as well.
        from pydantic import TypeAdapter

        from analytics.models import SourceID

        TypeAdapter(SourceID).validate_python(self.source_id)
        if (self.decision_token is None) != (self.decision_key is None):
            raise ValueError("Configure both decision credential and signing key")
        if self.decision_token is not None:
            if (
                not self.decision_token.isascii()
                or not 32 <= len(self.decision_token) <= 128
                or self.decision_token == self.ingest_token
                or len(self.decision_key) < 32
                or self.decision_key == self.hmac_key
            ):
                raise ValueError("Separate bounded decision credentials are required")

    @classmethod
    def from_env(cls):
        try:
            return cls(
                ingest_token=os.environ["APISENTINEL_INGEST_TOKEN"],
                source_id=os.environ["APISENTINEL_SOURCE_ID"],
                hmac_key=bytes.fromhex(os.environ["APISENTINEL_HMAC_KEY"]),
                key_version=os.environ["APISENTINEL_KEY_VERSION"],
                decision_token=os.environ.get("APISENTINEL_DECISION_TOKEN"),
                decision_key=(
                    bytes.fromhex(os.environ["APISENTINEL_DECISION_KEY"])
                    if "APISENTINEL_DECISION_KEY" in os.environ
                    else None
                ),
            )
        except (KeyError, ValueError):
            raise ValueError(
                "Analytics runtime configuration missing or invalid"
            ) from None


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def reject_constant(_):
    raise ValueError("Nonfinite JSON")


def create_app(settings=None, clock=None, resolver=None):
    settings = settings or Settings.from_env()
    clock = clock or (lambda: datetime.now(timezone.utc))
    normalizer = RouteNormalizer.from_file(
        settings.contract, settings.hmac_key, settings.key_version
    )
    store = MemoryStore(
        settings.hmac_key, settings.capacity, settings.retention_seconds
    )
    decision_service = None
    if settings.decision_token is not None:
        engine = DetectionEngine(
            normalizer, load_users(), load_orders(), flow=FlowMonitor(settings.hmac_key)
        )
        decision_service = DecisionService(
            engine, resolver, settings.decision_key, settings.hmac_key, clock
        )

    @asynccontextmanager
    async def lifespan(_):
        async def expire():
            while True:
                store.purge(clock())
                if decision_service is not None:
                    decision_service.audit.store.purge(clock())
                    decision_service.engine.flow.purge(clock())
                await asyncio.sleep(1)

        task = asyncio.create_task(expire())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="API-Sentinel Analytics",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.normalizer = normalizer
    app.state.decisions = decision_service
    in_flight = 0

    def error(status, code):
        LOG.info("ingestion outcome=%s", code)
        return JSONResponse({"detail": code}, status_code=status)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        nonlocal in_flight
        if request.method == "GET" and request.url.path == "/health":
            return await call_next(request)
        is_decision = request.url.path == "/v1/recommendations"
        if is_decision and decision_service is None:
            return error(404, "NOT_FOUND")
        authorization = request.headers.getlist("authorization")
        expected = (
            "Bearer "
            + (settings.decision_token if is_decision else settings.ingest_token)
        ).encode("ascii")
        if (
            len(authorization) != 1
            or len(authorization[0]) > 256
            or not hmac.compare_digest(authorization[0].encode("utf-8"), expected)
        ):
            return error(401, "AUTHENTICATION_REQUIRED")
        if request.method != "POST" or request.url.path not in {
            "/v1/events",
            "/v1/batches",
            "/v1/recommendations",
        }:
            return error(404, "NOT_FOUND")
        if request.headers.get("content-encoding", "identity") != "identity":
            return error(415, "CONTENT_ENCODING_UNSUPPORTED")
        content_types = request.headers.getlist("content-type")
        if len(content_types) != 1 or content_types[0].lower() not in {
            "application/json",
            "application/json; charset=utf-8",
        }:
            return error(415, "JSON_REQUIRED")
        limit = 262144 if request.url.path == "/v1/batches" else 4096
        lengths = request.headers.getlist("content-length")
        if lengths:
            if (
                len(lengths) != 1
                or not lengths[0].isascii()
                or not lengths[0].isdigit()
            ):
                return error(400, "INVALID_LENGTH")
            if len(lengths[0]) > 9 or int(lengths[0]) > limit:
                return error(413, "BODY_TOO_LARGE")
        if in_flight >= 4:
            return error(503, "INGESTION_BUSY")
        in_flight += 1

        async def read_bounded():
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > limit:
                    raise OverflowError()
                body.extend(chunk)
            return bytes(body)

        try:
            raw = await asyncio.wait_for(read_bounded(), timeout=1)
            if lengths and len(raw) != int(lengths[0]):
                return error(400, "INVALID_LENGTH")
            json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=unique_object,
                parse_constant=reject_constant,
            )
            request.state.wire = raw
            return await call_next(request)
        except OverflowError:
            return error(413, "BODY_TOO_LARGE")
        except TimeoutError:
            return error(408, "BODY_TIMEOUT")
        except (UnicodeError, ValueError, RecursionError):
            return error(400, "INVALID_JSON")
        except Exception:
            # Never attach exception text/traceback or raw request to telemetry.
            return error(503, "INGESTION_UNAVAILABLE")
        finally:
            in_flight -= 1

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "monitor_only", "storage": "volatile"}

    def append(items, now):
        try:
            store.append(items, now)
        except StoreError as failure:
            status = 409 if failure.reason == "EVENT_ID_CONFLICT" else 503
            return error(status, failure.reason)
        return None

    @app.post("/v1/events")
    async def ingest_event(request: Request):
        try:
            event = ApplicationEvent.model_validate_json(request.state.wire)
        except ValidationError:
            return error(422, "SCHEMA_INVALID")
        now = clock()
        if event.source_id != settings.source_id:
            return error(403, "SOURCE_NOT_AUTHORIZED")
        if not fresh(event.observed_at, now):
            return error(422, "EVENT_TIME_INVALID")
        result = normalizer.normalize(event.method, event.request_target)
        if result.classification == "invalid":
            return error(422, result.reason_code)
        summary = {**result.to_dict(), "status_code": event.status_code}
        if result.classification != "documented":
            summary["alert"] = Alert(
                finding_id=uuid4(),
                finding_class="shadow_candidate",
                reason_code=result.reason_code,
            ).model_dump(mode="json")
        # Dedup is over the masked semantic projection, never raw query/body.
        failed = append(
            [
                (
                    event.source_id,
                    event.event_id,
                    store.digest(summary_for_digest(summary)),
                    summary,
                )
            ],
            now,
        )
        if failed is not None:
            return failed
        LOG.info("ingestion outcome=ACCEPTED")
        return {"accepted_event_ids": [str(event.event_id)]}

    @app.post("/v1/batches")
    async def ingest_batch(request: Request):
        try:
            batch = CollectorBatch.model_validate_json(request.state.wire)
        except ValidationError:
            return error(422, "SCHEMA_INVALID")
        now = clock()
        if not fresh(batch.created_at, now):
            return error(422, "EVENT_TIME_INVALID")
        ids = [event.event_id for event in batch.events]
        if len(set(ids)) != len(ids):
            return error(422, "DUPLICATE_EVENT_ID")
        items = []
        registry = {entry.route: entry for entry in normalizer.templates}
        for event in batch.events:
            if len(event.model_dump_json().encode()) > 4096:
                return error(413, "EVENT_TOO_LARGE")
            if event.source_id != settings.source_id:
                return error(403, "SOURCE_NOT_AUTHORIZED")
            if not fresh(event.observed_at, now):
                return error(422, "EVENT_TIME_INVALID")
            if (
                event.route_template is not None
                and event.route_template not in registry
            ):
                # A producer label is not proof of approval; no raw marker storage.
                return error(422, "TEMPLATE_NOT_APPROVED")
            documented = event.route_template is not None and (
                event.method in registry[event.route_template].methods
            )
            summary = {
                "method": event.method,
                "route": event.route_template,
                "classification": "documented"
                if documented
                else "visibility_unavailable",
                "reason_code": "DOCUMENTED_OPERATION"
                if documented
                else "ROUTE_EVIDENCE_UNAVAILABLE",
                "contract_version": normalizer.contract_version,
                "status_code": event.status_code,
                "correlation_quality": event.correlation_quality,
            }
            items.append(
                (event.source_id, event.event_id, store.digest(summary), summary)
            )
        failed = append(items, now)
        if failed is not None:
            return failed
        LOG.info("ingestion outcome=ACCEPTED")
        # Exactly the two fields Member 3's deny_unknown_fields BatchAck accepts.
        return {
            "batch_id": str(batch.batch_id),
            "accepted_event_ids": [str(value) for value in ids],
        }

    @app.post("/v1/recommendations")
    async def recommendations(request: Request):
        try:
            context = RequestContext.model_validate_json(request.state.wire)
        except ValidationError:
            return error(422, "SCHEMA_INVALID")
        try:
            reply = decision_service.issue(context)
        except DecisionError as failure:
            status = {"REPLAY_REJECTED": 409, "REQUEST_TIME_INVALID": 422}.get(
                str(failure), 503
            )
            return error(status, str(failure))
        LOG.info("ingestion outcome=RECOMMENDATION_ISSUED")
        return reply.model_dump(mode="json")

    return app


def summary_for_digest(summary):
    # Random finding IDs do not turn a safe retry into a conflict.
    return {key: value for key, value in summary.items() if key != "alert"}
