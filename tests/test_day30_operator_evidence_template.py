"""Keep the Day 30 human-operator evidence template explicitly unfilled."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs" / "day30-member5-operator-evidence-checklist.md"


class Day30OperatorEvidenceTemplateTests(unittest.TestCase):
    def test_template_contains_all_eight_expected_local_cases(self):
        document = TEMPLATE.read_text(encoding="utf-8")
        rows = {
            line.split("|", 2)[1].strip(): line
            for line in document.splitlines()
            if line.startswith("| DEMO-")
        }
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
                self.assertIn(case_id, rows)
                self.assertTrue(rows[case_id].endswith("| NOT RUN |"), rows[case_id])

    def test_integrated_scenarios_and_human_decisions_remain_pending(self):
        document = TEMPLATE.read_text(encoding="utf-8")
        for required in (
            "Current execution status: NOT RUN",
            "**Operator:** NOT RECORDED",
            "**Independent witness/reviewer:** NOT RECORDED",
            "**Service-owner decision and date:** PENDING",
            "**Independent-reviewer decision and date:** PENDING",
            "**Release decision:** NOT APPROVED",
            "Durable-store outage",
            "Restore/re-purge",
        ):
            with self.subTest(required=required):
                self.assertIn(required, document)

        integrated_rows = [
            line for line in document.splitlines()
            if line.startswith("| End-to-end normal event |")
            or line.startswith("| BOLA/BFLA denial |")
            or line.startswith("| Tenant separation |")
            or line.startswith("| Masking/leak markers |")
            or line.startswith("| Durable-store outage |")
            or line.startswith("| Route-specific recovery |")
            or line.startswith("| Retention/deletion |")
            or line.startswith("| Restore/re-purge |")
            or line.startswith("| Emergency disable/rollback |")
        ]
        self.assertEqual(len(integrated_rows), 9)
        for row in integrated_rows:
            with self.subTest(row=row):
                self.assertTrue(row.endswith("| NOT RUN |"), row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
