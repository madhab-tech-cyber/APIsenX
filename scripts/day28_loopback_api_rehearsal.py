"""Run the synthetic Mock API over loopback HTTP and verify process reset.

This harness starts only a local Uvicorn child process, uses checked-in lab
identities, disables access logging, and removes optional Sentinel settings
from the child environment. It never contacts an external service.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
OWNER_TOKEN = "lab-user-a-token"
ADMIN_TOKEN = "lab-admin-token"
SUPPORT_TOKEN = "lab-support-token"
RESET_NONCE = "day28-admin-restart-0001"


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self, request, response, code, message, headers, new_url
    ):
        return None


LOOPBACK_OPENER = build_opener(ProxyHandler({}), RejectRedirects())


SENSITIVE_LOG_MARKERS = (
    OWNER_TOKEN,
    ADMIN_TOKEN,
    SUPPORT_TOKEN,
    "order-1001",
    "order-1002",
    "user-a",
    "user-b",
    RESET_NONCE,
)


def reserve_loopback_port() -> int:
    """Ask the OS for an unused loopback port, then release the reservation."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def http_request(
    port: int,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    policy: bool = True,
    nonce: str | None = None,
    payload: dict | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    """Issue one bounded request to this harness's loopback-only child API."""
    headers: dict[str, str] = {}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if policy:
        headers["X-Policy-Version"] = "AP-1.0"
    if nonce is not None:
        headers["X-Request-Nonce"] = nonce

    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"http://{HOST}:{port}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with LOOPBACK_OPENER.open(request, timeout=3) as response:
            return response.status, response.read(), {
                key.lower(): value for key, value in response.headers.items()
            }
    except HTTPError as error:
        return error.code, error.read(), {
            key.lower(): value for key, value in error.headers.items()
        }


def expect_status(
    label: str,
    expected: int,
    response: tuple[int, bytes, dict[str, str]],
) -> dict:
    status, body, headers = response
    if status != expected:
        raise AssertionError(
            f"{label}: expected HTTP {expected}, received HTTP {status}"
        )
    correlation_id = headers.get("x-correlation-id")
    try:
        uuid.UUID(correlation_id or "")
    except (ValueError, AttributeError):
        raise AssertionError(f"{label}: missing valid correlation ID") from None
    print(f"{label}: expected={expected} actual={status} PASS")
    if not body:
        return {}
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AssertionError(f"{label}: response was not valid JSON") from None


def stop_server(process: subprocess.Popen) -> str:
    """Stop only the child process created by this harness and collect its log."""
    if process.poll() is None:
        process.terminate()
    try:
        output, _ = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate(timeout=5)
    return output or ""


def start_server(port: int | None = None) -> tuple[subprocess.Popen, int]:
    """Start Uvicorn on loopback and wait for an authenticated readiness probe."""
    selected_port = reserve_loopback_port() if port is None else port
    environment = os.environ.copy()
    # Never let a developer/runner's optional observer configuration cause
    # this isolated API test to send telemetry to another process or service.
    for name in (
        "APISENTINEL_URL",
        "APISENTINEL_INGEST_TOKEN",
        "APISENTINEL_SOURCE_ID",
        "APISENTINEL_DIAGNOSTICS",
        "APISENX_TOKEN_TTL_SECONDS",
    ):
        environment.pop(name, None)

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(ROOT / "mock-api"),
        "--host",
        HOST,
        "--port",
        str(selected_port),
        "--no-access-log",
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            process.communicate(timeout=1)
            raise RuntimeError("The loopback Mock API exited before readiness")
        try:
            status, _, _ = http_request(
                selected_port,
                "/orders",
                token=OWNER_TOKEN,
            )
            if status == 200:
                return process, selected_port
        except OSError:
            pass
        time.sleep(0.1)

    stop_server(process)
    raise TimeoutError("The loopback Mock API did not become ready within 20 seconds")


def assert_log_privacy(logs: str) -> None:
    for marker in SENSITIVE_LOG_MARKERS:
        if marker in logs:
            raise AssertionError("A synthetic credential or object marker appeared in API logs")


def run_reset_probe() -> None:
    """Prove order state and nonce cache reset across a real HTTP process restart."""
    logs = []
    first, port = start_server()
    try:
        changed = expect_status(
            "day29-before-restart-admin-patch",
            200,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=ADMIN_TOKEN,
                nonce=RESET_NONCE,
                payload={"status": "shipped"},
            ),
        )
        if changed.get("status") != "shipped":
            raise AssertionError("The pre-restart mutation was not observed")
    finally:
        logs.append(stop_server(first))

    second, _ = start_server(port)
    try:
        baseline = expect_status(
            "day29-after-restart-owner-read",
            200,
            http_request(port, "/orders/order-1001", token=OWNER_TOKEN),
        )
        if baseline.get("status") != "processing":
            raise AssertionError("The fresh API process did not restore fixture state")

        replay = expect_status(
            "day29-after-restart-same-nonce",
            200,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=ADMIN_TOKEN,
                nonce=RESET_NONCE,
                payload={"status": "delivered"},
            ),
        )
        if replay.get("status") != "delivered":
            raise AssertionError("The fresh process did not accept the reset nonce")
    finally:
        logs.append(stop_server(second))

    assert_log_privacy("\n".join(logs))
    print("Day 29 HTTP process restart and nonce reset: PASS")


