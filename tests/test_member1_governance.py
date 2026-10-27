import json
import unittest
from copy import deepcopy

from scripts.check_member1_governance import (
    REGISTER,
    ROOT,
    completion_gaps,
    validate_register,
)


class Member1GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(REGISTER.read_text())

    def completed_example(self):
        # Synthetic validator fixture; not an actual meeting, comment or approval.
        item = self.record["checkpoints"][0]
        item["status"] = "complete"
        item["candidate_revision"] = "a" * 40
        reference = "https://github.com/madhab-tech-cyber/APIsenX/issues/14#synthetic"
        item["meeting"] = {
            "at": "2026-10-19T00:00:00Z",
            "attendees": ["synthetic-reviewer"],
            "reference": reference,
            "revision": "a" * 40,
        }
        for field in ("reviewer_comments", "owner_responses", "independent_signoffs"):
            item[field] = [{"by": "synthetic-reviewer", "reference": reference}]
        item["independent_signoffs"][0]["revision"] = "a" * 40
        item["independent_signoffs"][0]["submitted_at"] = "2026-10-19T01:00:00Z"
        return item

    def test_old_revision_approval_does_not_approve_new_candidate(self):
        item = self.completed_example()
        item["candidate_revision"] = "b" * 40
        item["meeting"]["revision"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "another checkpoint candidate"):
            validate_register(self.record)

    def test_decorated_author_login_cannot_bypass_independence(self):
        item = self.completed_example()
        for value in (" madhab-tech-cyber", "madhab-tech-cyber ", "@madhab-tech-cyber"):
            item["independent_signoffs"][0]["by"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_register(self.record)

    def test_meeting_must_identify_the_actual_candidate(self):
        item = self.completed_example()
        item["meeting"]["revision"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "meeting must identify"):
            validate_register(self.record)

    def test_signoff_needs_timezone_aware_submission_time(self):
        item = self.completed_example()
        item["independent_signoffs"][0]["submitted_at"] = "2026-10-19T01:00:00"
        with self.assertRaises(ValueError):
            validate_register(self.record)

    def test_followup_tracker_does_not_replace_historical_checkpoint(self):
        item = self.record["checkpoints"][0]
        item["tracking_issues"] = [item["issue"], 56]
        validate_register(self.record)
        for links in ([56], [14, True], [14, 14], [14, 0]):
            item["tracking_issues"] = links
            with self.subTest(links=links), self.assertRaises(ValueError):
                validate_register(self.record)

    def test_day30_cannot_bypass_prior_human_checkpoints(self):
        example = deepcopy(self.completed_example())
        self.record["checkpoints"][0]["status"] = "pending"
        self.record["checkpoints"][2] = dict(
            example,
            day=30,
            issue=23,
            tracking_issues=[23],
            run_manifest=example["meeting"]["reference"],
        )
        self.record["integration_status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "earlier human checkpoints"):
            validate_register(self.record)

    def test_green_implementation_does_not_release_pending_human_work(self):
        self.record.update(integration_status="accepted", release_status="approved")
        self.record["integration_evidence"] = [
            "https://github.com/madhab-tech-cyber/APIsenX/issues/61"
        ]
        with self.assertRaisesRegex(ValueError, "pending human checkpoints"):
            validate_register(self.record)

    def test_protection_flag_alone_is_not_settings_and_pr_gate_evidence(self):
        observation = self.record["protection_observation"]
        observation.update(main_protected=True, settings_verified=True)
        with self.assertRaises(KeyError):
            validate_register(self.record)

    def test_internal_consistency_success_is_not_completion(self):
        validate_register(self.record)
        self.assertIn("Day 14 human checkpoint", completion_gaps(self.record))
        self.assertIn("authorized release decision", completion_gaps(self.record))

    def test_accepted_integration_requires_its_own_evidence(self):
        self.record["integration_status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "integration evidence required"):
            validate_register(self.record)

    def test_synthetic_complete_example_requires_protection_and_all_human_gates(self):
        # Validator fixture only; never recorded as a real meeting or approval.
        example = deepcopy(self.completed_example())
        reference = example["meeting"]["reference"]
        self.record["checkpoints"] = [
            dict(
                deepcopy(example), day=day, issue=issue, tracking_issues=[issue],
                run_manifest=reference if day == 30 else None,
            )
            for day, issue in ((14, 14), (15, 21), (30, 23))
        ]
        self.record.update(integration_status="accepted", release_status="approved")
        self.record["integration_evidence"] = [reference]
        with self.assertRaisesRegex(ValueError, "unverified main protection"):
            validate_register(self.record)
        self.record["protection_observation"].update(
            main_protected=True, settings_verified=True,
            readback_reference=reference, merge_gate_reference=reference,
        )
        validate_register(self.record)
        self.assertEqual(completion_gaps(self.record), [])

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
            changed["checkpoints"][1] = dict(
                example, day=day, issue=issue, tracking_issues=[issue]
            )
            if day == 30:
                changed["checkpoints"][1], changed["checkpoints"][2] = (
                    dict(
                        example, day=15, issue=21,
                        tracking_issues=[21], status="pending",
                    ),
                    dict(
                        example,
                        day=30,
                        issue=23,
                        tracking_issues=[23],
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
