"""Ciclo 10 — achados executáveis do parecer #4 (crítica do artigo): R-03, R-04.

R-04 (bloqueante): a fusão de adversários pelo complemento da ortogonalidade,
fechada transitivamente, apagava um dono ortogonal do elenco via domínio
ponte. Regra vigente: um assento por dono (donos distintos nunca fundem).
R-03 (limite declarado): a fusão em cadeia de lentes pode unir extremos
mutuamente separáveis; agora isso dispara `chain_merge_warning` e o veredito
se declara candidato.

Fixtures idênticas às do parecer (reproduzidas em
docs/audits/artigo-rev2-critica-REPRODUCAO-integrador.md).
"""

from __future__ import annotations

import itertools
import json
import unittest

import derive_cast

R04_DOMAINS = [
    {"id": "dano-a", "what_is_harmed": "Bem A", "owner": "Dono 1",
     "power": "veto", "evidence": ["ev-a"]},
    {"id": "dano-b", "what_is_harmed": "Bem B", "owner": "Dono 2",
     "power": "veto", "evidence": ["ev-b"]},
    {"id": "dano-ponte", "what_is_harmed": "Bem ponte", "owner": "Dono 1",
     "power": "parecer", "evidence": ["ev-b"]},
]

R03_CONCERNS = [
    {"id": "lente-a", "label": "Lente A", "role": "a", "question": "A?",
     "domain": "dom-a", "evidence_scope": {"private": ["ev-a"]}},
    {"id": "lente-b", "label": "Lente B", "role": "b", "question": "B?",
     "domain": "dom-b", "evidence_scope": {"private": ["ev-b"]}},
    {"id": "lente-ponte", "label": "Ponte", "role": "ab", "question": "AB?",
     "domain": "dom-ponte", "evidence_scope": {"private": ["ev-a", "ev-b"]}},
]


def fresh(value):
    return json.loads(json.dumps(value))


def seat_of(kept: list[dict], domain_id: str) -> str:
    for seat in kept:
        if str(seat.get("id")) == domain_id:
            return str(seat.get("id"))
        if domain_id in (seat.get("merged_from") or []):
            return str(seat.get("id"))
    raise AssertionError(f"domínio {domain_id} não mapeia para assento algum")


def orthogonal(a: dict, b: dict) -> bool:
    disjoint = not (
        derive_cast.as_set(a.get("evidence")) & derive_cast.as_set(b.get("evidence"))
    )
    distinct = (
        str(a.get("owner", "")).strip() != str(b.get("owner", "")).strip()
    )
    return disjoint and distinct


class TestR04AdversaryBridge(unittest.TestCase):
    """A fixture exata do parecer: a ponte não pode apagar o Dono 2."""

    def test_bridge_never_erases_an_owner(self) -> None:
        kept, _ = derive_cast.derive_adversaries(fresh(R04_DOMAINS))
        self.assertEqual(len(kept), 2)
        owners = sorted(str(seat.get("owner")) for seat in kept)
        self.assertEqual(owners, ["Dono 1", "Dono 2"])

    def test_surviving_seats_carry_portfolio_and_power(self) -> None:
        kept, _ = derive_cast.derive_adversaries(fresh(R04_DOMAINS))
        by_owner = {str(seat.get("owner")): seat for seat in kept}
        seat_1 = by_owner["Dono 1"]
        self.assertEqual(seat_1.get("power"), "veto")  # mais forte do dono
        self.assertEqual(seat_1.get("evidence"), ["ev-a", "ev-b"])  # união
        self.assertEqual(seat_1.get("merged_from"), ["dano-ponte"])
        seat_2 = by_owner["Dono 2"]
        self.assertEqual(seat_2.get("power"), "veto")
        self.assertEqual(seat_2.get("evidence"), ["ev-b"])

    def test_cross_owner_overlap_is_logged_not_merged(self) -> None:
        kept, log = derive_cast.derive_adversaries(fresh(R04_DOMAINS))
        boundary = [e for e in log
                    if e.get("action") == "authority_boundary_preserved"]
        self.assertTrue(boundary)
        self.assertIn(sorted(["dano-b", "dano-ponte"]),
                      [e.get("domains") for e in boundary])


