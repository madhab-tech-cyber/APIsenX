"""Check checkpoint bookkeeping, not human approval or live GitHub settings."""

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/member1-checkpoints.json"
TRACKERS = {14: 14, 15: 21, 30: 23}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp must include a timezone")


def evidence_reference(value):
    parsed = urlsplit(value)
    require(
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith("/madhab-tech-cyber/APIsenX/"),
        "evidence must link to this repository over HTTPS",
    )


def validate_register(record):
    require(record["schema_version"] == 1, "unknown register version")
    timestamp(record["recorded_at"])
    require(re.fullmatch(r"[0-9a-f]{40}", record["baseline"]), "pin a full SHA")
    require(record["integration_status"] in {"blocked", "accepted"}, "bad status")
    require(record["release_status"] in {"held", "approved"}, "bad release status")
    require(type(record["active_rule_count"]) is int, "rule count must be an int")
    require(record["active_rule_count"] >= 0, "negative rule count")
    if record["integration_status"] != "accepted":
        require(record["release_status"] == "held", "blocked integration holds release")
        require(
            record["active_rule_count"] == 0, "blocked integration has no active rules"
        )
    checkpoints = record["checkpoints"]
    require(len(checkpoints) == 3, "exactly three checkpoint records required")
    by_day = {item["day"]: item for item in checkpoints}
    require(set(by_day) == set(TRACKERS), "duplicate/missing checkpoint day")
    for day, item in by_day.items():
        require(item["issue"] == TRACKERS[day], "wrong checkpoint tracker")
        require(item["status"] in {"pending", "complete"}, "unknown human status")
        complete = item["status"] == "complete"
        meeting = item["meeting"]
        if meeting is not None:
            timestamp(meeting["at"])
            require(bool(meeting["attendees"]), "meeting attendees required")
            require(all(meeting["attendees"]), "empty meeting attendee")
            evidence_reference(meeting["reference"])
        if complete and day in {14, 30}:
            require(meeting is not None, "actual meeting required")
        for field in ("reviewer_comments", "owner_responses", "independent_signoffs"):
            entries = item[field]
            require(isinstance(entries, list), "evidence collection must be a list")
            if complete:
                require(bool(entries), f"completion requires {field}")
            for entry in entries:
                require(bool(entry["by"]), "evidence actor required")
                evidence_reference(entry["reference"])
                if field == "independent_signoffs":
                    require(
                        entry["by"] != record["document_author"],
                        "author cannot independently approve their own work",
                    )
                    require(
                        re.fullmatch(r"[0-9a-f]{40}", entry["revision"]),
                        "sign-off must pin a full revision",
                    )
        if complete and day == 15:
            require(by_day[14]["status"] == "complete", "Day 14 feedback is required")
        if complete and day == 30:
            require(
                record["integration_status"] == "accepted", "integrated demo blocked"
            )
            evidence_reference(item["run_manifest"])


def main():
    try:
        record = json.loads(REGISTER.read_text())
        validate_register(record)
    except (KeyError, TypeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: Member 1 checkpoint bookkeeping is internally consistent.")
    print("This does not verify human evidence, live issue states or protection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
