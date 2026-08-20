> 🇧🇷 Versão em português. English version: [README.md](README.md)

# CORDA

Compilador de universos auditáveis para LLMs, com derivação de elenco por
topologia de evidência.

> **Versão:** `1.0.0-rc.1` — primeiro lançamento público; nada foi publicado
> antes dele. Os nomes de linhagem interna (v3/v4) aparecem apenas na trilha
> de auditoria preservada — ver [VERSIONING.md](VERSIONING.md).
>
> **Estado:** release candidate. A ferramenta é extensão opcional e aditiva do
> predecessor privado, medida contra ele pinado por hash: 0/3 vs 3/3 nos casos
> autorais de aceitação — presença de capacidade, **não superioridade**.
> Sobreviveu a duas auditorias cross-model e a um gate adversarial isolado
> cuja seção de ataque livre reprovou uma candidata que a bateria nominal
> completa aprovava (ver [docs/audits/README.md](docs/audits/README.md));
> cada achado foi reproduzido, corrigido e re-testado (70 testes, gate de
> rebuild byte a byte). O `-rc` só cai com o aceite humano explícito, ainda
> pendente — junto com o holdout selado e a revisão visual humana. Os claims
> são estreitos por desenho: sem superioridade, sem generalização, sem
> auditoria humana externa das extensões.

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

## Instalar como skill (Claude Code, apps do Claude, Codex, qualquer runner)

A pasta `gerar-corda/` é uma skill autocontida: `SKILL.md` é o contrato,
`references/` o método, `scripts/` Python puro sem dependência de fornecedor.
Instale onde o seu agente rodar:

```bash
# Claude Code — por projeto             # Claude Code — por usuário
cp -R gerar-corda .claude/skills/       cp -R gerar-corda ~/.claude/skills/

# Codex
cp -R gerar-corda "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Para os apps do Claude (Cowork / claude.ai), empacote a pasta como zip
`.skill` e adicione nas configurações de skills. Qualquer outro runner que
leia arquivos e execute Python pode seguir o `gerar-corda/SKILL.md`
diretamente. Instruções completas por runtime: [INSTALL.md](INSTALL.md).

A skill evita invocação implícita para não conflitar com skills de domínio —
e os universos compilados rodam em **qualquer** LLM via `BOOTSTRAP.md` +
`STATE.json`, sem skill nenhuma instalada.

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
| Compilador | 70 testes unitários, incluindo testes metamórficos de elenco e sondas adversariais re-derivadas de cada achado de auditoria; gate de rebuild do bundle byte a byte |
| Conformidade | 9 casos; 3 holdouts; 9/9 conformes |
| Derivação de elenco | 4 casos sintéticos; 2 holdouts; 4/4 conformes (invariante à ordem: partição única sob permutações da entrada) |
| Avaliação (ACCEPTANCE v1.2) | oráculo determinístico com relatório do scorer endereçado por conteúdo, obrigatório; medida contra o **predecessor executável pinado por hash**: 0/3 vs 3/3 nos casos autorais — presença de capacidade, não superioridade; `evaluated_inconclusive` até o holdout selado rodar |
| Auditoria cross-model nº 1 (2026-07-29) | **reprovada para promoção**; achados S-01…S-09, todos reproduzidos e corrigidos ([relatório](docs/audits/v4-audit-codex-sol.md)) |
| Parecer cross-model nº 2 (2026-08-19) | progresso material, utilidade demonstrada em um episódio de campo, **não promover**; achados N-01…N-04, todos reproduzidos e corrigidos |
| Gate cross-model isolado (2026-08-20) | bateria nominal integralmente PASS, **o ataque livre reprovou a candidata** (N-05…N-08), todos reproduzidos e corrigidos — ver [docs/audits/README.md](docs/audits/README.md) |
| Uso em campo | uma implantação real; uma rodada multi-agente real em que o gate do próprio universo rejeitou uma recomendação defeituosa e forçou o reparo; uma sessão externa em que a admissão de rodada recusou corretamente trabalho redundante |
| Generalização | Não demonstrada |
| Aceitação humana | Registrada mecanicamente (`record_acceptance.py`); a promoção continua exigindo aceite humano explícito — pendente |

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
