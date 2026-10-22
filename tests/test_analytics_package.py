"""Frozen source verification and deterministic candidate build, never publication."""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from analytics import package


class CandidatePackageTests(unittest.TestCase):
    def test_frozen_sources_match_and_release_is_held(self):
        package.check_freeze()
        frozen = json.loads(package.FREEZE.read_text())
        self.assertFalse(frozen["release_approved"])
        self.assertEqual(frozen["mode"], "monitor_only")
        self.assertEqual(frozen["rule_version"], "DET-1.2")

    def test_two_source_archives_are_byte_for_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = (
                Path(directory) / "first.zip",
                Path(directory) / "second.zip",
            )
            self.assertEqual(package.build(first), package.build(second))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    set(package.FILES) | {"analytics/release-candidate.json"},
                )
                for name, digest in package.current_manifest()["files"].items():
                    self.assertEqual(
                        hashlib.sha256(archive.read(name)).hexdigest(), digest
                    )

    def test_candidate_never_overwrites_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "candidate.zip"
            package.build(target)
            before = target.read_bytes()
            with self.assertRaises(FileExistsError):
                package.build(target)
            self.assertEqual(target.read_bytes(), before)

    def test_mutated_freeze_and_repository_output_fail(self):
        with patch("analytics.package.current_manifest", return_value={}):
            with self.assertRaises(ValueError):
                package.check_freeze()
        with self.assertRaises(ValueError):
            package.build(package.ROOT / "must-not-exist.zip")
        self.assertFalse((package.ROOT / "must-not-exist.zip").exists())

    def test_only_explicit_source_inputs_no_secrets_logs_or_binary_spools(self):
        for name in package.FILES:
            self.assertNotIn(".env", name)
            self.assertNotIn("runtime-data", name)
            self.assertFalse(name.endswith((".pem", ".key", ".log", ".pcap", ".zip")))
