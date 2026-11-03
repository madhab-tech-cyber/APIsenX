"""Protected API bypass, case scope, pagination, audit and privacy regressions."""

import logging
import secrets
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from analytics.app import Settings, create_app
from analytics.management import ReaderGrant


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)

        def grant(identity, role="analyst", case="case_a", expired=False):
            expiry = self.now + timedelta(hours=-1 if expired else 1)
            return ReaderGrant(identity, secrets.token_urlsafe(32), case, role, expiry)

        self.analyst, self.viewer = grant("analyst"), grant("viewer", "viewer")
        self.other, self.expired = (
            grant("other", case="case_b"),
            grant("expired", expired=True),
        )
        self.settings = Settings(
            secrets.token_urlsafe(32),
            "synthetic",
            secrets.token_bytes(32),
            case_id="case_a",
            readers=(self.analyst, self.viewer, self.other, self.expired),
        )
        self.app = create_app(self.settings, lambda: self.now)
        self.client = TestClient(self.app)
        self.headers = {"authorization": "Bearer " + self.analyst.token}
        self.ingest = {"authorization": "Bearer " + self.settings.ingest_token}
        client_logger = logging.getLogger("httpx")
        previous = client_logger.level
        client_logger.setLevel(logging.WARNING)
        self.addCleanup(client_logger.setLevel, previous)
        self.event_ids = []

    def add(self, target, method="GET"):
        identifier = str(uuid4())
        self.event_ids.append(identifier)
        payload = {
            "schema_name": "application_event",
            "schema_version": "1.0",
            "event_id": identifier,
            "source_id": "synthetic",
            "observed_at": self.now.isoformat(),
            "method": method,
            "request_target": target,
            "status_code": 200,
        }
        self.assertEqual(
            self.client.post(
                "/v1/events", json=payload, headers=self.ingest
            ).status_code,
            200,
        )

    def seed(self):
        for target in (
            "/orders",
            "/orders/order-1001",
            "/synthetic/SYNTHETIC_PERSON?token=SYNTHETIC_SECRET",
            "/synthetic/SYNTHETIC_OTHER",
        ):
            self.add(target)

    def test_empty_pages_report_partial_visibility_not_healthy(self):
        for endpoint in ("inventory", "alerts"):
            response = self.client.get("/v1/" + endpoint, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["items"], [])
            self.assertEqual(response.json()["visibility"], "partial_lab_visibility")
            self.assertEqual(
                response.json()["data_source"], "volatile_lab_observations"
            )
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_unauthenticated_wrong_scope_and_forwarded_role_cannot_read(self):
        for endpoint in ("/v1/inventory", "/v1/alerts", "/v1/alerts/" + str(uuid4())):
            for headers in (
                {},
                self.ingest,
                {"X-Reader-Role": "analyst", "X-Forwarded-User": "analyst"},
            ):
                self.assertEqual(
                    self.client.get(endpoint, headers=headers).status_code, 401
                )

    def test_reader_apis_disabled_by_default(self):
        settings = Settings(
            secrets.token_urlsafe(32), "synthetic", secrets.token_bytes(32)
        )
        self.assertEqual(
            TestClient(create_app(settings)).get("/v1/inventory").status_code, 404
        )

    def test_viewer_inventory_only_and_case_scope_enforced_on_backend(self):
        viewer = {"authorization": "Bearer " + self.viewer.token}
        self.assertEqual(
            self.client.get("/v1/inventory", headers=viewer).status_code, 200
        )
        self.assertEqual(
            self.client.get(
                "/v1/alerts", headers={**viewer, "X-Role": "analyst"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/v1/alerts/" + str(uuid4()), headers=viewer).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                "/v1/inventory", headers={"authorization": "Bearer " + self.other.token}
            ).status_code,
            403,
        )

    def test_expired_and_revoked_grants_deny_direct_reads(self):
        self.assertEqual(
            self.client.get(
                "/v1/inventory",
                headers={"authorization": "Bearer " + self.expired.token},
            ).status_code,
            401,
        )
        self.app.state.management.revoke(self.analyst.identity)
        self.assertEqual(
            self.client.get("/v1/inventory", headers=self.headers).status_code, 401
        )

    def test_session_maximum_and_duplicate_credentials_rejected(self):
        bad = ReaderGrant(
            "too_long",
            secrets.token_urlsafe(32),
            "case_a",
            "analyst",
            self.now + timedelta(hours=25),
        )
        with self.assertRaises(ValueError):
            create_app(
                Settings(
                    self.settings.ingest_token,
                    "synthetic",
                    self.settings.hmac_key,
                    case_id="case_a",
                    readers=(bad,),
                ),
                lambda: self.now,
            )
        reused = ReaderGrant(
            "reused",
            self.settings.ingest_token,
            "case_a",
            "viewer",
            self.now + timedelta(hours=1),
        )
        with self.assertRaises(ValueError):
            Settings(
                self.settings.ingest_token,
                "synthetic",
                self.settings.hmac_key,
                readers=(reused,),
            )

    def test_inventory_groups_unknowns_without_tokens_or_concrete_paths(self):
        self.seed()
        response = self.client.get("/v1/inventory", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 3)
        unknown = next(
            item for item in response.json()["items"] if item["route"] == "/__unknown__"
        )
        self.assertEqual(unknown["observation_count"], 2)
        for excluded in ("SYNTHETIC_", "order-1001", "unknown_route_token", "digest"):
            self.assertNotIn(excluded, response.text)

    def test_bounded_filtered_pagination(self):
        self.seed()
        first = self.client.get("/v1/inventory?limit=1", headers=self.headers).json()
        self.assertEqual(len(first["items"]), 1)
        second = self.client.get(
            "/v1/inventory",
            params={"limit": 1, "cursor": first["next_cursor"]},
            headers=self.headers,
        )
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first["items"], second.json()["items"])
        filtered = self.client.get(
            "/v1/inventory",
            params={"classification": "documented", "route": "/orders"},
            headers=self.headers,
        )
        self.assertEqual(len(filtered.json()["items"]), 1)

    def test_invalid_duplicate_unbounded_or_scope_widening_queries_reject(self):
        for query in (
            "limit=0",
            "limit=101",
            "limit=-1",
            "limit=nan",
            "limit=1&limit=2",
            "role=admin",
            "case_id=case_b",
            "owner=SYNTHETIC_SECRET",
            "route=/orders/order-1001",
            "classification=healthy",
            "method=get",
        ):
            response = self.client.get("/v1/inventory?" + query, headers=self.headers)
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("SYNTHETIC_SECRET", response.text)

    def test_cursors_are_signed_and_bound_to_reader_filters_and_limit(self):
        self.seed()
        cursor = self.client.get("/v1/inventory?limit=1", headers=self.headers).json()[
            "next_cursor"
        ]
        changed = cursor[:-1] + ("0" if cursor[-1] != "0" else "1")
        for token, limit, headers in (
            (changed, 1, self.headers),
            (cursor, 2, self.headers),
            (cursor, 1, {"authorization": "Bearer " + self.viewer.token}),
        ):
            response = self.client.get(
                "/v1/inventory",
                params={"limit": limit, "cursor": token},
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)

    def test_cursor_snapshot_change_returns_conflict_instead_of_skipping_rows(self):
        self.seed()
        cursor = self.client.get("/v1/inventory?limit=1", headers=self.headers).json()[
            "next_cursor"
        ]
        self.add("/orders")
        response = self.client.get(
            "/v1/inventory", params={"limit": 1, "cursor": cursor}, headers=self.headers
        )
        self.assertEqual(
            (response.status_code, response.json()),
            (409, {"detail": "SNAPSHOT_CHANGED"}),
        )

    def test_cursor_expiry_and_retention(self):
        self.seed()
        cursor = self.client.get("/v1/inventory?limit=1", headers=self.headers).json()[
            "next_cursor"
        ]
        self.now += timedelta(seconds=61)
        self.assertEqual(
            self.client.get(
                "/v1/inventory",
                params={"limit": 1, "cursor": cursor},
                headers=self.headers,
            ).status_code,
            400,
        )
        self.now += timedelta(seconds=239)
        self.assertEqual(
            self.client.get("/v1/inventory", headers=self.headers).json()["items"], []
        )

    def test_masked_alert_detail_and_explanation_are_read_only(self):
        self.seed()
        listing = self.client.get(
            "/v1/alerts?finding_class=shadow_candidate", headers=self.headers
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()["items"]), 2)
        identifier = listing.json()["items"][0]["alert_id"]
        detail = self.client.get("/v1/alerts/" + identifier, headers=self.headers)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["state"], "candidate")
        self.assertEqual(detail.json()["rule_id"], "DET-SHADOW-1")
        self.assertIn("under validation", detail.json()["explanation"])
        for excluded in (
            *self.event_ids,
            "SYNTHETIC_PERSON",
            "SYNTHETIC_SECRET",
            "unknown_route_token",
            self.analyst.token,
        ):
            self.assertNotIn(excluded, listing.text + detail.text)
        self.assertEqual(
            self.client.post(
                "/v1/alerts/" + identifier, headers=self.headers
            ).status_code,
            404,
        )

        original_ids = {
            item["alert_id"] for item in self.app.state.management.alert_items()
        }
        self.app.state.management.case_id = "case_b"
        scoped_ids = {
            item["alert_id"] for item in self.app.state.management.alert_items()
        }
        self.assertFalse(original_ids & scoped_ids)
        self.app.state.management.case_id = "case_a"

        # An ingestion observation and decision audit may share an event ID.
        # Both findings must remain individually addressable, not alias detail.
        row = next(
            row for row in self.app.state.store.snapshot(self.now) if row.get("alert")
        )
        with patch.object(self.app.state.management, "audit") as audit:
            audit.store.snapshot.return_value = [
                {
                    **row,
                    "schema_name": "analytics_audit",
                    "alert": None,
                    "finding_class": "shadow_candidate",
                    "rule_id": "DET-SHADOW-1",
                    "reason_code": "ROUTE_DRIFT",
                }
            ]
            findings = self.app.state.management.alert_items()
            self.assertEqual(len(findings), 3)
            self.assertEqual(len({item["alert_id"] for item in findings}), 3)
            for item in findings:
                self.assertEqual(
                    self.app.state.management.detail(item["alert_id"]), item
                )

    def test_unknown_or_malformed_alert_id_is_generic_not_found(self):
        for identifier in (str(uuid4()), "SYNTHETIC_SECRET", "a" * 128):
            response = self.client.get("/v1/alerts/" + identifier, headers=self.headers)
            self.assertEqual(response.json(), {"detail": "NOT_FOUND"})
            self.assertEqual(response.status_code, 404)

    def test_read_allow_and_role_denial_are_masked_audited(self):
        self.client.get("/v1/inventory", headers=self.headers)
        self.client.get(
            "/v1/alerts", headers={"authorization": "Bearer " + self.viewer.token}
        )
        rows = self.app.state.management.access.snapshot(self.now)
        self.assertEqual({row["outcome"] for row in rows}, {"allowed", "denied"})
        for excluded in (
            self.analyst.token,
            self.viewer.token,
            '"analyst"',
            '"viewer"',
        ):
            self.assertNotIn(excluded, str(rows))

    def test_access_audit_capacity_or_backend_failure_does_not_return_evidence(self):
        self.seed()
        with patch.object(
            self.app.state.management.access,
            "append",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            response = self.client.get("/v1/alerts", headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("SYNTHETIC_SECRET", response.text)
        self.assertNotIn("items", response.text)
        with patch.object(
            self.app.state.store,
            "snapshot",
            side_effect=RuntimeError("SYNTHETIC_SECRET"),
        ):
            self.assertEqual(
                self.client.get("/v1/inventory", headers=self.headers).status_code, 503
            )

    def test_environment_reader_configuration_requires_all_fields_and_aware_expiry(
        self,
    ):
        base = {
            "APISENTINEL_INGEST_TOKEN": self.settings.ingest_token,
            "APISENTINEL_SOURCE_ID": "synthetic",
            "APISENTINEL_HMAC_KEY": self.settings.hmac_key.hex(),
            "APISENTINEL_KEY_VERSION": "test-v1",
            "APISENTINEL_READER_ID": "analyst",
        }
        with patch.dict("os.environ", base, clear=True), self.assertRaises(ValueError):
            Settings.from_env()
        base.update(
            APISENTINEL_READER_TOKEN=self.analyst.token,
            APISENTINEL_READER_CASE="case_a",
            APISENTINEL_READER_ROLE="analyst",
            APISENTINEL_READER_EXPIRES_AT=self.analyst.expires_at.isoformat(),
        )
        with patch.dict("os.environ", base, clear=True):
            self.assertEqual(Settings.from_env().readers[0].identity, "analyst")
