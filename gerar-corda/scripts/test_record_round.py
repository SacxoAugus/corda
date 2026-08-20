"""Tests for record_round.py — achado de campo A-04 (STATE nunca soube da rodada)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "record_round.py"


def base_state() -> dict:
    return {
        "schema_version": "corda-state/1.5",
        "universe_id": "u-teste",
        "status": "initialized",
        "checkpoint": {"observed_at": "2026-08-18", "updated_at": "2026-08-18"},
        "rounds": {
            "policy": "conditional_rounds",
            "peer_rounds_used": 0,
            "admitted_peer_rounds": 0,
            "max_without_evidence_delta": 1,
            "evidence_deltas": [],
        },
        "gate": {"result": None, "caveats": [], "blocked_by": []},
        "events": [],
    }


def base_round() -> dict:
    return {
        "round_id": "rodada-01",
        "executed_at": ["2026-08-18", "2026-08-19"],
        "topology": "multi_agent",
        "gate_result": "pass_with_caveats",
        "deliverable_ref": "rodada-01/00-PACOTE-DECISAO-FOUNDER.md",
        "trace_ref": "rodada-01/rodada-01-trace.json",
        "mast_ref": "rodada-01/mast-assessment-rodada-01.json",
        "caveats_ref": "rodada-01/gate-veredito-v2.md",
        "repair_cycles": 1,
    }


class TestRecordRound(unittest.TestCase):
    def run_script(self, state: dict, record: dict):
        tmp = Path(tempfile.mkdtemp(prefix="corda-round-"))
        state_path = tmp / "state.json"
        round_path = tmp / "round.json"
        state_path.write_text(json.dumps(state, ensure_ascii=False))
        round_path.write_text(json.dumps(record, ensure_ascii=False))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--state", str(state_path),
             "--round", str(round_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        after = json.loads(state_path.read_text())
        return completed, after

    def test_records_round_and_updates_state(self):
        completed, after = self.run_script(base_state(), base_round())
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(after["rounds"]["peer_rounds_used"], 1)
        self.assertEqual(after["rounds"]["history"][0]["round_id"], "rodada-01")
        self.assertEqual(after["gate"]["result"], "pass_with_caveats")
        self.assertEqual(after["status"], "rounds_used_1")
        self.assertEqual(after["checkpoint"]["updated_at"], "2026-08-19")
        self.assertEqual(after["events"][-1]["type"], "round_recorded")

    def test_refuses_duplicate_round_id(self):
        state = base_state()
        completed, after = self.run_script(state, base_round())
        self.assertEqual(completed.returncode, 0)
        # segunda gravação do MESMO id sobre o estado já mutado
        completed2, after2 = self.run_script(after, base_round())
        self.assertEqual(completed2.returncode, 2)
        self.assertIn("duplicate round_id", completed2.stderr)
        self.assertEqual(after2["rounds"]["peer_rounds_used"], 1)

    def test_refuses_when_budget_exhausted(self):
        state = base_state()
        _, after = self.run_script(state, base_round())
        record2 = dict(base_round(), round_id="rodada-02")
        completed2, after2 = self.run_script(after, record2)
        self.assertEqual(completed2.returncode, 2)
        self.assertIn("budget exhausted", completed2.stderr)
        self.assertIn("record_evidence_delta", completed2.stderr)
        self.assertEqual(after2["rounds"]["peer_rounds_used"], 1)

    def test_budget_extends_with_admitted_delta(self):
        state = base_state()
        state["rounds"]["admitted_peer_rounds"] = 1
        _, after = self.run_script(state, base_round())
        record2 = dict(base_round(), round_id="rodada-02")
        completed2, after2 = self.run_script(after, record2)
        self.assertEqual(completed2.returncode, 0, completed2.stderr)
        self.assertEqual(after2["rounds"]["peer_rounds_used"], 2)

    def test_refuses_malformed_date_and_bad_verdict(self):
        bad_date = dict(base_round(), executed_at=["2026-13-99"])
        completed, after = self.run_script(base_state(), bad_date)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("S-05", completed.stderr)
        self.assertEqual(after["rounds"]["peer_rounds_used"], 0)
        bad_verdict = dict(base_round(), gate_result="approved")
        completed2, _ = self.run_script(base_state(), bad_verdict)
        self.assertEqual(completed2.returncode, 2)
        self.assertIn("gate_result", completed2.stderr)


if __name__ == "__main__":
    unittest.main()
