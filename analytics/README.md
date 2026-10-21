# Python analytics and detection

Member 4 delivery, implemented by `madhab-tech-cyber` while the assigned teammate
is unavailable. [Days 1–10 evidence](../docs/member4-days01-10-evidence.md) and
[service/contract boundaries](../docs/member4-ingestion-contract.md) distinguish
implemented local capabilities from unaccepted integration. Monitor-only always.

[Days 11–20](../docs/member4-days11-20-evidence.md) adds BFLA rules, a labelled
engineering corpus, signed dry-run recommendations, bounded replay/flow state
and minimal volatile audit records. Human Day 14/15 review/feedback remain
pending. [LAB-REC-1](../docs/member4-recommendation-contract.md) is not an active
enforcement contract or an already connected live principal resolver.

## Run on Kali (repository root)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Generate per-session credentials in memory; never echo them or commit them.
export APISENTINEL_INGEST_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export APISENTINEL_HMAC_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export APISENTINEL_SOURCE_ID=lab_application
export APISENTINEL_KEY_VERSION=lab-v1

python -m uvicorn analytics.app:create_app --factory --host 127.0.0.1 --port 8001 --no-access-log
```

Open [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health). Only liveness is
public. `/docs`, `/inventory` and `/alerts` do not expose evidence. The separate
mock API remains on port 8000. Never bind this lab credential setup to `0.0.0.0`
or expose it through a tunnel; shared use requires reviewed TLS and identity.
Shell command substitution above generates runtime values locally; no actual
credential is included in this README.

To send one synthetic event, leave the server running, open another terminal
and set its runtime credentials through your approved local environment (do not
paste credentials into chat). With matching variables and activated venv:

```bash
python -m analytics.demo
```

The demo prints only health/acknowledgement and minimized policy outcomes, not
the Bearer credential, raw event or object identities. Raw targets exist only
in memory until masking. Restart clears all summaries and idempotency state.

## Tests and checks

```bash
python -m pip install ruff==0.17.1 bandit==1.8.6 pip-audit==2.10.1 detect-secrets==1.5.0
python -m unittest discover -s tests -p 'test_analytics*.py' -v
python -m ruff check analytics tests scripts/check_analytics_secrets.py
python -m bandit -r analytics -q
python scripts/check_analytics_secrets.py
python -m pip_audit -r requirements.txt
python -m analytics.schemas
python -m analytics.evaluate
python -m analytics.review_demo
```

The Days 1–10 baseline had no BFLA or signed recommendations; the Days 11–20
extension supplies those as local dry-run capabilities. No database, protected
dashboard read APIs or active blocking is shipped. Evaluation reuses Member 5's fixture
policy but cannot run on collector events lacking authenticated actor/object
context. M3's structural batch format is accepted under stricter limits, but its
mTLS-only client is not yet authenticated by this lab Bearer endpoint.

`python -m analytics.review_demo` needs no runtime secrets: it generates them
in memory and injects explicitly synthetic context into an in-process service.
It demonstrates owner/BOLA/BFLA/shadow outcomes, verifies signatures and checks
masked audit output without printing private values. This is an automated demo,
not a completed human review.

The normal Uvicorn service leaves `/v1/recommendations` disabled. Configuring
separate `APISENTINEL_DECISION_TOKEN` and `APISENTINEL_DECISION_KEY` enables its
authentication boundary, but **without a trusted internal resolver it returns
503**, never a guessed decision. Read the contract before integrating. Use one
loopback worker with per-session keys; volatile replay state is not safe for
distributed/active enforcement. Do not set public test credentials or expose it
with `--host 0.0.0.0`.

