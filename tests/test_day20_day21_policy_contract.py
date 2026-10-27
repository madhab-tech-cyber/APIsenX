import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Day20Day21PolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit_policy = (
            ROOT / "docs" / "audit-retention-and-investigation.md"
        ).read_text(encoding="utf-8")
        cls.failure_policy = (
            ROOT / "docs" / "route-failure-policy.md"
        ).read_text(encoding="utf-8")

    def test_day20_retention_policy_keeps_all_eight_classes_and_blockers_explicit(self):
        retention_rows = {
            line.split("|")[1].strip()
            for line in self.audit_policy.splitlines()
            if line.startswith("| RT-")
        }
        self.assertEqual(
            retention_rows,
            {f"RT-{number:02d}" for number in range(1, 9)},
        )
        self.assertIn(
            "no audit store or access-control implementation is accepted",
            self.audit_policy.lower(),
        )
        self.assertIn("R-001/R-008/R-009 remain High", self.audit_policy)

    def test_day21_policy_keeps_all_five_route_failure_rows_and_pending_boundary(self):
        route_rows = {
            line.split("|")[1].strip()
            for line in self.failure_policy.splitlines()
            if line.startswith("| RF-")
        }
        self.assertEqual(
            route_rows,
            {f"RF-{number:02d}" for number in range(1, 6)},
        )
        self.assertIn(
            "current stdout logs do not implement this column",
            self.failure_policy,
        )
        self.assertIn(
            "Per-route implementation acceptance remains BLOCKED",
            self.failure_policy,
        )
        self.assertIn(
            "An audit outage must not prevent emergency disablement.",
            self.failure_policy,
        )


if __name__ == "__main__":
    unittest.main()
