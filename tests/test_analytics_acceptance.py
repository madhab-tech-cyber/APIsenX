"""Synthetic bookkeeping fixtures, never actual independent review/attendance."""

import json
import unittest
from copy import deepcopy

from analytics.acceptance import DAYS, REGISTER, candidate_sha, pending, validate_record


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(REGISTER.read_text())

    def review(self):
        return {
            "by": "synthetic-reviewer",
            "decision": "APPROVED",
            "revision": candidate_sha(self.record),
            "rules_digest": self.record["candidate_rules_digest"],
            "submitted_at": "2026-10-27T08:00:00Z",
            "reference": "https://github.com/madhab-tech-cyber/APIsenX/issues/48#synthetic",
        }

    def verified_gate(self):
        return {
            "status": "verified",
            "evidence": [self.review()["reference"]],
            "independent_reviews": [self.review()],
        }

    def test_checked_in_record_is_consistent_but_pending(self):
        validate_record(self.record)
        self.assertEqual(len(pending(self.record)), 12)

    def test_verified_gate_requires_evidence_and_independent_review(self):
        for field in ("evidence", "independent_reviews"):
            gate = self.verified_gate()
            gate[field] = []
            self.record["acceptance_gates"]["independent_accuracy"] = gate
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_record(self.record)

    def test_self_and_decorated_approval_are_rejected(self):
        for actor in (
            self.record["implementation_owner"].upper(),
            " " + self.record["implementation_owner"],
            "@synthetic-reviewer",
        ):
            gate = self.verified_gate()
            gate["independent_reviews"][0]["by"] = actor
            self.record["acceptance_gates"]["independent_accuracy"] = gate
            with self.subTest(actor=actor), self.assertRaises(ValueError):
                validate_record(self.record)

    def test_old_revision_digest_or_unsubmitted_approval_cannot_transfer(self):
        for field, value in (
            ("revision", "a" * 40),
            ("rules_digest", "b" * 64),
            ("submitted_at", "2026-10-27T08:00:00"),
            ("decision", "REQUESTED"),
        ):
            gate = self.verified_gate()
            gate["independent_reviews"][0][field] = value
            self.record["acceptance_gates"]["independent_accuracy"] = gate
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_record(self.record)

    def test_complete_human_demo_requires_real_record_fields(self):
        item = self.record["day14"]
        item.update(status="complete", independent_signoffs=[self.review()])
        with self.assertRaises((ValueError, TypeError)):
            validate_record(self.record)

    def test_day15_cannot_bypass_day14(self):
        self.record["day15"].update(
            status="complete", independent_signoffs=[self.review()]
        )
        with self.assertRaisesRegex(ValueError, "Day 14"):
            validate_record(self.record)

    def test_human_demonstration_must_pin_the_reviewed_candidate(self):
        self.record["day14"].update(
            status="complete",
            independent_signoffs=[self.review()],
            meeting_date="2026-10-27T08:00:00Z",
            demonstrated_revision="a" * 40,
            actual_attendees=["synthetic-reviewer"],
            review_comments=[self.review()],
        )
        with self.assertRaisesRegex(ValueError, "demonstration belongs"):
            validate_record(self.record)

    def test_unknown_or_omitted_gate_rejected(self):
        for name in ("independent_accuracy", "unrecognized_gate"):
            changed = deepcopy(self.record)
            if name in changed["acceptance_gates"]:
                del changed["acceptance_gates"][name]
            else:
                changed["acceptance_gates"][name] = self.verified_gate()
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_record(changed)

    def test_stale_contract_rule_or_source_rejected(self):
        for field, value in (
            ("contract_version", "sha256:" + "a" * 64),
            ("candidate_rules_digest", "b" * 64),
            ("rule_version", "DET-1.1"),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_record(dict(self.record, **{field: value}))

    def test_no_enforcement_release_or_calendar_claim(self):
        for field, value in (
            ("mode", "active"),
            ("active_rules", True),
            ("active_rules", 1),
            ("release_approved", True),
            ("calendar_days_claimed", True),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_record(dict(self.record, **{field: value}))

    def test_foreign_evidence_rejected(self):
        gate = self.verified_gate()
        gate["evidence"] = ["https://example.com/approval"]
        self.record["acceptance_gates"]["shared_transport"] = gate
        with self.assertRaises(ValueError):
            validate_record(self.record)

    def test_synthetic_complete_fixture_still_cannot_authorize_release(self):
        for name in self.record["acceptance_gates"]:
            self.record["acceptance_gates"][name] = self.verified_gate()
        for day in DAYS:
            item = self.record[f"day{day}"]
            item.update(status="complete", independent_signoffs=[self.review()])
            if day in (14, 30):
                item.update(
                    meeting_date="2026-10-27T08:00:00Z",
                    demonstrated_revision=candidate_sha(self.record),
                    actual_attendees=["synthetic-reviewer"],
                    review_comments=[self.review()],
                )
            if day == 15:
                item.update(
                    actual_feedback=[self.review()], owner_dispositions=[self.review()]
                )
        validate_record(self.record)
        self.assertEqual(pending(self.record), [])
        self.assertIs(self.record["release_approved"], False)
        self.record["acceptance_gates"]["shared_transport"]["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "integrated acceptance"):
            validate_record(self.record)
