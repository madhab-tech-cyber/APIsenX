"""Exercise the real Mock API -> Sentinel adapter -> Analytics loopback path.

This is an isolated synthetic lab check. It does not start an eBPF sensor,
enable enforcement, or claim production/shared transport.
"""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_ready(url, process, log_file):
    for _ in range(60):
        if process.poll() is not None:
            log_file.flush()
            raise RuntimeError("A lab service exited before becoming ready")
        try:
            status, _ = request(url)
            if status == 200:
                return
        except (OSError, TimeoutError, ValueError):
            time.sleep(0.1)
    raise RuntimeError("A lab service health check timed out")


def main():
    analytics_port, api_port = free_port(), free_port()
    ingest_token = secrets.token_urlsafe(36)
    hmac_key = secrets.token_hex(32)
    reader_token = secrets.token_urlsafe(36)
    now = datetime.now(timezone.utc)
    expiry = (now + timedelta(minutes=15)).isoformat()

    analytics_env = os.environ.copy()
    analytics_env.update(
        {
            "APISENTINEL_INGEST_TOKEN": ingest_token,
            "APISENTINEL_HMAC_KEY": hmac_key,
            "APISENTINEL_SOURCE_ID": "mock_api",
            "APISENTINEL_KEY_VERSION": "lab-e2e-v1",
            "APISENTINEL_READER_ID": "api-analytics-e2e-reader",
            "APISENTINEL_READER_TOKEN": reader_token,
            "APISENTINEL_READER_CASE": "lab_case",
            "APISENTINEL_READER_ROLE": "analyst",
            "APISENTINEL_READER_EXPIRES_AT": expiry,
        }
    )
    api_env = os.environ.copy()
    api_env.update(
        {
            "APISENTINEL_URL": f"http://127.0.0.1:{analytics_port}",
            "APISENTINEL_INGEST_TOKEN": ingest_token,
            "APISENTINEL_SOURCE_ID": "mock_api",
        }
    )

    processes = []
    log_handles = []
    try:
        for label, command, cwd, environment in (
            (
                "analytics",
                [
                    sys.executable, "-m", "uvicorn",
                    "analytics.app:create_app", "--factory",
                    "--host", "127.0.0.1", "--port", str(analytics_port),
                    "--no-access-log",
                ],
                ROOT,
                analytics_env,
            ),
            (
                "mock-api",
                [
                    sys.executable, "-m", "uvicorn", "main:app",
                    "--app-dir", str(ROOT / "mock-api"),
                    "--host", "127.0.0.1", "--port", str(api_port),
                    "--no-access-log",
                ],
                ROOT,
                api_env,
            ),
        ):
            handle = tempfile.NamedTemporaryFile(
                mode="w+", encoding="utf-8", prefix=f"apisenx-{label}-",
                suffix=".log", delete=False,
            )
            log_handles.append((handle, label))
            process = subprocess.Popen(
                command, cwd=cwd, env=environment,
                stdout=handle, stderr=subprocess.STDOUT, text=True,
            )
            processes.append(process)
            if label == "analytics":
                wait_ready(
                    f"http://127.0.0.1:{analytics_port}/health",
                    process, handle,
                )
            else:
                wait_ready(
                    f"http://127.0.0.1:{api_port}/health",
                    process, handle,
                )

        api_base = f"http://127.0.0.1:{api_port}"
        policy = {"X-Policy-Version": "AP-1.0"}
        owner_headers = {
            "Authorization": "Bearer lab-user-a-token",
            **policy,
        }

        owner_status, _ = request(
            api_base + "/orders/order-1001", owner_headers
        )
        bola_status, _ = request(
            api_base + "/orders/order-1002", owner_headers
        )
        if owner_status != 200 or bola_status != 404:
            raise RuntimeError(
                f"Mock API authorization outcomes unexpected: "
                f"owner={owner_status}, cross-owner={bola_status}"
            )

        inventory_status, inventory = request(
            f"http://127.0.0.1:{analytics_port}/v1/inventory",
            {"Authorization": "Bearer " + reader_token},
        )
        if inventory_status != 200:
            raise RuntimeError("Analytics protected inventory read failed")
        matching = [
            item for item in inventory.get("items", [])
            if item.get("method") == "GET"
            and item.get("route") == "/orders/{orderId}"
            and item.get("classification") == "documented"
        ]
        if len(matching) != 1 or matching[0]["observation_count"] != 2:
            raise RuntimeError(
                "Analytics inventory did not contain both API observations"
            )
        if inventory.get("mode") != "monitor_only":
            raise RuntimeError("Analytics mode unexpectedly changed")
        rendered = json.dumps(inventory, sort_keys=True)
        for secret in (
            ingest_token, hmac_key, reader_token,
            "order-1001", "order-1002", "lab-user-a-token",
        ):
            if secret in rendered:
                raise RuntimeError("Sensitive API data appeared in analytics inventory")

        print(
            "PASS: Mock API owner read=200 and BOLA denial=404; "
            "both route-template observations reached authenticated Analytics "
            "inventory; secrets and raw object IDs absent; monitor_only preserved"
        )
    finally:
        for process in reversed(processes):
            process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for handle, _label in log_handles:
            handle.flush()
            handle.seek(0)
            logs = handle.read()
            if any(
                secret in logs
                for secret in (ingest_token, hmac_key, reader_token)
            ):
                raise RuntimeError("A runtime credential appeared in service logs")
            handle.close()
            try:
                os.unlink(handle.name)
            except OSError:
                pass


if __name__ == "__main__":
    main()
