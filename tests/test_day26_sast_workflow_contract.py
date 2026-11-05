"""Guard the Mock API SAST workflow's security-sensitive source coverage."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "mock-api-tests.yml"


def step_block(document: str, name: str) -> str:
    """Return one named GitHub Actions step without parsing YAML's on key."""
    pattern = (
        r"(?ms)^      - name: "
        + re.escape(name)
        + r"\n(?P<body>.*?)(?=^      - name: |\Z)"
    )
    match = re.search(pattern, document)
    if match is None:
        raise AssertionError(f"Required workflow step is missing: {name}")
    return match.group("body")


def run_command(block: str) -> str:
    match = re.search(r"(?m)^        run: (.+)$", block)
    if match is None:
        raise AssertionError("Workflow step has no single-line run command")
    return match.group(1).strip()


class Day26SastWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_security_tool_versions_are_pinned(self):
        block = step_block(self.workflow, "Install security and quality tools")
        command = run_command(block)
        for package in (
            "ruff==0.17.1",
            "pip-audit==2.10.1",
            "bandit==1.9.4",
        ):
            with self.subTest(package=package):
                self.assertIn(package, command)

    def test_ruff_covers_api_authorization_source_and_tests(self):
        block = step_block(self.workflow, "Run Ruff lint checks")
        self.assertEqual(
            run_command(block),
            "python -m ruff check mock-api src tests",
        )

    def test_bandit_covers_api_and_shared_authorization_source(self):
        block = step_block(
            self.workflow,
            "Run Mock API and authorization-source Bandit SAST",
        )
        command = run_command(block)
        self.assertEqual(command, "python -m bandit -r mock-api src -q")
        self.assertNotRegex(command, r"(^|\s)-s(\s|$)")
        self.assertNotRegex(command, r"(^|\s)--skip(\s|=)")

    def test_dependency_audit_and_full_regression_suite_are_present(self):
        audit = step_block(self.workflow, "Audit dependency vulnerabilities")
        suite = step_block(
            self.workflow,
            "Run authorization, API, and OpenAPI tests",
        )
        self.assertEqual(
            run_command(audit),
            "python -m pip_audit -r requirements.txt",
        )
        self.assertEqual(
            run_command(suite),
            "python -m unittest discover -s tests -v",
        )

    def test_independent_security_gates_precede_full_test_suite(self):
        names = [
            "Run Ruff lint checks",
            "Run Mock API and authorization-source Bandit SAST",
            "Audit dependency vulnerabilities",
            "Run authorization, API, and OpenAPI tests",
        ]
        positions = [
            self.workflow.index(f"- name: {name}") for name in names
        ]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main(verbosity=2)
