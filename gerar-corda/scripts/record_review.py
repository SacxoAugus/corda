#!/usr/bin/env python3
"""Record semantic and visual review without conflating mechanical validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STATUSES = ("pass", "pass_with_caveats", "fail", "not_performed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record CORDA review status.")
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--date", required=True, help="Review date in YYYY-MM-DD")
    parser.add_argument("--semantic", choices=STATUSES)
    parser.add_argument("--visual", choices=STATUSES)
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--repair-iterations", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.semantic and not args.visual and args.repair_iterations is None:
        print("ERROR: choose semantic, visual or repair iterations", file=sys.stderr)
        return 2
    if not args.date or len(args.date) != 10:
        print("ERROR: --date must use YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        data = json.loads(args.verification.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for key, status in (
        ("semantic_review", args.semantic),
        ("visual_review", args.visual),
    ):
        if status:
            review = data.setdefault(key, {})
            review["status"] = status
            review["inspected_by"] = args.reviewer
            review["inspected_at"] = args.date
            review["notes"] = list(args.note)

    if args.repair_iterations is not None:
        policy = data.setdefault("repair_policy", {})
        maximum = int(policy.get("max_iterations", 2))
        if args.repair_iterations < 0 or args.repair_iterations > maximum:
            print(
                f"ERROR: repair iterations must be between 0 and {maximum}",
                file=sys.stderr,
            )
            return 2
        policy["iterations_used"] = args.repair_iterations
        if args.repair_iterations == maximum:
            policy["status"] = "exhausted_escalate"

    args.verification.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated: {args.verification}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
