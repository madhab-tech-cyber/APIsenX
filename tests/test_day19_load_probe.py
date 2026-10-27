import importlib.util
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "day19_load_probe.py"
SPEC = importlib.util.spec_from_file_location("day19_load_probe", SCRIPT)
load_probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(load_probe)


class ProbeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/limited":
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b'{"error":"limited"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"orders":[]}')

    def log_message(self, format_string, *args):
        return


class Day19LoadProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_probe_records_success_without_returning_credentials(self):
        result = load_probe.probe(
            f"{self.base_url}/orders",
            "test-secret-token",
            "AP-1.0",
            2.0,
        )
        self.assertEqual(result[0], 200)
        self.assertGreaterEqual(result[1], 0)
        self.assertEqual(result[2], "")
        self.assertNotIn("test-secret-token", repr(result))

    def test_probe_records_rate_limit_response(self):
        result = load_probe.probe(
            f"{self.base_url}/limited",
            "test-secret-token",
            "AP-1.0",
            2.0,
        )
        self.assertEqual(result[0], 429)
        self.assertGreaterEqual(result[1], 0)
        self.assertEqual(result[2], "http_error")

    def test_probe_records_connection_failure_without_sensitive_detail(self):
        result = load_probe.probe(
            "http://127.0.0.1:1/unavailable",
            "test-secret-token",
            "AP-1.0",
            0.2,
        )
        self.assertEqual(result[0], 0)
        self.assertNotEqual(result[2], "")
        self.assertNotIn("test-secret-token", repr(result))


if __name__ == "__main__":
    unittest.main()
