#!/usr/bin/env python3
"""Render a CORDA/SGM manifest as SVG, PNG and an audit ledger.

The renderer is intentionally deterministic and uses only the Python standard
library plus Pillow for PNG output. The SVG and ledger are still produced when
Pillow is unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import random
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


WIDTH = 2400
HEIGHT = 1500
BG = "#050711"
PANEL = "#0c1222"
PANEL_ALT = "#111a2d"
TEXT = "#f0f5ff"
MUTED = "#9aa9c1"
FAINT = "#52617a"
BLUE = "#2f81f7"
CYAN = "#55d6ff"
VIOLET = "#a78bfa"
GREEN = "#63e6be"
ORANGE = "#ffb454"
RED = "#ff6b7a"


class ManifestError(ValueError):
    pass


def normalize_evidence_text(value: str) -> str:
    """Match the compiler's declared text-hash normalization contract."""
    normalized = (
        unicodedata.normalize("NFC", value)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    return max(low, min(high, number))


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def words(text: Any, limit: int) -> list[str]:
    """Wrap using a character budget suitable for compact visual labels."""
    raw = " ".join(str(text or "").split())
    if not raw:
        return []
    result: list[str] = []
    current = ""
    for word in raw.split():
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                result.append(current)
            current = word
    if current:
        result.append(current)
    return result


def validate_manifest(data: dict[str, Any], *, require_topology: bool = True) -> None:
    required = ("title", "boundary", "integrator", "modes") if require_topology else ("title",)
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ManifestError(f"Missing required field(s): {', '.join(missing)}")
    if "modes" in data and not isinstance(data.get("modes"), list):
        raise ManifestError("'modes' must be a list")
    ids: set[str] = set()
    for index, mode in enumerate(data.get("modes", [])):
        if not isinstance(mode, dict):
            raise ManifestError(f"modes[{index}] must be an object")
        mode_id = mode.get("id")
        if not mode_id:
            raise ManifestError(f"modes[{index}].id is required")
        if mode_id in ids:
            raise ManifestError(f"Duplicate mode id: {mode_id}")
        ids.add(str(mode_id))
        evidence_access = mode.get("evidence_access")
        if evidence_access is not None and not isinstance(evidence_access, list):
            raise ManifestError(f"modes[{index}].evidence_access must be a list")
        evidence_scope = mode.get("evidence_scope")
        if evidence_scope is not None:
            if not isinstance(evidence_scope, dict):
                raise ManifestError(f"modes[{index}].evidence_scope must be an object")
            for field in ("shared", "private", "tools", "prior"):
                value = evidence_scope.get(field)
                if value is not None and not isinstance(value, list):
                    raise ManifestError(
                        f"modes[{index}].evidence_scope.{field} must be a list"
                    )
            source_hashes = evidence_scope.get("source_hashes")
            if source_hashes is not None and not isinstance(source_hashes, dict):
                raise ManifestError(
                    f"modes[{index}].evidence_scope.source_hashes must be an object"
                )
            coverage = evidence_scope.get("coverage")
            if coverage is not None and (
                isinstance(coverage, bool)
                or not isinstance(coverage, (int, float))
                or not 0 <= coverage <= 1
            ):
                raise ManifestError(
                    f"modes[{index}].evidence_scope.coverage must be between 0 and 1"
                )
            shared = {str(value) for value in evidence_scope.get("shared", [])}
            private = {str(value) for value in evidence_scope.get("private", [])}
            if shared & private:
                raise ManifestError(
                    f"modes[{index}].evidence_scope shared/private must not overlap"
                )
    evidence_registry = data.get("evidence_registry")
    if evidence_registry is not None:
        if not isinstance(evidence_registry, list):
            raise ManifestError("'evidence_registry' must be a list")
        evidence_ids: set[str] = set()
        for index, item in enumerate(evidence_registry):
            if not isinstance(item, dict):
                raise ManifestError(f"evidence_registry[{index}] must be an object")
            evidence_id = str(item.get("id", "")).strip()
            if not evidence_id:
                raise ManifestError(f"evidence_registry[{index}].id is required")
            if evidence_id in evidence_ids:
                raise ManifestError(f"Duplicate evidence id: {evidence_id}")
            evidence_ids.add(evidence_id)
            digest = item.get("content_sha256")
            if digest is not None and not re.fullmatch(
                r"[0-9a-fA-F]{64}", str(digest)
            ):
                raise ManifestError(
                    f"evidence_registry[{index}].content_sha256 must be SHA-256"
                )
            if digest is not None and isinstance(item.get("content"), str):
                normalized_content = normalize_evidence_text(item["content"])
                computed = hashlib.sha256(
                    normalized_content.encode("utf-8")
                ).hexdigest()
                if computed != str(digest).lower():
                    raise ManifestError(
                        f"evidence_registry[{index}].content_sha256 does not "
                        "match normalized inline content"
                    )
    runtime = data.get("runtime")
    if runtime is not None:
        if not isinstance(runtime, dict):
            raise ManifestError("'runtime' must be an object")
        execution_topology = runtime.get("execution_topology")
        if execution_topology is not None and execution_topology not in {
            "single_llm_sequential",
            "multi_agent",
            "component_system",
        }:
            raise ManifestError(
                "runtime.execution_topology must be single_llm_sequential, "
                "multi_agent or component_system"
            )
    validation_profiles = data.get("validation_profiles")
    if validation_profiles is not None and not isinstance(validation_profiles, list):
        raise ManifestError("'validation_profiles' must be a list")
    evaluation = data.get("evaluation_contract")
    if evaluation is not None and not isinstance(evaluation, dict):
        raise ManifestError("'evaluation_contract' must be an object")
    integrator = data.get("integrator") or {}
    if integrator and not isinstance(integrator, dict):
        raise ManifestError("'integrator' must be an object")
    integrator_id = str(integrator.get("id", "integrator"))
    valid_ids = ids | {integrator_id, "synthesis", "gate", "owner", "bulk"}
    for index, string in enumerate(data.get("strings", [])):
        if not isinstance(string, dict):
            raise ManifestError(f"strings[{index}] must be an object")
        for end in ("from", "to"):
            endpoint = str(string.get(end, ""))
            if not endpoint:
                raise ManifestError(f"strings[{index}].{end} is required")
            if endpoint not in valid_ids:
                raise ManifestError(
                    f"strings[{index}].{end} references unknown id '{endpoint}'"
                )


def color_for_status(status: str, tension: float = 0.5) -> str:
    status = str(status or "active").lower()
    if status in {"critical", "blocked", "stale"}:
        return RED if tension >= 0.7 else ORANGE
    if status in {"live", "new", "shielded", "protected"}:
        return BLUE
    if status in {"closed", "pass"}:
        return GREEN
    if status in {"archived", "inactive"}:
        return FAINT
    return CYAN


def independence_summary_text(data: dict[str, Any]) -> str:
    summary = data.get("independence_report", {}).get("summary", {})
    if not isinstance(summary, dict) or not summary:
        return "SÍNTESE · convergência não é corroboração"
    correlated = int(summary.get("correlated", 0)) + int(summary.get("weak", 0))
    corroborating = int(summary.get("corroborating", 0))
    unknown = int(summary.get("unknown", 0))
    parts = [f"correlacionados {correlated}", f"corroborantes {corroborating}"]
    if unknown:
        parts.append(f"desconhecidos {unknown}")
    return "INDEPENDÊNCIA · " + " · ".join(parts)


def layout_modes(modes: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    count = len(modes)
    if count == 0:
        return {}
    if count == 1:
        return {str(modes[0]["id"]): (1200.0, 800.0)}
    if count == 2:
        return {
            str(modes[0]["id"]): (650.0, 800.0),
            str(modes[1]["id"]): (1750.0, 800.0),
        }
    radius_x = 890 if count <= 8 else 920
    radius_y = 275 if count <= 8 else 300
    center_x, center_y = 1200.0, 850.0
    offset = math.radians(22.5 if count == 8 else 360.0 / max(count * 2, 1))
    positions: dict[str, tuple[float, float]] = {}
    for index, mode in enumerate(modes):
        angle = offset + (2 * math.pi * index / count)
        positions[str(mode["id"])] = (
            center_x + radius_x * math.cos(angle),
            center_y + radius_y * math.sin(angle),
        )
    return positions


def cubic_points(
    start: tuple[float, float],
    end: tuple[float, float],
    bend: float,
    steps: int = 48,
) -> list[tuple[float, float]]:
    x1, y1 = start
    x4, y4 = end
    dx, dy = x4 - x1, y4 - y1
    length = max(math.hypot(dx, dy), 1.0)
    nx, ny = -dy / length, dx / length
    c1 = (x1 + dx * 0.32 + nx * bend, y1 + dy * 0.32 + ny * bend)
    c2 = (x1 + dx * 0.68 - nx * bend, y1 + dy * 0.68 - ny * bend)
    pts: list[tuple[float, float]] = []
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        x = u**3 * x1 + 3 * u**2 * t * c1[0] + 3 * u * t**2 * c2[0] + t**3 * x4
        y = u**3 * y1 + 3 * u**2 * t * c1[1] + 3 * u * t**2 * c2[1] + t**3 * y4
        pts.append((x, y))
    return pts


def svg_text(
    x: float,
    y: float,
    text: Any,
    *,
    size: int,
    fill: str = TEXT,
    weight: int = 500,
    anchor: str = "middle",
    max_chars: int = 30,
    line_height: float = 1.22,
    italic: bool = False,
) -> str:
    lines = words(text, max_chars)
    if not lines:
        return ""
    attrs = (
        f'x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'fill="{fill}" font-size="{size}" font-weight="{weight}"'
    )
    if italic:
        attrs += ' font-style="italic"'
    tspans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else f"{line_height:.2f}em"
        tspans.append(f'<tspan x="{x:.1f}" dy="{dy}">{esc(line)}</tspan>')
    return f"<text {attrs}>{''.join(tspans)}</text>"


def svg_panel(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    stroke: str,
    fill: str = PANEL,
    stroke_width: float = 2.0,
    radius: float = 24,
    glow: bool = False,
) -> str:
    filter_attr = ' filter="url(#glow)"' if glow else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{filter_attr}/>'
    )


def svg_path_for_points(points: Iterable[tuple[float, float]]) -> str:
    values = list(points)
    if not values:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in values)


