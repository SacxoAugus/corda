#!/usr/bin/env python3
"""Record and mechanically score an evidenced CORDA benchmark run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a CORDA evaluation run.")
    parser.add_argument("--evaluation", required=True, type=Path)
    parser.add_argument("--run-result", required=True, type=Path)
    parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help=(
            "STATE.json opcional a sincronizar (S-07): espelha status/promocao "
            "da avaliacao e registra evento"
        ),
    )
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_run(run: dict[str, Any]) -> None:
    missing = [
        field
        for field in (
            "run_id",
            "observed_at",
            "evidence_refs",
            "case_results",
            "baseline_metrics",
            "candidate_metrics",
            "verdict_source",
        )
        if not run.get(field)
    ]
    if missing:
        raise ValueError(f"run result missing: {', '.join(missing)}")
    for field in ("evidence_refs", "case_results"):
        if not isinstance(run[field], list):
            raise ValueError(f"{field} must be a list")
    for field in ("baseline_metrics", "candidate_metrics"):
        if not isinstance(run[field], dict):
            raise ValueError(f"{field} must be an object")
    verdict_source = run["verdict_source"]
    if not isinstance(verdict_source, dict):
        raise ValueError("verdict_source must be an object")
    if verdict_source.get("kind") not in {"deterministic_scorer", "human_oracle"}:
        raise ValueError(
            "verdict_source.kind must be deterministic_scorer or human_oracle"
        )
    if not verdict_source.get("source_ref"):
        raise ValueError("verdict_source.source_ref is required")

    # Correcao S-02 (auditoria Codex Sol): metricas autodeclaradas deixam de
    # ser aceitas quando os resultados por caso permitem recomputa-las. Se os
    # case_results carregam `success` booleano e uma metrica `task_success` e
    # declarada, o registrador RECOMPUTA e rejeita divergencia — o cenario
    # demonstrado pelo auditor (4x success:false + candidate 1.0) agora falha.
    def recompute_task_success(results: list) -> float | None:
        flags = [item.get("success") for item in results if isinstance(item, dict)]
        if not flags or any(not isinstance(flag, bool) for flag in flags):
            return None
        return round(sum(1 for flag in flags if flag) / len(flags), 4)

    candidate_declared = run["candidate_metrics"].get("task_success")
    if isinstance(candidate_declared, (int, float)) and not isinstance(
        candidate_declared, bool
    ):
        recomputed = recompute_task_success(run["case_results"])
        if recomputed is None:
            raise ValueError(
                "declared task_success requires boolean case_results[].success "
                "for recomputation (S-02)"
            )
        if abs(float(candidate_declared) - recomputed) > 1e-9:
            raise ValueError(
                f"candidate_metrics.task_success={candidate_declared} diverges from the "
                f"recomputation over case_results ({recomputed}) (S-02)"
            )
    baseline_declared = run["baseline_metrics"].get("task_success")
    baseline_results = run.get("baseline_case_results")
    if isinstance(baseline_declared, (int, float)) and not isinstance(
        baseline_declared, bool
    ):
        if not isinstance(baseline_results, list):
            raise ValueError(
                "declared baseline_metrics.task_success requires "
                "baseline_case_results[] with boolean success (S-02/S-03)"
            )
        recomputed_baseline = recompute_task_success(baseline_results)
        if recomputed_baseline is None:
            raise ValueError(
                "baseline_case_results[].success missing or not boolean (S-02)"
            )
        if abs(float(baseline_declared) - recomputed_baseline) > 1e-9:
            raise ValueError(
                f"baseline_metrics.task_success={baseline_declared} diverges from the "
                f"recomputation over baseline_case_results "
                f"({recomputed_baseline}) (S-02)"
            )

    # Correcao S-02b (parecer Codex Sol, N-01): o relatorio content-addressed
    # do scorer deixa de ser opcional quando o veredito e deterministico — sem
    # ele, o vinculo entre case_results e a execucao real do scorer e prosa.
    report_ref = run.get("scorer_report_ref")
    report_sha = run.get("scorer_report_sha256")
    if verdict_source.get("kind") == "deterministic_scorer" and not (
        report_ref and report_sha
    ):
        raise ValueError(
            "verdict_source deterministic_scorer requires scorer_report_ref and "
            "scorer_report_sha256 (S-02b/N-01)"
        )
    if report_ref or report_sha:
        if not (report_ref and report_sha):
            raise ValueError(
                "scorer_report_ref and scorer_report_sha256 must come together (S-02)"
            )
        report_path = Path(str(report_ref))
        if not report_path.is_file():
            raise ValueError(f"scorer_report_ref does not exist: {report_ref} (S-02)")
        import hashlib

        digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
        if digest != str(report_sha).strip().lower():
            raise ValueError(
                f"scorer_report_sha256 diverges from the content of {report_ref} (S-02)"
            )


def _canonical_case_ids(items: Any, field: str, finding: str) -> list[str]:
    """Correcao N-05 (gate isolado Codex Sol): IDs falsy ('', 0, None, espaco)
    eram ignorados pela igualdade de conjuntos mas contados pelo recomputo.
    Agora todo item precisa ser objeto com case_id string nao vazia apos strip
    — item invalido recusa o registro inteiro, nada e filtrado em silencio."""
    if not isinstance(items, list):
        raise ValueError(f"{field} must be a list ({finding})")
    ids: list[str] = []
    for position, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(
                f"{field}[{position}] is not an object ({finding})"
            )
        raw = item.get("case_id")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(
                f"{field}[{position}].case_id missing, non-string or empty "
                f"({finding})"
            )
        ids.append(raw.strip())
    return ids


def validate_contract_benchmark(contract: dict[str, Any]) -> None:
    """Correcao N-08 (gate isolado Codex Sol): IDs duplicados no benchmark
    colapsavam em set/dict e o ultimo item vencia em silencio — um resultado
    unico satisfazia dois casos declarados. O contrato agora e validado antes
    de qualquer cobertura: lista nao vazia, ids canonicos unicos, truth
    presente."""
    benchmark = contract.get("benchmark")
    if not isinstance(benchmark, list) or not benchmark:
        raise ValueError("contract.benchmark must be a non-empty list (N-08)")
    seen: set[str] = set()
    for position, item in enumerate(benchmark):
        if not isinstance(item, dict):
            raise ValueError(f"contract.benchmark[{position}] is not an object (N-08)")
        raw = item.get("id")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(
                f"contract.benchmark[{position}].id missing or empty (N-08)"
            )
        canonical = raw.strip()
        if canonical in seen:
            raise ValueError(
                f"contract.benchmark has a duplicate id: {canonical!r} (N-08)"
            )
        seen.add(canonical)
        if not item.get("ground_truth_ref"):
            raise ValueError(
                f"contract.benchmark[{position}] is missing ground_truth_ref (N-08)"
            )


def validate_contract_cases(
    contract: dict[str, Any], run: dict[str, Any]
) -> None:
    """Correcao N-01 (parecer Codex Sol): igualdade exata e unicidade entre os
    casos do contrato e os resultados. A sonda do parecerista (1 holdout
    esperado em false + 99 casos estranhos em true → promotion_candidate)
    passa a ser recusada aqui, antes de qualquer recomputo."""
    validate_contract_benchmark(contract)
    expected = {
        str(item["id"]).strip() for item in contract["benchmark"]
    }
    actual_ids = _canonical_case_ids(
        run.get("case_results"), "case_results", "N-05"
    )
    duplicates = sorted({cid for cid in actual_ids if actual_ids.count(cid) > 1})
    if duplicates:
        raise ValueError(
            f"case_results has a duplicate case_id: {', '.join(duplicates)} (N-01)"
        )
    extras = sorted(set(actual_ids) - expected)
    if extras:
        raise ValueError(
            "case_results contains cases outside the contract: "
            f"{', '.join(extras[:5])}{'...' if len(extras) > 5 else ''} (N-01)"
        )
    baseline_results = run.get("baseline_case_results")
    if isinstance(baseline_results, list):
        baseline_ids = _canonical_case_ids(
            baseline_results, "baseline_case_results", "N-05"
        )
        base_dup = sorted({c for c in baseline_ids if baseline_ids.count(c) > 1})
        if base_dup:
            raise ValueError(
                f"baseline_case_results has a duplicate case_id: "
                f"{', '.join(base_dup)} (N-01)"
            )
        if set(baseline_ids) != set(actual_ids):
            raise ValueError(
                "baseline_case_results must cover exactly the same set "
                "of cases as the candidate (N-01)"
            )


def assess_case_coverage(
    contract: dict[str, Any], run: dict[str, Any]
) -> dict[str, Any]:
    expected = {
        str(item.get("id")): item
        for item in contract.get("benchmark", [])
        if isinstance(item, dict) and item.get("id")
    }
    actual = {
        str(item.get("case_id")): item
        for item in run.get("case_results", [])
        if isinstance(item, dict) and item.get("case_id")
    }
    missing = sorted(set(expected) - set(actual))
    invalid = sorted(
        case_id
        for case_id, item in actual.items()
        if case_id in expected
        and (
            not item.get("oracle_evidence_ref")
            or item.get("ground_truth_ref")
            != expected[case_id].get("ground_truth_ref")
        )
    )
    holdout_ids = sorted(
        case_id
        for case_id, item in expected.items()
        if item.get("split") == "holdout"
    )
    holdout_covered = bool(holdout_ids) and not (set(holdout_ids) & set(missing + invalid))
    return {
        "complete": not missing and not invalid and bool(expected),
        "expected_case_count": len(expected),
        "observed_case_count": len(actual),
        "missing_case_ids": missing,
        "invalid_case_ids": invalid,
        "holdout_case_ids": holdout_ids,
        "holdout_covered": holdout_covered,
    }


def score_thresholds(
    contract: dict[str, Any], run: dict[str, Any]
) -> dict[str, Any]:
    metrics = {
        str(item.get("name")): item
        for item in contract.get("metrics", [])
        if isinstance(item, dict) and item.get("name")
    }
    thresholds = contract.get("promotion_threshold", {})
    baseline = run["baseline_metrics"]
    candidate = run["candidate_metrics"]
    checks: list[dict[str, Any]] = []
    for name, rule in thresholds.items():
        spec = metrics.get(str(name), {})
        if (
            not isinstance(rule, dict)
            or not isinstance(baseline.get(name), (int, float))
            or isinstance(baseline.get(name), bool)
            or not isinstance(candidate.get(name), (int, float))
            or isinstance(candidate.get(name), bool)
        ):
            checks.append(
                {
                    "metric": name,
                    "status": "invalid",
                    "reason": "threshold or numeric baseline/candidate missing",
                }
            )
            continue
        before = float(baseline[name])
        after = float(candidate[name])
        raw_improvement = (
            after - before
            if spec.get("direction") == "maximize"
            else before - after
        )
        comparison = rule.get("comparison", "absolute")
        if comparison == "relative":
            improvement = raw_improvement / abs(before) if before else None
        else:
            improvement = raw_improvement
        minimum = float(rule.get("min_improvement", 0.0))
        passed = improvement is not None and improvement >= minimum
        checks.append(
            {
                "metric": name,
                "status": "pass" if passed else "fail",
                "direction": spec.get("direction"),
                "comparison": comparison,
                "baseline": before,
                "candidate": after,
                "improvement": improvement,
                "minimum_improvement": minimum,
                "scorer": spec.get("scorer"),
            }
        )
    status = (
        "invalid"
        if not checks or any(item["status"] == "invalid" for item in checks)
        else "pass"
        if all(item["status"] == "pass" for item in checks)
        else "fail"
    )
    return {"status": status, "checks": checks}


def main() -> int:
    args = parse_args()
    try:
        evaluation = load_object(args.evaluation)
        run = load_object(args.run_result)
        validate_run(run)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    runs = evaluation.setdefault("runs", [])
    if not isinstance(runs, list):
        print("ERROR: evaluation.runs must be a list", file=sys.stderr)
        return 2
    if any(
        isinstance(existing, dict) and existing.get("run_id") == run["run_id"]
        for existing in runs
    ):
        print(f"ERROR: duplicate run_id: {run['run_id']}", file=sys.stderr)
        return 2

    contract = evaluation.get("contract")
    if not isinstance(contract, dict):
        print("ERROR: evaluation.contract must be an object", file=sys.stderr)
        return 2
    try:
        validate_contract_cases(contract, run)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Correcao S-07b (parecer Codex Sol, N-03): transacional, nao best-effort.
    # TODOS os destinos sao lidos e validados ANTES de qualquer escrita; um
    # STATE ilegivel deixa a EVALUATION intocada.
    state = None
    if args.state is not None:
        try:
            state = load_object(args.state)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(
                f"ERROR: STATE unreadable for sync: {exc} "
                "(S-07b: nothing was written)",
                file=sys.stderr,
            )
            return 2
        # Correcao N-06 (gate isolado Codex Sol): JSON valido com estrutura
        # errada ('events' dict, 'evaluation' string) estourava DEPOIS da
        # EVALUATION escrita. O schema mutavel e validado aqui, antes de
        # qualquer escrita.
        if "evaluation" in state and not isinstance(state["evaluation"], dict):
            print(
                "ERROR: STATE.evaluation must be an object "
                "(N-06: nothing was written)",
                file=sys.stderr,
            )
            return 2
        if "events" in state and not isinstance(state["events"], list):
            print(
                "ERROR: STATE.events must be a list (N-06: nothing was written)",
                file=sys.stderr,
            )
            return 2

    coverage = assess_case_coverage(contract, run)
    threshold = score_thresholds(contract, run)
    run["mechanical_assessment"] = {
        "case_coverage": coverage,
        "thresholds": threshold,
        "note": (
            "CORDA recomputes numeric thresholds and coverage; oracle/"
            "scorer validity remains external and is linked by source_ref."
        ),
    }
    runs.append(run)

    eligible = (
        evaluation.get("contract_complete") is True
        and coverage["complete"]
        and coverage["holdout_covered"]
        and threshold["status"] == "pass"
    )
    promotion = evaluation.setdefault("promotion", {})
    if eligible:
        evaluation["status"] = "promotion_candidate"
        promotion["status"] = "awaiting_human_acceptance"
    elif threshold["status"] == "fail":
        evaluation["status"] = "evaluated_fail"
        promotion["status"] = "not_eligible"
    else:
        evaluation["status"] = "evaluated_inconclusive"
        promotion["status"] = "not_eligible"

    def atomic_write(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        import os

        os.replace(temporary, path)

    # Correcao N-06: TODAS as mutacoes (dos dois payloads) acontecem em memoria
    # ANTES de qualquer replace — um TypeError estrutural nao pode mais ocorrer
    # entre as escritas. Janela residual declarada: crash do processo ENTRE os
    # dois os.replace ainda deixaria so a EVALUATION nova em disco; journal de
    # commit para atomicidade de par de arquivos fica registrado como candidato
    # (recomendacao N-06 do gate), nao implementado.
    if state is not None:
        state.setdefault("evaluation", {})
        state["evaluation"]["status"] = evaluation["status"]
        state["evaluation"]["promotion"] = (
            evaluation.get("promotion", {}).get("status", "not_accepted")
        )
        state.setdefault("events", []).append(
            {
                "at": run["observed_at"],
                "what": (
                    f"evaluation sync (S-07): status={evaluation['status']}, "
                    f"run_id={run['run_id']}"
                ),
                "by": "record_evaluation.py",
            }
        )

    atomic_write(args.evaluation, evaluation)
    print(f"Updated: {args.evaluation}")
    print(f"Status: {evaluation['status']}")
    if state is not None:
        atomic_write(args.state, state)
        print(f"State synced: {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
