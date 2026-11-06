# Member 5 — Day 29 clean and reproducible lab reset

**Objective:** Reset the Mock API's volatile test state and prove that every run
starts from the same reviewed synthetic dataset.

## Reset boundary

The Mock API stores order updates, revoked-token state, PATCH nonces, rate-limit
buckets and subject semaphores in process memory. The supported reset is to stop
the local API process and start a fresh process. The reset does not delete,
rewrite or regenerate checked-in fixtures. It does not clear logs, backups or
any durable store; this Mock API has no durable order or audit store.

Use only the loopback lab from the Day 28 runbook. Stop only the API process you
started for this lab; do not kill unrelated processes.

## Repeatable verification

From the repository root, in PowerShell:

```powershell
python scripts/verify_day29_lab_reset.py
python -m unittest discover -s tests -p 'test_day29_lab_reset.py' -v
```

The verifier:
- Checks Git blob SHA-1 identifiers for orders, users, sharing grants and authorization cases.
- Checks the expected synthetic record counts and confirms the sharing-grant fixture is empty.
- Dirties volatile state in an isolated parent interpreter, starts a separate fresh Python process, and verifies original order state plus empty revoked-token, nonce, rate-limit and subject-semaphore state.
- Starts the actual Mock API on an OS-selected loopback port, applies a synthetic admin PATCH, terminates only that child process, and starts a fresh API process on the same port.
- Verifies the fresh HTTP process restores the original order fixture and accepts the same nonce again, proving the process-local replay cache was reset.
- Removes optional Sentinel endpoint/credential settings from the harness child environment, disables Uvicorn access logging, bypasses proxies/redirects, and never contacts an external target.
- Never edits checked-in fixture files.

The reviewed digests live in `tests/fixtures/day29_lab_baseline.json`. A fixture
change intentionally fails the verifier until the change is reviewed and the
baseline is updated in the same PR. Do not update expected hashes merely to make
a failing check green.

## Evidence and limits

The new process-level checks are pending exact-head CI. After they pass, record the exact tested SHA and Mock API Security workflow URL; do not reuse earlier baseline CI as evidence for these new checks.

The verifier demonstrates fixture integrity, process-local reset, HTTP restart and nonce-cache reset only;
it does not prove durable audit deletion, backup/restore, database reset,
multi-worker state reset or production data sanitization.

AP-1.0 remains monitor-only, active enforcement rules remain zero, and release
approval remains false. Day 30 remains a separate authorised synthetic attack
demonstration and human explanation task.
