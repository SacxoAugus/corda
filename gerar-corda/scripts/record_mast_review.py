#!/usr/bin/env python3
"""Record evidenced MAST checks in a CORDA verification artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"not_observed", "observed", "uncertain", "not_applicable"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a CORDA MAST review.")
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--assessment", required=True, type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--date", required=True, help="Review date in YYYY-MM-DD")
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    args = parse_args()
    if len(args.date) != 10:
        print("ERROR: --date must use YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        verification = load_object(args.verification)
        assessment = load_object(args.assessment)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    mast = verification.get("mast_validation")
    if not isinstance(mast, dict) or not mast.get("applicable"):
        print("ERROR: MAST profile is not applicable in this verification", file=sys.stderr)
        return 2
    checks = mast.get("checks")
    if not isinstance(checks, list):
        print("ERROR: mast_validation.checks must be a list", file=sys.stderr)
        return 2
    by_id = {
        str(item.get("id")): item for item in checks if isinstance(item, dict)
    }
    unknown = sorted(set(assessment) - set(by_id))
    if unknown:
        print(f"ERROR: unknown MAST ids: {', '.join(unknown)}", file=sys.stderr)
        return 2

    for mode_id, value in assessment.items():
        if not isinstance(value, dict):
            print(f"ERROR: assessment {mode_id} must be an object", file=sys.stderr)
            return 2
        status = value.get("status")
        if status not in STATUSES:
            print(
                f"ERROR: assessment {mode_id}.status must be one of "
                f"{', '.join(sorted(STATUSES))}",
                file=sys.stderr,
            )
            return 2
        if status in {"observed", "not_observed"} and not value.get("evidence_ref"):
            print(
                f"ERROR: assessment {mode_id} requires evidence_ref",
                file=sys.stderr,
            )
            return 2
        by_id[mode_id]["status"] = status
        by_id[mode_id]["evidence_ref"] = value.get("evidence_ref")
        by_id[mode_id]["note"] = value.get("note")

    statuses = {item.get("status") for item in checks if isinstance(item, dict)}
    mast["status"] = (
        "fail"
        if "observed" in statuses
        else "pass_with_caveats"
        if statuses & {"uncertain", "not_assessed"}
        else "pass"
    )
    mast["inspected_by"] = args.reviewer
    mast["inspected_at"] = args.date
    verification["mast_validation"] = mast
    args.verification.write_text(
        json.dumps(verification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated: {args.verification}")
    print(f"MAST status: {mast['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
