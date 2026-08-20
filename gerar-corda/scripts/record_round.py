#!/usr/bin/env python3
"""Record a used peer round into a CORDA STATE (sanctioned mutator).

Achado de campo A-04 (primeiro assunto real, 2026-08-19): uma rodada foi
executada e gate-aprovada num universo implantado, mas nada a escreveu no
STATE — o BOOTSTRAP seguiu declarando o universo virgem e induzia qualquer
sessão de boa-fé a reexecutar a rodada como trabalho novo. Não existia script sancionado para
registrar uso de rodada; editar o STATE à mão é proibido. Este script fecha o
buraco: registro determinístico, validado, com recusa (rc=2) em duplicata,
orçamento estourado, data malformada ou veredito fora do vocabulário.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

GATE_RESULTS = {"pass", "pass_with_caveats", "fail", "escalate"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a used CORDA peer round.")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument(
        "--round",
        required=True,
        type=Path,
        dest="round_record",
        help="JSON com round_id, executed_at, topology, gate_result, "
        "deliverable_ref, trace_ref (opcionais: mast_ref, repair_cycles, "
        "caveats_ref, notes)",
    )
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_round(record: dict[str, Any]) -> list[str]:
    missing = [
        field
        for field in (
            "round_id",
            "executed_at",
            "topology",
            "gate_result",
            "deliverable_ref",
            "trace_ref",
        )
        if not record.get(field)
    ]
    if missing:
        raise ValueError(f"round record missing: {', '.join(missing)}")
    dates = record["executed_at"]
    if isinstance(dates, str):
        dates = [dates]
    if not isinstance(dates, list) or not dates:
        raise ValueError("executed_at must be an ISO date or a list of ISO dates")
    for item in dates:
        try:
            datetime.date.fromisoformat(str(item))
        except ValueError as exc:
            raise ValueError(f"executed_at invalid ISO date: {item!r} (S-05)") from exc
    if record["gate_result"] not in GATE_RESULTS:
        raise ValueError(
            f"gate_result must be one of {sorted(GATE_RESULTS)}, "
            f"got {record['gate_result']!r}"
        )
    repair = record.get("repair_cycles", 0)
    if not isinstance(repair, int) or isinstance(repair, bool) or repair < 0:
        raise ValueError("repair_cycles must be a non-negative integer")
    return [str(item) for item in dates]


def main() -> int:
    args = parse_args()
    try:
        state = load_object(args.state)
        record = load_object(args.round_record)
        dates = validate_round(record)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rounds = state.get("rounds")
    if not isinstance(rounds, dict):
        print("ERROR: STATE has no rounds section", file=sys.stderr)
        return 2
    used = rounds.get("peer_rounds_used")
    admitted = rounds.get("admitted_peer_rounds")
    free = rounds.get("max_without_evidence_delta")
    if any(
        not isinstance(value, int) or isinstance(value, bool)
        for value in (used, admitted, free)
    ):
        print("ERROR: rounds counters must be integers", file=sys.stderr)
        return 2

    history = rounds.setdefault("history", [])
    if not isinstance(history, list):
        print("ERROR: rounds.history must be a list", file=sys.stderr)
        return 2
    round_id = str(record["round_id"])
    if any(
        isinstance(item, dict) and item.get("round_id") == round_id
        for item in history
    ):
        print(f"ERROR: duplicate round_id: {round_id}", file=sys.stderr)
        return 2

    budget = admitted + free
    if used >= budget:
        print(
            f"ERROR: round budget exhausted ({used}/{budget}); admit an "
            "evidence_delta via record_evidence_delta.py before recording "
            "another round",
            file=sys.stderr,
        )
        return 2

    entry = {
        "round_id": round_id,
        "executed_at": dates,
        "topology": str(record["topology"]),
        "gate_result": record["gate_result"],
        "deliverable_ref": str(record["deliverable_ref"]),
        "trace_ref": str(record["trace_ref"]),
        "recorded_by": "record_round.py",
    }
    for optional in ("mast_ref", "caveats_ref", "notes"):
        if record.get(optional):
            entry[optional] = str(record[optional])
    if record.get("repair_cycles"):
        entry["repair_cycles"] = record["repair_cycles"]
    history.append(entry)
    rounds["peer_rounds_used"] = used + 1

    gate = state.setdefault("gate", {})
    if isinstance(gate, dict):
        gate["result"] = record["gate_result"]
        if record.get("caveats_ref"):
            gate["caveats_ref"] = str(record["caveats_ref"])

    state["status"] = f"rounds_used_{used + 1}"
    checkpoint = state.get("checkpoint")
    if isinstance(checkpoint, dict):
        checkpoint["updated_at"] = max(dates)
    state.setdefault("events", []).append(
        {
            "type": "round_recorded",
            "round_id": round_id,
            "observed_at": max(dates),
            "gate_result": record["gate_result"],
            "deliverable_ref": str(record["deliverable_ref"]),
            "by": "record_round.py",
        }
    )

    args.state.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Recorded round {round_id}: peer_rounds_used={used + 1}/{budget}")
    print(f"Updated: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
