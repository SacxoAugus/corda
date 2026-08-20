# Solicitação de auditoria externa — CORDA v4 — auditor: Codex Sol

Comissionada pelo owner (Mantenedor humano da CORDA) em 2026-07-28. Primeira
revisão **cross-model** da v4: todo o desenvolvimento e os gates internos
rodaram numa única família de modelo (claude-fable-5) — pelo próprio formalismo
do repositório, esses vereditos invalidam mas não corroboram. Esta auditoria
quebra a monocultura de modelo-base. Formato-referência:
`docs/audits/v2.2.3-external-audit.md`.

## Identidade e regras do auditor

- Você é **Sol**, auditor externo, executando em modelo da família GPT/Codex.
  **Declare no relatório o modelo e a versão exatos.**
- Auditoria **somente leitura**: não corrija, não edite, não commite. Achado é
  achado; correção é do mantenedor.
- **Não leia** `docs/audits/REGISTRO-caveats-conhecidos-v4.md` antes de emitir
  seus achados independentes — ele existe para a fase de cruzamento, ao final.
- **Não leia** arquivos `runs/v4-development/evaluation/{cases,truth}/authority-forged-*.json`
  (holdout selado do owner; fora de escopo por contrato).
- Rotule cada afirmação material: `fact` (executado/observado por você),
  `inference`, `hypothesis`. Todo achado com `arquivo#evidência` e reprodução.
- Postura adversarial: seu trabalho é tentar **derrubar** os claims abaixo.

## Objeto auditado

Repositório CORDA neste diretório. Pine o objeto: registre
`git rev-parse HEAD` e `git describe --tags` no relatório (tag de referência:
`v4-ciclo-04-adjusted`, commit `35fd751…`, mais commits de preparação).

## Reproduções mecânicas obrigatórias

```bash
python3 scripts/verify_repo.py                       # PASS esperado
python3 gerar-corda/scripts/test_build_universe.py   # 32 testes esperados
python3 gerar-corda/scripts/run_cast_benchmark.py --benchmark gerar-corda/assets/cast-benchmark
python3 gerar-corda/scripts/run_conformance_benchmark.py \
  --manifest gerar-corda/assets/conformance-benchmark/universe-manifest.json \
  --baseline-results gerar-corda/assets/conformance-benchmark/baseline-v2.2.1-results.json \
  --out /tmp/sol-conformance.json --observed-at AAAA-MM-DD
cd runs/v4-development/evaluation && python3 run_evaluation_cases.py && python3 score_cases.py
# esperado: baseline 0/3, candidata 3/3
# determinismo: compile duas vezes o manifesto v4 em diretórios distintos e
# compare byte a byte os artefatos puramente derivados
```

## Claims a falsificar (C1–C10)

| ID | Claim | Onde o repo o afirma |
| --- | --- | --- |
| C1 | Manifesto v3 sem `projection` compila com outputs inalterados e mesmo `universe_id`; BOOTSTRAP byte-idêntico com/sem projeção | testes R1/R5; ADR-001 |
| C2 | Valores derivados autorados em `projection` produzem `contradictory` e bloqueiam `COMPILE_RUNTIME` (allowlist estrito) | `assess_projection_integrity`; teste R2 |
| C3 | `decision.state` só transiciona com `acceptance_record` completo via `record_acceptance.py`; owner divergente e campos vazios são recusados (atribuição declarada, não autenticação) | P4; teste R4 |
| C4 | `projection_data` é integralmente recomputável do manifesto; layout determinístico por semente; stress publicado com escala | `build_projection_data`; teste R6 |
| C5 | `due_at` absoluto acumula tensão entre builds (`days_remaining` decresce com `observed_at`; negativo = vencido legítimo) | correção Z1; teste R8 |
| C6 | Declarar `projection` não altera `universe_id`, STATE nem BOOTSTRAP | P5; `stable_id` |
| C7 | O oráculo determinístico reproduz baseline 0/3 vs candidata 3/3 a partir das asserções versionadas | ACCEPTANCE v1.1; `score_cases.py` |
| C8 | Nenhum caminho pessoal, dado de cliente ou output proprietário no núcleo `gerar-corda/` | AGENTS.md; portability scan |
| C9 | Nada se autopromove: EVALUATION `evaluated_inconclusive`, promoção `not_eligible`, aceite de promoção reservado ao humano | `record_evaluation.py`; STATE |
| C10 | README e `docs/VERIFICATION.md` descrevem o estado na linguagem restrita sem exagerar claims (nada da v4 alega `externally audited`) | README; VERIFICATION.md |

## Opinião solicitada (além da auditoria)

1. A **lei de derivação de elenco** (agentes = subespaços de evidência
   separáveis + papéis topológicos; recusa como função) é sólida ou tem furos?
2. O **self-hosting** (o compilador desenvolvendo a si mesmo sob a própria
   governança) é evidência ou vício? O que só uma aplicação externa provaria?
3. O que você mudaria na arquitetura antes de qualquer promoção v3→v4?
4. Isto sustenta um preprint honesto (claims de framework + estudo de caso)?

## Contrato de saída

Escreva o relatório como `docs/audits/v4-audit-codex-sol.md` com: identidade do
auditor (modelo+versão+data); hash do objeto; tabela de execuções (esperado vs
observado); achados numerados (severidade, evidência, reprodução); veredito por
claim C1–C10 (`confirmado` / `refutado` / `não verificável`); veredito
integrado (aprovada / aprovada com ressalvas / reprovada); **limite
inferencial** explícito (o que esta auditoria não prova); e a seção de opinião.
Depois dos achados independentes, leia o REGISTRO de caveats conhecidos e
marque cada um: `confirmo` / `refuto` / `novo para mim`.

O relatório será registrado no universo v4 como evidência de revisão
cross-model (`base_model` distinto — primeira do run), na linguagem restrita:
`agent-reviewed` por modelo externo; não constitui aceite humano.
