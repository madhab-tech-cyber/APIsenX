import json
import unittest
from copy import deepcopy

from scripts.check_member1_governance import REGISTER, ROOT, validate_register


class Member1GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(REGISTER.read_text())

    def completed_example(self):
        # Synthetic validator fixture; not an actual meeting, comment or approval.
        item = self.record["checkpoints"][0]
        item["status"] = "complete"
        reference = "https://github.com/madhab-tech-cyber/APIsenX/issues/14#synthetic"
        item["meeting"] = {
            "at": "2026-10-19T00:00:00Z",
            "attendees": ["synthetic-reviewer"],
            "reference": reference,
        }
        for field in ("reviewer_comments", "owner_responses", "independent_signoffs"):
            item[field] = [{"by": "synthetic-reviewer", "reference": reference}]
        item["independent_signoffs"][0]["revision"] = "a" * 40
        return item

    def test_checked_in_register_is_consistent(self):
        validate_register(self.record)

    def test_pending_records_do_not_require_invented_meetings(self):
        for item in self.record["checkpoints"]:
            item.update(status="pending", meeting=None)
        validate_register(self.record)

    def test_complete_record_requires_each_kind_of_human_evidence(self):
        item = self.completed_example()
        validate_register(self.record)
        for field in ("reviewer_comments", "owner_responses", "independent_signoffs"):
            with self.subTest(field=field):
                changed = deepcopy(self.record)
                changed["checkpoints"][0][field] = []
                with self.assertRaises(ValueError):
                    validate_register(changed)
        item["meeting"] = None
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_author_signoff_is_not_independent(self):
        item = self.completed_example()
        item["independent_signoffs"][0]["by"] = self.record["document_author"]
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_case_changed_author_signoff_is_still_self_approval(self):
        item = self.completed_example()
        item["independent_signoffs"][0]["by"] = self.record["document_author"].upper()
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_component_approval_cannot_complete_human_checkpoint(self):
        self.assertTrue(self.record["component_reviews"])
        self.record["checkpoints"][1]["status"] = "complete"
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_component_approval_rejects_self_review_or_unpinned_revision(self):
        for field, value in (("by", "PAPPUKUMAR96727-SKETCH"), ("revision", "main")):
            record = deepcopy(self.record)
            record["component_reviews"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_register(record)

    def test_closed_trackers_and_partial_response_do_not_complete_checkpoint(self):
        observed = self.record["tracker_observations"]
        observed["states"] = dict.fromkeys(observed["states"], "closed")
        validate_register(self.record)
        self.assertTrue(self.record["checkpoints"][1]["owner_responses"])
        self.assertTrue(
            all(c["status"] == "pending" for c in self.record["checkpoints"])
        )

    def test_signoff_requires_pinned_revision_and_repository_reference(self):
        item = self.completed_example()
        for field, value in (("revision", "main"), ("reference", "http://example.com")):
            changed = deepcopy(self.record)
            changed["checkpoints"][0]["independent_signoffs"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_register(changed)
        item["meeting"]["at"] = "2026-10-19T00:00:00"
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_day15_needs_day14_feedback_and_day30_needs_integration(self):
        example = deepcopy(self.completed_example())
        self.record["checkpoints"][0]["status"] = "pending"
        for day, issue in ((15, 21), (30, 23)):
            changed = deepcopy(self.record)
            changed["checkpoints"][1] = dict(example, day=day, issue=issue)
            if day == 30:
                changed["checkpoints"][1], changed["checkpoints"][2] = (
                    dict(example, day=15, issue=21, status="pending"),
                    dict(
                        example,
                        day=30,
                        issue=23,
                        run_manifest=example["meeting"]["reference"],
                    ),
                )
            with self.subTest(day=day), self.assertRaises(ValueError):
                validate_register(changed)

    def test_invalid_bookkeeping_is_rejected(self):
        changes = (
            {"schema_version": 99},
            {"baseline": "main"},
            {"active_rule_count": True},
            {"active_rule_count": 1},
            {"release_status": "approved"},
            {"checkpoints": self.record["checkpoints"][:1]},
        )
        for fields in changes:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                validate_register(dict(self.record, **fields))

    def test_integration_baseline_does_not_repeat_repaired_blockers(self):
        text = (ROOT / "docs/integration-data-flow.md").read_text()
        for stale in (
            "still-open administrative permission failure",
            "implemented locally, contract drift remains",
            "`openapi.yaml` differs from the mock API authentication",
            "main PR coverage and protection evidence pending",
            "matrix is due with the Day 21 review",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, text)
        self.assertIn("member1-checkpoints.json", text)
        self.assertIn("member1-governance-correction.md", text)


if __name__ == "__main__":
    unittest.main()
