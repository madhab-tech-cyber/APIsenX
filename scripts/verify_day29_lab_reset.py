"""Verify the Day 29 synthetic lab baseline and process-restart reset."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "day29_lab_baseline.json"
LOOPBACK_REHEARSAL = ROOT / "scripts" / "day28_loopback_api_rehearsal.py"


def verify_fixture_hashes(root: Path, manifest: dict) -> list[str]:
    """Return fixture paths whose bytes differ from the reviewed baseline."""
    mismatches = []
    for relative_path, expected in manifest["fixtures"].items():
        path = root / relative_path
        if not path.is_file():
            mismatches.append(relative_path)
            continue
        data = path.read_bytes()
        git_header = f"blob {len(data)}\0".encode("ascii")
        actual = hashlib.sha1(git_header + data).hexdigest()
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
    cases_path = root / "mock_data" / "authorization_cases.json"
    with cases_path.open(encoding="utf-8") as handle:
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
    """Prove a new API interpreter reloads fixtures and clears volatile state."""
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
    limiter_probes = (
        (main.SERVICE_LIMITER, ("service", "day29-probe")),
        (main.SUBJECT_LIMITER, ("subject", "day29-probe")),
        (main.ROUTE_COST_LIMITER, ("route-cost", "day29-probe")),
        (main.SOURCE_LIMITER, ("source", "day29-probe")),
    )
    for limiter, key in limiter_probes:
        allowed, _, _ = limiter.consume(key, 1.0, 1.0)
        if not allowed or key not in limiter.buckets:
            raise SystemExit("Unable to dirty every volatile rate-limit bucket")
    main.SUBJECT_SEMAPHORES[("day29-probe", "read")] = (
        threading.BoundedSemaphore(1)
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
    print("fresh-process reset: PASS")


def verify_loopback_http_process_restart() -> None:
    """Prove the real API process reloads fixture state and clears PATCH nonces."""
    result = subprocess.run(
        [sys.executable, str(LOOPBACK_REHEARSAL), "--mode", "reset-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("Loopback HTTP process-restart verification failed")
    if "Day 29 HTTP process restart and nonce reset: PASS" not in result.stdout:
        raise SystemExit("Loopback HTTP process-restart evidence missing")
    print("Day 29 HTTP process restart and nonce reset: PASS")


def main_cli() -> int:
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    mismatches = verify_fixture_hashes(ROOT, manifest)
    if mismatches:
        raise SystemExit("Fixture baseline mismatch: " + ", ".join(mismatches))
    verify_fixture_shape(ROOT, manifest)
    verify_fresh_process_reset()
    verify_loopback_http_process_restart()
    print("Day 29 clean synthetic lab reset: PASS")
    print("Fixture hashes, record counts, fresh-interpreter state, and live HTTP process restart verified.")
    print("No checked-in fixture was modified; only 127.0.0.1 was contacted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
