> 🇧🇷 Versão em português. English version: [README.md](README.md)

# CORDA

Compilador de universos auditáveis para LLMs, com derivação de elenco por
topologia de evidência.

> **Estado:** candidato baseado na CORDA v3 com extensões v4 aditivas (projeção
> explorável, aceite computável, prazos absolutos, avaliação com oráculo
> determinístico), aceitas pelo owner como *adjusted* em 2026-07-28 e pinadas
> na tag `v4-ciclo-04-adjusted`. O núcleo do compilador foi auditado
> externamente na v2.2.3; as extensões v3/v4 têm verificação determinística e
> revisão por agentes (mesmo modelo-base — declarado), mas **não** foram
> auditadas externamente nem validadas em distribuição desconhecida.

## O que faz

A CORDA transforma uma descrição, documentos, dados ou um grafo opcional em um
runtime operacional para LLM:

```text
assunto + evidência
→ derivação do elenco
→ manifesto
→ preflight
→ runtime neutro + estado + evidência + projeção opcional
```

O sistema:

- deriva quantos modos/agentes o assunto sustenta;
- funde observadores com evidência correlacionada;
- recusa universos artificiais de uma única lente;
- separa fatos, inferências, hipóteses, recomendações e decisões;
- bloqueia rodadas sem evidência nova;
- mantém a autoridade decisória no owner humano;
- gera `SYSTEM`, `UNIVERSE`, `STATE`, `EVIDENCE` e `BOOTSTRAP`;
- mantém a metáfora física em um overlay opcional.

Um grafo pode ser usado como fonte, mas nunca é pré-requisito.

## Início rápido

Requer Python 3.10 ou superior. Pillow é opcional e habilita a saída PNG.

```bash
python3 -m pip install Pillow
python3 scripts/verify_repo.py
```

Derivar um elenco:

```bash
python3 gerar-corda/scripts/derive_cast.py \
  --brief gerar-corda/assets/cast-benchmark/cases/dois-danos-ortogonais.json \
  --out-dir build/cast-demo \
  --basename demo
```

Compilar um universo narrativo sem grafo:

```bash
python3 gerar-corda/scripts/build_universe.py \
  --spec gerar-corda/assets/conformance-benchmark/cases/dynamic-runtime.json \
  --out-dir build/runtime-demo \
  --basename demo
```

Para operar o universo em uma LLM, carregue primeiro
`build/runtime-demo/demo-BOOTSTRAP.md` e preserve
`build/runtime-demo/demo-STATE.json` como checkpoint.

## Instalar como skill do Codex

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R gerar-corda "$CODEX_SKILLS_DIR/gerar-corda"
```

Depois, invoque explicitamente:

```text
Use $gerar-corda para derivar e compilar um universo para esta decisão: [...]
```

A skill não tem invocação implícita para evitar conflito com skills de domínio.
Outras LLMs podem consumir os artefatos gerados; a embalagem `SKILL.md` é
específica do Codex.

## Estrutura

```text
gerar-corda/
  SKILL.md
  agents/
  assets/
    cast-benchmark/
    conformance-benchmark/
  references/
  scripts/
scripts/
  verify_repo.py
docs/
  VERIFICATION.md
```

## Evidência disponível

| Superfície | Evidência atual |
| --- | --- |
| Compilador | 32 testes unitários (24 v3 + 8 das extensões v4) |
| Conformidade | 9 casos; 3 holdouts; 9/9 conformes |
| Derivação de elenco | 4 casos sintéticos; 2 holdouts; 4/4 conformes |
| Avaliação v4 (ACCEPTANCE v1.1) | oráculo determinístico; ablação 0/3 vs 3/3 (não é baseline v3 histórica — auditoria Sol S-03); `evaluated_inconclusive` |
| Auditoria cross-model (Codex Sol, 2026-07-29) | **reprovada para promoção**: C2–C4 refutados, 6 achados novos; C5–C10 confirmados ([relatório](docs/audits/v4-audit-codex-sol.md)) |
| Generalização | Não demonstrada |
| Aceitação humana | Registrada mecanicamente (`record_acceptance.py`); promoção continua exigindo aceite explícito |

Consulte [docs/VERIFICATION.md](docs/VERIFICATION.md) para o limite exato dos
claims e [o relatório externo da v2.2.3](docs/audits/v2.2.3-external-audit.md)
para a evidência herdada.

## Segurança

A CORDA organiza contexto e evidência; ela não cria uma fronteira de segurança
por si só. Permissões, isolamento, segredos e ações externas continuam sob
responsabilidade do host. Consulte [SECURITY.md](SECURITY.md).

## Licença

**Apache License 2.0** (decisão do mantenedor, 2026-08-20) — arquivo
[`LICENSE`](LICENSE), atribuição em [`NOTICE`](NOTICE). Em resumo: uso, cópia,
modificação e distribuição livres (inclusive comercial), preservando aviso de
autoria e NOTICE; concessão explícita de patente com cláusula de retaliação;
**nenhum direito sobre o nome "CORDA"** (§6 — marca é do autor). Contribuições
externas: até existir um CLA publicado, contribuições são aceitas apenas sob os
termos da própria Apache-2.0 (§5).
