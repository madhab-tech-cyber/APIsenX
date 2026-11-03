#!/usr/bin/env python3
"""Controlled HTTP load/overload probe for the APISenX local lab.

Example:
  python scripts/day19_load_probe.py --url http://127.0.0.1:8000/orders \
      --requests 200 --concurrency 10 --token lab-user-a-token

Run only against an authorized local/test instance. This tool records observations;
it does not certify production capacity or change enforcement mode.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone


def probe(
    url: str, token: str, policy_version: str, timeout: float
) -> tuple[int, float, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Policy-Version": policy_version,
            "Accept": "application/json",
        },
        method="GET",
    )
    started = time.perf_counter()
    retry_after = ""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024 * 1024)
            status = response.status
            retry_after = response.headers.get("Retry-After", "")
            error = ""
    except urllib.error.HTTPError as exc:
        status = exc.code
        retry_after = exc.headers.get("Retry-After", "")
        exc.read(4096)
        error = "http_error"
    except Exception as exc:  # record class only; never include headers/tokens
        status = 0
        error = type(exc).__name__
    return status, time.perf_counter() - started, error, retry_after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Authorized local/test endpoint")
    parser.add_argument(
        "--token", required=True, help="Demo bearer token (not printed)"
    )
    parser.add_argument("--policy-version", default="AP-1.0")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 10000:
        parser.error("--requests must be between 1 and 10000")
    if args.concurrency < 1 or args.concurrency > 100:
        parser.error("--concurrency must be between 1 and 100")
    if args.timeout <= 0 or args.timeout > 30:
        parser.error("--timeout must be greater than 0 and at most 30 seconds")

    started = time.perf_counter()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(probe, args.url, args.token, args.policy_version, args.timeout)
            for _ in range(args.requests)
        ]
        results.extend(
            future.result() for future in concurrent.futures.as_completed(futures)
        )
    elapsed = time.perf_counter() - started
    latencies_ms = [latency * 1000 for _, latency, _, _ in results]
    statuses = Counter(str(status) for status, _, _, _ in results)
    errors = Counter(error for _, _, error, _ in results if error)
    retry_after_values = Counter(value for _, _, _, value in results if value)
    rate_limited = [row for row in results if row[0] == 429]
    valid_retry_after = [
        row for row in rate_limited
        if row[3].isdigit() and int(row[3]) >= 1
    ]
    ordered = sorted(latencies_ms)

    def percentile(p: float) -> float:
        if not ordered:
            return 0.0
        index = min(len(ordered) - 1, int((len(ordered) - 1) * p))
        return round(ordered[index], 2)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": args.url,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_rps": round(len(results) / elapsed, 2) if elapsed else 0,
        "status_counts": dict(statuses),
        "transport_error_classes": dict(errors),
        "retry_after": {
            "observed_values": dict(retry_after_values),
            "http_429_count": len(rate_limited),
            "http_429_with_positive_integer_count": len(valid_retry_after),
            "http_429_missing_or_invalid_count": (
                len(rate_limited) - len(valid_retry_after)
            ),
        },
        "latency_ms": {
            "min": round(min(ordered), 2) if ordered else 0,
            "median": round(statistics.median(ordered), 2) if ordered else 0,
            "p95": percentile(0.95),
            "max": round(max(ordered), 2) if ordered else 0,
        },
        "limitations": [
            "single client process and one target endpoint",
            "not a distributed/multi-worker test",
            "not a production capacity certification",
            "Retry-After validation here accepts positive integer seconds only",
            "compare normal-load, overload, and recovery runs "
            "before drawing conclusions",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