def render_svg(data: dict[str, Any], output: Path) -> None:
    modes = data.get("modes", [])
    positions = layout_modes(modes)
    shielded = set(data.get("shielding", {}).get("mode_ids", []))
    strings = data.get("strings", [])
    mode_by_id = {str(mode["id"]): mode for mode in modes}
    integrator = data["integrator"]
    integrator_id = str(integrator.get("id", "integrator"))
    synthesis = data.get("synthesis", {})
    gate = data.get("gate", {})
    boundary = data.get("boundary", {})
    axes = data.get("axes", {})

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<defs>",
        '<radialGradient id="bulk" cx="50%" cy="45%" r="75%">'
        f'<stop offset="0%" stop-color="#16233d"/><stop offset="45%" stop-color="{BG}"/>'
        '<stop offset="100%" stop-color="#02030a"/></radialGradient>',
        '<linearGradient id="brane" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#1b2a48"/><stop offset="50%" stop-color="#0c1222"/>'
        '<stop offset="100%" stop-color="#11122b"/></linearGradient>',
        '<filter id="glow" x="-70%" y="-70%" width="240%" height="240%">'
        '<feGaussianBlur stdDeviation="9" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="4" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        f'<path d="M0,0 L10,4 L0,8 Z" fill="{CYAN}"/></marker>',
        "</defs>",
        '<rect width="100%" height="100%" fill="url(#bulk)"/>',
    ]

    seed = int(hashlib.sha256(str(data.get("title", "")).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    for _ in range(125):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        r = rng.choice((0.7, 0.9, 1.2, 1.6))
        opacity = rng.uniform(0.12, 0.4)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#8fb7ff" opacity="{opacity:.2f}"/>')

    parts.extend(
        [
            svg_text(1200, 64, f"CORDA — {data['title']}", size=42, weight=760, max_chars=70),
            svg_text(1200, 105, data.get("subtitle", ""), size=18, fill=MUTED, max_chars=110),
            '<ellipse cx="1200" cy="850" rx="970" ry="340" fill="none" '
            f'stroke="{VIOLET}" stroke-width="1.5" opacity="0.24" stroke-dasharray="9 14"/>',
            '<ellipse cx="1200" cy="850" rx="760" ry="250" fill="none" '
            f'stroke="{CYAN}" stroke-width="1.2" opacity="0.18"/>',
        ]
    )

    axis_labels = [
        ("X", axes.get("x", "Operação"), 1640, 430, BLUE),
        ("Y", axes.get("y", "Valor/Ambiente"), 1510, 500, GREEN),
        ("Z", axes.get("z", "Governança"), 760, 500, VIOLET),
        ("W", axes.get("w", "Cognição"), 1200, 300, CYAN),
    ]
    for axis, label, x, y, color in axis_labels:
        parts.append(
            f'<line x1="1200" y1="430" x2="{x}" y2="{y}" stroke="{color}" '
            f'stroke-width="2" opacity="0.45" marker-end="url(#arrow)"/>'
        )
        parts.append(svg_text(x, y - 10, f"{axis} · {label}", size=16, fill=color, weight=650, max_chars=32))

    inputs = data.get("inputs", [])[:4]
    if inputs:
        card_width = min(520, (WIDTH - 220) / len(inputs) - 24)
        gap = (WIDTH - 2 * 110 - len(inputs) * card_width) / max(len(inputs) - 1, 1)
        for index, item in enumerate(inputs):
            x = 110 + index * (card_width + gap)
            status = item.get("status", "normal")
            color = color_for_status(status, 0.8 if status == "critical" else 0.5)
            parts.append(svg_panel(x, 135, card_width, 135, stroke=color, glow=status in {"live", "critical"}))
            parts.append(svg_text(x + 28, 177, item.get("label", "Entrada"), size=24, fill=color, weight=720, anchor="start", max_chars=25))
            parts.append(svg_text(x + 28, 216, item.get("detail", ""), size=16, fill=MUTED, anchor="start", max_chars=max(18, int(card_width / 13))))
            parts.append(
                f'<path d="M {x + card_width / 2:.1f},270 C {x + card_width / 2:.1f},315 '
                f'1200,315 1200,340" fill="none" stroke="{color}" stroke-width="2" '
                f'opacity="0.35" stroke-dasharray="7 10"/>'
            )

    parts.append(svg_panel(900, 340, 600, 165, stroke=CYAN, fill="url(#brane)", stroke_width=2.5, glow=True))
    parts.append('<ellipse cx="1200" cy="422" rx="270" ry="105" fill="none" '
                 f'stroke="{CYAN}" stroke-width="4" opacity="0.42" filter="url(#softGlow)"/>')
    parts.append('<ellipse cx="1200" cy="422" rx="225" ry="72" fill="none" '
                 f'stroke="{VIOLET}" stroke-width="2" opacity="0.42" stroke-dasharray="10 12"/>')
    parts.append(svg_text(1200, 397, integrator.get("label", "Integração"), size=31, weight=760, max_chars=33))
    parts.append(svg_text(1200, 441, integrator.get("role", ""), size=17, fill=MUTED, max_chars=52))
    parts.append(svg_text(1200, 482, "POÇO COGNITIVO · loop fechado W", size=13, fill=CYAN, weight=650, max_chars=50))

    synthesis_center = (1200.0, 850.0)
    endpoint_positions: dict[str, tuple[float, float]] = dict(positions)
    endpoint_positions[integrator_id] = (1200.0, 505.0)
    endpoint_positions["synthesis"] = synthesis_center
    endpoint_positions["gate"] = (1200.0, 1260.0)
    endpoint_positions["owner"] = (1200.0, 1460.0)

    if not strings:
        strings = [
            {"from": str(mode["id"]), "to": "synthesis", "kind": "projection", "tension": 0.5}
            for mode in modes
        ]
    for index, string in enumerate(strings):
        start = endpoint_positions.get(str(string.get("from")))
        end = endpoint_positions.get(str(string.get("to")))
        if not start or not end:
            continue
        tension = clamp(string.get("tension", 0.5))
        state = str(string.get("state", "active"))
        color = color_for_status(state, tension)
        bend = (1 if index % 2 == 0 else -1) * (28 + 34 * tension)
        path = svg_path_for_points(cubic_points(start, end, bend))
        width = 1.5 + tension * 5.0
        dash = ' stroke-dasharray="11 10"' if string.get("kind") in {"evidence", "gate"} else ""
        parts.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width:.1f}" '
            f'opacity="0.48" stroke-linecap="round"{dash} filter="url(#softGlow)"/>'
        )

    for mode in modes:
        mode_id = str(mode["id"])
        x, y = positions[mode_id]
        status = str(mode.get("status", "active"))
        protected = mode_id in shielded or status == "shielded"
        color = BLUE if protected else color_for_status(status)
        mass = clamp(mode.get("mass", 0.5))
        card_w, card_h = 340.0, 140.0
        if protected:
            parts.append(
                f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="204" ry="102" fill="none" '
                f'stroke="{BLUE}" stroke-width="8" opacity="0.22" filter="url(#glow)"/>'
            )
        parts.append(svg_panel(x - card_w / 2, y - card_h / 2, card_w, card_h, stroke=color, stroke_width=2.2 + mass * 2, glow=protected))
        parts.append(
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{150 + mass * 22:.1f}" ry="58" '
            f'fill="none" stroke="{VIOLET}" stroke-width="2" opacity="0.62" '
            f'stroke-dasharray="8 9" transform="rotate(-8 {x:.1f} {y:.1f})"/>'
        )
        parts.append(svg_text(x, y - 27, mode.get("label", mode_id), size=24, fill=color, weight=750, max_chars=21))
        parts.append(svg_text(x, y + 9, mode.get("role", ""), size=15, fill=TEXT, max_chars=34))
        confidence = clamp(mode.get("loop", {}).get("confidence", 0.5))
        parts.append(svg_text(x, y + 55, f"↻ W · confiança {confidence:.0%}", size=12, fill=VIOLET, weight=640, max_chars=30))

    parts.append(svg_panel(920, 755, 560, 190, stroke=VIOLET, fill="url(#brane)", stroke_width=3.0, glow=True))
    parts.append('<ellipse cx="1200" cy="850" rx="245" ry="118" fill="none" '
                 f'stroke="{VIOLET}" stroke-width="5" opacity="0.36" filter="url(#glow)"/>')
    parts.append(svg_text(1200, 815, synthesis.get("label", "Mesa de síntese"), size=28, weight=760, max_chars=34))
    parts.append(svg_text(1200, 859, synthesis.get("operator", "Convergências · conflitos · causalidade"), size=16, fill=MUTED, max_chars=48))
    summary_text = independence_summary_text(data)
    summary_color = RED if "correlacionados 0" not in summary_text else VIOLET
    parts.append(svg_text(1200, 914, summary_text, size=12, fill=summary_color, weight=650, max_chars=62))

    parts.append(
        f'<path d="M1200,945 C1200,1050 1200,1100 1200,1190" fill="none" '
        f'stroke="{ORANGE}" stroke-width="4" opacity="0.68" stroke-dasharray="13 10" '
        'filter="url(#softGlow)"/>'
    )
    parts.append(
        f'<ellipse cx="1200" cy="1278" rx="365" ry="104" fill="#080914" stroke="{ORANGE}" '
        'stroke-width="4" opacity="0.96" filter="url(#softGlow)"/>'
    )
    parts.append('<ellipse cx="1200" cy="1278" rx="410" ry="125" fill="none" '
                 f'stroke="{RED}" stroke-width="2" opacity="0.35" stroke-dasharray="14 12"/>')
    parts.append(svg_text(1200, 1253, gate.get("label", "Gate adversarial"), size=27, fill=ORANGE, weight=760, max_chars=34))
    tests = " · ".join(gate.get("tests", ["evidência", "autoridade", "coerência"]))
    parts.append(svg_text(1200, 1296, tests, size=15, fill=MUTED, max_chars=70))
    outcomes = " / ".join(gate.get("outcomes", ["pass", "fail", "escalate"]))
    parts.append(svg_text(1200, 1338, outcomes.upper(), size=12, fill=RED, weight=650, max_chars=70))

    owner = boundary.get("human_owner", "Owner humano")
    decision = boundary.get("decision", "Aceitar, rejeitar ou alterar")
    parts.append(svg_panel(680, 1410, 1040, 65, stroke=BLUE, fill="#081223", stroke_width=3, radius=18, glow=True))
    parts.append(svg_text(1200, 1444, f"CONDIÇÃO DE CONTORNO · {owner} · {decision}", size=18, fill=BLUE, weight=700, max_chars=100))

    archived = data.get("archived", [])
    if archived:
        parts.append('<circle cx="205" cy="1290" r="74" fill="#02030a" stroke="#344158" stroke-width="3"/>')
        parts.append('<circle cx="205" cy="1290" r="48" fill="#000" stroke="#1d2636" stroke-width="2"/>')
        parts.append(svg_text(205, 1268, "SINGULARIDADE", size=12, fill=FAINT, weight=650, max_chars=22))
        parts.append(svg_text(205, 1303, " · ".join(map(str, archived)), size=14, fill=MUTED, max_chars=28))

    entropy = data.get("entropy", {})
    if entropy:
        threshold = entropy.get("threshold_days", "?")
        parts.append(svg_panel(1830, 1200, 440, 145, stroke=RED, fill="#160c14", stroke_width=2.5, radius=20, glow=True))
        parts.append(svg_text(2050, 1240, f"ENTROPIA · >{threshold}d", size=21, fill=RED, weight=760, max_chars=30))
        parts.append(svg_text(2050, 1278, entropy.get("rule", ""), size=14, fill=MUTED, max_chars=43))
        items = " · ".join(map(str, entropy.get("items", [])[:3]))
        parts.append(svg_text(2050, 1320, items, size=12, fill=ORANGE, max_chars=48))

    shielding = data.get("shielding", {})
    if shielding:
        parts.append(svg_text(210, 1412, f"BLINDAGEM · {shielding.get('label', '')}", size=14, fill=BLUE, weight=700, anchor="start", max_chars=36))
        parts.append(svg_text(210, 1441, shielding.get("rule", ""), size=12, fill=MUTED, anchor="start", max_chars=55))

    parts.append(svg_text(2265, 1462, "projeção 2D de um campo 4D · SGM", size=12, fill=FAINT, anchor="end", italic=True, max_chars=48))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        return None
    return Image, ImageDraw, ImageFilter, ImageFont


