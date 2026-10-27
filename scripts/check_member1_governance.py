"""Check checkpoint bookkeeping, not human approval or live GitHub settings."""

import argparse
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
    require(isinstance(value, str), "timestamp must be text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp must include a timezone")


def evidence_reference(value):
    require(isinstance(value, str), "evidence reference must be text")
    parsed = urlsplit(value)
    require(
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith("/madhab-tech-cyber/APIsenX/"),
        "evidence must link to this repository over HTTPS",
    )


def actor(value):
    require(
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value),
        "evidence actor must be an exact GitHub login",
    )


def validate_register(record):
    require(record["schema_version"] == 1, "unknown register version")
    timestamp(record["recorded_at"])
    actor(record["document_author"])
    require(re.fullmatch(r"[0-9a-f]{40}", record["baseline"]), "pin a full SHA")
    require(record["integration_status"] in {"blocked", "accepted"}, "bad status")
    require(record["release_status"] in {"held", "approved"}, "bad release status")
    require(type(record["active_rule_count"]) is int, "rule count must be an int")
    require(record["active_rule_count"] >= 0, "negative rule count")
    for issue in (record["followup_issue"], *record.get("related_issues", [])):
        require(type(issue) is int and issue > 0, "invalid follow-up issue")
    if "tracker_observations" in record:
        observation = record["tracker_observations"]
        timestamp(observation["observed_at"])
        require(
            all(
                state in {"open", "closed"} for state in observation["states"].values()
            ),
            "invalid observed tracker state",
        )
    for review in record.get("component_reviews", []):
        actor(review["author"])
        actor(review["by"])
        require(
            type(review["pull_request"]) is int and review["pull_request"] > 0,
            "component review requires a PR number",
        )
        require(review["state"] == "APPROVED", "record actual component approval only")
        require(
            review["by"].casefold() != review["author"].casefold(),
            "component author cannot independently approve their own PR",
        )
        require(
            re.fullmatch(r"[0-9a-f]{40}", review["revision"]),
            "component approval must pin its own revision",
        )
        timestamp(review["submitted_at"])
        evidence_reference(review["reference"])
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
        candidate = item.get("candidate_revision", record["baseline"])
        require(re.fullmatch(r"[0-9a-f]{40}", candidate), "pin checkpoint candidate")
        tracking = item.get("tracking_issues", [item["issue"]])
        require(
            isinstance(tracking, list)
            and item["issue"] in tracking
            and all(type(issue) is int and issue > 0 for issue in tracking)
            and len(set(tracking)) == len(tracking),
            "invalid checkpoint tracker links",
        )
        require(item["status"] in {"pending", "complete"}, "unknown human status")
        complete = item["status"] == "complete"
        meeting = item["meeting"]
        if meeting is not None:
            timestamp(meeting["at"])
            require(bool(meeting["attendees"]), "meeting attendees required")
            require(all(meeting["attendees"]), "empty meeting attendee")
            evidence_reference(meeting["reference"])
            require(
                meeting.get("revision") == candidate,
                "meeting must identify the checkpoint candidate",
            )
        if complete and day in {14, 30}:
            require(meeting is not None, "actual meeting required")
        for field in ("reviewer_comments", "owner_responses", "independent_signoffs"):
            entries = item[field]
            require(isinstance(entries, list), "evidence collection must be a list")
            if complete:
                require(bool(entries), f"completion requires {field}")
            for entry in entries:
                actor(entry["by"])
                evidence_reference(entry["reference"])
                if field == "independent_signoffs":
                    require(
                        entry["by"].casefold() != record["document_author"].casefold(),
                        "author cannot independently approve their own work",
                    )
                    require(
                        re.fullmatch(r"[0-9a-f]{40}", entry["revision"]),
                        "sign-off must pin a full revision",
                    )
                    require(
                        entry["revision"] == candidate,
                        "sign-off belongs to another checkpoint candidate",
                    )
                    timestamp(entry["submitted_at"])
        if complete and day == 15:
            require(by_day[14]["status"] == "complete", "Day 14 feedback is required")
        if complete and day == 30:
            require(
                all(by_day[prior]["status"] == "complete" for prior in (14, 15)),
                "Day 30 requires completed earlier human checkpoints",
            )
            require(
                record["integration_status"] == "accepted", "integrated demo blocked"
            )
            evidence_reference(item["run_manifest"])
    protection = record.get("protection_observation")
    if protection is not None:
        timestamp(protection["observed_at"])
        require(type(protection["main_protected"]) is bool, "invalid protection flag")
        require(type(protection["settings_verified"]) is bool, "invalid settings flag")
        evidence_reference(protection["reference"])
        if protection["settings_verified"]:
            require(protection["main_protected"], "verified protection must be enabled")
            evidence_reference(protection["readback_reference"])
            evidence_reference(protection["merge_gate_reference"])
    if record["integration_status"] == "accepted":
        require(
            bool(record.get("integration_evidence")), "integration evidence required"
        )
        for reference in record["integration_evidence"]:
            evidence_reference(reference)
    if record["release_status"] == "approved":
        require(
            all(item["status"] == "complete" for item in checkpoints),
            "pending human checkpoints hold release",
        )
        require(
            protection is not None and protection["settings_verified"],
            "unverified main protection holds release",
        )


def completion_gaps(record):
    """Conservative bookkeeping gate; never authenticates remote human evidence."""
    gaps = [
        f"Day {item['day']} human checkpoint"
        for item in record["checkpoints"]
        if item["status"] != "complete"
    ]
    if record["integration_status"] != "accepted":
        gaps.append("integrated acceptance")
    if not record.get("protection_observation", {}).get("settings_verified"):
        gaps.append("verified main protection and real PR gate evidence")
    if record["release_status"] != "approved":
        gaps.append("authorized release decision")
    return gaps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete", action="store_true", help="exit 2 for outstanding gates"
    )
    options = parser.parse_args()
    try:
        record = json.loads(REGISTER.read_text())
        validate_register(record)
    except (KeyError, TypeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: Member 1 checkpoint bookkeeping is internally consistent.")
    print("This does not verify human evidence, live issue states or protection.")
    gaps = completion_gaps(record)
    for gap in gaps:
        print(f"PENDING: {gap}")
    return 2 if options.require_complete and gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
