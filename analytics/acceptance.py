"""Validate M4 evidence bookkeeping; never manufacture approval or enable rules."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from analytics.decisions import rules_digest
from analytics.detection import RULE_VERSION
from analytics.normalization import RouteNormalizer
from analytics.package import check_freeze

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/member4-review-checkpoints.json"
GATES = {
    "independent_accuracy",
    "trusted_context",
    "shared_transport",
    "durable_audit",
    "dashboard_handoff",
    "performance_route_failure_rollback",
    "independent_final_review",
}
DAYS = (14, 15, 22, 28, 30)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference(value):
    require(isinstance(value, str), "evidence reference required")
    url = urlsplit(value)
    require(
        url.scheme == "https"
        and url.netloc == "github.com"
        and url.path.startswith("/madhab-tech-cyber/APIsenX/"),
        "evidence must reference this repository over HTTPS",
    )


def login(value):
    require(
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value),
        "exact GitHub login required",
    )


def timestamp(value):
    require(isinstance(value, str), "timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.utcoffset() is not None, "timezone-aware timestamp required")


def entries(values):
    require(isinstance(values, list) and len(values) <= 100, "bounded evidence list")
    for item in values:
        login(item["by"])
        reference(item["reference"])


def reviews(values, record):
    entries(values)
    for item in values:
        require(
            item["by"].casefold() != record["implementation_owner"].casefold(),
            "implementer cannot independently approve own work",
        )
        require(item["decision"] == "APPROVED", "actual approval decision required")
        require(
            item["revision"] == candidate_sha(record)
            and item["rules_digest"] == record["candidate_rules_digest"],
            "review belongs to a different candidate",
        )
        timestamp(item["submitted_at"])


def candidate_sha(record):
    value = record["candidate_commit"]
    reference(value)
    match = re.fullmatch(
        r"https://github\.com/madhab-tech-cyber/APIsenX/commit/([0-9a-f]{40})",
        value,
    )
    require(match is not None, "full candidate commit reference required")
    return match.group(1)


def validate_record(record):
    require(record["schema_version"] == 2, "unknown M4 evidence version")
    login(record["implementation_owner"])
    candidate_sha(record)
    require(record["calendar_days_claimed"] is False, "day labels are not attendance")
    require(record["mode"] == "monitor_only", "monitor-only required")
    require(
        type(record["active_rules"]) is int and record["active_rules"] == 0,
        "zero active rules required",
    )
    require(record["release_approved"] is False, "checker cannot authorize release")
    require(record["rule_version"] == RULE_VERSION, "stale rule version")
    require(
        record["candidate_rules_digest"] == "sha256:" + rules_digest(),
        "stale rule source",
    )
    # Key affects private tokens, not the public contract version.
    contract = RouteNormalizer.from_file(
        ROOT / "docs/openapi.yaml", b"synthetic-check-only-key-material!", "check-v1"
    ).contract_version
    require(record["contract_version"] == contract, "stale contract")
    require(set(record["acceptance_gates"]) == GATES, "missing/unknown acceptance gate")
    for gate in record["acceptance_gates"].values():
        require(gate["status"] in {"pending", "verified"}, "unknown gate status")
        require(isinstance(gate["evidence"], list), "evidence list required")
        for link in gate["evidence"]:
            reference(link)
        reviews(gate["independent_reviews"], record)
        if gate["status"] == "verified":
            require(
                bool(gate["evidence"]) and bool(gate["independent_reviews"]),
                "verified gate requires evidence and independent approval",
            )
    for day in DAYS:
        item = record[f"day{day}"]
        require(
            item["status"]
            in {
                "pending_human_demonstration",
                "pending_actual_feedback",
                "pending_independent_regression_review",
                "pending_independent_rule_schema_review",
                "pending_human_final_demonstration",
                "complete",
            },
            "unknown human checkpoint status",
        )
        reviews(item["independent_signoffs"], record)
        if item["status"] != "complete":
            continue
        require(
            bool(item["independent_signoffs"]), "independent human sign-off required"
        )
        if day in (14, 30):
            timestamp(item["meeting_date"])
            require(
                item["demonstrated_revision"] == candidate_sha(record),
                "demonstration belongs to another candidate",
            )
            require(
                isinstance(item["actual_attendees"], list)
                and bool(item["actual_attendees"])
                and all(
                    isinstance(x, str) and x.strip() for x in item["actual_attendees"]
                ),
                "actual attendees required",
            )
            require(bool(item["review_comments"]), "actual review comments required")
            entries(item["review_comments"])
        if day == 15:
            require(record["day14"]["status"] == "complete", "Day 14 feedback missing")
            for name in ("actual_feedback", "owner_dispositions"):
                require(bool(item[name]), "actual feedback and dispositions required")
                entries(item[name])
        if day == 30:
            require(
                all(record[f"day{x}"]["status"] == "complete" for x in DAYS[:-1]),
                "earlier human checkpoints incomplete",
            )
            require(
                all(
                    gate["status"] == "verified"
                    for gate in record["acceptance_gates"].values()
                ),
                "integrated acceptance incomplete",
            )
    require(
        record["day29"]["status"] == "source_candidate_only"
        and record["day29"]["release_approved"] is False,
        "source candidate only",
    )


def pending(record):
    return [
        f"Day {day}" for day in DAYS if record[f"day{day}"]["status"] != "complete"
    ] + [
        name
        for name, gate in record["acceptance_gates"].items()
        if gate["status"] != "verified"
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-accepted", action="store_true")
    args = parser.parse_args()
    try:
        record = json.loads(REGISTER.read_text())
        validate_record(record)
        check_freeze()
    except (ValueError, TypeError, KeyError, OSError):
        print("FAIL: M4 evidence/source record invalid; acceptance remains blocked")
        return 1
    print("PASS: frozen M4 evidence bookkeeping; not independent approval")
    for gap in pending(record):
        print("PENDING:", gap)
    print("monitor_only; zero active rules; release NOT APPROVED")
    return 2 if args.require_accepted and pending(record) else 0


if __name__ == "__main__":
    raise SystemExit(main())
