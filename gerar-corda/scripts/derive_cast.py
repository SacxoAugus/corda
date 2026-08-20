#!/usr/bin/env python3
"""Deriva o elenco de um universo CORDA a partir do assunto e da evidência.

Etapa aditiva, executada ANTES do compilador. Não substitui build_universe.py:
emite o contrato de elenco e o esqueleto de manifesto que ele consome.

Lei central: o número de agentes não se escolhe. É o número de subespaços de
evidência separáveis, mais os papéis exigidos pela topologia. Duas lentes com a
mesma evidência são a mesma lente. Lente sem evidência própria é eco do briefing.

Uso:
    python3 derive_cast.py --brief assunto.json --out-dir saida/ [--basename nome]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "corda-cast/1.0"

# Uma lente estreita deixa muito por explicar: o resíduo dela vale um loop.
# Uma lente que vê quase tudo tem resíduo vazio: o loop seria redundante.
RESIDUAL_SEPARATION_THRESHOLD = 0.34

ADVERSARY_POWERS = ("parecer", "veto", "escalonamento")


# --------------------------------------------------------------------------
# utilidades


def as_set(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {value}
    return {str(item) for item in value if str(item).strip()}


def scope_of(concern: dict[str, Any]) -> dict[str, set[str]]:
    scope = concern.get("evidence_scope") or {}
    return {
        "shared": as_set(scope.get("shared")),
        "private": as_set(scope.get("private")),
        "tools": as_set(scope.get("tools")),
        "prior": as_set(scope.get("prior")),
    }


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


# --------------------------------------------------------------------------
# 1. fusão de lentes correlacionadas


def relation(a: dict[str, Any], b: dict[str, Any]) -> tuple[str, str]:
    """Classifica duas lentes candidatas pela topologia de evidência.

    Mesma lógica de `compare_observers`: identidade de evidência governa. Aqui
    ela roda ao contrário — não para medir corroboração, mas para descobrir que
    duas lentes propostas são a mesma.
    """
    sa, sb = scope_of(a), scope_of(b)
    pa, pb = sa["private"], sb["private"]
    ta, tb = sa["tools"], sb["tools"]

    if not pa and not ta and not pb and not tb:
        return "duplicate_echo", "nenhuma das duas tem evidência ou ferramenta própria"
    if pa == pb and ta == tb:
        return "same_lens", "evidência privada e ferramentas idênticas"
    if pa and pb and (pa <= pb or pb <= pa) and not (ta - tb) and not (tb - ta):
        return "same_lens", "evidência privada contida; nenhuma observação exclusiva"

    exclusive_a = (pa | ta) - (pb | tb)
    exclusive_b = (pb | tb) - (pa | ta)
    if not exclusive_a or not exclusive_b:
        return "subsumed", "uma das lentes não observa nada que a outra não observe"
    return "separable", "cada lente observa algo que a outra não observa"


def provisional_key(concern: dict[str, Any]) -> str:
    """Assinatura de separabilidade quando ainda não existe corpus.

    Sem evidência, separação real não é observável. O melhor substituto honesto
    é o observável declarado: duas preocupações que fazem a mesma pergunta sobre
    o mesmo domínio são a mesma lente, mesmo que tenham nomes diferentes.
    """
    domain = str(concern.get("domain") or concern.get("label") or "").strip().lower()
    question = str(concern.get("question") or "").strip().lower()
    return f"{domain}||{question}"


def merge_concerns(
    concerns: list[dict[str, Any]], *, provisional: bool = False
) -> tuple[list[dict], list[dict]]:
    """Funde lentes que a evidência não distingue. Retorna (sobreviventes, log).

    Em modo provisório (cold start) a ausência de evidência privada não é motivo
    de corte: ainda não há corpus onde ela pudesse existir. Cortar aqui apagaria
    o elenco inteiro de qualquer projeto que esteja começando.
    """
    # Correção S-01 (auditoria Codex Sol, 2026-07-29): a fusão deixa de ser um
    # passe guloso dependente da ordem e vira um FECHAMENTO por componentes
    # conexos da relação de fusão. A partição resultante é invariante à
    # permutação da entrada; o representante de cada componente é derivado do
    # conteúdo (maior escopo original; empate → menor id lexicográfico), nunca
    # da posição. Transitividade: a~c e b~c fundem {a,b,c} mesmo que a e b não
    # se relacionem diretamente — é o "reavaliar após ampliar o escopo" feito
    # de forma definida.
    log: list[dict[str, Any]] = []

    candidates: list[dict[str, Any]] = []
    for concern in concerns:
        if provisional:
            entry = json.loads(json.dumps(concern))
            entry["provisional"] = True
            entry["evidence_type"] = "hypothesis"
            candidates.append(entry)
            continue
        scope = scope_of(concern)
        if not scope["private"] and not scope["tools"]:
            log.append({
                "action": "cut_echo",
                "concern": concern.get("id"),
                "label": concern.get("label"),
                "reason": (
                    "sem evidência privada e sem ferramenta: não é lente, é eco do "
                    "briefing. Convocá-la produz uma cópia do enquadramento."
                ),
            })
            continue
        candidates.append(json.loads(json.dumps(concern)))

    def mergeable(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, str, str]:
        if provisional:
            if provisional_key(a) == provisional_key(b):
                return True, "same_observable", "mesmo domínio e mesma pergunta declarada"
            return False, "", ""
        verdict, why = relation(a, b)
        if verdict in {"same_lens", "subsumed", "duplicate_echo"}:
            return True, verdict, why
        verdict, why = relation(b, a)
        if verdict in {"same_lens", "subsumed", "duplicate_echo"}:
            return True, verdict, why
        return False, "", ""

    count = len(candidates)
    parent = list(range(count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[max(root_left, root_right)] = min(root_left, root_right)

    edge_reason: dict[frozenset[int], tuple[str, str]] = {}
    for i in range(count):
        for j in range(i + 1, count):
            merged, verdict, why = mergeable(candidates[i], candidates[j])
            if merged:
                union(i, j)
                edge_reason[frozenset((i, j))] = (verdict, why)

    components: dict[int, list[int]] = {}
    for index in range(count):
        components.setdefault(find(index), []).append(index)

    def scope_weight(index: int) -> int:
        scope = scope_of(candidates[index])
        return len(scope["private"]) + len(scope["tools"])

    survivors: list[dict[str, Any]] = []
    for members in components.values():
        if len(members) == 1:
            survivors.append(candidates[members[0]])
            continue
        representative_index = sorted(
            members,
            key=lambda idx: (-scope_weight(idx), str(candidates[idx].get("id"))),
        )[0]
        representative = candidates[representative_index]
        merged_private: set[str] = set()
        merged_tools: set[str] = set()
        merged_ids: list[str] = []
        for index in members:
            scope = scope_of(candidates[index])
            merged_private |= scope["private"]
            merged_tools |= scope["tools"]
            if index != representative_index:
                merged_ids.append(str(candidates[index].get("id")))
        if not provisional:
            representative.setdefault("evidence_scope", {})
            representative["evidence_scope"]["private"] = sorted(merged_private)
            representative["evidence_scope"]["tools"] = sorted(merged_tools)
        representative["merged_from"] = sorted(merged_ids)
        for merged_id in sorted(merged_ids):
            member_index = next(
                index
                for index in members
                if str(candidates[index].get("id")) == merged_id
            )
            verdict, why = edge_reason.get(
                frozenset((representative_index, member_index)),
                (
                    "same_observable" if provisional else "closure",
                    "fundida por fechamento transitivo da relação de fusão",
                ),
            )
            log.append({
                "action": "merge",
                "concern": merged_id,
                "into": representative.get("id"),
                "verdict": verdict,
                "reason": why,
            })
        survivors.append(representative)

    survivors.sort(key=lambda concern: str(concern.get("id")))
    return survivors, log


# --------------------------------------------------------------------------
# 2. adversários por domínio de dano ortogonal


def derive_adversaries(harm_domains: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """Um adversário por domínio de dano ortogonal.

    Ortogonal = evidência disjunta E dono distinto. Domínios que se sobrepõem
    são o mesmo dano visto de dois ângulos e recebem um único adversário.
    """
    # Correção S-01 (auditoria Codex Sol): a implementação agora é o COMPLEMENTO
    # exato da condição declarada. Ortogonal = evidência disjunta E dono
    # distinto; logo dois domínios se fundem quando compartilham dono OU
    # compartilham evidência. Fechamento por componentes conexos, invariante à
    # ordem; representante = maior evidência (empate → menor id); poder do
    # componente = o mais forte declarado entre os membros (veto >
    # escalonamento > parecer).
    log: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for domain in harm_domains:
        entry = dict(domain)
        power = str(entry.get("power", "parecer")).strip().lower()
        if power not in ADVERSARY_POWERS:
            power = "parecer"
            log.append({
                "action": "default_power",
                "domain": entry.get("id"),
                "reason": (
                    "poder do adversário não declarado; assumido `parecer`. "
                    "Veto e escalonamento exigem declaração explícita."
                ),
            })
        entry["power"] = power
        entries.append(entry)

    count = len(entries)
    parent = list(range(count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[max(root_left, root_right)] = min(root_left, root_right)

    for i in range(count):
        for j in range(i + 1, count):
            same_owner = (
                str(entries[i].get("owner", "")).strip()
                == str(entries[j].get("owner", "")).strip()
            )
            overlap = as_set(entries[i].get("evidence")) & as_set(
                entries[j].get("evidence")
            )
            if same_owner or overlap:
                union(i, j)

    components: dict[int, list[int]] = {}
    for index in range(count):
        components.setdefault(find(index), []).append(index)

    power_rank = {"parecer": 0, "escalonamento": 1, "veto": 2}
    kept: list[dict[str, Any]] = []
    for members in components.values():
        if len(members) == 1:
            kept.append(entries[members[0]])
            continue
        representative_index = sorted(
            members,
            key=lambda idx: (
                -len(as_set(entries[idx].get("evidence"))),
                str(entries[idx].get("id")),
            ),
        )[0]
        representative = entries[representative_index]
        strongest = max(
            (entries[idx]["power"] for idx in members),
            key=lambda value: power_rank[value],
        )
        if strongest != representative["power"]:
            log.append({
                "action": "escalate_power",
                "domain": representative.get("id"),
                "reason": (
                    f"componente fundido herda o poder mais forte declarado "
                    f"({strongest}) entre os domínios fundidos"
                ),
            })
            representative["power"] = strongest
        merged_evidence: set[str] = set()
        for index in members:
            merged_evidence |= as_set(entries[index].get("evidence"))
            if index != representative_index:
                log.append({
                    "action": "merge_harm_domain",
                    "domain": entries[index].get("id"),
                    "into": representative.get("id"),
                    "reason": (
                        "não ortogonal ao componente: compartilha dono ou "
                        "evidência (ortogonal exige evidência disjunta E dono "
                        "distinto)"
                    ),
                })
        representative["evidence"] = sorted(merged_evidence)
        kept.append(representative)

    kept.sort(key=lambda domain: str(domain.get("id")))
    return kept, log


# --------------------------------------------------------------------------
# 3. cordas ajuste/resíduo por separação


def universe_evidence(concerns: list[dict[str, Any]], registry: list[dict]) -> set[str]:
    total: set[str] = {str(item.get("id")) for item in registry if item.get("id")}
    for concern in concerns:
        scope = scope_of(concern)
        total |= scope["shared"] | scope["private"]
    return {item for item in total if item}


def derive_cordas(
    concerns: list[dict[str, Any]], all_evidence: set[str], *, provisional: bool = False
) -> list[dict[str, Any]]:
    """Toda lente tem a corda de ajuste. A do resíduo entra por separação.

    Separação = fração da evidência do universo que a lente NÃO tem em escopo.
    Lente estreita deixa resto grande: o loop entre as cordas é pesado e
    informativo. Lente que vê quase tudo tem resto vazio: o loop seria ruído.
    """
    out: list[dict[str, Any]] = []
    for concern in concerns:
        scope = scope_of(concern)
        seen = scope["shared"] | scope["private"]
        unseen = all_evidence - seen
        if provisional or not all_evidence:
            # Sem corpus não há separação observável. Não inventar um número.
            separation = None
        else:
            separation = round(len(unseen) / len(all_evidence), 4)

        cordas = [{
            "id": f"{concern['id']}::ajuste",
            "observable": "ajuste",
            "question": concern.get("question")
                or "O que a evidência disponível sustenta nesta lente?",
            "emits": "conclusão sustentada por evidência citada",
        }]
        if separation is None:
            # Cold start: o resíduo é onde se aprende mais rápido. Admitir, mas
            # como hipótese, e rederivar quando houver corpus.
            admitted = True
        else:
            admitted = separation >= RESIDUAL_SEPARATION_THRESHOLD
        if admitted:
            cordas.append({
                "id": f"{concern['id']}::residuo",
                "observable": "resíduo",
                "question": (
                    "O que esta lente NÃO explica, e esse resto tem estrutura? "
                    "Se o resíduo tem padrão, o ajuste está errado."
                ),
                "emits": "resto estruturado, ou declaração de resto sem estrutura",
                "devils_advocate": {
                    "targets": f"{concern['id']}::ajuste",
                    "power": "parecer",
                    "blind_to": ["conclusão pretendida do ajuste"],
                },
            })

        out.append({
            "id": concern["id"],
            "label": concern.get("label"),
            "role": concern.get("role") or concern.get("label"),
            "evidence_scope": {
                key: sorted(value) for key, value in scope_of(concern).items()
            },
            "separation": separation,
            "provisional": bool(concern.get("provisional")),
            "residual_admitted": admitted,
            "residual_rationale": (
                "separação não observável sem corpus; resíduo admitido como "
                "hipótese e sujeito a rederivação"
                if separation is None
                else f"separação {separation:.0%} ≥ limiar "
                     f"{RESIDUAL_SEPARATION_THRESHOLD:.0%}"
                if admitted
                else f"separação {separation:.0%} < limiar "
                     f"{RESIDUAL_SEPARATION_THRESHOLD:.0%}: resíduo redundante"
            ),
            "cordas": cordas,
            "source_ref": concern.get("source_ref"),
        })
    return out


# --------------------------------------------------------------------------
# 4. derivação principal


def derive(brief: dict[str, Any]) -> dict[str, Any]:
    concerns = brief.get("concerns") or []
    registry = brief.get("evidence_registry") or []
    harm_domains = brief.get("harm_domains") or []

    requirements: list[dict[str, Any]] = []
    log: list[dict[str, Any]] = []

    # modo de derivação: com corpus é forte; sem corpus é provisório e rotulado
    evidence_backed = bool(registry) and any(scope_of(c)["private"] for c in concerns)
    derivation_mode = (
        "evidence_derived" if evidence_backed else "structure_derived_provisional"
    )

    provisional = derivation_mode == "structure_derived_provisional"
    survivors, merge_log = merge_concerns(concerns, provisional=provisional)
    log.extend(merge_log)

    adversaries, adv_log = derive_adversaries(harm_domains)
    log.extend(adv_log)

    all_evidence = universe_evidence(survivors, registry)
    lenses = derive_cordas(survivors, all_evidence, provisional=provisional)

    # papéis estruturais: entram pela topologia, não pelo assunto
    owner = brief.get("human_owner")
    requirements.append({
        "requirement": "human_boundary_condition",
        "status": "present" if has_text(owner) else "missing",
        "reason": "quem aceita, rejeita ou altera a decisão; o universo não cria autoridade",
    })
    requirements.append({
        "requirement": "integrator",
        "status": "required" if len(lenses) >= 2 else "not_required",
        "reason": (
            f"{len(lenses)} lentes a reconciliar" if len(lenses) >= 2
            else "uma lente não precisa de integração"
        ),
    })
    requirements.append({
        "requirement": "adversary",
        "status": "present" if adversaries else "missing",
        "reason": (
            f"{len(adversaries)} domínio(s) de dano ortogonal(is)" if adversaries
            else "nenhum domínio de dano declarado: o universo não tem como falhar por escrito"
        ),
    })
    requirements.append({
        "requirement": "subject_boundary",
        "status": "present" if (brief.get("subject_boundary") or {}).get("included")
                  else "missing",
        "reason": (
            "escopo de assunto (o que o universo pode tratar) é distinto do escopo "
            "de evidência (quais fontes ele lê)"
        ),
    })

    # veredito
    if not lenses:
        verdict = "NO_UNIVERSE"
        rationale = (
            "nenhuma lente sobreviveu: as preocupações propostas não têm evidência "
            "própria. Isto não pede universo, pede uma resposta."
        )
    elif len(lenses) == 1:
        verdict = "SINGLE_LENS"
        rationale = (
            "uma lente separável. Um universo com um só modo não integra nem "
            "confronta nada: responda direto, ou traga evidência que separe outra lente."
        )
    else:
        verdict = "DERIVE_CAST"
        rationale = (
            f"{len(lenses)} subespaço(s) de evidência separável(is) + "
            f"{len(adversaries)} adversário(s) por dano ortogonal"
        )

    unsatisfied = [r for r in requirements if r["status"] == "missing"]

    return {
        "schema_version": SCHEMA,
        "subject": brief.get("subject"),
        "decision": brief.get("decision"),
        "human_owner": owner,
        "verdict": verdict,
        "rationale": rationale,
        "derivation_mode": derivation_mode,
        "derivation_caveat": (
            None if derivation_mode == "evidence_derived" else
            "ELENCO PROVISÓRIO. Sem corpus, a separação entre lentes é hipótese "
            "estrutural, não observação. Rotular todas as lentes como `hypothesis` e "
            "rederivar quando a primeira evidência real entrar."
        ),
        "cast_size": {
            "proposed": len(concerns),
            "surviving_lenses": len(lenses),
            "adversaries": len(adversaries),
            "integrator": 1 if len(lenses) >= 2 else 0,
            "human_owner": 1 if has_text(owner) else 0,
        },
        "lenses": lenses,
        "adversaries": adversaries,
        "subject_boundary": brief.get("subject_boundary"),
        "requirements_assessment": requirements,
        "requirements_unsatisfied": [r["requirement"] for r in unsatisfied],
        "derivation_log": log,
        "limits": [
            "A derivação mede separação de evidência declarada. Não mede se a "
            "evidência é suficiente, verdadeira ou bem escolhida.",
            "Um buraco sistemático no corpus não produz lente: a derivação não "
            "enxerga o que a fonte inteira omite. Esse piso só um humano levanta.",
            "Fundir lentes correlacionadas remove redundância, não viés comum.",
        ],
    }


# --------------------------------------------------------------------------
# 5. saídas


def render_markdown(cast: dict[str, Any]) -> str:
    size = cast["cast_size"]
    lines = [
        f"# Contrato de elenco — {cast.get('subject') or 'sem assunto declarado'}",
        "",
        f"- Veredito: `{cast['verdict']}`",
        f"- Razão: {cast['rationale']}",
        f"- Modo de derivação: `{cast['derivation_mode']}`",
        f"- Owner humano: {cast.get('human_owner') or '**ausente**'}",
        "",
        "## Tamanho do elenco",
        "",
        "| Papel | Quantidade |",
        "| --- | ---: |",
        f"| Lentes propostas | {size['proposed']} |",
        f"| Lentes sobreviventes | {size['surviving_lenses']} |",
        f"| Adversários | {size['adversaries']} |",
        f"| Integrador | {size['integrator']} |",
        f"| Condição de contorno humana | {size['human_owner']} |",
        "",
    ]
    if cast.get("derivation_caveat"):
        lines += [f"> {cast['derivation_caveat']}", ""]

    lines += ["## Lentes", "", "| Lente | Separação | Corda do resíduo | Razão |",
              "| --- | ---: | --- | --- |"]
    for lens in cast["lenses"]:
        lines.append(
            f"| {lens['label']} | "
            f"{'—' if lens['separation'] is None else format(lens['separation'], '.0%')} | "
            f"{'sim' if lens['residual_admitted'] else 'não'} | "
            f"{lens['residual_rationale']} |"
        )

    lines += ["", "## Adversários", ""]
    if cast["adversaries"]:
        lines += ["| Adversário | Protege | Poder | Dono |", "| --- | --- | --- | --- |"]
        for adv in cast["adversaries"]:
            lines.append(
                f"| {adv.get('id')} | {adv.get('what_is_harmed', '—')} | "
                f"`{adv['power']}` | {adv.get('owner', '—')} |"
            )
    else:
        lines.append("**Nenhum.** O universo não declarou como pode causar dano.")

    if cast["derivation_log"]:
        lines += ["", "## O que a derivação removeu", ""]
        for entry in cast["derivation_log"]:
            target = entry.get("concern") or entry.get("domain")
            into = f" → `{entry['into']}`" if entry.get("into") else ""
            lines.append(f"- `{entry['action']}` `{target}`{into} — {entry['reason']}")

    if cast["requirements_unsatisfied"]:
        lines += ["", "## Exigências não satisfeitas", ""]
        for req in cast["requirements_unsatisfied"]:
            reason = next(
                r["reason"] for r in cast["requirements_assessment"]
                if r["requirement"] == req
            )
            lines.append(f"- **{req}** — {reason}")

    lines += ["", "## Limites desta derivação", ""]
    lines += [f"- {item}" for item in cast["limits"]]
    lines.append("")
    return "\n".join(lines)


def to_manifest_skeleton(cast: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    """Esqueleto no schema que build_universe.py já consome."""
    modes = []
    for lens in cast["lenses"]:
        modes.append({
            "id": lens["id"],
            "label": lens["label"],
            "role": lens["role"],
            "status": "active",
            "base_model": "unknown",
            "evidence_scope": lens["evidence_scope"],
            "context_fingerprint": f"briefing::{lens['id']}",
            "prompt_family": "dossier-lente-isolada",
            "run_id": f"run::{lens['id']}",
            "blind_to": ["synthesis", "gate"],
            "loop": {
                "question": lens["cordas"][0]["question"],
                "emission_threshold": lens["cordas"][0]["emits"],
            },
            "cordas": lens["cordas"],
            "source_ref": lens.get("source_ref") or "derivado do briefing do assunto",
        })

    primary = cast["adversaries"][0] if cast["adversaries"] else None
    return {
        "title": cast.get("subject"),
        "subtitle": f"Elenco derivado — modo `{cast['derivation_mode']}`",
        "source": brief.get("source", {"kind": "narrative"}),
        "build_mode": "auto",
        "boundary": {
            "bulk": (brief.get("subject_boundary") or {}).get("included"),
            "human_owner": cast.get("human_owner"),
            "decision": cast.get("decision"),
        },
        "modes": modes,
        "integrator": (
            {"id": "integrator", "label": "Integração",
             "role": "Enquadra, seleciona, integra e entrega. Único integrador."}
            if cast["cast_size"]["integrator"] else {}
        ),
        "gate": {
            "label": "Gate adversarial",
            "adversaries": cast["adversaries"],
            "outcomes": ["pass", "pass_with_caveats", "fail", "escalate"],
            "executor": {"prompt_family": "adversarial-blind",
                         "blind_to": ["intended_conclusion"],
                         "power": primary["power"] if primary else "parecer"},
        },
        "evidence_registry": brief.get("evidence_registry", []),
        "_cast_contract": f"ver o contrato de elenco emitido junto a este esqueleto",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deriva o elenco de um universo CORDA.")
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--basename", default="corda")
    args = parser.parse_args()

    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    cast = derive(brief)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    base = args.out_dir / args.basename
    (base.with_name(f"{args.basename}-CAST.json")).write_text(
        json.dumps(cast, ensure_ascii=False, indent=2), encoding="utf-8")
    (base.with_name(f"{args.basename}-CAST.md")).write_text(
        render_markdown(cast), encoding="utf-8")
    (base.with_name(f"{args.basename}-manifest-skeleton.json")).write_text(
        json.dumps(to_manifest_skeleton(cast, brief), ensure_ascii=False, indent=2),
        encoding="utf-8")

    print(f"Veredito: {cast['verdict']} — {cast['rationale']}")
    print(f"Modo: {cast['derivation_mode']}")
    print(f"Elenco: {cast['cast_size']}")
    if cast["requirements_unsatisfied"]:
        print("Não satisfeitas: " + ", ".join(cast["requirements_unsatisfied"]))
    return 0 if cast["verdict"] == "DERIVE_CAST" else 2


if __name__ == "__main__":
    sys.exit(main())
