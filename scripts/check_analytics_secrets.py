"""Fail on detect-secrets candidates in the Member 4 delivery (never print values)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [
        "analytics",
        *[
            str(path.relative_to(ROOT))
            for path in sorted((ROOT / "docs").glob("member4*"))
        ],
        "tests/fixtures/detection_cases.json",
        "scripts/check_analytics_secrets.py",
        *[
            str(path.relative_to(ROOT))
            for path in sorted((ROOT / "tests").glob("test_analytics*.py"))
        ],
    ]
    result = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan", "--all-files", *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode:
        print("BLOCKED: detect-secrets did not complete")
        return 2
    findings = json.loads(result.stdout)["results"]
    count = sum(len(values) for values in findings.values())
    print(f"Member 4 secret scan: {count} candidate(s) in {len(findings)} file(s)")
    return 1 if count else 0


if __name__ == "__main__":
    raise SystemExit(main())
