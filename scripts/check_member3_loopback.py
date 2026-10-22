"""Synthetic Rust -> Python lab handoff. Requires project Python deps and Cargo.

This starts a short-lived loopback analytics process, generates per-run secrets
only in memory, and never claims a Linux sensor, TLS or active enforcement.
"""

import os
import json
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def expect_rejected_batch(url, token, batch, status):
    request = urllib.request.Request(
        url,
        data=json.dumps(batch).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=2)
    except urllib.error.HTTPError as error:
        if error.code == status:
            return
    raise RuntimeError("Analytics did not reject invalid schema/time as expected")


def main():
    cargo = shutil.which("cargo") or str(Path.home() / ".cargo/bin/cargo")
    if not Path(cargo).is_file():
        raise SystemExit("Cargo is required for the Rust loopback check")
    environment = os.environ.copy()
    environment["APISENTINEL_INGEST_TOKEN"] = secrets.token_urlsafe(32)
    environment["APISENTINEL_HMAC_KEY"] = secrets.token_hex(32)
    environment["APISENTINEL_SOURCE_ID"] = "lab_collector_1"
    environment["APISENTINEL_KEY_VERSION"] = "lab-v1"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    environment["APISENTINEL_INGEST_URL"] = (
        f"http://127.0.0.1:{port}/v1/batches"
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "analytics.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    result_ok = False
    try:
        for _ in range(50):
            if server.poll() is not None:
                raise RuntimeError("Analytics stopped before health check")
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=0.5
                ) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        else:
            raise RuntimeError("Analytics health check timed out")
        sender = subprocess.run(
            [
                cargo,
                "run",
                "--quiet",
                "--locked",
                "--manifest-path",
                "collector/Cargo.toml",
                "--example",
                "loopback_ingest",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if sender.returncode != 0 or "idempotent retry" not in sender.stdout:
            raise RuntimeError("Rust sender/receiver contract check failed")
        now = datetime.now(timezone.utc)
        event = {
            "schema_name": "collector_event",
            "schema_version": "1.1",
            "event_id": str(uuid4()),
            "correlation_id": None,
            "correlation_quality": "unsupported",
            "source_id": "lab_collector_1",
            "sensor_sequence": 3,
            "sensor_monotonic_ns": 3,
            "observed_at": now.isoformat(),
            "direction": "ingress",
            "method": "GET",
            "status_code": None,
            "route_template": None,
            "route_quality": "route_unavailable",
            "data_classification": "restricted",
        }
        batch = {
            "schema_name": "collector_batch",
            "schema_version": "1.0",
            "batch_id": str(uuid4()),
            "created_at": now.isoformat(),
            "events": [event],
        }
        expect_rejected_batch(
            environment["APISENTINEL_INGEST_URL"],
            "x" * 32,
            batch,
            401,
        )
        wrong_source = json.loads(json.dumps(batch))
        wrong_source["events"][0]["source_id"] = "other_source"
        expect_rejected_batch(
            environment["APISENTINEL_INGEST_URL"],
            environment["APISENTINEL_INGEST_TOKEN"],
            wrong_source,
            403,
        )
        wrong_version = json.loads(json.dumps(batch))
        wrong_version["events"][0]["schema_version"] = "9.9"
        expect_rejected_batch(
            environment["APISENTINEL_INGEST_URL"],
            environment["APISENTINEL_INGEST_TOKEN"],
            wrong_version,
            422,
        )
        stale = json.loads(json.dumps(batch))
        stale["events"][0]["observed_at"] = (now - timedelta(seconds=3)).isoformat()
        expect_rejected_batch(
            environment["APISENTINEL_INGEST_URL"],
            environment["APISENTINEL_INGEST_TOKEN"],
            stale,
            422,
        )
        result_ok = True
    finally:
        server.terminate()
        try:
            stdout, stderr = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            stdout, stderr = server.communicate(timeout=5)
        if any(
            secret in stdout + stderr
            for secret in (
                environment["APISENTINEL_INGEST_TOKEN"],
                environment["APISENTINEL_HMAC_KEY"],
            )
        ):
            raise RuntimeError("Runtime secret appeared in analytics logs")
    if result_ok:
        print(
            "PASS: loopback Rust/Python ack, idempotent retry, invalid credential, "
            "wrong source, schema/freshness rejection and server log privacy; "
            "no sensor or enforcement"
        )


if __name__ == "__main__":
    main()
