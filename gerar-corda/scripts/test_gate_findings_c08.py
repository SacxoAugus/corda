"""Ciclo 08 — sondas do gate isolado cross-model (Codex Sol): N-05..N-08.

Cada teste re-encena a sonda do gate e exige que ela FALHE em reproduzir.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build_universe
from test_build_universe import dynamic_narrative

SCRIPT = Path(__file__).resolve().parent / "record_evaluation.py"


def case(cid, ok: bool, truth: str = "th") -> dict:
    return {"case_id": cid, "success": ok,
            "oracle_evidence_ref": "o", "ground_truth_ref": truth}


class RecordHarness(unittest.TestCase):
    def record(self, benchmark: list, cases: list, baseline, metric: float,
               state: dict | None = None):
        tmp = Path(tempfile.mkdtemp(prefix="corda-c08-"))
        report = tmp / "rep.json"
        report.write_text('{"scorer": "probe"}', encoding="utf-8")
        evaluation = {
            "contract_complete": True,
            "contract": {
                "benchmark": benchmark,
                "metrics": [{"name": "task_success", "direction": "maximize"}],
                "promotion_threshold": {"task_success": {"min_improvement": 0.1}},
            },
            "runs": [],
        }
        run = {
            "run_id": "probe", "observed_at": "2026-08-20",
            "evidence_refs": ["e"], "case_results": cases,
            "baseline_metrics": {"task_success": 0.0}
            if baseline is not None else {"nota": "sem baseline"},
            "candidate_metrics": {"task_success": metric},
            "verdict_source": {"kind": "deterministic_scorer", "source_ref": "s"},
            "scorer_report_ref": str(report),
            "scorer_report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
        }
        if baseline is not None:
            run["baseline_case_results"] = baseline
        (tmp / "e.json").write_text(json.dumps(evaluation))
        (tmp / "r.json").write_text(json.dumps(run))
        cmd = [sys.executable, str(SCRIPT), "--evaluation", str(tmp / "e.json"),
               "--run-result", str(tmp / "r.json")]
        if state is not None:
            (tmp / "st.json").write_text(json.dumps(state))
            cmd += ["--state", str(tmp / "st.json")]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        after = json.loads((tmp / "e.json").read_text())
        state_after = (
            json.loads((tmp / "st.json").read_text()) if state is not None else None
        )
        return completed, after, state_after


class TestN05FalsyIds(RecordHarness):
    BENCH = [{"id": "expected", "split": "holdout", "ground_truth_ref": "th"}]

    def test_sonda_do_gate_99_ids_vazios(self) -> None:
        cases = [case("expected", False)] + [case("", True) for _ in range(99)]
        completed, after, _ = self.record(
            self.BENCH, cases, [{"case_id": "expected", "success": False}], 0.99
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("N-05", completed.stderr)
        self.assertEqual(after.get("runs"), [])

    def test_variantes_falsy_none_zero_whitespace(self) -> None:
        for bad in (None, 0, "   ", [], {}):
            cases = [case("expected", False), case(bad, True)]
            completed, after, _ = self.record(
                self.BENCH, cases,
                [{"case_id": "expected", "success": False}], 0.5
            )
            self.assertEqual(completed.returncode, 2, f"{bad!r}: {completed.stderr}")
            self.assertIn("N-05", completed.stderr)
            self.assertEqual(after.get("runs"), [])


class TestN06StructuralState(RecordHarness):
    BENCH = [{"id": "c1", "split": "holdout", "ground_truth_ref": "th"}]

    def test_events_com_tipo_errado_nao_escreve_nada(self) -> None:
        completed, after, state_after = self.record(
            self.BENCH, [case("c1", True)],
            [{"case_id": "c1", "success": False}], 1.0,
            state={"schema_version": "corda-state/1.5",
                   "evaluation": {}, "events": {}},
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("N-06", completed.stderr)
        self.assertEqual(after.get("runs"), [])
        self.assertEqual(state_after, {"schema_version": "corda-state/1.5",
                                       "evaluation": {}, "events": {}})

    def test_evaluation_string_nao_escreve_nada(self) -> None:
        completed, after, _ = self.record(
            self.BENCH, [case("c1", True)],
            [{"case_id": "c1", "success": False}], 1.0,
            state={"evaluation": "corrompido", "events": []},
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("N-06", completed.stderr)
        self.assertEqual(after.get("runs"), [])


class TestN08DuplicateBenchmark(RecordHarness):
    def test_sonda_do_gate_ids_duplicados_no_contrato(self) -> None:
        bench = [
            {"id": "same", "split": "validation", "ground_truth_ref": "tv"},
            {"id": "same", "split": "holdout", "ground_truth_ref": "th"},
        ]
        completed, after, _ = self.record(
            bench, [case("same", True)],
            [{"case_id": "same", "success": False}], 1.0
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("N-08", completed.stderr)
        self.assertEqual(after.get("runs"), [])

    def test_benchmark_id_vazio_recusado(self) -> None:
        bench = [{"id": "  ", "split": "holdout", "ground_truth_ref": "th"}]
        completed, after, _ = self.record(
            bench, [case("x", True)], None, 1.0
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("N-08", completed.stderr)


class TestN07StructuredOwner(unittest.TestCase):
    def unsatisfied(self, adversary: dict) -> bool:
        manifest = dynamic_narrative()
        manifest["gate"]["adversaries"] = [adversary]
        preflight = build_universe.assess_applicability(manifest)
        return any(
            item["primitive"] == "veto_owner"
            for item in preflight["requirements_unsatisfied"]
        )

    def test_placeholders_da_sonda_do_gate_agora_bloqueiam(self) -> None:
        for owner in ("pendente", "por nomear", "unknown", "-", "a nomear"):
            self.assertTrue(
                self.unsatisfied(
                    {"id": "dano-x", "power": "veto", "owner": owner}
                ),
                owner,
            )

    def test_owner_sem_assercao_estruturada_bloqueia(self) -> None:
        self.assertTrue(
            self.unsatisfied(
                {"id": "dano-x", "power": "veto", "owner": "Fulana (papel Y)"}
            )
        )

    def test_owner_com_assercao_satisfaz(self) -> None:
        self.assertFalse(
            self.unsatisfied(
                {"id": "dano-x", "power": "veto",
                 "owner": "Fulana (papel Y)", "owner_named": True}
            )
        )

    def test_assercao_sem_owner_nao_satisfaz(self) -> None:
        self.assertTrue(
            self.unsatisfied(
                {"id": "dano-x", "power": "veto", "owner": "",
                 "owner_named": True}
            )
        )


if __name__ == "__main__":
    unittest.main()
