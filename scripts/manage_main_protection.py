"""Check or create only the owner's approved API-Sentinel main protection."""

import argparse
import json
import re
import subprocess
from pathlib import Path

REPOSITORY = "madhab-tech-cyber/APIsenX"
REPO_PATH = f"repos/{REPOSITORY}"
PROTECTION_PATH = f"{REPO_PATH}/branches/main/protection"
SETTINGS = Path(__file__).resolve().parents[1] / "docs/main-protection-settings.json"
CHECK = {"context": "API Security and Quality Gates", "app_id": 15368}


class ProtectionError(Exception):
    pass


class ApiError(ProtectionError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"GitHub access failed (HTTP {status or 'unknown'}).")


def gh_request(method, path, payload=None):
    args = [
        "gh",
        "api",
        "--hostname",
        "github.com",
        "--include",
        "--method",
        method,
        path,
    ]
    if payload is not None:
        args.extend(["--input", "-"])
    result = subprocess.run(
        args,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout.replace("\r\n", "\n")
    match = re.search(r"^HTTP/\S+ (\d{3})", output, re.MULTILINE)
    status = int(match.group(1)) if match else None
    if result.returncode or status is None or status >= 400:
        # Do not echo credentials, headers, server body or arbitrary CLI stderr.
        raise ApiError(status)
    try:
        return json.loads(output.split("\n\n", 1)[1])
    except (IndexError, ValueError) as error:
        raise ProtectionError("GitHub returned an invalid JSON response.") from error


def enabled(value):
    return value.get("enabled") if isinstance(value, dict) else value


def protection_gaps(observed):
    gaps = []
    for field, expected in (
        ("enforce_admins", True),
        ("required_conversation_resolution", True),
        ("allow_force_pushes", False),
        ("allow_deletions", False),
    ):
        if enabled(observed.get(field)) is not expected:
            gaps.append(field)
    status = observed.get("required_status_checks") or {}
    if status.get("strict") is not True:
        gaps.append("up-to-date required status checks")
    if not any(
        item.get("context") == CHECK["context"]
        and item.get("app_id") == CHECK["app_id"]
        for item in status.get("checks", [])
    ):
        gaps.append("API check bound to GitHub Actions app 15368")
    reviews = observed.get("required_pull_request_reviews") or {}
    count = reviews.get("required_approving_review_count", 0)
    if type(count) is not int or count < 2:
        gaps.append("two independent approvals")
    gaps.extend(
        field
        for field in (
            "dismiss_stale_reviews",
            "require_code_owner_reviews",
            "require_last_push_approval",
        )
        if reviews.get(field) is not True
    )
    bypass = reviews.get("bypass_pull_request_allowances") or {}
    if any(bypass.get(kind) for kind in ("users", "teams", "apps")):
        gaps.append("empty review-bypass lists")
    return gaps


def configure(apply=False, request=None):
    request = request or gh_request
    try:
        observed = request("GET", PROTECTION_PATH)
    except ApiError as error:
        if error.status != 404:
            raise
        observed = None
    if observed is not None:
        gaps = protection_gaps(observed)
        if gaps:
            if apply:
                raise ProtectionError(
                    "Existing protection is not overwritten. Reconcile in owner UI: "
                    + ", ".join(gaps)
                )
            return {"verified": False, "gaps": gaps}
        return {"verified": True, "changed": False, "protection": observed}
    if not apply:
        return {"verified": False, "gaps": ["main has no legacy protection"]}

    repo = request("GET", REPO_PATH)
    if repo.get("full_name") != REPOSITORY or not repo.get("permissions", {}).get(
        "admin"
    ):
        raise ProtectionError("The authenticated repository owner/admin is required.")
    payload = json.loads(SETTINGS.read_text())
    if protection_gaps(payload):
        raise ProtectionError(
            "The approved settings file is incomplete; nothing submitted."
        )
    request("PUT", PROTECTION_PATH, payload)
    try:
        observed = request("GET", PROTECTION_PATH)
        branch = request("GET", f"{REPO_PATH}/branches/main")
    except ProtectionError as error:
        raise ProtectionError(
            "Protection was submitted but readback failed; inspect owner settings."
        ) from error
    gaps = protection_gaps(observed)
    if branch.get("protected") is not True:
        gaps.append("main protected flag")
    if gaps:
        raise ProtectionError("Submitted but verification failed: " + ", ".join(gaps))
    return {"verified": True, "changed": True, "protection": observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only check (default)")
    mode.add_argument("--apply", action="store_true", help="create approved main rule")
    options = parser.parse_args()
    try:
        result = configure(apply=options.apply)
    except (ProtectionError, OSError, subprocess.TimeoutExpired, ValueError) as error:
        if isinstance(error, ProtectionError):
            print(f"BLOCKED: {error}")
        else:
            print("BLOCKED: local CLI/configuration unavailable or timed out.")
        print(
            "Restore GitHub Administration access; "
            "never paste credential values in chat."
        )
        return 2
    print(json.dumps({"repository": REPOSITORY, "branch": "main", **result}, indent=2))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
