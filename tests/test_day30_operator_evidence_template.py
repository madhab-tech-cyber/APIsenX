"""Keep the Day 30 human-operator evidence template explicitly unfilled."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (
    ROOT / "docs" / "day30-member5-operator-evidence-checklist.md"
)


class Day30OperatorEvidenceTemplateTests(unittest.TestCase):
    def test_template_contains_all_eight_expected_local_cases(self):
        document = TEMPLATE.read_text(encoding="utf-8")
        for case_id in (
            "DEMO-01",
            "DEMO-02",
            "DEMO-03",
            "DEMO-04",
            "DEMO-05",
            "DEMO-06",
            "DEMO-07",
            "DEMO-08",
        ):
            with self.subTest(case_id=case_id):
                self.assertIn(f"| {case_id} |", document)
                self.assertIn("| NOT RUN |", document)

    def test_integrated_scenarios_and_human_decisions_remain_pending(self):
        document = TEMPLATE.read_text(encoding="utf-8")
        for required in (
            "Current execution status: NOT RUN",
            "Operator: NOT RECORDED",
            "Independent witness/reviewer: NOT RECORDED",
            "Service-owner decision and date: PENDING",
            "Independent-reviewer decision and date: PENDING",
            "Release decision:** NOT APPROVED",
            "durable-store outage",
            "Restore/re-purge",
        ):
            with self.subTest(required=required):
                self.assertIn(required, document)


if __name__ == "__main__":
    unittest.main(verbosity=2)
