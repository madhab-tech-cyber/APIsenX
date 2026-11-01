"""Day 24: outbound Sentinel URLs cannot escape the literal loopback boundary."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

from sentinel_adapter import SentinelObservationAdapter  # noqa: E402


TOKEN = "synthetic-sentinel-ingest-token-0123456789"


class Day24SentinelEndpointValidationTests(unittest.TestCase):
    def adapter(self, endpoint):
        return SentinelObservationAdapter(endpoint, TOKEN, "mock_api")

    def test_accepts_and_canonicalizes_literal_ipv4_loopback_urls(self):
        cases = (
            ("http://127.0.0.1:9000", "http://127.0.0.1:9000/v1/events"),
            ("http://127.0.0.1:9000/", "http://127.0.0.1:9000/v1/events"),
            ("http://127.0.0.2:9001", "http://127.0.0.2:9001/v1/events"),
        )
        for endpoint, expected in cases:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.adapter(endpoint).endpoint, expected)

    def test_rejects_dns_names_non_loopback_and_alternate_host_forms(self):
        endpoints = (
            "http://localhost:9000",
            "http://localhost.evil.example:9000",
            "http://127.0.0.1.evil.example:9000",
            "http://2130706433:9000",
            "http://0x7f000001:9000",
            "http://10.0.0.1:9000",
            "http://192.168.1.10:9000",
            "https://127.0.0.1:9000",
            "http://[::1]:9000",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):
                    self.adapter(endpoint)

    def test_rejects_userinfo_paths_queries_fragments_and_invalid_ports(self):
        endpoints = (
            "http://user@127.0.0.1:9000",
            "http://127.0.0.1:9000@attacker.example",
            "http://127.0.0.1:9000/path",
            "http://127.0.0.1:9000?next=http://attacker.example",
            "http://127.0.0.1:9000#fragment",
            "http://127.0.0.1:0",
            "http://127.0.0.1:65536",
            "http://127.0.0.1:abc",
            "http://127.0.0.1:",
            "",
            None,
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):
                    self.adapter(endpoint)


if __name__ == "__main__":
    unittest.main(verbosity=2)