class TestAdversaryInvariants(unittest.TestCase):
    """Propriedades por construção, exercidas sobre uma bateria determinística.

    (i)   nenhum dono declarado desaparece;
    (ii)  pares ortogonais nunca compartilham assento;
    (iii) invariância à ordem (S-01 preservada).
    """

    def battery(self) -> list[list[dict]]:
        owners = ["o1", "o2", "o3"]
        pools = [["a"], ["b"], ["a", "b"], ["b", "c"], ["c"]]
        combos = list(itertools.product(owners, pools))
        cases: list[list[dict]] = []
        # todos os conjuntos de tamanho 2 e 3 sobre uma sub-lista fixa
        seeds = combos[::2][:8]
        for size in (2, 3):
            for chosen in itertools.combinations(seeds, size):
                cases.append([
                    {"id": f"d{i}", "owner": owner, "power": "parecer",
                     "evidence": list(evidence)}
                    for i, (owner, evidence) in enumerate(chosen)
                ])
        return cases

    def test_no_declared_owner_disappears(self) -> None:
        for domains in self.battery():
            kept, _ = derive_cast.derive_adversaries(fresh(domains))
            self.assertEqual(
                {str(d["owner"]) for d in domains},
                {str(seat.get("owner")) for seat in kept},
                domains,
            )

    def test_orthogonal_pairs_never_share_a_seat(self) -> None:
        for domains in self.battery():
            kept, _ = derive_cast.derive_adversaries(fresh(domains))
            for a, b in itertools.combinations(domains, 2):
                if orthogonal(a, b):
                    self.assertNotEqual(
                        seat_of(kept, a["id"]), seat_of(kept, b["id"]),
                        (a, b),
                    )

    def test_partition_is_order_invariant(self) -> None:
        for domains in self.battery():
            reference = None
            for perm in itertools.permutations(domains):
                kept, _ = derive_cast.derive_adversaries(fresh(list(perm)))
                snapshot = json.dumps(kept, ensure_ascii=False, sort_keys=True)
                if reference is None:
                    reference = snapshot
                else:
                    self.assertEqual(reference, snapshot, domains)


class TestR03ChainMergeWarning(unittest.TestCase):
    """O limite declarado da cadeia de lentes agora fala, em vez de calar."""

    def test_bridge_merge_still_happens_but_warns(self) -> None:
        survivors, log = derive_cast.merge_concerns(fresh(R03_CONCERNS))
        self.assertEqual(len(survivors), 1)  # comportamento caracterizado
        warnings = [e for e in log if e.get("action") == "chain_merge_warning"]
        self.assertTrue(warnings)
        self.assertIn(["lente-a", "lente-b"],
                      [e.get("concerns") for e in warnings])

    def test_verdict_declares_candidate_and_warning(self) -> None:
        brief = {
            "subject": "R-03", "decision": "d", "human_owner": "h",
            "evidence_registry": [
                {"id": "ev-a", "kind": "document", "source_ref": "a"},
                {"id": "ev-b", "kind": "document", "source_ref": "b"},
            ],
            "concerns": fresh(R03_CONCERNS),
            "harm_domains": [],
        }
        cast = derive_cast.derive(brief)
        self.assertEqual(cast["verdict"], "SINGLE_LENS")
        self.assertIn("ATENÇÃO", cast["rationale"])
        self.assertTrue(any(
            e.get("action") == "chain_merge_warning"
            for e in cast["derivation_log"]
        ))

    def test_no_warning_without_bridge(self) -> None:
        survivors, log = derive_cast.merge_concerns(fresh(R03_CONCERNS[:2]))
        self.assertEqual(len(survivors), 2)
        self.assertFalse(
            [e for e in log if e.get("action") == "chain_merge_warning"]
        )


if __name__ == "__main__":
    unittest.main()
