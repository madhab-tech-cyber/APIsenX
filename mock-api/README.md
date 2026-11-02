# Mock e-commerce API

Owner: Member 5 — Mock API and OpenAPI Engineer.

This service is an **authorised, loopback-only security lab**. Use only the
synthetic fixture identities and data in this repository. Never point it at a
third-party or production system.

## Quick start

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --app-dir mock-api --host 127.0.0.1 --port 8000 --no-access-log
```

Open the interactive runtime schema at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The reviewed,
version-controlled contract is [`docs/openapi.yaml`](../docs/openapi.yaml).

## Reproducible attacks and reset

Follow [the Member 5 Day 28 lab runbook](../docs/day28-member5-lab-runbook.md)
for setup, synthetic credentials, expected owner/BOLA/BFLA outcomes, nonce
handling, OpenAPI checks, and clean reset steps.

The API loads order fixtures once per process. Order updates, token revocation,
and PATCH replay nonces are process-local; stop and restart the server to reset
them. No database or durable persistence is provided. Demo tokens have a
15-minute default lifetime and are not production credentials.

## Security validation

```powershell
python -m unittest discover -s tests -v
python -m ruff check mock-api src tests
python -m bandit -r mock-api src -q
python -m pip_audit -r requirements.txt
```

The repository's Mock API Security Tests workflow runs these checks plus the
isolated integration and bounded load checks. A local run or a green subset
does not satisfy independent review, durable audit, integrated acceptance, or
the project release gate.
