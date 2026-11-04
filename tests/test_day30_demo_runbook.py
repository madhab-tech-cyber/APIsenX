"""Keep the Day 30 documented API rehearsal executable and contract-aligned."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = ROOT / "docs" / "final-demonstration-and-handover.md"


class Day30DemoRunbookTests(unittest.TestCase):
    def test_documented_rehearsal_executes_against_current_api(self):
        document = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("## Reproducible local rehearsal", document)
        section = document.split("## Reproducible local rehearsal", 1)[1]
        section = section.split("## Handover owners", 1)[0]
        match = re.search(r"```python\s+(.*?)\s+```", section, re.DOTALL)
        self.assertIsNotNone(match, "Day 30 Python rehearsal block is missing")

        result = subprocess.run(
            [sys.executable, "-c", match.group(1)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        expected_statuses = {
            "DEMO-01 owner read": 200,
            "DEMO-02 cross-owner read": 404,
            "DEMO-03 missing identity": 401,
            "DEMO-04 customer admin list": 403,
            "DEMO-05 permitted admin list": 200,
            "DEMO-06 customer patch": 403,
            "DEMO-07 admin patch": 200,
            "DEMO-08 protected field": 400,
        }
        for case_id, status in expected_statuses.items():
            self.assertIn(
                f"{case_id}: expected={status} actual={status} PASS",
                result.stdout,
            )
        self.assertIn(
            "Inventory restored; all JSON fixture digests unchanged: PASS",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
