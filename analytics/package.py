"""Reproducible SOURCE candidate, not a public release or authorization to deploy."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from analytics.decisions import rules_digest
from analytics.detection import RULE_VERSION

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "analytics/release-candidate.json"
FILES = (
    "requirements.txt",
    "pyproject.toml",
    "src/authorization.py",
    "mock_data/users.json",
    "mock_data/orders.json",
    "mock_data/sharing_grants.json",
    "docs/openapi.yaml",
    "analytics/README.md",
    "analytics/__init__.py",
    "analytics/app.py",
    "analytics/audit.py",
    "analytics/decisions.py",
    "analytics/demo.py",
    "analytics/detection.py",
    "analytics/evaluate.py",
    "analytics/flow.py",
    "analytics/masking.py",
    "analytics/management.py",
    "analytics/models.py",
    "analytics/normalization.py",
    "analytics/ownership.py",
    "analytics/package.py",
    "analytics/review_demo.py",
    "analytics/final_demo.py",
    "analytics/schemas.py",
    "analytics/store.py",
    "docs/member4-ingestion-contract.md",
    "docs/member4-recommendation-contract.md",
    "docs/member4-management-contract.md",
    "docs/member4-rule-catalog.md",
    "docs/member4-release-checklist.md",
    "docs/member4-days01-10-evidence.md",
    "docs/member4-days11-20-evidence.md",
    "docs/member4-days21-30-evidence.md",
    "docs/member4-review-checkpoints.json",
    "tests/fixtures/detection_cases.json",
    "tests/test_analytics_normalization.py",
    "tests/test_analytics_ownership.py",
    "tests/test_analytics_service.py",
    "tests/test_analytics_detection.py",
    "tests/test_analytics_decisions.py",
    "tests/test_analytics_management.py",
    "tests/test_analytics_hardening.py",
    "tests/test_analytics_package.py",
    "scripts/check_analytics_secrets.py",
)


def canonical_bytes(path: Path) -> bytes:
    """Normalize text line endings for cross-platform reproducibility."""
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def current_manifest():
    hashes = {}
    for name in sorted(FILES):
        path = ROOT / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(ROOT)
            or path.stat().st_size > 1048576
        ):
            raise ValueError("Unsafe candidate input")
        hashes[name] = hashlib.sha256(canonical_bytes(path)).hexdigest()
    return {
        "package_version": "0.1.0-lab-candidate",
        "rule_version": RULE_VERSION,
        "mode": "monitor_only",
        "release_approved": False,
        "dependency_lock": "Direct pins only; transitive lock/SBOM pending",
        "rules_digest": rules_digest(),
        "files": hashes,
    }


def check_freeze():
    if json.loads(FREEZE.read_text()) != current_manifest():
        raise ValueError("Candidate source differs from the frozen manifest")


def build(output):
    check_freeze()
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError(
            "Build outside the repository; do not commit generated archives"
        )
    with zipfile.ZipFile(
        output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name in sorted((*FILES, "analytics/release-candidate.json")):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(
                info, canonical_bytes(ROOT / name), compresslevel=9
            )
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--manifest", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--output", type=Path)
    options = parser.parse_args()
    if options.manifest:
        print(json.dumps(current_manifest(), indent=2, sort_keys=True))
    elif options.check:
        check_freeze()
        print("Frozen candidate source matches; release remains NOT APPROVED")
    else:
        print("Candidate archive SHA256:", build(options.output))
        print("Source candidate only; no tag, publication or deployment approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