def font_factory(ImageFont):
    regular_candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def get(size: int, bold: bool = False):
        for candidate in bold_candidates if bold else regular_candidates:
            if Path(candidate).exists():
                try:
                    return ImageFont.truetype(candidate, size)
                except OSError:
                    continue
        return ImageFont.load_default()

    return get


def hex_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def render_png(data: dict[str, Any], output: Path) -> bool:
    pillow = load_pillow()
    if pillow is None:
        return False
    Image, ImageDraw, ImageFilter, ImageFont = pillow
    font = font_factory(ImageFont)
    image = Image.new("RGB", (WIDTH, HEIGHT), hex_rgb(BG))
    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        t = y / HEIGHT
        base = (
            int(5 + 8 * (1 - abs(t - 0.45))),
            int(7 + 14 * (1 - abs(t - 0.45))),
            int(17 + 25 * (1 - abs(t - 0.45))),
        )
        draw.line([(0, y), (WIDTH, y)], fill=base)

    seed = int(hashlib.sha256(str(data.get("title", "")).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    for _ in range(140):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        c = rng.randrange(70, 145)
        draw.ellipse((x, y, x + 2, y + 2), fill=(c, c + 20, min(c + 60, 255)))

    def text_center(
        xy: tuple[float, float],
        value: Any,
        *,
        size: int,
        color: str = TEXT,
        bold: bool = False,
        max_chars: int = 30,
        spacing: int = 5,
    ) -> None:
        lines = words(value, max_chars)
        if not lines:
            return
        fnt = font(size, bold)
        line_boxes = [draw.textbbox((0, 0), line, font=fnt) for line in lines]
        heights = [box[3] - box[1] for box in line_boxes]
        total_height = sum(heights) + spacing * (len(lines) - 1)
        y = xy[1] - total_height / 2
        for line, box, height in zip(lines, line_boxes, heights):
            width = box[2] - box[0]
            draw.text((xy[0] - width / 2, y), line, font=fnt, fill=hex_rgb(color))
            y += height + spacing

    def panel(
        box: tuple[float, float, float, float],
        *,
        stroke: str,
        fill: str = PANEL,
        width: int = 3,
        radius: int = 24,
        glow: bool = False,
    ) -> None:
        if glow:
            glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            gd.rounded_rectangle(box, radius=radius, outline=hex_rgb(stroke) + (170,), width=max(width * 3, 8))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(14))
            image.paste(glow_layer, (0, 0), glow_layer)
        draw.rounded_rectangle(box, radius=radius, fill=hex_rgb(fill), outline=hex_rgb(stroke), width=width)

    def glow_line(points: list[tuple[float, float]], color: str, width: int, dashed: bool = False) -> None:
        if dashed:
            segments = []
            for index in range(0, len(points) - 1, 6):
                segments.append(points[index : min(index + 4, len(points))])
        else:
            segments = [points]
        glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        for segment in segments:
            if len(segment) > 1:
                gd.line(segment, fill=hex_rgb(color) + (110,), width=width + 7, joint="curve")
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8))
        image.paste(glow_layer, (0, 0), glow_layer)
        for segment in segments:
            if len(segment) > 1:
                draw.line(segment, fill=hex_rgb(color), width=width, joint="curve")

    text_center((1200, 62), f"CORDA — {data['title']}", size=42, bold=True, max_chars=70)
    text_center((1200, 105), data.get("subtitle", ""), size=18, color=MUTED, max_chars=110)
    draw.ellipse((230, 510, 2170, 1190), outline=hex_rgb(VIOLET), width=2)
    draw.ellipse((440, 600, 1960, 1100), outline=hex_rgb(CYAN), width=1)

    axes = data.get("axes", {})
    axis_labels = [
        ("X", axes.get("x", "Operação"), (1640, 430), BLUE),
        ("Y", axes.get("y", "Valor/Ambiente"), (1510, 500), GREEN),
        ("Z", axes.get("z", "Governança"), (760, 500), VIOLET),
        ("W", axes.get("w", "Cognição"), (1200, 300), CYAN),
    ]
    for axis, label, endpoint, color in axis_labels:
        draw.line([(1200, 430), endpoint], fill=hex_rgb(color), width=2)
        text_center((endpoint[0], endpoint[1] - 16), f"{axis} · {label}", size=16, color=color, bold=True, max_chars=32)

    inputs = data.get("inputs", [])[:4]
    if inputs:
        card_width = min(520, (WIDTH - 220) / len(inputs) - 24)
        gap = (WIDTH - 220 - len(inputs) * card_width) / max(len(inputs) - 1, 1)
        for index, item in enumerate(inputs):
            x = 110 + index * (card_width + gap)
            status = item.get("status", "normal")
            color = color_for_status(status, 0.8 if status == "critical" else 0.5)
            panel((x, 135, x + card_width, 270), stroke=color, glow=status in {"live", "critical"})
            text_center((x + card_width / 2, 177), item.get("label", "Entrada"), size=23, color=color, bold=True, max_chars=26)
            text_center((x + card_width / 2, 224), item.get("detail", ""), size=15, color=MUTED, max_chars=max(18, int(card_width / 13)))
            glow_line(cubic_points((x + card_width / 2, 270), (1200, 340), 10), color, 2, dashed=True)

    panel((900, 340, 1500, 505), stroke=CYAN, fill=PANEL_ALT, width=3, glow=True)
    draw.ellipse((930, 317, 1470, 527), outline=hex_rgb(CYAN), width=4)
    draw.ellipse((975, 350, 1425, 494), outline=hex_rgb(VIOLET), width=2)
    integrator = data["integrator"]
    text_center((1200, 395), integrator.get("label", "Integração"), size=31, bold=True, max_chars=33)
    text_center((1200, 442), integrator.get("role", ""), size=17, color=MUTED, max_chars=54)
    text_center((1200, 485), "POÇO COGNITIVO · loop fechado W", size=13, color=CYAN, bold=True, max_chars=52)

    modes = data.get("modes", [])
    positions = layout_modes(modes)
    shielded = set(data.get("shielding", {}).get("mode_ids", []))
    endpoint_positions = dict(positions)
    integrator_id = str(integrator.get("id", "integrator"))
    endpoint_positions[integrator_id] = (1200.0, 505.0)
    endpoint_positions["synthesis"] = (1200.0, 850.0)
    endpoint_positions["gate"] = (1200.0, 1260.0)
    endpoint_positions["owner"] = (1200.0, 1460.0)

    strings = data.get("strings", [])
    if not strings:
        strings = [
            {"from": str(mode["id"]), "to": "synthesis", "kind": "projection", "tension": 0.5}
            for mode in modes
        ]
    for index, string in enumerate(strings):
        start = endpoint_positions.get(str(string.get("from")))
        end = endpoint_positions.get(str(string.get("to")))
        if not start or not end:
            continue
        tension = clamp(string.get("tension", 0.5))
        state = str(string.get("state", "active"))
        color = color_for_status(state, tension)
        bend = (1 if index % 2 == 0 else -1) * (28 + 34 * tension)
        glow_line(
            cubic_points(start, end, bend),
            color,
            max(2, int(2 + tension * 4)),
            dashed=string.get("kind") in {"evidence", "gate"},
        )

    for mode in modes:
        mode_id = str(mode["id"])
        x, y = positions[mode_id]
        status = str(mode.get("status", "active"))
        protected = mode_id in shielded or status == "shielded"
        color = BLUE if protected else color_for_status(status)
        mass = clamp(mode.get("mass", 0.5))
        if protected:
            glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            gd.ellipse((x - 205, y - 105, x + 205, y + 105), outline=hex_rgb(BLUE) + (180,), width=10)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(13))
            image.paste(glow_layer, (0, 0), glow_layer)
        panel((x - 170, y - 70, x + 170, y + 70), stroke=color, width=int(2 + mass * 3), glow=protected)
        draw.ellipse((x - 160, y - 58, x + 160, y + 58), outline=hex_rgb(VIOLET), width=2)
        text_center((x, y - 26), mode.get("label", mode_id), size=23, color=color, bold=True, max_chars=21)
        text_center((x, y + 8), mode.get("role", ""), size=15, max_chars=34)
        confidence = clamp(mode.get("loop", {}).get("confidence", 0.5))
        text_center((x, y + 51), f"↻ W · confiança {confidence:.0%}", size=12, color=VIOLET, bold=True, max_chars=30)

    synthesis = data.get("synthesis", {})
    panel((920, 755, 1480, 945), stroke=VIOLET, fill=PANEL_ALT, width=3, glow=True)
    draw.ellipse((955, 732, 1445, 968), outline=hex_rgb(VIOLET), width=4)
    text_center((1200, 812), synthesis.get("label", "Mesa de síntese"), size=28, bold=True, max_chars=34)
    text_center((1200, 858), synthesis.get("operator", "Convergências · conflitos · causalidade"), size=16, color=MUTED, max_chars=48)
    summary_text = independence_summary_text(data)
    summary_color = RED if "correlacionados 0" not in summary_text else VIOLET
    text_center((1200, 917), summary_text, size=12, color=summary_color, bold=True, max_chars=62)

    glow_line(cubic_points((1200, 945), (1200, 1190), 18), ORANGE, 4, dashed=True)
    draw.ellipse((835, 1174, 1565, 1382), fill=hex_rgb("#080914"), outline=hex_rgb(ORANGE), width=4)
    draw.ellipse((790, 1153, 1610, 1403), outline=hex_rgb(RED), width=2)
    gate = data.get("gate", {})
    text_center((1200, 1252), gate.get("label", "Gate adversarial"), size=27, color=ORANGE, bold=True, max_chars=34)
    text_center((1200, 1297), " · ".join(gate.get("tests", ["evidência", "autoridade", "coerência"])), size=15, color=MUTED, max_chars=70)
    text_center((1200, 1340), " / ".join(gate.get("outcomes", ["pass", "fail", "escalate"])).upper(), size=12, color=RED, bold=True, max_chars=70)

    boundary = data.get("boundary", {})
    panel((680, 1410, 1720, 1475), stroke=BLUE, fill="#081223", width=3, radius=18, glow=True)
    text_center(
        (1200, 1443),
        f"CONDIÇÃO DE CONTORNO · {boundary.get('human_owner', 'Owner humano')} · "
        f"{boundary.get('decision', 'Aceitar, rejeitar ou alterar')}",
        size=18,
        color=BLUE,
        bold=True,
        max_chars=100,
    )

    archived = data.get("archived", [])
    if archived:
        draw.ellipse((131, 1216, 279, 1364), fill=(0, 0, 0), outline=hex_rgb(FAINT), width=3)
        draw.ellipse((157, 1242, 253, 1338), fill=(0, 0, 0), outline=(30, 40, 56), width=2)
        text_center((205, 1265), "SINGULARIDADE", size=12, color=FAINT, bold=True, max_chars=22)
        text_center((205, 1308), " · ".join(map(str, archived)), size=14, color=MUTED, max_chars=28)

    entropy = data.get("entropy", {})
    if entropy:
        panel((1830, 1200, 2270, 1345), stroke=RED, fill="#160c14", width=3, glow=True)
        text_center((2050, 1240), f"ENTROPIA · >{entropy.get('threshold_days', '?')}d", size=21, color=RED, bold=True, max_chars=30)
        text_center((2050, 1280), entropy.get("rule", ""), size=14, color=MUTED, max_chars=43)
        text_center((2050, 1321), " · ".join(map(str, entropy.get("items", [])[:3])), size=12, color=ORANGE, max_chars=48)

    shielding = data.get("shielding", {})
    if shielding:
        draw.text((210, 1390), f"BLINDAGEM · {shielding.get('label', '')}", font=font(14, True), fill=hex_rgb(BLUE))
        draw.text((210, 1424), " ".join(words(shielding.get("rule", ""), 55)[:1]), font=font(12), fill=hex_rgb(MUTED))

    footer = "projeção 2D de um campo 4D · SGM"
    footer_font = font(12)
    box = draw.textbbox((0, 0), footer, font=footer_font)
    draw.text((2265 - (box[2] - box[0]), 1452), footer, font=footer_font, fill=hex_rgb(FAINT))

    image.save(output, "PNG", optimize=True)
    return True


