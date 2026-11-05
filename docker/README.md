# Containers and SBOM

Container configuration for the APIsenX lab (Member 6 scope), plus the
project software bill of materials.

## Images

| File | Contents | Run |
|---|---|---|
| `Dockerfile.mock-api` | Mock API (Member 5), uvicorn on 8000 | via compose |
| `Dockerfile.analytics` | Analytics service (Member 4), uvicorn on 8001 | via compose |
| `Dockerfile.dashboard` | Dashboard (Member 6), Vite build served by nginx | via compose |
| `Dockerfile.collector` | Collector crate (Member 3) build/test image | `docker build -f docker/Dockerfile.collector .` |

The collector is a tested library, not a deployed daemon, so it has a
build/test image rather than a compose service: its test suite runs during
the image build, and the runtime stage carries the `baseline` example.
The eBPF sensor targets a Linux host and is not containerized here.

## Compose

```sh
export APISENTINEL_INGEST_TOKEN=<lab-only value>
export APISENTINEL_HMAC_KEY=<lab-only value>
docker compose up --build
```

Services publish on host loopback only: mock API `127.0.0.1:8000`,
analytics `127.0.0.1:8001`, dashboard `127.0.0.1:3000`. No secret is baked
into any image; analytics fails to start if the ingest token or HMAC key
is unset.

## SBOM

`sbom.cdx.json` (repo root) is a CycloneDX 1.5 bill of materials covering
all three ecosystems — PyPI (requirements files), crates.io
(`collector/Cargo.lock`) and npm (`dashboard/package-lock.json`).
Regenerate after any lockfile change:

```sh
python scripts/generate_sbom.py
```
