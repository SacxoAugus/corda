#!/usr/bin/env python3
"""Admit a peer round only when evidence snapshots differ materially."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DELTA_TYPES = {
    "new_source",
    "new_observation",
    "new_tool_result",
    "new_test_result",
    "new_counterexample",
    "targeted_verification",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically record a CORDA evidence delta."
    )
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--delta-type", required=True, choices=sorted(DELTA_TYPES))
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--source-ref", required=True)
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def tokens(snapshot: dict[str, Any]) -> set[str]:
    raw = snapshot.get("canonical_tokens")
    if not isinstance(raw, list):
        raise ValueError("evidence snapshot requires canonical_tokens[]")
    return {str(item) for item in raw if str(item).strip()}


def entry_identities(snapshot: dict[str, Any]) -> dict[str, str]:
    entries = snapshot.get("entries")
    if not isinstance(entries, list):
        return {}
    return {
        str(item["id"]): str(item["identity_token"])
        for item in entries
        if isinstance(item, dict) and item.get("id") and item.get("identity_token")
    }


def main() -> int:
    args = parse_args()
    try:
        state = load_object(args.state)
        before = load_object(args.before)
        after = load_object(args.after)
        before_tokens = tokens(before)
        after_tokens = tokens(after)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    added = sorted(after_tokens - before_tokens)
    before_entries = entry_identities(before)
    after_entries = entry_identities(after)
    changed = sorted(
        evidence_id
        for evidence_id in before_entries.keys() & after_entries.keys()
        if before_entries[evidence_id] != after_entries[evidence_id]
    )
    if not added and not changed:
        print(
            "REJECTED: no new canonical token or changed content identity; "
            "alias/persona/model changes do not admit a round",
            file=sys.stderr,
        )
        return 3

    rounds = state.get("rounds")
    if not isinstance(rounds, dict):
        print("ERROR: STATE.rounds must be an object", file=sys.stderr)
        return 2
    event = {
        "delta_type": args.delta_type,
        "observed_at": args.observed_at,
        "source_ref": args.source_ref,
        "before_snapshot_sha256": before.get("snapshot_sha256"),
        "after_snapshot_sha256": after.get("snapshot_sha256"),
        "added_canonical_tokens": added,
        "changed_evidence_ids": changed,
        "admission": "accepted_deterministically",
    }
    deltas = rounds.setdefault("evidence_deltas", [])
    if not isinstance(deltas, list):
        print("ERROR: STATE.rounds.evidence_deltas must be a list", file=sys.stderr)
        return 2
    deltas.append(event)
    rounds["admitted_peer_rounds"] = int(rounds.get("admitted_peer_rounds", 0)) + 1
    rounds["current_evidence_snapshot_hash"] = after.get("snapshot_sha256")
    state.setdefault("events", []).append(
        {
            "type": "peer_round_admitted",
            "observed_at": args.observed_at,
            "source_ref": args.source_ref,
            "evidence_delta_index": len(deltas) - 1,
        }
    )
    args.state.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Accepted evidence delta: {args.delta_type}")
    print(f"Added tokens: {len(added)}")
    print(f"Changed evidence ids: {len(changed)}")
    print(f"Updated: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
