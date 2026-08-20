"""Ciclo 07 — achados de campo A-01 (veto órfão), §6.7 (MAST auto) e A-02 (carimbo)."""

from __future__ import annotations

import unittest

import build_universe
from test_build_universe import dynamic_narrative


def unsatisfied_ids(manifest: dict) -> set[str]:
    preflight = build_universe.assess_applicability(manifest)
    return {item["primitive"] for item in preflight["requirements_unsatisfied"]}


class TestA01VetoOrfao(unittest.TestCase):
    def test_veto_sem_dono_entra_em_requirements_unsatisfied(self) -> None:
        manifest = dynamic_narrative()
        manifest["gate"]["adversaries"] = [
            {"id": "dano-x", "power": "veto",
             "owner": "a nomear — pendente de decisão"}
        ]
        self.assertIn("veto_owner", unsatisfied_ids(manifest))

    def test_veto_com_dono_assertado_nao_bloqueia(self) -> None:
        # N-07 (c08): dono nomeado exige tambem a assercao estruturada
        # owner_named:true — inferencia lexical foi removida.
        manifest = dynamic_narrative()
        manifest["gate"]["adversaries"] = [
            {"id": "dano-x", "power": "veto",
             "owner": "Fulana (autoridade Y)", "owner_named": True}
        ]
        self.assertNotIn("veto_owner", unsatisfied_ids(manifest))

    def test_escalonamento_sem_dono_nao_e_veto_morto(self) -> None:
        manifest = dynamic_narrative()
        manifest["gate"]["adversaries"] = [
            {"id": "dano-x", "power": "escalonamento", "owner": ""}
        ]
        self.assertNotIn("veto_owner", unsatisfied_ids(manifest))


class TestMastAutoRequired(unittest.TestCase):
    def test_topologia_multiagente_exige_mast_sem_declaracao(self) -> None:
        result = build_universe.build_mast_validation(
            {"runtime": {"execution_topology": "multi_agent"}}
        )
        self.assertTrue(result["selected"])
        self.assertTrue(result["auto_required"])
        self.assertEqual(result["status"], "not_performed")

    def test_sequencial_continua_opcional(self) -> None:
        result = build_universe.build_mast_validation(
            {"runtime": {"execution_topology": "single_llm_sequential"}}
        )
        self.assertFalse(result["auto_required"])
        self.assertEqual(result["status"], "not_selected")


class TestA02CompilerStamp(unittest.TestCase):
    def test_verification_carrega_carimbo_do_compilador(self) -> None:
        stamp = build_universe.compiler_stamp()
        self.assertEqual(stamp["version"], build_universe.COMPILER_VERSION)
        self.assertRegex(stamp["build_universe_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(stamp["derive_cast_sha256"], r"^[0-9a-f]{64}$")
        manifest = dynamic_narrative()
        preflight = build_universe.assess_applicability(manifest)
        normalized = build_universe.normalize(manifest, preflight)
        verification = build_universe.build_verification(
            normalized, png_written=False, runtime_emitted=True
        )
        self.assertEqual(
            verification["compiler"]["version"], build_universe.COMPILER_VERSION
        )


if __name__ == "__main__":
    unittest.main()
