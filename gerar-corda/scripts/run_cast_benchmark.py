#!/usr/bin/env python3
"""Roda o benchmark de derivação de elenco contra o ground truth rotulado."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_cast import derive  # noqa: E402

CHECKS = ("verdict", "derivation_mode", "surviving_lenses", "adversaries",
          "integrator", "requirements_unsatisfied")


def actual_of(cast: dict) -> dict:
    log = cast["derivation_log"]
    return {
        "verdict": cast["verdict"],
        "derivation_mode": cast["derivation_mode"],
        "surviving_lenses": cast["cast_size"]["surviving_lenses"],
        "adversaries": cast["cast_size"]["adversaries"],
        "integrator": cast["cast_size"]["integrator"],
        "requirements_unsatisfied": sorted(cast["requirements_unsatisfied"]),
        "cut_echo": sorted(e["concern"] for e in log if e["action"] == "cut_echo"),
        "merged_lenses": sorted(
            e["concern"] for e in log
            if e["action"] == "merge" and e.get("verdict") != "merge_harm_domain"
        ),
        "merged_harm_domains": sorted(
            e["domain"] for e in log if e["action"] == "merge_harm_domain"
        ),
        "separation_is_null": all(
            lens["separation"] is None for lens in cast["lenses"]
        ) if cast["lenses"] else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, type=Path,
                        help="pasta assets/cast-benchmark")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    manifest = json.loads((args.benchmark / "universe-manifest.json").read_text("utf-8"))
    results, failures = [], 0

    for case in manifest["cases"]:
        cid = case["id"]
        brief = json.loads((args.benchmark / "cases" / f"{cid}.json").read_text("utf-8"))
        truth = json.loads((args.benchmark / "truth" / f"{cid}.json").read_text("utf-8"))
        actual = actual_of(derive(brief))

        diffs = {}
        for key in CHECKS:
            if key not in truth:
                continue
            expected = sorted(truth[key]) if isinstance(truth[key], list) else truth[key]
            if actual.get(key) != expected:
                diffs[key] = {"expected": expected, "actual": actual.get(key)}
        for key in ("cut_echo", "merged_lenses", "merged_harm_domains",
                    "separation_is_null"):
            if key in truth:
                expected = sorted(truth[key]) if isinstance(truth[key], list) else truth[key]
                if actual.get(key) != expected:
                    diffs[key] = {"expected": expected, "actual": actual.get(key)}

        passed = not diffs
        failures += 0 if passed else 1
        results.append({"case": cid, "split": case["split"], "pass": passed,
                        "diffs": diffs, "actual": actual})
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {cid} ({case['split']})")
        for key, diff in diffs.items():
            print(f"        {key}: esperado {diff['expected']!r}, obtido {diff['actual']!r}")

    total = len(results)
    accuracy = round((total - failures) / total, 4) if total else 0.0
    print(f"\n{total - failures}/{total} casos conformes — acurácia {accuracy:.0%}")
    print("Amostra pequena e sintética: mede conformidade nestes casos, "
          "não generalização.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "benchmark_id": manifest["benchmark_id"],
            "case_count": total, "passed": total - failures,
            "accuracy": accuracy, "results": results,
            "limits": manifest["limits"],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saída: {args.out}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
