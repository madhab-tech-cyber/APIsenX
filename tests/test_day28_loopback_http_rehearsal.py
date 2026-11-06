"""Exercise the synthetic Mock API through a real loopback HTTP process."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "day28_loopback_api_rehearsal.py"


class Day28LoopbackHTTPRehearsalTests(unittest.TestCase):
    def test_harness_is_loopback_only_and_does_not_use_proxy_or_redirects(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            'HOST = "127.0.0.1"',
            "ProxyHandler({})",
            "class RejectRedirects",
            '"--no-access-log"',
            '"APISENTINEL_URL"',
            '"APISENTINEL_INGEST_TOKEN"',
            '"APISENTINEL_SOURCE_ID"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_documented_attack_matrix_runs_over_loopback_http(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--mode", "full"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        expected = (
            "DEMO-01 owner-read: expected=200 actual=200 PASS",
            "DEMO-02 cross-owner-bola: expected=404 actual=404 PASS",
            "DEMO-03 customer-admin-bfla: expected=403 actual=403 PASS",
            "DEMO-04 missing-authentication: expected=401 actual=401 PASS",
            "DEMO-05 missing-policy-version: expected=400 actual=400 PASS",
            "DEMO-06 support-masked-view: expected=200 actual=200 PASS",
            "DEMO-07 customer-patch-denied: expected=403 actual=403 PASS",
            "DEMO-07a denied-patch-nonmutation: expected=200 actual=200 PASS",
            "DEMO-08 authorized-admin-patch: expected=200 actual=200 PASS",
            "DEMO-08a duplicate-nonce-rejected: expected=400 actual=400 PASS",
            "DEMO-08b duplicate-nonce-nonmutation: expected=200 actual=200 PASS",
            "DAY29 restart-restores-fixture: expected=200 actual=200 PASS",
            "DAY29 nonce-cache-cleared-on-restart: expected=200 actual=200 PASS",
            "Day 28 loopback HTTP rehearsal: PASS",
            "Day 29 HTTP process restart and nonce reset: PASS",
            "Only 127.0.0.1 was contacted; Uvicorn access logging was disabled.",
        )
        for evidence in expected:
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
