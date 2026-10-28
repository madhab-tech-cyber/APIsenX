import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def table_rows(document, pattern):
    rows = {}
    for line in document.splitlines():
        match = re.match(pattern, line)
        if match:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows[match.group(1)] = cells
    return rows


class Day22Day23PolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enforcement_review = (
            ROOT / "docs" / "enforcement-residual-risk-review.md"
        ).read_text(encoding="utf-8")
        cls.enforcement_policy = (
            ROOT / "docs" / "enforcement-approval-and-rollback.md"
        ).read_text(encoding="utf-8")
        cls.risk_register = (ROOT / "docs" / "risk-register.md").read_text(
            encoding="utf-8"
        )
        cls.masking_policy = (
            ROOT / "docs" / "masking-field-policy.md"
        ).read_text(encoding="utf-8")
        cls.classification_policy = (
            ROOT / "docs" / "data-classification-policy.md"
        ).read_text(encoding="utf-8")
        cls.audit_policy = (
            ROOT / "docs" / "audit-retention-and-investigation.md"
        ).read_text(encoding="utf-8")

    def test_day22_has_all_eight_gates_and_keeps_enforcement_unapproved(self):
        gates = table_rows(self.enforcement_review, r"^\|\s*(EG-\d{2})\b")
        self.assertEqual(set(gates), {f"EG-{number:02d}" for number in range(1, 9)})

        gate_text = " ".join(" ".join(cells) for cells in gates.values()).lower()
        for marker in ("pending", "blocked", "not run", "unmeasured"):
            self.assertIn(marker, gate_text)

        review = self.enforcement_review.lower()
        self.assertIn("enforcement acceptance: **not approved**", review)
        self.assertIn("active authorization set remains empty", review)
        self.assertIn("no active drop/rate-limit rule", review)
        self.assertIn("no high risk is accepted for release", review)

        policy = self.enforcement_policy.lower()
        self.assertIn("current mode is monitor-only", policy)
        self.assertIn(
            "a failed or missing gate keeps the proposal monitor-only", policy
        )

    def test_day22_keeps_material_residual_risks_high(self):
        risks = table_rows(self.risk_register, r"^\|\s*(R-\d{3})\s*\|")
        for risk_id in ("R-002", "R-003", "R-008", "R-010", "R-013"):
            with self.subTest(risk=risk_id):
                self.assertIn(risk_id, risks)
                self.assertGreaterEqual(len(risks[risk_id]), 9)
                self.assertEqual(risks[risk_id][8], "High")

    def test_day23_defines_exactly_ten_masking_field_decisions(self):
        fields = table_rows(self.masking_policy, r"^\|\s*(MK-\d{2})\b")
        self.assertEqual(set(fields), {f"MK-{number:02d}" for number in range(1, 11)})
        for field_id, cells in fields.items():
            with self.subTest(field=field_id):
                self.assertGreaterEqual(len(cells), 4)
                self.assertTrue(cells[1], "input field must be documented")
                self.assertTrue(cells[2], "classification must be documented")
                self.assertTrue(cells[3], "handling decision must be documented")

    def test_day23_excluded_and_correlated_fields_keep_safe_handling(self):
        fields = table_rows(self.masking_policy, r"^\|\s*(MK-\d{2})\b")
        handling = {field_id: cells[3].lower() for field_id, cells in fields.items()}

        self.assertIn("exclude at first boundary", handling["MK-01"])
        self.assertIn("never hash and retain a credential", handling["MK-01"])
        self.assertIn(
            "exclude from logs, metrics, persistence and dashboard",
            handling["MK-02"],
        )
        self.assertIn("approved canonical template", handling["MK-03"])
        self.assertIn("no concrete path values", handling["MK-03"])
        self.assertIn("domain-separated keyed token", handling["MK-04"])
        self.assertIn("never plain unsalted hash", handling["MK-05"])
        self.assertIn("exclude by default", handling["MK-06"])
        self.assertIn("versioned allowlisted enums", handling["MK-07"])
        self.assertIn(
            "never token/body/path-derived raw identifiers", handling["MK-08"]
        )
        self.assertIn(
            "unmeasured value is unavailable, not healthy/zero", handling["MK-09"]
        )
        self.assertIn("no raw object serialization fallback", handling["MK-10"])

    def test_day23_requires_domain_separation_and_no_cross_tenant_fallback(self):
        policy = " ".join(self.masking_policy.split()).lower()
        self.assertIn("hmac-sha-256 key with at least 128 output bits", policy)
        self.assertIn("domain-separate purpose and tenant", policy)
        self.assertIn("deny missing required tenant context", policy)
        self.assertIn(
            "falling back to a cross-tenant correlation namespace",
            policy,
        )
        self.assertIn("no raw disk spool", policy)

    def test_day23_runtime_leak_acceptance_remains_pending(self):
        policy = " ".join(self.masking_policy.split()).lower()
        classification = " ".join(self.classification_policy.split()).lower()
        audit = " ".join(self.audit_policy.split()).lower()

        self.assertIn(
            "runtime masking, leak tests and independent affected-owner review "
            "remain pending",
            policy,
        )
        self.assertIn("no forbidden marker may appear in any forbidden output", policy)
        self.assertIn("including stderr and tracebacks", policy)
        self.assertIn(
            "documentation is not proof that masking, access control or retention "
            "is implemented",
            classification,
        )
        self.assertIn("until leak tests pass, persistence stays blocked", audit)


if __name__ == "__main__":
    unittest.main()
