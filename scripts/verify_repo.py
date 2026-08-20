#!/usr/bin/env python3
"""Run the standalone CORDA repository's deterministic acceptance checks."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "gerar-corda"
SCRIPTS = SKILL / "scripts"
PRIVATE_MARKERS = (
    "/Users/af/",
    "VISLO_ESTRATEGIA",
    "Gravitacional/",
)
SCAN_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml"}


def run(label: str, command: list[str]) -> None:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed with exit {completed.returncode}")
    print(f"[PASS] {label}")


def validate_skill_frontmatter() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise RuntimeError("gerar-corda/SKILL.md has invalid frontmatter")
    frontmatter = match.group(1)
    if not re.search(r"^name:\s*gerar-corda\s*$", frontmatter, re.MULTILINE):
        raise RuntimeError("skill name is missing or invalid")
    description = re.search(
        r'^description:\s*"(.+)"\s*$',
        frontmatter,
        re.MULTILINE,
    )
    if not description or len(description.group(1).strip()) < 40:
        raise RuntimeError("skill description must be a quoted informative string")
    print("[PASS] skill frontmatter")


def _is_sealed_or_out_of_scope(path: Path) -> bool:
    """Correcao S-08 (auditoria Codex Sol): gates do nucleo nao atravessam a
    fronteira de materiais selados nem de areas descartaveis. Exclusoes
    executaveis, nao prosa."""
    name = path.name
    parts = path.parts
    if name.startswith("authority-forged-"):
        return True
    if name.startswith("REGISTRO-caveats"):
        return True
    if "_to_delete" in parts:
        return True
    return False


def scan_private_coupling() -> None:
    findings: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path == Path(__file__).resolve()
            or ".git" in path.parts
            or path.suffix.lower() not in SCAN_SUFFIXES
            or _is_sealed_or_out_of_scope(path)
        ):
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for marker in PRIVATE_MARKERS:
            if marker in content:
                findings.append(f"{path.relative_to(ROOT)}: {marker}")
    if findings:
        raise RuntimeError(
            "private/project coupling found:\n" + "\n".join(findings)
        )
    print("[PASS] portability scan")


def verify_bundle_rebuild() -> None:
    """Correcao S-06b (parecer Codex Sol, N-02): o bundle candidato precisa
    fechar por rebuild. Recompila o universo de desenvolvimento a partir da
    fonte, com a raiz de evidencia canonica, e exige igualdade byte a byte dos
    derivados portaveis (universe, EVIDENCE, projection-data). STATE,
    verification e BOOTSTRAP ficam fora: sao mutaveis por scripts sancionados.
    """
    spec = ROOT / "runs" / "v4-development" / "manifest" / "corda-v4-manifest.json"
    build_dir = ROOT / "runs" / "v4-development" / "build"
    if not spec.is_file() or not build_dir.is_dir():
        print("[SKIP] bundle rebuild gate (development universe absent)")
        return
    portable = (
        "corda-v4-universe.json",
        "corda-v4-EVIDENCE.json",
        "corda-v4-projection-data.json",
    )
    with tempfile.TemporaryDirectory(prefix="corda-rebuild-") as tmp:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "build_universe.py"),
                "--spec", str(spec),
                "--out-dir", tmp,
                "--basename", "corda-v4",
                "--evidence-root", str(ROOT),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "bundle rebuild failed: "
                + completed.stderr.strip()[-300:]
            )
        mismatches = []
        for name in portable:
            committed = build_dir / name
            rebuilt = Path(tmp) / name
            if not committed.is_file() or not rebuilt.is_file():
                mismatches.append(f"{name}: missing")
                continue
            if committed.read_bytes() != rebuilt.read_bytes():
                mismatches.append(f"{name}: bytes diverge")
        if mismatches:
            raise RuntimeError(
                "bundle does not close under rebuild (N-02): " + "; ".join(mismatches)
            )
    print("[PASS] bundle rebuild gate")


def main() -> int:
    try:
        validate_skill_frontmatter()
        scan_private_coupling()
        verify_bundle_rebuild()
        with tempfile.TemporaryDirectory(prefix="corda-verify-") as tmp:
            temporary = Path(tmp)
            run(
                "cast benchmark",
                [
                    sys.executable,
                    str(SCRIPTS / "run_cast_benchmark.py"),
                    "--benchmark",
                    str(SKILL / "assets" / "cast-benchmark"),
                ],
            )
            run(
                "compiler conformance",
                [
                    sys.executable,
                    str(SCRIPTS / "run_conformance_benchmark.py"),
                    "--manifest",
                    str(
                        SKILL
                        / "assets"
                        / "conformance-benchmark"
                        / "universe-manifest.json"
                    ),
                    "--baseline-results",
                    str(
                        SKILL
                        / "assets"
                        / "conformance-benchmark"
                        / "baseline-v2.2.1-results.json"
                    ),
                    "--out",
                    str(temporary / "conformance.json"),
                    "--run-id",
                    "standalone-verification",
                    "--observed-at",
                    "2026-07-28",
                ],
            )
            run(
                "unit tests",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(SCRIPTS),
                    "-p",
                    "test_*.py",
                    "-q",
                ],
            )
            result = json.loads(
                (temporary / "conformance.json").read_text(encoding="utf-8")
            )
            if not result.get("all_candidate_cases_pass"):
                raise RuntimeError("candidate conformance cases did not all pass")
        print("CORDA standalone verification: PASS")
        return 0
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"CORDA standalone verification: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
