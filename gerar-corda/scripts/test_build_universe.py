#!/usr/bin/env python3
"""Discoverable regression tests for the CORDA compiler."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build_universe
import derive_cast
import record_evaluation
import render_corda


def characteristic(value: bool | None, source_ref: str = "test#characteristics") -> dict:
    return {"value": value, "source_ref": source_ref}


def observer(
    observer_id: str,
    model: str,
    evidence: list[str],
    context: str,
) -> dict:
    return {
        "id": observer_id,
        "label": observer_id,
        "role": "test",
        "base_model": model,
        "evidence_scope": {
            "shared": [],
            "private": evidence,
            "tools": [],
            "prior": [],
        },
        "context_fingerprint": context,
        "prompt_family": observer_id,
        "run_id": f"{observer_id}-run",
        "blind_to": ["synthesis"],
        "loop": {
            "question": "Qual é a conclusão sustentada?",
            "last_checked": "2026-07-26",
        },
        "source_ref": f"test#{observer_id}",
    }


def evaluation_contract() -> dict:
    return {
        "baseline": "single-pass-neutral",
        "task": {
            "id": "decision-test",
            "description": "Escolher a decisão sustentada pela fixture.",
            "expected_output_contract": ["decision", "evidence_refs"],
            "oracle": {
                "kind": "deterministic",
                "source_ref": "fixture-oracle.json",
                "scoring_procedure": "exact match da decisão",
            },
        },
        "benchmark": [
            {
                "id": "fixture-a",
                "input_ref": "fixture-a-input.json",
                "ground_truth_ref": "fixture-a-truth.json",
                "split": "development",
            },
            {
                "id": "fixture-holdout",
                "input_ref": "fixture-holdout-input.json",
                "ground_truth_ref": "fixture-holdout-truth.json",
                "split": "holdout",
            },
        ],
        "metrics": [
            {
                "name": "accuracy",
                "direction": "maximize",
                "scorer": "exact-match-v1",
            },
            {
                "name": "token_cost",
                "direction": "minimize",
                "scorer": "runtime-counter-v1",
            },
        ],
        "cost_budget": {"tokens": 10000},
        "promotion_threshold": {
            "accuracy": {
                "min_improvement": 0.01,
                "comparison": "absolute",
            },
            "token_cost": {
                "min_improvement": 0.0,
                "comparison": "relative",
            },
        },
        "status": "compiled_unevaluated",
    }


def dynamic_narrative() -> dict:
    return {
        "title": "Sistema narrativo",
        "source": {
            "kind": "narrative",
            "description": "Dois componentes decidem sob prazo e estado mutável.",
        },
        "system_characteristics": {
            name: characteristic(True) for name in build_universe.CHARACTERISTICS
        },
        "boundary": {
            "bulk": "sistema de teste",
            "human_owner": "owner",
            "decision": "autorizar próximo passo",
            "time_horizon": "uma semana",
            "source_ref": "test#boundary",
        },
        "runtime": {
            "memory": {
                "mutable_state": "STATE.json",
                "source_ref": "test#state",
            }
        },
        "evidence_registry": [
            {
                "id": "source-a",
                "kind": "document",
                "content": "evidence A",
                "claim_ids": ["claim-a"],
                "source_ref": "test#source-a",
            },
            {
                "id": "source-b",
                "kind": "document",
                "content": "evidence B",
                "claim_ids": ["claim-b"],
                "source_ref": "test#source-b",
            },
            {
                "id": "gate-source",
                "kind": "test_result",
                "content": "gate evidence",
                "claim_ids": ["claim-gate"],
                "source_ref": "test#gate-source",
            },
        ],
        "integrator": {
            "id": "integrator",
            "label": "Integração",
            "role": "integrar",
            "source_ref": "test#integrator",
        },
        "modes": [
            observer("a", "model-a", ["source-a"], "context-a"),
            observer("b", "model-b", ["source-b"], "context-b"),
        ],
        "strings": [
            {
                "from": "a",
                "to": "synthesis",
                "label": "emissão a",
                "state": "active",
                "lead_time_days": 1,
                "source_ref": "test#edge-a",
            },
            {
                "from": "b",
                "to": "synthesis",
                "label": "emissão b",
                "state": "active",
                "lead_time_days": 1,
                "source_ref": "test#edge-b",
            },
        ],
        "synthesis": {
            "label": "Síntese",
            "operator": "conflitos",
            "source_ref": "test#synthesis",
        },
        "gate": {
            "label": "Gate",
            "tests": ["evidência"],
            "executor": {
                "id": "gate",
                "base_model": "gate-model",
                "evidence_scope": {
                    "shared": [],
                    "private": ["gate-source"],
                    "tools": ["test"],
                    "prior": [],
                },
                "context_fingerprint": "gate-context",
                "prompt_family": "blind",
                "run_id": "gate-run",
                "blind_to": ["intended_conclusion"],
            },
        },
        "independence_attestations": [
            {
                "modes": ["a", "b"],
                "status": "verified",
                "basis": "fontes e execuções isoladas",
                "verification_method": "hash_audit",
                "verified_by": "test-auditor",
                "verified_at": "2026-07-26",
                "source_ref": "test#attestation",
            }
        ],
        "evaluation_contract": evaluation_contract(),
    }


def static_document() -> dict:
    return {
        "title": "Documento estático",
        "source": {"kind": "document", "path": "documento.md"},
        "system_characteristics": {
            key: characteristic(False, "documento.md#applicability")
            for key in build_universe.CHARACTERISTICS
        },
    }


def static_faq() -> dict:
    modes = [
        observer("writer", "model-a", ["faq"], "faq-writer"),
        observer("reviewer", "model-b", ["faq"], "faq-reviewer"),
    ]
    for mode in modes:
        mode["loop"].pop("last_checked")
    return {
        "title": "FAQ estático",
        "source": {"kind": "document", "path": "faq.md"},
        "boundary": {
            "bulk": "redação de FAQ",
            "human_owner": "editor",
            "decision": "aprovar o texto",
            "time_horizon": "sem prazo",
            "source_ref": "faq.md#brief",
        },
        "integrator": {
            "id": "integrator",
            "label": "Editor",
            "role": "integrar texto",
            "source_ref": "faq.md#editor",
        },
        "modes": modes,
        "strings": [
            {
                "from": "writer",
                "to": "synthesis",
                "label": "rascunho",
                "state": "closed",
                "source_ref": "faq.md#flow",
            }
        ],
        "synthesis": {
            "label": "Texto final",
            "operator": "revisão editorial",
            "source_ref": "faq.md#output",
        },
        "gate": {"label": "Revisão", "tests": ["ortografia"]},
        "evidence_registry": [
            {
                "id": "faq",
                "kind": "document",
                "content": "Perguntas e respostas.",
                "source_ref": "faq.md",
            }
        ],
    }


def attach_scorer_report(run: dict, directory: Path) -> dict:
    """S-02b: relatorio content-addressed do scorer e obrigatorio para
    deterministic_scorer; fixture cria um real e vincula por sha256."""
    report = directory / "score-report.json"
    report.write_text('{"scorer": "fixture", "cases": 2}', encoding="utf-8")
    run["scorer_report_ref"] = str(report)
    run["scorer_report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    return run


def passing_run_result() -> dict:
    return {
        "run_id": "eval-1",
        "observed_at": "2026-07-26",
        "evidence_refs": ["fixture-oracle.json", "score-log.json"],
        "verdict_source": {
            "kind": "deterministic_scorer",
            "source_ref": "score-log.json",
        },
        "case_results": [
            {
                "case_id": "fixture-a",
                "ground_truth_ref": "fixture-a-truth.json",
                "oracle_evidence_ref": "fixture-a-score.json",
            },
            {
                "case_id": "fixture-holdout",
                "ground_truth_ref": "fixture-holdout-truth.json",
                "oracle_evidence_ref": "fixture-holdout-score.json",
            },
        ],
        "baseline_metrics": {"accuracy": 0.80, "token_cost": 7000},
        "candidate_metrics": {"accuracy": 0.83, "token_cost": 6500},
    }


class TestApplicability(unittest.TestCase):
    def test_narrative_without_graph_compiles_runtime(self) -> None:
        manifest = dynamic_narrative()
        render_corda.validate_manifest(manifest, require_topology=False)
        preflight = build_universe.assess_applicability(manifest)
        self.assertEqual(preflight["result"], build_universe.RUNTIME_RESULT)
        self.assertEqual(preflight["contradictions"], [])

    def test_time_horizon_sem_prazo_does_not_create_temporal_dynamics(self) -> None:
        preflight = build_universe.assess_applicability(static_faq())
        self.assertNotEqual(preflight["result"], build_universe.RUNTIME_RESULT)
        self.assertIsNone(
            preflight["characteristics"]["temporal_dynamics"]["structural_value"]
        )

    def test_explicit_positive_without_structure_is_contradictory(self) -> None:
        manifest = static_faq()
        manifest["system_characteristics"] = {
            "temporal_dynamics": characteristic(True, "faq.md#sem-prazo")
        }
        preflight = build_universe.assess_applicability(manifest)
        self.assertEqual(
            preflight["characteristics"]["temporal_dynamics"]["consistency"],
            "contradictory",
        )
        self.assertIn("temporal_dynamics", preflight["contradictions"])
        requirement = next(
            item
            for item in preflight["requirements_assessment"]
            if item["primitive"] == "temporal_dynamics"
        )
        self.assertEqual(requirement["status"], "contradictory")
        self.assertIn(requirement, preflight["requirements_unsatisfied"])

    def test_not_applicable_requires_negative_provenance(self) -> None:
        manifest = static_document()
        self.assertEqual(
            build_universe.assess_applicability(manifest)["result"],
            build_universe.NOT_APPLICABLE_RESULT,
        )
        for item in manifest["system_characteristics"].values():
            item.pop("source_ref")
        self.assertEqual(
            build_universe.assess_applicability(manifest)["result"],
            build_universe.INSUFFICIENT_RESULT,
        )

    def test_explicit_false_conflicting_with_structure_cannot_abort(self) -> None:
        manifest = dynamic_narrative()
        manifest["system_characteristics"]["interacting_components"] = characteristic(
            False
        )
        preflight = build_universe.assess_applicability(manifest)
        self.assertNotEqual(preflight["result"], build_universe.NOT_APPLICABLE_RESULT)
        self.assertIn("interacting_components", preflight["contradictions"])


class TestEvidenceAndIndependence(unittest.TestCase):
    def test_same_evidence_different_model_is_correlated(self) -> None:
        manifest = dynamic_narrative()
        manifest["modes"][1]["evidence_scope"]["private"] = ["source-a"]
        manifest["independence_attestations"] = []
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "correlated")
        self.assertFalse(pair["same_model"])

    def test_aliases_with_same_content_hash_are_correlated(self) -> None:
        manifest = dynamic_narrative()
        manifest["evidence_registry"].append(
            {
                "id": "source-a-alias",
                "kind": "document",
                "content": "evidence A",
                "source_ref": "test#alias",
            }
        )
        manifest["modes"][1]["evidence_scope"]["private"] = ["source-a-alias"]
        manifest["independence_attestations"] = []
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "correlated")

    def test_paraphrases_without_claim_id_are_not_merged(self) -> None:
        manifest = dynamic_narrative()
        manifest["evidence_registry"][0].update(
            {"content": "A receita aumentou.", "claim_ids": []}
        )
        manifest["evidence_registry"][1].update(
            {"content": "Houve crescimento de receita.", "claim_ids": []}
        )
        manifest["independence_attestations"] = []
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "independent_candidate")

    def test_legacy_scope_is_fail_safe(self) -> None:
        manifest = dynamic_narrative()
        for mode in manifest["modes"]:
            evidence = mode.pop("evidence_scope")["private"]
            mode["evidence_access"] = evidence
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "weak")
        self.assertTrue(pair["legacy_unscoped"])
        self.assertEqual(
            build_universe.assess_evidence_topology(manifest)["classification"],
            "legacy_unscoped",
        )

    def test_prior_blocks_corroboration(self) -> None:
        manifest = dynamic_narrative()
        manifest["modes"][0]["evidence_scope"]["prior"] = ["model-weights"]
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "weak")
        self.assertTrue(pair["prior_dependency"])

    def test_attestation_requires_external_verification_metadata(self) -> None:
        manifest = dynamic_narrative()
        manifest["independence_attestations"][0].pop("verification_method")
        pair = build_universe.assess_independence(manifest)["mode_pairs"][0]
        self.assertEqual(pair["classification"], "independent_candidate")
        self.assertFalse(pair["attestation_valid"])

    def test_direct_compare_revalidates_every_attestation_field(self) -> None:
        manifest = dynamic_narrative()
        first, second = manifest["modes"]
        valid = manifest["independence_attestations"][0]
        invalid_variants = []
        for field in (
            "modes",
            "status",
            "verification_method",
            "verified_by",
            "verified_at",
            "source_ref",
        ):
            candidate = copy.deepcopy(valid)
            if field == "modes":
                candidate[field] = ["a", "other"]
            elif field == "status":
                candidate[field] = "claimed"
            elif field == "verification_method":
                candidate[field] = "model_self_report"
            else:
                candidate[field] = ""
            invalid_variants.append(candidate)

        for candidate in invalid_variants:
            with self.subTest(attestation=candidate):
                pair = build_universe.compare_observers(
                    first,
                    second,
                    attestation=candidate,
                    registry=build_universe.canonical_registry(manifest),
                )
                self.assertEqual(
                    pair["classification"], "independent_candidate"
                )
                self.assertFalse(pair["attestation_valid"])
                self.assertIsNone(pair["attestation_source"])

    def test_verified_attestation_and_hashes_allow_corroboration(self) -> None:
        pair = build_universe.assess_independence(dynamic_narrative())[
            "mode_pairs"
        ][0]
        self.assertEqual(pair["classification"], "corroborating")
        self.assertTrue(pair["identities_verified"])
        self.assertTrue(pair["attestation_valid"])

    def test_declared_hash_must_match_inline_content(self) -> None:
        manifest = dynamic_narrative()
        manifest["evidence_registry"][0]["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            render_corda.ManifestError,
            "does not match normalized inline content",
        ):
            render_corda.validate_manifest(manifest, require_topology=False)


class TestEvaluation(unittest.TestCase):
    def test_contract_requires_task_ground_truth_and_holdout(self) -> None:
        assessment = build_universe.evaluation_contract_assessment(
            evaluation_contract()
        )
        self.assertTrue(assessment["contract_complete"])
        contract = evaluation_contract()
        contract["benchmark"] = [
            item for item in contract["benchmark"] if item["split"] != "holdout"
        ]
        self.assertFalse(
            build_universe.evaluation_contract_assessment(contract)[
                "contract_complete"
            ]
        )

    def test_thresholds_are_mechanically_scored(self) -> None:
        passing = record_evaluation.score_thresholds(
            evaluation_contract(), passing_run_result()
        )
        self.assertEqual(passing["status"], "pass")
        failing_run = passing_run_result()
        failing_run["candidate_metrics"] = {
            "accuracy": 0.79,
            "token_cost": 8000,
        }
        failing = record_evaluation.score_thresholds(
            evaluation_contract(), failing_run
        )
        self.assertEqual(failing["status"], "fail")

    def test_record_evaluation_creates_candidate_not_promotion(self) -> None:
        manifest = dynamic_narrative()
        preflight = build_universe.assess_applicability(manifest)
        normalized = build_universe.normalize(manifest, preflight)
        evaluation = build_universe.build_evaluation(
            normalized, runtime_emitted=True
        )
        with tempfile.TemporaryDirectory(prefix="corda-evaluation-") as tmp:
            root = Path(tmp)
            evaluation_path = root / "evaluation.json"
            run_path = root / "run.json"
            evaluation_path.write_text(
                json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            run_path.write_text(
                json.dumps(
                    attach_scorer_report(passing_run_result(), root),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(record_evaluation.__file__)),
                    "--evaluation",
                    str(evaluation_path),
                    "--run-result",
                    str(run_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            recorded = json.loads(evaluation_path.read_text(encoding="utf-8"))
            self.assertEqual(recorded["status"], "promotion_candidate")
            self.assertEqual(
                recorded["promotion"]["status"], "awaiting_human_acceptance"
            )
            self.assertIsNone(recorded["promotion"]["accepted_by"])


class TestRuntimeInvariants(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = dynamic_narrative()
        self.preflight = build_universe.assess_applicability(self.manifest)
        self.normalized = build_universe.normalize(
            self.manifest, self.preflight
        )

    def test_normalized_schema_and_round_policy(self) -> None:
        self.assertEqual(self.normalized["schema_version"], "corda-universe/1.4")
        self.assertEqual(
            self.normalized["evidence_topology"]["classification"], "disjoint"
        )
        self.assertTrue(
            self.normalized["round_admission"]["evidence_delta_required"]
        )

    def test_overlay_isolation_is_structural_and_lexical(self) -> None:
        isolation = build_universe.build_overlay_isolation(self.normalized)
        self.assertEqual(isolation["status"], "pass")
        self.assertFalse(
            isolation["construction"]["overlay_renderer_in_bootstrap"]
        )
        contaminated = copy.deepcopy(self.normalized)
        contaminated["runtime"]["mission"] += " poço de potencial"
        self.assertEqual(
            build_universe.build_overlay_isolation(contaminated)["status"],
            "fail",
        )

    def test_design_validation_applies_without_mast(self) -> None:
        verification = build_universe.build_verification(
            self.normalized, png_written=False, runtime_emitted=True
        )
        self.assertEqual(verification["design_validation"]["status"], "pass")
        self.assertEqual(verification["mast_validation"]["status"], "not_selected")

    def test_mast_is_selected_only_for_multi_agent(self) -> None:
        manifest = dynamic_narrative()
        manifest["runtime"]["execution_topology"] = "multi_agent"
        preflight = build_universe.assess_applicability(manifest)
        normalized = build_universe.normalize(manifest, preflight)
        verification = build_universe.build_verification(
            normalized, png_written=False, runtime_emitted=True
        )
        self.assertIn(build_universe.MAST_PROFILE_ID, normalized["validation_profiles"])
        self.assertEqual(verification["mast_validation"]["status"], "not_performed")
        self.assertEqual(len(verification["mast_validation"]["checks"]), 14)


class TestScriptsIntegration(unittest.TestCase):
    def test_evidence_delta_rejects_same_and_accepts_new_content(self) -> None:
        manifest = dynamic_narrative()
        preflight = build_universe.assess_applicability(manifest)
        normalized = build_universe.normalize(manifest, preflight)
        before = build_universe.build_evidence_snapshot(normalized)
        state = build_universe.build_state(normalized, before)
        with tempfile.TemporaryDirectory(prefix="corda-delta-") as tmp:
            root = Path(tmp)
            state_path = root / "state.json"
            before_path = root / "before.json"
            same_path = root / "same.json"
            after_path = root / "after.json"
            for path, value in (
                (state_path, state),
                (before_path, before),
                (same_path, before),
            ):
                path.write_text(
                    json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            script = Path(build_universe.__file__).with_name(
                "record_evidence_delta.py"
            )
            common = [
                sys.executable,
                str(script),
                "--state",
                str(state_path),
                "--before",
                str(before_path),
                "--delta-type",
                "new_observation",
                "--observed-at",
                "2026-07-26",
                "--source-ref",
                "test",
            ]
            rejected = subprocess.run(
                [*common, "--after", str(same_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rejected.returncode, 3)

            changed = copy.deepcopy(manifest)
            changed["evidence_registry"].append(
                {
                    "id": "source-c",
                    "kind": "observation",
                    "content": "new evidence C",
                    "claim_ids": ["claim-c"],
                    "source_ref": "test#source-c",
                }
            )
            changed["modes"][0]["evidence_scope"]["private"].append("source-c")
            after = build_universe.build_evidence_snapshot(changed)
            after_path.write_text(
                json.dumps(after, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            accepted = subprocess.run(
                [*common, "--after", str(after_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["rounds"]["admitted_peer_rounds"], 1)

    def test_compiler_emits_runtime_and_aborts_static_document(self) -> None:
        with tempfile.TemporaryDirectory(prefix="corda-build-") as tmp:
            root = Path(tmp)
            cases = [
                ("runtime", dynamic_narrative(), 0, True),
                ("faq", static_faq(), 0, False),
                ("static", static_document(), 3, False),
            ]
            for name, manifest, expected_code, expect_runtime in cases:
                spec = root / f"{name}.json"
                out = root / name
                spec.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(Path(build_universe.__file__)),
                        "--spec",
                        str(spec),
                        "--out-dir",
                        str(out),
                        "--basename",
                        name,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    completed.returncode,
                    expected_code,
                    (name, completed.stdout, completed.stderr),
                )
                self.assertTrue((out / f"{name}-preflight.json").exists())
                self.assertEqual(
                    (out / f"{name}-SYSTEM.md").exists(), expect_runtime
                )
                self.assertEqual(
                    (out / f"{name}-EVIDENCE.json").exists(),
                    expected_code == 0,
                )


class TestConformanceBenchmark(unittest.TestCase):
    def test_bundled_holdout_closes_false_open_and_invariants(self) -> None:
        skill_root = Path(build_universe.__file__).parent.parent
        benchmark_root = skill_root / "assets" / "conformance-benchmark"
        runner = Path(build_universe.__file__).with_name(
            "run_conformance_benchmark.py"
        )
        with tempfile.TemporaryDirectory(prefix="corda-conformance-") as tmp:
            out = Path(tmp) / "run.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--manifest",
                    str(benchmark_root / "universe-manifest.json"),
                    "--baseline-results",
                    str(benchmark_root / "baseline-v2.2.1-results.json"),
                    "--out",
                    str(out),
                    "--observed-at",
                    "2026-07-26",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(result["all_candidate_cases_pass"])
            self.assertEqual(len(result["case_results"]), 9)
            self.assertEqual(
                {
                    item["case_id"]
                    for item in result["case_results"]
                    if item["split"] == "holdout"
                },
                {
                    "duplicate-mode-id",
                    "invalid-build-mode",
                    "long-narrative-no-graph",
                },
            )
            self.assertEqual(
                {
                    item["case_id"]
                    for item in result["case_results"]
                    if item["case_role"] == "regression"
                },
                {"faq-sem-prazo", "faq-contradictory"},
            )
            self.assertEqual(
                result["candidate_metrics"]["applicability_accuracy"], 1.0
            )
            self.assertEqual(
                result["candidate_metrics"]["false_open_rate"], 0.0
            )
            self.assertEqual(
                result["candidate_metrics"]["invariant_accuracy"], 1.0
            )
            self.assertLess(
                result["baseline_metrics"]["applicability_accuracy"], 1.0
            )


class TestCastDerivationClosure(unittest.TestCase):
    """Correção S-01 (auditoria Codex Sol): testes metamórficos da derivação.

    A partição do elenco deve ser invariante à permutação da entrada,
    idempotente e estável sob duplicação; a fusão de adversários deve ser o
    complemento exato da condição declarada de ortogonalidade (evidência
    disjunta E dono distinto)."""

    SOL_CASE = [
        {"id": "a", "evidence_scope": {"private": ["a"]}},
        {"id": "b", "evidence_scope": {"private": ["b"]}},
        {"id": "c", "evidence_scope": {"private": ["a", "b"]}},
    ]

    def survivors(self, concerns: list) -> list[str]:
        merged, _ = derive_cast.merge_concerns(
            [json.loads(json.dumps(c)) for c in concerns]
        )
        return sorted(str(c["id"]) for c in merged)

    def test_permutation_invariance(self) -> None:
        from itertools import permutations

        results = {
            tuple(self.survivors(list(p))) for p in permutations(self.SOL_CASE)
        }
        self.assertEqual(len(results), 1, results)
        self.assertEqual(results.pop(), ("c",))

    def test_idempotence(self) -> None:
        once, _ = derive_cast.merge_concerns(
            [json.loads(json.dumps(c)) for c in self.SOL_CASE]
        )
        twice, _ = derive_cast.merge_concerns(json.loads(json.dumps(once)))
        self.assertEqual(
            sorted(str(c["id"]) for c in once),
            sorted(str(c["id"]) for c in twice),
        )

    def test_duplication_stability(self) -> None:
        duplicated = self.SOL_CASE + [
            {"id": "a2", "evidence_scope": {"private": ["a"]}}
        ]
        self.assertEqual(self.survivors(duplicated), ["c"])

    def test_transitive_closure_merges_indirectly_related(self) -> None:
        # a~c e b~c fundem {a,b,c} mesmo sem relação direta a~b
        self.assertEqual(self.survivors(self.SOL_CASE), ["c"])

    def test_adversary_orthogonality_is_exact_complement(self) -> None:
        cases = [
            (
                [{"id": "h1", "owner": "x", "evidence": ["a"]},
                 {"id": "h2", "owner": "x", "evidence": ["b"]}],
                1,  # mesmo dono => não ortogonal
            ),
            (
                [{"id": "h1", "owner": "x", "evidence": ["a"]},
                 {"id": "h2", "owner": "y", "evidence": ["a"]}],
                1,  # evidência sobreposta => não ortogonal
            ),
            (
                [{"id": "h1", "owner": "x", "evidence": ["a"]},
                 {"id": "h2", "owner": "y", "evidence": ["b"]}],
                2,  # disjunta E dono distinto => ortogonal
            ),
        ]
        for harm_domains, expected in cases:
            kept, _ = derive_cast.derive_adversaries(
                json.loads(json.dumps(harm_domains))
            )
            self.assertEqual(len(kept), expected, harm_domains)

    def test_merged_component_inherits_strongest_power(self) -> None:
        kept, log = derive_cast.derive_adversaries([
            {"id": "h1", "owner": "x", "evidence": ["a", "b"], "power": "parecer"},
            {"id": "h2", "owner": "x", "evidence": ["a"], "power": "veto"},
        ])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["power"], "veto")


class TestProjectionContract(unittest.TestCase):
    """ADR-001 (ciclo 02 da v4): contrato aditivo de projecao — casos R1 a R6."""

    def normalized(self, manifest: dict) -> dict:
        preflight = build_universe.assess_applicability(manifest)
        return build_universe.normalize(manifest, preflight)

    def test_r1_v3_manifest_without_block_changes_nothing(self) -> None:
        manifest = dynamic_narrative()
        normalized = self.normalized(manifest)
        self.assertIsNone(build_universe.build_projection_data(normalized))
        self.assertNotIn("projection_data", normalized)

    def test_r2_authored_derived_values_are_contradictory(self) -> None:
        for poison in (
            {"projection_data": {"anything": 1}},
            {"projection": {"pairs": [{"observers": ["a", "b"], "jaccard": 0.9}]}},
            {"projection": {"layout": {"algorithm": "mds", "seed": 1, "kruskal_stress": 0.0}}},
            # allowlist: chaves fora do vocabulario declarado tambem violam P1
            {"projection": {"layout": {"algorithm": "mds", "seed": 1, "stress": 0.01}}},
            {"projection": {"layout": {"algorithm": "mds", "seed": 1, "positions": [{"px": 0, "py": 1}]}}},
            {"projection": {"anything_else": {"value": 7}}},
            {"projection": {"panels": [{"sneaky": True}]}},
            # schema estrito (S-04, auditoria Codex Sol): enums, bounds e tipos
            {"projection": {"panels": ["unknown-panel"]}},
            {"projection": {"layout": {"algorithm": "not-implemented", "seed": 1}}},
            {"projection": {"layout": {"algorithm": "smacof-gradiente-fixo", "seed": True}}},
            {"projection": {"layout": {"algorithm": "smacof-gradiente-fixo", "seed": 1, "dimensions": 7}}},
            {"projection": {"layout": {"algorithm": "smacof-gradiente-fixo", "seed": 1, "iterations": -1}}},
        ):
            manifest = dynamic_narrative()
            manifest["build_mode"] = "runtime"
            manifest.update(copy.deepcopy(poison))
            preflight = build_universe.assess_applicability(manifest)
            self.assertNotEqual(
                preflight["result"], build_universe.RUNTIME_RESULT, poison
            )
            self.assertIn("projection_integrity", preflight["contradictions"])
            self.assertTrue(
                any(
                    item["primitive"] == "projection_integrity"
                    and item["status"] == "contradictory"
                    for item in preflight["requirements_unsatisfied"]
                )
            )

    def test_r3_temporal_classes_and_anchor(self) -> None:
        manifest = dynamic_narrative()
        manifest["source"]["observed_at"] = "2026-07-28"
        manifest["projection"] = {"panels": ["temporal_tension"]}
        manifest["entropy"] = {
            "threshold_days": 7,
            "rule": "sem data explicita nao existe contador",
            "items": ["item vivo sem data"],
        }
        normalized = self.normalized(manifest)
        block = build_universe.build_projection_data(normalized)["temporal_tension"]
        self.assertEqual(block["observed_at"], "2026-07-28")
        by_class: dict[str, list] = {}
        for item in block["items"]:
            by_class.setdefault(item["class"], []).append(item)
        for item in by_class.get("undated", []):
            self.assertFalse(item["counter"])
            self.assertIsNone(item["days_remaining"])
        self.assertTrue(by_class.get("undated"), "fixture deve produzir undated")
        for item in by_class.get("dated", []):
            self.assertTrue(item["counter"])
            self.assertIsInstance(item["days_remaining"], int)
            self.assertTrue(item["due_at"])
        # sem ancora nao existe contador (P3)
        manifest_no_anchor = dynamic_narrative()
        manifest_no_anchor["projection"] = {"panels": ["temporal_tension"]}
        block_no_anchor = build_universe.build_projection_data(
            self.normalized(manifest_no_anchor)
        )["temporal_tension"]
        self.assertIsNone(block_no_anchor["observed_at"])
        self.assertEqual(block_no_anchor["items"], [])

    def test_r4_state_transition_requires_acceptance_record(self) -> None:
        manifest = dynamic_narrative()
        normalized = self.normalized(manifest)
        snapshot = build_universe.build_evidence_snapshot(normalized)
        state = build_universe.build_state(normalized, snapshot)
        self.assertEqual(state["decision"]["acceptance_records"], [])
        script = Path(build_universe.__file__).with_name("record_acceptance.py")
        with tempfile.TemporaryDirectory(prefix="corda-accept-") as tmp:
            state_path = Path(tmp) / "state.json"
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            common = [sys.executable, str(script), "--state", str(state_path)]
            refused = subprocess.run(
                [
                    *common,
                    "--outcome",
                    "accepted",
                    "--owner",
                    "owner",
                    "--date",
                    "2026-07-28",
                    "--statement",
                    "   ",
                    "--source-ref",
                    "test",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(refused.returncode, 2)
            untouched = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                untouched["decision"]["state"], "pending_human_acceptance"
            )
            wrong_owner = subprocess.run(
                [
                    *common,
                    "--outcome",
                    "accepted",
                    "--owner",
                    "impostor",
                    "--date",
                    "2026-07-28",
                    "--statement",
                    "aceito",
                    "--source-ref",
                    "test",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(wrong_owner.returncode, 2)
            accepted = subprocess.run(
                [
                    *common,
                    "--outcome",
                    "accepted",
                    "--owner",
                    "owner",
                    "--date",
                    "2026-07-28",
                    "--statement",
                    "aceito o incremento",
                    "--source-ref",
                    "test#decisao",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            mutated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(mutated["decision"]["state"], "accepted")
            self.assertEqual(len(mutated["decision"]["acceptance_records"]), 1)
            record = mutated["decision"]["acceptance_records"][0]
            for field in ("decided_at", "owner", "outcome", "statement", "source_ref"):
                self.assertTrue(str(record[field]).strip())

    def test_r5_bootstrap_and_identity_unchanged_by_projection(self) -> None:
        base = dynamic_narrative()
        base["source"]["observed_at"] = "2026-07-28"
        with_projection = copy.deepcopy(base)
        with_projection["projection"] = {
            "panels": [
                "evidence_separation",
                "temporal_tension",
                "acceptance_boundary",
            ],
            "layout": {"algorithm": "smacof-gradiente-fixo", "seed": 42},
        }
        norm_a = self.normalized(base)
        norm_b = self.normalized(with_projection)
        self.assertEqual(norm_a["universe_id"], norm_b["universe_id"])
        snap_a = build_universe.build_evidence_snapshot(norm_a)
        snap_b = build_universe.build_evidence_snapshot(norm_b)
        state_a = build_universe.build_state(norm_a, snap_a)
        state_b = build_universe.build_state(norm_b, snap_b)
        bootstrap_a = build_universe.render_bootstrap(
            build_universe.render_system(norm_a),
            build_universe.render_universe(norm_a),
            state_a,
        )
        projected = copy.deepcopy(norm_b)
        projected["projection_data"] = build_universe.build_projection_data(norm_b)
        bootstrap_b = build_universe.render_bootstrap(
            build_universe.render_system(projected),
            build_universe.render_universe(projected),
            state_b,
        )
        self.assertEqual(bootstrap_a, bootstrap_b)

    def test_r7_state_downgrade_preserves_acceptance_records(self) -> None:
        manifest = dynamic_narrative()
        normalized = self.normalized(manifest)
        snapshot = build_universe.build_evidence_snapshot(normalized)
        state = build_universe.build_state(normalized, snapshot)
        accept_script = Path(build_universe.__file__).with_name("record_acceptance.py")
        downgrade_script = Path(build_universe.__file__).with_name("downgrade_state.py")
        with tempfile.TemporaryDirectory(prefix="corda-downgrade-") as tmp:
            state_path = Path(tmp) / "state.json"
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            accepted = subprocess.run(
                [
                    sys.executable,
                    str(accept_script),
                    "--state",
                    str(state_path),
                    "--outcome",
                    "accepted",
                    "--owner",
                    "owner",
                    "--date",
                    "2026-07-28",
                    "--statement",
                    "aceito",
                    "--source-ref",
                    "test#aceite",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            downgraded = subprocess.run(
                [
                    sys.executable,
                    str(downgrade_script),
                    "--state",
                    str(state_path),
                    "--date",
                    "2026-07-28",
                    "--owner",
                    "owner",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(downgraded.returncode, 0, downgraded.stderr)
            after = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(after["schema_version"], "corda-state/1.4")
            self.assertNotIn("acceptance_records", after["decision"])
            archive_path = state_path.with_name("state-acceptance-archive.json")
            self.assertTrue(archive_path.is_file())
            archive = json.loads(archive_path.read_text(encoding="utf-8"))
            self.assertEqual(len(archive["exports"]), 1)
            self.assertEqual(len(archive["exports"][0]["acceptance_records"]), 1)
            self.assertTrue(
                any("downgrade" in str(event.get("what", "")) for event in after["events"])
            )
            rerun = subprocess.run(
                [
                    sys.executable,
                    str(downgrade_script),
                    "--state",
                    str(state_path),
                    "--date",
                    "2026-07-28",
                    "--owner",
                    "owner",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rerun.returncode, 0)
            # ciclo repetido: re-upgrade manual + novo aceite + novo downgrade
            # NAO pode sobrescrever o export anterior (append-only)
            state_2 = json.loads(state_path.read_text(encoding="utf-8"))
            state_2["schema_version"] = "corda-state/1.5"
            state_2["decision"]["acceptance_records"] = [
                {
                    "decided_at": "2026-07-29",
                    "owner": "owner",
                    "outcome": "adjusted",
                    "statement": "segundo ciclo",
                    "source_ref": "test#segundo",
                }
            ]
            state_path.write_text(
                json.dumps(state_2, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            second = subprocess.run(
                [
                    sys.executable,
                    str(downgrade_script),
                    "--state",
                    str(state_path),
                    "--date",
                    "2026-07-29",
                    "--owner",
                    "owner",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            archive_2 = json.loads(archive_path.read_text(encoding="utf-8"))
            self.assertEqual(len(archive_2["exports"]), 2)
            self.assertEqual(
                archive_2["exports"][0]["acceptance_records"][0]["statement"],
                "aceito",
            )

    def test_r10_malformed_dates_are_contradictory_and_refused(self) -> None:
        """Correção S-05 (auditoria Codex Sol): datas malformadas nunca são
        aceitas nem descartadas em silêncio."""
        manifest = dynamic_narrative()
        manifest["source"]["observed_at"] = "2026-07-28"
        manifest["strings"] = [
            {"from": "integrator", "to": "synthesis", "label": "x", "kind": "open",
             "due_at": "not-a-date", "state": "active", "source_ref": "test#x"}
        ]
        preflight = build_universe.assess_applicability(manifest)
        self.assertIn("temporal_integrity", preflight["contradictions"])
        self.assertNotEqual(preflight["result"], build_universe.RUNTIME_RESULT)

        manifest_bad_anchor = dynamic_narrative()
        manifest_bad_anchor["source"]["observed_at"] = "yesterday"
        preflight_bad = build_universe.assess_applicability(manifest_bad_anchor)
        self.assertIn("temporal_integrity", preflight_bad["contradictions"])

        # record_acceptance recusa decided_at malformado (rc 2, STATE intocado)
        normalized = self.normalized(dynamic_narrative())
        snapshot = build_universe.build_evidence_snapshot(normalized)
        state = build_universe.build_state(normalized, snapshot)
        script = Path(build_universe.__file__).with_name("record_acceptance.py")
        with tempfile.TemporaryDirectory(prefix="corda-date-") as tmp:
            state_path = Path(tmp) / "state.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False))
            refused = subprocess.run(
                [sys.executable, str(script), "--state", str(state_path),
                 "--outcome", "accepted", "--owner", "owner",
                 "--date", "not-a-date", "--statement", "ok",
                 "--source-ref", "test"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(refused.returncode, 2)
            untouched = json.loads(state_path.read_text())
            self.assertEqual(untouched["decision"]["state"], "pending_human_acceptance")

    def test_r11_record_evaluation_rejects_self_declared_metrics(self) -> None:
        """Correção S-02 (auditoria Codex Sol): elegibilidade não é fabricável —
        task_success declarado deve bater com o recomputo de case_results."""
        script = Path(build_universe.__file__).with_name("record_evaluation.py")
        evaluation = {
            "runs": [],
            "contract_complete": False,
            "contract": {
                "benchmark": [
                    {"id": "case-x", "ground_truth_ref": "truth-x.json",
                     "split": "development"}
                ],
                "metrics": [{"name": "task_success", "direction": "maximize"}],
                "promotion_threshold": {
                    "task_success": {"min_improvement": 0.05}
                },
            },
            "promotion": {"status": "not_eligible"},
            "status": "compiled_unevaluated",
        }
        fabricated = {
            "run_id": "fabricado",
            "observed_at": "2026-07-29",
            "evidence_refs": ["x.json"],
            "verdict_source": {"kind": "deterministic_scorer", "source_ref": "s.py"},
            "case_results": [
                {"case_id": "case-x", "success": False,
                 "ground_truth_ref": "truth-x.json",
                 "oracle_evidence_ref": "o.json"}
            ],
            "baseline_metrics": {"task_success": 0.0},
            "candidate_metrics": {"task_success": 1.0},
        }
        honest = json.loads(json.dumps(fabricated))
        honest["run_id"] = "honesto"
        honest["case_results"][0]["success"] = True
        honest["baseline_case_results"] = [
            {"case_id": "case-x", "success": False}
        ]
        with tempfile.TemporaryDirectory(prefix="corda-eval-") as tmp:
            root = Path(tmp)
            eval_path = root / "evaluation.json"
            for name, run in (("fabricado", fabricated), ("honesto", honest)):
                eval_path.write_text(json.dumps(evaluation, ensure_ascii=False))
                run_path = root / f"{name}.json"
                run_path.write_text(
                    json.dumps(attach_scorer_report(run, root), ensure_ascii=False)
                )
                result = subprocess.run(
                    [sys.executable, str(script), "--evaluation", str(eval_path),
                     "--run-result", str(run_path)],
                    check=False, capture_output=True, text=True,
                )
                if name == "fabricado":
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("S-02", result.stderr)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_r8_absolute_due_at_accumulates_tension_across_builds(self) -> None:
        """Correcao Z1: com due_at absoluto, days_remaining decresce quando
        observed_at avanca entre builds; pode ficar negativo (vencido com data
        explicita); lead_time_days sem due_at mantem o comportamento v3 com
        limitacao declarada."""

        def temporal(observed_at: str) -> dict:
            manifest = dynamic_narrative()
            manifest["source"]["observed_at"] = observed_at
            manifest["projection"] = {"panels": ["temporal_tension"]}
            manifest["strings"] = [
                {
                    "from": "integrator",
                    "to": "synthesis",
                    "label": "prazo absoluto",
                    "kind": "open",
                    "due_at": "2026-08-01",
                    "state": "active",
                    "source_ref": "test#prazo",
                },
                {
                    "from": "integrator",
                    "to": "synthesis",
                    "label": "prazo relativo legado",
                    "kind": "open",
                    "lead_time_days": 4,
                    "state": "active",
                    "source_ref": "test#legado",
                },
            ]
            preflight = build_universe.assess_applicability(manifest)
            normalized = build_universe.normalize(manifest, preflight)
            block = build_universe.build_projection_data(normalized)[
                "temporal_tension"
            ]
            return {item["source_ref"]: item for item in block["items"]}

        first = temporal("2026-07-28")
        second = temporal("2026-07-30")
        third = temporal("2026-08-03")
        self.assertEqual(first["test#prazo"]["days_remaining"], 4)
        self.assertEqual(second["test#prazo"]["days_remaining"], 2)
        self.assertEqual(third["test#prazo"]["days_remaining"], -2)
        self.assertTrue(third["test#prazo"]["overdue"])
        self.assertEqual(first["test#prazo"]["due_basis"], "declared_absolute")
        # legado: nao acumula, e a limitacao e declarada
        self.assertEqual(first["test#legado"]["days_remaining"], 4)
        self.assertEqual(second["test#legado"]["days_remaining"], 4)
        self.assertIn("derived_from_observed_at", second["test#legado"]["due_basis"])
        self.assertFalse(second["test#legado"]["overdue"])

    def test_r6_topology_label_and_deterministic_layout(self) -> None:
        manifest = dynamic_narrative()
        manifest["source"]["observed_at"] = "2026-07-28"
        manifest["projection"] = {
            "panels": ["evidence_separation"],
            "layout": {"algorithm": "smacof-gradiente-fixo", "seed": 42},
        }
        normalized = self.normalized(manifest)
        block = build_universe.build_projection_data(normalized)["evidence_separation"]
        self.assertEqual(
            block["label_rule"], "topologia/separacao de evidencia; nunca eixo W"
        )
        self.assertIn("1 - jaccard", block["transformation"])
        for pair in block["pairs"]:
            if pair["jaccard"] is not None:
                self.assertAlmostEqual(
                    pair["distance"], round(1 - pair["jaccard"], 4)
                )
        layout_a = block.get("layout")
        block_again = build_universe.build_projection_data(normalized)[
            "evidence_separation"
        ]
        self.assertEqual(layout_a, block_again.get("layout"))
        if layout_a and layout_a.get("coordinates"):
            self.assertFalse(layout_a["coordinates_canonical"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