def ledger_section(title: str, items: Iterable[Any]) -> str:
    material = list(items)
    lines = [f"## {title}", ""]
    if not material:
        lines.extend(["- Nenhum item registrado.", ""])
        return "\n".join(lines)
    for item in material:
        if isinstance(item, dict):
            label = item.get("label") or item.get("id") or json.dumps(item, ensure_ascii=False)
            source = item.get("source_ref") or item.get("evidence_type") or "fonte não indicada"
            lines.append(f"- {label} — `{source}`")
        else:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_ledger(data: dict[str, Any], output: Path, svg_path: Path, png_path: Path | None) -> None:
    source = data.get("source", {})
    boundary = data.get("boundary", {})
    lines = [
        f"# Ledger da CORDA — {data.get('title', '')}",
        "",
        "## Proveniência",
        "",
        f"- Tipo: `{source.get('kind', 'unknown')}`",
        f"- Origem: `{source.get('path', 'não indicada')}`",
        f"- Observado em: `{source.get('observed_at', 'não indicado')}`",
        f"- Bulk: {boundary.get('bulk', 'não indicado')}",
        f"- Owner humano: {boundary.get('human_owner', 'não indicado')}",
        f"- Decisão suportada: {boundary.get('decision', 'não indicada')}",
        "",
        "## Compilador (A-02: carimbo)",
        "",
        f"- Versão: `{data.get('compiler', {}).get('version', 'não carimbada')}`",
        f"- build_universe sha256: `{str(data.get('compiler', {}).get('build_universe_sha256', 'n/a'))[:16]}…`",
        f"- derive_cast sha256: `{str(data.get('compiler', {}).get('derive_cast_sha256', 'n/a'))[:16]}…`",
        f"- render_corda sha256: `{str(data.get('compiler', {}).get('render_corda_sha256', 'n/a'))[:16]}…`",
        "",
        "## Saídas",
        "",
        # Correcao S-09 (auditoria Codex Sol): caminhos relativos ao diretorio
        # de saida — o ledger deixa de depender da localizacao absoluta.
        f"- SVG: `{svg_path.name}`",
    ]
    if png_path:
        lines.append(f"- PNG: `{png_path.name}`")
    else:
        lines.append("- PNG: não gerado (Pillow indisponível)")
    lines.append("")
    lines.append(ledger_section("Entradas mapeadas", data.get("inputs", [])))
    lines.append(ledger_section("Modos/branas", data.get("modes", [])))
    lines.append(ledger_section("Cordas abertas", data.get("strings", [])))
    lines.append(ledger_section("Suposições explícitas", data.get("assumptions", [])))
    lines.append(ledger_section("Não mapeado ou ilegível", data.get("unmapped", [])))
    lines.append(
        ledger_section(
            "Exigências não satisfeitas",
            data.get("requirements_unsatisfied", []),
        )
    )
    lines.extend(
        [
            "## Estado de verificação",
            "",
            "- `schema_validation`: `pass` para o manifesto compilado.",
            "- `invariant_validation`: consultar o arquivo `verification.json`.",
            "- `semantic_review`: `not_performed` até registro de revisor e data.",
            f"- `visual_review`: `not_performed`; PNG {'presente' if png_path else 'não gerado'}.",
            "",
            "> A CORDA é uma projeção operacional. A linguagem de física é um formalismo de",
            "> modelagem e não uma afirmação científica sobre o sistema observado.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a CORDA/SGM manifest.")
    parser.add_argument("--spec", required=True, type=Path, help="Input JSON manifest")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    parser.add_argument("--basename", default="corda", help="Output base name")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.spec.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ManifestError("The manifest root must be an object")
        validate_manifest(data)
    except (OSError, json.JSONDecodeError, ManifestError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = args.out_dir / f"{args.basename}.svg"
    png_path = args.out_dir / f"{args.basename}.png"
    ledger_path = args.out_dir / f"{args.basename}-ledger.md"
    render_svg(data, svg_path)
    png_written = render_png(data, png_path)
    render_ledger(data, ledger_path, svg_path, png_path if png_written else None)

    print(f"SVG: {svg_path}")
    if png_written:
        print(f"PNG: {png_path}")
    else:
        print("PNG: skipped (Pillow unavailable)")
    print(f"Ledger: {ledger_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