def run_full_rehearsal() -> None:
    """Run the documented API matrix, replay check, and restart on loopback."""
    logs = []
    first, port = start_server()
    try:
        owner = expect_status(
            "DEMO-01 owner-read",
            200,
            http_request(port, "/orders/order-1001", token=OWNER_TOKEN),
        )
        if owner.get("id") != "order-1001" or owner.get("status") != "processing":
            raise AssertionError("Owner read did not return the baseline fixture")

        bola = expect_status(
            "DEMO-02 cross-owner-bola",
            404,
            http_request(port, "/orders/order-1002", token=OWNER_TOKEN),
        )
        if "order-1002" in json.dumps(bola) or "user-b" in json.dumps(bola):
            raise AssertionError("BOLA denial disclosed the protected object")

        expect_status(
            "DEMO-03 customer-admin-bfla",
            403,
            http_request(port, "/admin/orders", token=OWNER_TOKEN),
        )
        expect_status(
            "DEMO-04 missing-authentication",
            401,
            http_request(port, "/orders", token=None),
        )
        expect_status(
            "DEMO-05 missing-policy-version",
            400,
            http_request(port, "/orders", token=OWNER_TOKEN, policy=False),
        )

        support = expect_status(
            "DEMO-06 support-masked-view",
            200,
            http_request(port, "/support/orders", token=SUPPORT_TOKEN),
        )
        support_rows = support.get("orders")
        if not isinstance(support_rows, list) or any(
            set(row) != {"id", "status"} for row in support_rows
        ):
            raise AssertionError("Support response included fields outside id/status")

        expect_status(
            "DEMO-07 customer-patch-denied",
            403,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=OWNER_TOKEN,
                nonce="day28-customer-0001",
                payload={"status": "shipped"},
            ),
        )
        unchanged = expect_status(
            "DEMO-07a denied-patch-nonmutation",
            200,
            http_request(port, "/orders/order-1001", token=OWNER_TOKEN),
        )
        if unchanged.get("status") != "processing":
            raise AssertionError("Denied customer PATCH mutated the order")

        admin_patch = expect_status(
            "DEMO-08 authorized-admin-patch",
            200,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=ADMIN_TOKEN,
                nonce=RESET_NONCE,
                payload={"status": "shipped"},
            ),
        )
        if admin_patch.get("status") != "shipped":
            raise AssertionError("Authorized admin PATCH did not update the status")

        expect_status(
            "DEMO-08a duplicate-nonce-rejected",
            400,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=ADMIN_TOKEN,
                nonce=RESET_NONCE,
                payload={"status": "delivered"},
            ),
        )
        after_replay = expect_status(
            "DEMO-08b duplicate-nonce-nonmutation",
            200,
            http_request(port, "/orders/order-1001", token=OWNER_TOKEN),
        )
        if after_replay.get("status") != "shipped":
            raise AssertionError("Rejected replay changed order state")
    finally:
        logs.append(stop_server(first))

    second, _ = start_server(port)
    try:
        reset = expect_status(
            "DAY29 restart-restores-fixture",
            200,
            http_request(port, "/orders/order-1001", token=OWNER_TOKEN),
        )
        if reset.get("status") != "processing":
            raise AssertionError("Process restart did not restore the original fixture")

        reused = expect_status(
            "DAY29 nonce-cache-cleared-on-restart",
            200,
            http_request(
                port,
                "/orders/order-1001",
                method="PATCH",
                token=ADMIN_TOKEN,
                nonce=RESET_NONCE,
                payload={"status": "shipped"},
            ),
        )
        if reused.get("status") != "shipped":
            raise AssertionError("The nonce was not reset with the API process")
    finally:
        logs.append(stop_server(second))

    assert_log_privacy("\n".join(logs))
    print("Day 28 loopback HTTP rehearsal: PASS")
    print("Day 29 HTTP process restart and nonce reset: PASS")
    print("Only 127.0.0.1 was contacted; Uvicorn access logging was disabled.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("full", "reset-only"),
        default="full",
        help="Run the Day 28 HTTP matrix or only the Day 29 restart proof.",
    )
    args = parser.parse_args()
    if args.mode == "reset-only":
        run_reset_probe()
    else:
        run_full_rehearsal()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
