"""Ciclo 07 — fronteiras de promoção (parecer Codex Sol: N-01, N-02, N-03).

Cada teste reencena a sonda do parecerista e exige que ela FALHE em reproduzir.
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

SCRIPT = Path(__file__).resolve().parent / "record_evaluation.py"


def contract_eval() -> dict:
    return {
        "contract_complete": True,
        "contract": {
            "benchmark": [
                {"id": "caso-1", "split": "holdout", "ground_truth_ref": "t#1"}
            ],
            "metrics": [{"name": "task_success", "direction": "maximize"}],
            "promotion_threshold": {"task_success": {"min_improvement": 0.1}},
        },
        "runs": [],
    }


def run_with(cases: list, baseline: list | None, directory: Path) -> dict:
    report = directory / "report.json"
    report.write_text('{"scorer": "probe"}', encoding="utf-8")
    run = {
        "run_id": "probe",
        "observed_at": "2026-08-19",
        "evidence_refs": ["e"],
        "case_results": cases,
        "baseline_metrics": (
            {"task_success": 0.0} if baseline is not None
            else {"nota": "sem baseline declarada"}
        ),
        "candidate_metrics": {
            "task_success": round(
                sum(1 for c in cases if c.get("success")) / len(cases), 4
            )
        },
        "verdict_source": {"kind": "deterministic_scorer", "source_ref": "s"},
        "scorer_report_ref": str(report),
        "scorer_report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    }
    if baseline is not None:
        run["baseline_case_results"] = baseline
    return run


def case(cid: str, success: bool) -> dict:
    return {
        "case_id": cid,
        "success": success,
        "oracle_evidence_ref": "o",
        "ground_truth_ref": "t#1",
    }


class TestN01PaddingRejected(unittest.TestCase):
    def record(self, run: dict, directory: Path):
        eval_path = directory / "eval.json"
        run_path = directory / "run.json"
        eval_path.write_text(json.dumps(contract_eval()))
        run_path.write_text(json.dumps(run))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--evaluation", str(eval_path),
             "--run-result", str(run_path)],
            capture_output=True, text=True, check=False,
        )
        return completed, json.loads(eval_path.read_text())

    def test_sonda_do_parecer_1_holdout_false_99_extras_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [case("caso-1", False)] + [
                case(f"estranho-{i}", True) for i in range(99)
            ]
            baseline = [{"case_id": c["case_id"], "success": False} for c in cases]
            completed, after = self.record(run_with(cases, baseline, root), root)
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertIn("N-01", completed.stderr)
            self.assertEqual(after.get("runs"), [])
            self.assertNotEqual(after.get("status"), "promotion_candidate")

    def test_duplicata_recusada(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [case("caso-1", True), case("caso-1", True)]
            completed, after = self.record(run_with(cases, None, root), root)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("duplicate", completed.stderr)
            self.assertEqual(after.get("runs"), [])

    def test_baseline_fora_do_conjunto_recusada(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [case("caso-1", True)]
            baseline = [{"case_id": "outro", "success": False}]
            completed, after = self.record(run_with(cases, baseline, root), root)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("same set", completed.stderr)

    def test_caminho_feliz_conjunto_exato_passa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [case("caso-1", True)]
            baseline = [{"case_id": "caso-1", "success": False}]
            completed, after = self.record(run_with(cases, baseline, root), root)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(len(after["runs"]), 1)


class TestN03Transactional(unittest.TestCase):
    def test_state_malformado_nao_escreve_nada(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eval_path = root / "eval.json"
            run_path = root / "run.json"
            state_path = root / "state.json"
            eval_path.write_text(json.dumps(contract_eval()))
            run_path.write_text(
                json.dumps(run_with([case("caso-1", True)],
                                    [{"case_id": "caso-1", "success": False}],
                                    root))
            )
            state_path.write_text("{ MALFORMADO")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--evaluation", str(eval_path),
                 "--run-result", str(run_path), "--state", str(state_path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("S-07b", completed.stderr)
            after = json.loads(eval_path.read_text())
            self.assertEqual(after.get("runs"), [])
            self.assertEqual(state_path.read_text(), "{ MALFORMADO")

    def test_scorer_report_obrigatorio_para_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = run_with([case("caso-1", True)], None, root)
            run.pop("scorer_report_ref")
            run.pop("scorer_report_sha256")
            eval_path = root / "eval.json"
            run_path = root / "run.json"
            eval_path.write_text(json.dumps(contract_eval()))
            run_path.write_text(json.dumps(run))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--evaluation", str(eval_path),
                 "--run-result", str(run_path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("S-02b", completed.stderr)


class TestS06bHardFail(unittest.TestCase):
    def test_content_path_ausente_recusa_compilacao(self) -> None:
        data = {"evidence_registry": [
            {"id": "fantasma", "kind": "document",
             "content_path": "nao-existe/arquivo.md", "source_ref": "x"}
        ]}
        with self.assertRaises(SystemExit) as ctx:
            build_universe.canonical_registry(data)
        self.assertIn("S-06b", str(ctx.exception))
        self.assertIn("fantasma", str(ctx.exception))

    def test_content_path_resolvido_contra_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "prova.md").write_text("conteudo real", encoding="utf-8")
            expected = hashlib.sha256(b"conteudo real").hexdigest()
            original = build_universe.EVIDENCE_ROOT
            build_universe.EVIDENCE_ROOT = root
            try:
                registry = build_universe.canonical_registry(
                    {"evidence_registry": [
                        {"id": "real", "kind": "document",
                         "content_path": "prova.md", "source_ref": "x"}
                    ]}
                )
            finally:
                build_universe.EVIDENCE_ROOT = original
            self.assertEqual(
                registry["real"]["identity_token"], f"sha256:{expected}"
            )
            self.assertEqual(
                registry["real"]["identity_strength"], "content_hash_computed"
            )


if __name__ == "__main__":
    unittest.main()
