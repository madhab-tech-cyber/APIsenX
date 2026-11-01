"""Day 24: OWASP API Security Top 10 metadata stays tied to real API evidence."""

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MAPPING_PATH = ROOT / "docs" / "owasp-api-security-mapping.json"
OPENAPI_PATH = ROOT / "docs" / "openapi.yaml"

EXPECTED_NAMES = {
    "API1:2023": "Broken Object Level Authorization",
    "API2:2023": "Broken Authentication",
    "API3:2023": "Broken Object Property Level Authorization",
    "API4:2023": "Unrestricted Resource Consumption",
    "API5:2023": "Broken Function Level Authorization",
    "API6:2023": "Unrestricted Access to Sensitive Business Flows",
    "API7:2023": "Server Side Request Forgery",
    "API8:2023": "Security Misconfiguration",
    "API9:2023": "Improper Inventory Management",
    "API10:2023": "Unsafe Consumption of APIs",
}


class Day24OWASPMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with MAPPING_PATH.open(encoding="utf-8") as mapping_file:
            cls.mapping = json.load(mapping_file)
        with OPENAPI_PATH.open(encoding="utf-8-sig") as contract_file:
            cls.contract = yaml.safe_load(contract_file)

    def test_all_2023_categories_are_present_once_with_canonical_names(self):
        entries = self.mapping["mappings"]
        identifiers = [entry["id"] for entry in entries]
        self.assertEqual(len(entries), 10)
        self.assertEqual(set(identifiers), set(EXPECTED_NAMES))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for entry in entries:
            with self.subTest(identifier=entry["id"]):
                self.assertEqual(entry["name"], EXPECTED_NAMES[entry["id"]])

    def test_every_mapped_route_exists_in_the_openapi_contract(self):
        paths = self.contract["paths"]
        for entry in self.mapping["mappings"]:
            for route in entry["routes"]:
                method, path = route.split(" ", 1)
                with self.subTest(category=entry["id"], route=route):
                    self.assertIn(path, paths)
                    self.assertIn(method.lower(), paths[path])

    def test_evidence_paths_and_examples_are_present(self):
        for entry in self.mapping["mappings"]:
            self.assertTrue(entry["example"]["scenario"])
            self.assertTrue(entry["example"]["expected_result"])
            for evidence_path in entry["evidence_files"]:
                with self.subTest(category=entry["id"], evidence=evidence_path):
                    self.assertTrue((ROOT / evidence_path).is_file())

    def test_coverage_labels_preserve_unassessed_and_partial_categories(self):
        allowed = {"regression_tested", "partial", "not_assessed"}
        by_id = {entry["id"]: entry for entry in self.mapping["mappings"]}
        for entry in self.mapping["mappings"]:
            self.assertIn(entry["coverage"], allowed)
        self.assertEqual(by_id["API6:2023"]["coverage"], "not_assessed")
        for identifier in ("API4:2023", "API7:2023", "API8:2023", "API9:2023", "API10:2023"):
            self.assertEqual(by_id[identifier]["coverage"], "partial")
        self.assertIn("not a full OWASP assessment", self.mapping["disclaimer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
