#!/usr/bin/env python3
"""Registrar um aceite humano e efetuar a unica transicao valida de decision.state.

Invariante P4 (ADR-001): decision.state so muda com um acceptance_record
persistido e atribuivel {decided_at, owner, outcome, statement, source_ref}.
Este script e o mutador sancionado; edicao manual de STATE nao constitui aceite.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

VALID_OUTCOMES = {"accepted", "rejected", "adjusted", "escalated"}
OUTCOME_TO_STATE = {
    "accepted": "accepted",
    "rejected": "rejected",
    "adjusted": "adjusted",
    "escalated": "escalated",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True, help="STATE.json a mutar")
    parser.add_argument("--outcome", required=True, choices=sorted(VALID_OUTCOMES))
    parser.add_argument("--owner", required=True, help="quem decide (atribuivel)")
    parser.add_argument("--date", required=True, help="decided_at AAAA-MM-DD")
    parser.add_argument("--statement", required=True, help="texto da decisao")
    parser.add_argument("--source-ref", required=True, help="registro auditavel da decisao")
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"REFUSED: {message}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    for name in ("owner", "date", "statement", "source_ref"):
        if not str(getattr(args, name.replace("-", "_"))).strip():
            return fail(f"campo obrigatorio vazio: {name}")
    # Correcao S-05 (auditoria Codex Sol): registro completo exige data ISO
    # valida, nao apenas texto de 10 caracteres.
    try:
        datetime.date.fromisoformat(args.date.strip())
    except ValueError:
        return fail(f"decided_at malformado: {args.date!r} (exigido AAAA-MM-DD)")
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"STATE ilegivel: {exc}")
    decision = state.get("decision")
    if not isinstance(decision, dict):
        return fail("STATE sem bloco decision")
    declared_owner = str(decision.get("owner") or "").strip()
    if declared_owner and declared_owner != args.owner.strip():
        return fail(
            "owner divergente: o STATE declara "
            f"'{declared_owner}'; a transicao exige o mesmo owner ou nova "
            "autoridade registrada no manifesto"
        )
    record = {
        "decided_at": args.date.strip(),
        "owner": args.owner.strip(),
        "outcome": args.outcome,
        "statement": args.statement.strip(),
        "source_ref": args.source_ref.strip(),
    }
    records = decision.setdefault("acceptance_records", [])
    if not isinstance(records, list):
        return fail("decision.acceptance_records corrompido (nao e lista)")
    records.append(record)
    decision["state"] = OUTCOME_TO_STATE[args.outcome]
    state.setdefault("events", []).append(
        {
            "at": record["decided_at"],
            "what": f"decision.state -> {decision['state']} via acceptance_record",
            "by": record["owner"],
            "source_ref": record["source_ref"],
        }
    )
    args.state.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Recorded acceptance: {args.outcome}")
    print(f"decision.state: {decision['state']}")
    print(f"Updated: {args.state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
