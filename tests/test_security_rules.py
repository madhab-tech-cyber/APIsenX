"""
Security & Compliance Automated Test Suite
Role: Member 2 (eBPF Traffic Engineer)
Validates compliance with Section 5 Security and Review Checklist
"""

import unittest
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FORBIDDEN_PATTERNS = [
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----", "Private cryptographic key"),
    (r"(password|passwd|secret|api_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "Hardcoded credential/secret"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"bearer\s+[A-Za-z0-9_\-\.]{32,}", "Hardcoded Bearer Token"),
]

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
EXCLUDED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".lock"}


class TestSecurityAndCompliance(unittest.TestCase):
    """Test suite ensuring zero secret leakage and compliance with security rules."""

    def test_zero_staged_secrets_or_private_keys(self):
        """Rule 1: Never commit secrets, personal data, raw packet captures, or private keys."""
        violations = []
        for root, dirs, files in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in EXCLUDED_EXTENSIONS:
                    continue

                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, REPO_ROOT)

                # Skip tests checking patterns themselves
                if relpath.replace("\\", "/").endswith("test_security_rules.py"):
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pattern, desc in FORBIDDEN_PATTERNS:
                            if re.search(pattern, content, re.IGNORECASE):
                                violations.append(f"{relpath}: contains {desc}")
                except Exception as e:
                    violations.append(f"Could not read {relpath}: {e}")

        self.assertEqual(
            len(violations),
            0,
            "Security rule violation! Sensitive data detected in repository:\n" + "\n".join(violations),
        )

    def test_sensor_records_are_fully_initialized_and_sequenced(self):
        """Both producer paths must zero records and use the shared sequence."""
        sensor_path = os.path.join(REPO_ROOT, "ebpf", "src", "api_sentinel_sensor.c")
        with open(sensor_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertIn("api_sentinel_event_sequence SEC(\".maps\")", source)
        self.assertIn("__sync_fetch_and_add(sequence, 1) + 1", source)
        self.assertEqual(source.count("__builtin_memset(event, 0, sizeof(*event));"), 2)
        self.assertEqual(source.count("event->event_id = event_id;"), 2)

        ingress = source.split("int api_sentinel_tc_ingress", 1)[1].split(
            "int api_sentinel_tc_egress", 1
        )[0]
        egress = source.split("int api_sentinel_tc_egress", 1)[1]
        for producer in (ingress, egress):
            self.assertIn("next_event_id(&event_id)", producer)
            self.assertIn("__builtin_memset(event, 0, sizeof(*event));", producer)
            self.assertIn("bpf_ringbuf_submit(event, 0);", producer)

    def test_no_pcap_files_tracked(self):
        """Rule 2: Ensure raw packet captures (*.pcap, *.pcapng) are not tracked."""
        pcap_files = []
        for root, dirs, files in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file.lower().endswith((".pcap", ".pcapng", ".cap")):
                    pcap_files.append(os.path.join(root, file))

        self.assertEqual(
            len(pcap_files),
            0,
            f"Raw packet capture files found in repository: {pcap_files}. Must not be committed.",
        )

    def test_gitignore_covers_sensitive_artifacts(self):
        """Verify .gitignore properly blocks .env, keys, and pcaps."""
        gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
        self.assertTrue(os.path.isfile(gitignore_path), ".gitignore must exist")
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gi_content = f.read()

        self.assertIn("*.pcap", gi_content)
        self.assertIn("*.key", gi_content)
        self.assertIn(".env", gi_content)


if __name__ == "__main__":
    unittest.main()
