import re
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
        cls.normalized_failure_policy = " ".join(
            cls.failure_policy.split()
        )

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
            match.group(1)
            for line in self.failure_policy.splitlines()
            if (match := re.match(r"^\|\s*(RF-\d{2})\b", line))
        }
        self.assertEqual(
            route_rows,
            {f"RF-{number:02d}" for number in range(1, 6)},
        )
        self.assertIn(
            "current stdout logs do not implement this column.",
            self.normalized_failure_policy,
        )
        self.assertIn(
            "Per-route implementation acceptance remains BLOCKED",
            self.normalized_failure_policy,
        )
        self.assertIn(
            "An audit outage must not prevent emergency disablement.",
            self.normalized_failure_policy,
        )


    def test_day21_route_rows_pin_operation_specific_failure_behavior(self):
        rows = {}
        for line in self.failure_policy.splitlines():
            match = re.match(r"^\|\s*(RF-\d{2})\b", line)
            if match:
                rows[match.group(1)] = [
                    cell.strip() for cell in line.strip().strip("|").split("|")
                ]

        self.assertEqual(
            set(rows), {f"RF-{number:02d}" for number in range(1, 6)}
        )
        self.assertIn("GET /orders", rows["RF-01"][0])
        self.assertIn("Fail closed", rows["RF-01"][1])
        self.assertIn("Owner read may continue", rows["RF-01"][3])

        self.assertIn("GET /orders/{orderId}", rows["RF-02"][0])
        self.assertIn("Fail closed", rows["RF-02"][1])
        self.assertIn("privileged read fails closed", rows["RF-02"][3])

        self.assertIn("PATCH /orders/{orderId}", rows["RF-03"][0])
        self.assertIn("Fail closed", rows["RF-03"][1])
        self.assertIn("Keep API permission/field checks", rows["RF-03"][2])
        self.assertIn("generic 503 before mutation", rows["RF-03"][3])

        self.assertIn("GET /admin/orders", rows["RF-04"][0])
        self.assertIn("Fail closed", rows["RF-04"][1])
        self.assertIn("Keep API function permission gate", rows["RF-04"][2])
        self.assertIn(
            "generic 503 before privileged data delivery", rows["RF-04"][3]
        )

        self.assertIn("Unknown route/method or invalid path", rows["RF-05"][0])
        self.assertIn("Router/validation rejects", rows["RF-05"][1])
        self.assertIn("No raw path/credentials", rows["RF-05"][3])

        normalized = self.normalized_failure_policy
        self.assertIn(
            "Fail-open applies only to optional Sentinel "
            "observation/enforcement overlays",
            normalized,
        )
        self.assertIn(
            "Missing or untrusted identity/policy context denies the API action",
            normalized,
        )
        self.assertIn(
            "An audit outage must not prevent emergency disablement.",
            normalized,
        )
        self.assertIn("Per-route implementation acceptance remains BLOCKED", normalized)


if __name__ == "__main__":
    unittest.main()
