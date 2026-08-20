#!/usr/bin/env python3
"""Run the bundled CORDA compiler conformance benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_universe
import render_corda


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate CORDA applicability and invariant conformance."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--baseline-results", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--run-id", default="corda-conformance-v1")
    parser.add_argument("--observed-at", required=True)
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def observe_case(manifest: dict[str, Any]) -> dict[str, Any]:
    try:
        render_corda.validate_manifest(manifest, require_topology=False)
    except render_corda.ManifestError as exc:
        return {
            "schema_status": "fail",
            "schema_error": str(exc),
            "preflight_result": "SCHEMA_ERROR",
            "contradictions": [],
            "requirement_status": {},
        }
    preflight = build_universe.assess_applicability(manifest)
    requirement_status = {
        str(item["primitive"]): str(item["status"])
        for item in preflight["requirements_assessment"]
    }
    observed: dict[str, Any] = {
        "schema_status": "pass",
        "preflight_result": preflight["result"],
        "contradictions": sorted(map(str, preflight.get("contradictions", []))),
        "requirement_status": requirement_status,
    }
    if preflight["result"] in {
        build_universe.RUNTIME_RESULT,
        build_universe.PROJECTION_RESULT,
    }:
        normalized = build_universe.normalize(manifest, preflight)
        observed["evidence_topology"] = normalized["evidence_topology"][
            "classification"
        ]
        observed["round_policy"] = normalized["round_admission"]["policy"]
    return observed


def score_case(
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, expected_value: Any, observed_value: Any) -> None:
        checks.append(
            {
                "name": name,
                "expected": expected_value,
                "observed": observed_value,
                "pass": observed_value == expected_value,
            }
        )

    add_check(
        "preflight_result",
        expected.get("expected_preflight_result"),
        observed.get("preflight_result"),
    )
    if "expected_schema_status" in expected:
        add_check(
            "schema_status",
            expected["expected_schema_status"],
            observed.get("schema_status"),
        )
    if "expected_contradictions" in expected:
        add_check(
            "contradictions",
            sorted(map(str, expected["expected_contradictions"])),
            sorted(map(str, observed.get("contradictions", []))),
        )
    for primitive, status in expected.get("expected_requirement_status", {}).items():
        add_check(
            f"requirement_status.{primitive}",
            status,
            observed.get("requirement_status", {}).get(primitive),
        )
    for field in ("evidence_topology", "round_policy"):
        expected_key = f"expected_{field}"
        if expected_key in expected:
            add_check(field, expected[expected_key], observed.get(field))
    return {
        "pass": all(item["pass"] for item in checks),
        "checks": checks,
    }


def aggregate(
    expected_by_id: dict[str, dict[str, Any]],
    observed_by_id: dict[str, dict[str, Any]],
) -> dict[str, float]:
    applicability_checks = 0
    applicability_passes = 0
    invariant_checks = 0
    invariant_passes = 0
    non_runtime_expected = 0
    false_opens = 0
    for case_id, expected in expected_by_id.items():
        observed = observed_by_id.get(case_id, {})
        score = score_case(expected, observed)
        for check in score["checks"]:
            if check["name"] == "preflight_result":
                applicability_checks += 1
                applicability_passes += int(check["pass"])
            else:
                invariant_checks += 1
                invariant_passes += int(check["pass"])
        if expected.get("expected_preflight_result") != build_universe.RUNTIME_RESULT:
            non_runtime_expected += 1
            false_opens += int(
                observed.get("preflight_result") == build_universe.RUNTIME_RESULT
            )
    return {
        "applicability_accuracy": (
            applicability_passes / applicability_checks
            if applicability_checks
            else 0.0
        ),
        "false_open_rate": (
            false_opens / non_runtime_expected if non_runtime_expected else 0.0
        ),
        "invariant_accuracy": (
            invariant_passes / invariant_checks if invariant_checks else 0.0
        ),
    }


def main() -> int:
    args = parse_args()
    try:
        universe_manifest = load_object(args.manifest)
        baseline = load_object(args.baseline_results)
        contract = universe_manifest.get("evaluation_contract")
        if not isinstance(contract, dict):
            raise ValueError("manifest.evaluation_contract must be an object")
        benchmark = contract.get("benchmark")
        if not isinstance(benchmark, list) or not benchmark:
            raise ValueError("evaluation_contract.benchmark must not be empty")
        base = args.manifest.parent
        expected_by_id: dict[str, dict[str, Any]] = {}
        candidate_by_id: dict[str, dict[str, Any]] = {}
        case_results: list[dict[str, Any]] = []
        evidence_refs = [str(args.baseline_results)]
        for case in benchmark:
            if not isinstance(case, dict):
                raise ValueError("benchmark cases must be objects")
            case_id = str(case["id"])
            input_path = resolve(base, str(case["input_ref"]))
            truth_path = resolve(base, str(case["ground_truth_ref"]))
            expected = load_object(truth_path)
            observed = observe_case(load_object(input_path))
            expected_by_id[case_id] = expected
            candidate_by_id[case_id] = observed
            score = score_case(expected, observed)
            case_results.append(
                {
                    "case_id": case_id,
                    "ground_truth_ref": str(case["ground_truth_ref"]),
                    "oracle_evidence_ref": f"{args.out.name}#{case_id}",
                    "split": case.get("split"),
                    "case_role": case.get("case_role", "evaluation"),
                    "pass": score["pass"],
                    "observed": observed,
                    "checks": score["checks"],
                }
            )
            evidence_refs.extend([str(input_path), str(truth_path)])
        baseline_cases = baseline.get("case_results")
        if not isinstance(baseline_cases, list):
            raise ValueError("baseline-results.case_results must be a list")
        baseline_by_id = {
            str(item["case_id"]): item.get("observed", {})
            for item in baseline_cases
            if isinstance(item, dict) and item.get("case_id")
        }
        baseline_metrics = aggregate(expected_by_id, baseline_by_id)
        candidate_metrics = aggregate(expected_by_id, candidate_by_id)
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    run = {
        "run_id": args.run_id,
        "observed_at": args.observed_at,
        "evidence_refs": sorted(set(evidence_refs)),
        "verdict_source": {
            "kind": "deterministic_scorer",
            "source_ref": "gerar-corda/scripts/run_conformance_benchmark.py",
        },
        "case_results": case_results,
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "all_candidate_cases_pass": all(item["pass"] for item in case_results),
        "baseline_source": baseline.get("source"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Benchmark cases: {len(case_results)}")
    print(f"Baseline metrics: {json.dumps(baseline_metrics, sort_keys=True)}")
    print(f"Candidate metrics: {json.dumps(candidate_metrics, sort_keys=True)}")
    print(f"All candidate cases pass: {run['all_candidate_cases_pass']}")
    print(f"Output: {args.out}")
    return 0 if run["all_candidate_cases_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
