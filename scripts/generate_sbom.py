#!/usr/bin/env python3
"""Generate the project CycloneDX SBOM (sbom.cdx.json) from lockfiles.

Sources (all committed, so the SBOM is reproducible in CI):
  - requirements.txt + requirements-dev.txt  (PyPI, pinned versions)
  - collector/Cargo.lock                     (crates.io)
  - dashboard/package-lock.json              (npm)

Standard library only. Usage:
  python scripts/generate_sbom.py [--output PATH]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pypi_components(path, scope):
    components = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)", line)
        if not match:
            continue
        name, version = match.groups()
        normalized = re.sub(r"[-_]+", "-", name).lower()
        components.append({
            "type": "library",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{normalized}@{version}",
            "scope": scope,
            "properties": [{"name": "ecosystem", "value": "pypi"}],
        })
    return components


def cargo_components(path):
    text = path.read_text()
    components = []
    for block in text.split("[[package]]")[1:]:
        name = re.search(r'^name = "(.+)"', block, re.M)
        version = re.search(r'^version = "(.+)"', block, re.M)
        if not name or not version:
            continue
        if name.group(1) == "api-sentinel-collector":
            continue  # the workspace crate itself, not a dependency
        components.append({
            "type": "library",
            "name": name.group(1),
            "version": version.group(1),
            "purl": f"pkg:cargo/{name.group(1)}@{version.group(1)}",
            "properties": [{"name": "ecosystem", "value": "cargo"}],
        })
    return components


def npm_components(path):
    data = json.loads(path.read_text())
    components = []
    for key, entry in data.get("packages", {}).items():
        if not key or "node_modules/" not in key:
            continue
        name = key.split("node_modules/")[-1]
        version = entry.get("version")
        if not version:
            continue
        purl_name = name.replace("@", "%40", 1) if name.startswith("@") else name
        component = {
            "type": "library",
            "name": name,
            "version": version,
            "purl": f"pkg:npm/{purl_name}@{version}",
            "properties": [{"name": "ecosystem", "value": "npm"}],
        }
        license_id = entry.get("license")
        if isinstance(license_id, str) and " " not in license_id:
            component["licenses"] = [{"license": {"id": license_id}}]
        components.append(component)
    return components


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / "sbom.cdx.json"))
    args = parser.parse_args()

    components = []
    components += pypi_components(ROOT / "requirements.txt", "required")
    components += pypi_components(ROOT / "requirements-dev.txt", "optional")
    components += cargo_components(ROOT / "collector" / "Cargo.lock")
    lockfile = ROOT / "dashboard" / "package-lock.json"
    if lockfile.exists():
        components += npm_components(lockfile)
    else:
        print("warning: dashboard/package-lock.json missing; npm omitted",
              file=sys.stderr)

    seen = set()
    unique = []
    for component in components:
        if component["purl"] not in seen:
            seen.add(component["purl"])
            unique.append(component)
    unique.sort(key=lambda c: c["purl"])

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [{"name": "scripts/generate_sbom.py", "version": "1.0"}],
            "component": {
                "type": "application",
                "name": "APIsenX (API-Sentinel lab)",
                "version": "0.1.0",
            },
        },
        "components": unique,
    }
    Path(args.output).write_text(json.dumps(sbom, indent=2) + "\n")
    counts = {}
    for component in unique:
        eco = component["properties"][0]["value"]
        counts[eco] = counts.get(eco, 0) + 1
    print(f"wrote {args.output}: {len(unique)} components {counts}")


if __name__ == "__main__":
    main()
