"""Day 29 clean, reproducible synthetic lab reset checks."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from scripts.verify_day29_lab_reset import verify_fixture_hashes

MANIFEST_PATH = ROOT / "tests" / "fixtures" / "day29_lab_baseline.json"
SCRIPT_PATH = ROOT / "scripts" / "verify_day29_lab_reset.py"


class Day29LabResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            cls.manifest = json.load(handle)

    def test_checked_in_fixture_bytes_match_reviewed_baseline(self):
        self.assertEqual(verify_fixture_hashes(ROOT, self.manifest), [])

    def test_fixture_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative_path in self.manifest["fixtures"]:
                destination = root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative_path, destination)
            changed = root / "mock_data" / "orders.json"
            changed.write_text(changed.read_text(encoding="utf-8") + " ", encoding="utf-8")
            self.assertEqual(
                verify_fixture_hashes(root, self.manifest),
                ["mock_data/orders.json"],
            )

    def test_fresh_interpreter_reloads_clean_baseline(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Day 29 clean synthetic lab reset: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
