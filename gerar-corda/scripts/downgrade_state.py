#!/usr/bin/env python3
"""Downgrade sancionado de STATE corda-state/1.5 para corda-state/1.4.

Rollback do eixo de estado do ADR-001. Regra de conservacao: os
acceptance_records NUNCA sao descartados — sao exportados para um arquivo de
arquivo morto ao lado do STATE e a exportacao fica registrada em events.
Downgrade sem exportacao seria perda de registro atribuivel e e recusado.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True, help="STATE.json 1.5 a rebaixar")
    parser.add_argument("--date", required=True, help="data do downgrade AAAA-MM-DD")
    parser.add_argument("--owner", required=True, help="quem autoriza o downgrade")
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"REFUSED: {message}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    if not args.owner.strip():
        return fail("owner e obrigatorio")
    try:
        datetime.date.fromisoformat(args.date.strip())
    except ValueError:
        return fail(f"data malformada: {args.date!r} (exigido AAAA-MM-DD; S-05)")
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"STATE ilegivel: {exc}")
    version = str(state.get("schema_version", ""))
    if version == "corda-state/1.4":
        print("STATE is already corda-state/1.4; nothing to do")
        return 0
    if version != "corda-state/1.5":
        return fail(f"schema_version inesperado: {version}")
    decision = state.get("decision")
    if not isinstance(decision, dict):
        return fail("STATE sem bloco decision")
    # Atomicidade (caveat do gate c04): validar TUDO que sera mutado antes de
    # escrever qualquer arquivo — events malformado nao pode crashar depois do
    # arquivo morto ja gravado.
    events = state.get("events")
    if events is not None and not isinstance(events, list):
        return fail("STATE.events corrompido (nao e lista); nada foi escrito")
    records = decision.get("acceptance_records", [])
    archive_path = args.state.with_name(args.state.stem + "-acceptance-archive.json")
    if records:
        # Conservacao em ciclos repetidos: o arquivo morto e append-only —
        # exports anteriores nunca sao sobrescritos (achado da lente de
        # compatibilidade no ciclo 03).
        previous_exports: list = []
        if archive_path.is_file():
            try:
                existing = json.loads(archive_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return fail(
                    f"arquivo morto existente ilegivel ({archive_path}): {exc}; "
                    "downgrade recusado para nao arriscar perda de registro"
                )
            if isinstance(existing, dict) and "exports" in existing:
                previous_exports = existing.get("exports", [])
            elif isinstance(existing, dict):
                previous_exports = [existing]
            else:
                return fail(
                    f"arquivo morto existente com formato inesperado ({archive_path})"
                )
        previous_exports.append(
            {
                "exported_at": args.date.strip(),
                "exported_by": args.owner.strip(),
                "from_state": str(args.state),
                "universe_id": state.get("universe_id"),
                "acceptance_records": records,
            }
        )
        archive = {
            "note": (
                "Exportado por downgrade_state.py (append-only): registros de "
                "aceite preservados fora do STATE 1.4; nao constituem estado "
                "corrente"
            ),
            "exports": previous_exports,
        }
        archive_path.write_text(
            json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    decision.pop("acceptance_records", None)
    state["schema_version"] = "corda-state/1.4"
    state.setdefault("events", []).append(
        {
            "at": args.date.strip(),
            "what": (
                "downgrade corda-state/1.5 -> 1.4; "
                + (
                    f"{len(records)} acceptance_record(s) exportado(s) para "
                    f"{archive_path.name}"
                    if records
                    else "nenhum acceptance_record a exportar"
                )
            ),
            "by": args.owner.strip(),
        }
    )
    args.state.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Downgraded: {args.state}")
    if records:
        print(f"Acceptance archive: {archive_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
