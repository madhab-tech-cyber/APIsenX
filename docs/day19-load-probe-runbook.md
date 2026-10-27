# Day 19 Load Probe Runbook

**Status:** Ready to execute in an authorized isolated lab; measurements have not yet been collected.
**Tool:** `scripts/day19_load_probe.py`
**Policy:** AP-1.0. Keep enforcement in `monitor_only`; do not run against production or third-party targets.

## 1. Preconditions

- Check out the intended reviewed commit and record `git rev-parse HEAD`.
- Start the local Mock API using the repository's documented development command.
- Confirm the service is healthy and that the demo token is valid for the lab.
- Use only `http://127.0.0.1` or another explicitly authorized test endpoint.
- Do not paste bearer tokens into issue comments, committed files, or retained reports.

## 2. Capture normal-load baseline

PowerShell example, from the repository root:

```powershell
New-Item -ItemType Directory -Force evidence/day19 | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
python scripts/day19_load_probe.py --url http://127.0.0.1:8000/orders --requests 100 --concurrency 5 --token lab-user-a-token --policy-version AP-1.0 |
  Tee-Object -FilePath "evidence/day19/normal-$stamp.json"
```

## 3. Capture overload behavior

Run a bounded higher-concurrency test only after confirming the API is a local isolated lab:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
python scripts/day19_load_probe.py --url http://127.0.0.1:8000/orders --requests 500 --concurrency 25 --token lab-user-a-token --policy-version AP-1.0 |
  Tee-Object -FilePath "evidence/day19/overload-$stamp.json"
```

The probe permits at most 10,000 requests and concurrency 100. Do not raise these limits or run repeated aggressive probes just to force a desired outcome.

## 4. Capture recovery

Allow the service to settle. If a restart is part of the scenario, record it because process-local rate/concurrency state resets on restart. Then rerun the baseline:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
python scripts/day19_load_probe.py --url http://127.0.0.1:8000/orders --requests 100 --concurrency 5 --token lab-user-a-token --policy-version AP-1.0 |
  Tee-Object -FilePath "evidence/day19/recovery-$stamp.json"
```

## 5. Review and attach evidence

For each report, review `status_counts`, `transport_error_classes`, `throughput_rps`, `latency_ms` (min, median, p95, max), and the `retry_after` section. The probe now records observed `Retry-After` values and counts 429 responses with a positive integer value. Record the exact commit SHA and whether the service was restarted between runs.

- Treat any `http_429_missing_or_invalid_count` above zero as a failed rate-limit evidence check requiring investigation. The probe records headers only for measurement; it does not change server behavior.
- Confirm overload rejection does not mutate order state by comparing authorized fixture state before/after in the lab.
- Do not interpret status 0/transport errors as an HTTP response.
- Do not claim recovery until the recovery run is compared with the baseline.
- Preserve raw JSON output only after checking it contains no credentials or sensitive data.

## 6. Acceptance gate

Day 19 is not fully accepted until real normal/overload/recovery reports exist, results and limitations are reviewed by the service owner and an independent reviewer, and the repository's evidence record links the artifacts. CI passing alone is not sufficient. Keep `monitor_only`, zero active enforcement rules, and release **NOT APPROVED**.
