"""Verify the Day 29 synthetic lab baseline and process-restart reset."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "day29_lab_baseline.json"


def verify_fixture_hashes(root: Path, manifest: dict) -> list[str]:
    """Return fixture paths whose bytes differ from the reviewed baseline."""
    mismatches = []
    for relative_path, expected in manifest["fixtures"].items():
        path = root / relative_path
        if not path.is_file():
            mismatches.append(relative_path)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(relative_path)
    return mismatches


def verify_fixture_shape(root: Path, manifest: dict) -> None:
    """Check that the immutable baseline contains the expected synthetic records."""
    expected = manifest["expected"]
    with (root / "mock_data" / "orders.json").open(encoding="utf-8") as handle:
        orders = json.load(handle)["orders"]
    with (root / "mock_data" / "users.json").open(encoding="utf-8") as handle:
        users = json.load(handle)["users"]
    with (root / "mock_data" / "sharing_grants.json").open(encoding="utf-8") as handle:
        grants = json.load(handle)["grants"]
    with (root / "mock_data" / "authorization_cases.json").open(encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]

    if len(orders) != expected["orders"]:
        raise SystemExit("Unexpected synthetic order count")
    if len(users) != expected["users"]:
        raise SystemExit("Unexpected synthetic user count")
    if len(grants) != expected["sharing_grants"]:
        raise SystemExit("Sharing-grant fixture is not clean")
    if len(cases) != expected["authorization_cases"]:
        raise SystemExit("Unexpected authorization-case count")
    if any(not item["id"].startswith("order-") for item in orders):
        raise SystemExit("Non-lab order identifier found")
    if any(not item["id"].startswith("user-") and item["id"] not in {
        "admin-1", "support-1", "tenant-admin-1"
    } for item in users):
        raise SystemExit("Unexpected identity in synthetic user fixture")


def verify_fresh_process_reset() -> None:
    """Prove a new API process reloads fixtures and clears volatile runtime state."""
    child = r"""
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "mock-api"))
import main

assert main.ORDERS == main.load_orders()
assert main.ORDERS["order-1001"]["status"] == "processing"
assert main.REVOKED_TOKENS == set()
assert main.USED_NONCES == {}
for limiter in (
    main.SERVICE_LIMITER,
    main.SUBJECT_LIMITER,
    main.ROUTE_COST_LIMITER,
    main.SOURCE_LIMITER,
):
    assert limiter.buckets == {}
assert main.SUBJECT_SEMAPHORES == {}
print("fresh-process reset: PASS")
"""
    # The parent process below is deliberately dirtied first. This child starts
    # with a separate interpreter and must see only the checked-in baseline.
    sys.path.insert(0, str(ROOT / "mock-api"))
    import main

    main.ORDERS["order-1001"]["status"] = "shipped"
    main.REVOKED_TOKENS.add("lab-user-a-token")
    main.USED_NONCES["day29-reset-probe"] = main.utc_now()
    main.SERVICE_LIMITER.consume(("day29-probe",), 1.0, 1.0)
    main.SUBJECT_SEMAPHORES[("day29-probe", "read")] = (
        __import__("threading").BoundedSemaphore(1)
    )

    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("Fresh-process reset verification failed")
    if "fresh-process reset: PASS" not in result.stdout:
        raise SystemExit("Fresh-process reset evidence missing")


def main_cli() -> int:
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    mismatches = verify_fixture_hashes(ROOT, manifest)
    if mismatches:
        raise SystemExit("Fixture baseline mismatch: " + ", ".join(mismatches))
    verify_fixture_shape(ROOT, manifest)
    verify_fresh_process_reset()
    print("Day 29 clean synthetic lab reset: PASS")
    print("Fixture hashes, record counts and fresh-process reset verified.")
    print("No checked-in fixture was modified; no external target was contacted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
