> **REDACTED PUBLIC COPY** — names and paths of the field-test subject were replaced by a declared mechanical map (see PUBLIC-CUT-NOTE.md). The canonical original lives in the maintainer's private archive; original sha256 (first 16): `6386776d3b90284b`.

# Gate adversarial isolado cross-model — CORDA v4 ciclo 07

**Executor:** Codex Sol (família de modelo distinta da implementação)  
**Data:** 2026-08-20  
**Objeto lógico:** tag `v4-ciclo-07-fronteiras`  
**Commit testado:** `954565f64c856825b4aef2a345c5d7846002a1c7`  
**Natureza:** execução adversarial e veredito de gate; não é decisão de promoção

## VEREDITO DE GATE

**`fail`**.

A bateria determinística e as reproduções literais de N-01, N-02 e N-03
passam. A-01, MAST automático e o carimbo A-02 também aparecem nos casos
nominais. O ataque livre, porém, encontrou quatro falhas novas e
reprodutíveis:

- **N-05 (alta):** `case_id` vazio é ignorado pela igualdade de conjuntos, mas
  continua contando em `task_success`; o cenário de padding volta a chegar a
  `promotion_candidate`.
- **N-06 (média):** um STATE que é JSON válido, porém tem `events` com tipo
  errado, ainda provoca escrita parcial EVALUATION→STATE.
- **N-07 (média):** o detector de veto órfão é uma denylist lexical; owners
  semanticamente órfãos como `"pendente"` e `"-"` passam como exercíveis.
- **N-08 (alta):** IDs duplicados no benchmark do próprio contrato colapsam em
  `set`/`dict`; dois casos podem ser cobertos por um só e produzir
  `promotion_candidate`.

N-05 e N-08 atravessam diretamente a fronteira mecânica de elegibilidade. A
reprovação é, portanto, material mesmo sem atribuir autenticidade ao oracle e
sem acessar o holdout selado. O owner conserva integralmente a autoridade de
decisão; este documento não promove nem rejeita o produto em seu lugar.

## 1. Identidade, isolamento e escopo

### 1.1 Estado encontrado no worktree

Os comandos prescritos, executados antes da bateria, retornaram:

```text
$ git log --oneline -1
9cfe114 ciclo 07: solicitacao de EXECUCAO do gate adversarial isolado cross-model (Codex Sol) sobre a candidata v4-ciclo-07-fronteiras — bateria deterministica + sondas re-derivadas pelo executor + ataque livre; veredito de gate, nunca decisao

$ git rev-parse HEAD
9cfe114e67b01f58e5ffc7c5ad7170442570f217

$ git tag --points-at HEAD

$ git status --porcelain
?? paper/
```

Logo, o worktree vivo **não** estava no commit esperado nem limpo. Nenhuma
bateria foi executada nele. A sujeira preexistente `paper/` não foi lida,
alterada ou removida.

Para não confundir a candidata com o commit posterior da solicitação e não
contaminar o objeto com a árvore suja, extraí o objeto Git imutável para um
diretório temporário limpo:

```bash
git rev-parse 'v4-ciclo-07-fronteiras^{commit}'
git archive v4-ciclo-07-fronteiras | tar -x -C "$DIR_LIMPO"
```

Identidade resolvida:

```text
tag:    v4-ciclo-07-fronteiras
commit: 954565f64c856825b4aef2a345c5d7846002a1c7
tree:   ef197873dee79f82c94e63977c071e32dc2a4c29
parent: 0bf926ed299081bf5a9b807d36539adcd6a6843f
```

O diretório de execução foi `/tmp/corda-sol-c07-gate.NGeKxn`. Ele contém
exatamente a árvore da tag e não contém `.git`. A única escrita no repo vivo é
este entregável, expressamente solicitado.

### 1.2 Escopo efetivo

- Li e executei somente conteúdo do repo CORDA.
- Não li nem executei qualquer arquivo `authority-forged-*`.
- Não li qualquer conteúdo do [field-project].
- Todos os fixtures e destinos mutáveis das sondas ficaram em diretórios
  temporários.
- O `REGISTRO-caveats-conhecidos-v4.md` só foi relido depois de os achados
  N-05…N-08 terem sido formados.

## 2. Bateria determinística

Comando no arquivo limpo da tag:

```bash
python3 scripts/verify_repo.py
```

**Retorno:** `rc=0`.

Últimas linhas verbatim de stdout:

```text
[PASS] dois-danos-ortogonais (development)
[PASS] assunto-simples (validation)
[PASS] elenco-inflado (holdout)
[PASS] cold-start (holdout)

4/4 casos conformes — acurácia 100%
Amostra pequena e sintética: mede conformidade nestes casos, não generalização.
Benchmark cases: 9
Baseline metrics: {"applicability_accuracy": 0.6666666666666666, "false_open_rate": 0.42857142857142855, "invariant_accuracy": 0.7719298245614035}
Candidate metrics: {"applicability_accuracy": 1.0, "false_open_rate": 0.0, "invariant_accuracy": 1.0}
All candidate cases pass: True
Output: /var/folders/xf/_h5zsn9d1_zbv2kx_tjqv4s40000gn/T/corda-verify-arb2vij7/conformance.json
[PASS] skill frontmatter
[PASS] portability scan
[PASS] bundle rebuild gate
[PASS] cast benchmark
[PASS] compiler conformance
[PASS] unit tests
CORDA standalone verification: PASS
```

Últimas linhas verbatim de stderr:

```text
----------------------------------------------------------------------
Ran 60 tests in 1.446s

OK
```

Isto verifica deterministicamente 4/4 CAST, 9 casos de conformidade com todos
os casos da candidata passando, 60 testes e o rebuild byte a byte. Continua
sendo conformidade nessa amostra, não prova de generalização.

## 3. Sondas requeridas, re-derivadas pelo executor

Não invoquei o arquivo de testes da implementação como reprodutor. Montei
contratos, runs, relatórios e estados independentes em `TemporaryDirectory`,
chamei os executáveis públicos por `subprocess` e comparei bytes antes/depois.
O núcleo do fixture de caso foi:

```python
def case(cid, success, truth="truth#expected"):
    return {
        "case_id": cid,
        "success": success,
        "oracle_evidence_ref": "oracle#probe",
        "ground_truth_ref": truth,
    }
```

### 3.1 N-01 — padding e variações nominais

Construção principal:

```python
candidate = [case("expected", False)] + [
    case(f"extra-{i}", True) for i in range(99)
]
baseline = [
    {"case_id": item["case_id"], "success": False}
    for item in candidate
]
```

Cada run foi submetido a:

```bash
python3 gerar-corda/scripts/record_evaluation.py \
  --evaluation "$EVALUATION" --run-result "$RUN"
```

Resultados:

| Sonda | rc | Última linha de stderr | Destino |
|---|---:|---|---|
| 1 esperado `false` + 99 extras `true` | 2 | `ERROR: case_results contem casos fora do contrato: extra-0, extra-1, extra-10, extra-11, extra-12... (N-01)` | EVALUATION byte-idêntica |
| `case_id` esperado duplicado | 2 | `ERROR: case_results com case_id duplicado: expected (N-01)` | EVALUATION byte-idêntica |
| baseline com conjunto diferente | 2 | `ERROR: baseline_case_results deve cobrir exatamente o mesmo conjunto de casos da candidata (N-01)` | EVALUATION byte-idêntica |
| scorer determinístico sem relatório | 2 | `ERROR: verdict_source deterministic_scorer exige scorer_report_ref e scorer_report_sha256 (S-02b/N-01)` | EVALUATION byte-idêntica |

**Resultado nominal:** as quatro sondas estão mortas. N-05 demonstra, contudo,
que a propriedade de conjunto exato ainda é contornável por IDs falsy.

### 3.2 N-03 — sincronização EVALUATION→STATE

Usei run válido e relatório real vinculado pelo SHA-256.

| Sonda | rc | Resultado |
|---|---:|---|
| STATE com JSON sintaticamente malformado | 2 | `ERROR: STATE ilegivel para sync: Expecting property name enclosed in double quotes: line 1 column 2 (char 1) (S-07b: nada foi escrito)`; EVALUATION e STATE byte-idênticos |
| STATE bem formado, caminho feliz | 0 | stdout termina em `State synced: <state temporário>`; ambos os destinos mudam e concordam em `evaluated_inconclusive` / `not_eligible` |

**Resultado nominal:** a reprodução original de N-03 está morta e o caminho
feliz sincroniza. N-06 mostra que a validação prévia cobre sintaxe/top-level,
mas não a estrutura que será mutada.

### 3.3 N-02 — rebuild independente da tag

Comandos:

```bash
git archive v4-ciclo-07-fronteiras | tar -x -C "$DIR_LIMPO"
cd "$DIR_LIMPO"
python3 gerar-corda/scripts/build_universe.py \
  --spec runs/v4-development/manifest/corda-v4-manifest.json \
  --out-dir "$OUT_N02" --basename corda-v4 \
  --evidence-root "$DIR_LIMPO"
cmp runs/v4-development/build/corda-v4-universe.json \
    "$OUT_N02/corda-v4-universe.json"
cmp runs/v4-development/build/corda-v4-EVIDENCE.json \
    "$OUT_N02/corda-v4-EVIDENCE.json"
cmp runs/v4-development/build/corda-v4-projection-data.json \
    "$OUT_N02/corda-v4-projection-data.json"
```

O build retornou `rc=0`. Comparações independentes:

| Derivado portátil | Byte a byte | SHA-256 |
|---|---|---|
| `corda-v4-universe.json` | idêntico | `6558600afa70b13e5a1dbf75f1c11cbcfe1579203a065d05b9728fce11b43dcf` |
| `corda-v4-EVIDENCE.json` | idêntico | `fdbaed5a5b7181b800f1cd232c1b60e24812a643c1562ad8b46c4c6bc8598d53` |
| `corda-v4-projection-data.json` | idêntico | `c00e77babf4c2f87ae291a9586143e2617b9194068537a0a266ecb65b2fbf348` |

Vínculos pedidos:

```text
auditoria-codex-sol.identity_token = sha256:a5eead8e9edc90fc4b3ac12febf428fbb29b50b96e8df54d0500be059feb1262
compilador-v3.source_ref = runs/v4-development/evaluation/baseline-v3/build_universe.py (snapshot v3 pinado; hash em BASELINE.md)
compilador-v3.identity_token = sha256:b8cf827a578f86162b8028d4a6fb65c8e86c579d83ced1a73ada24e6fcd00717
```

**Resultado:** N-02 está fechado no objeto testado.

### 3.4 A-01 — veto órfão nominal

Sobre cópia do manifesto canônico, substituí `gate.adversaries` por:

```json
[{"id": "probe-veto", "power": "veto", "owner": "a nomear"}]
```

`assess_applicability()` retornou:

```text
veto_owner.status = missing
veto_owner in requirements_unsatisfied = true
rationale = veto sem dono exercivel (gate morto): probe-veto — nomear o dono ou rebaixar o poder para escalonamento
```

**Resultado nominal:** passa. N-07 mostra o bypass lexical.

### 3.5 §6.7 — MAST automático

Entrada mínima da sonda:

```python
build_mast_validation({
    "runtime": {"execution_topology": "multi_agent"}
})
```

Resultado:

```json
{"selected": true, "auto_required": true, "applicable": true, "status": "not_performed"}
```

**Resultado:** passa; a seleção deixa de depender da declaração voluntária do
perfil. No artefato canônico, o perfil já está declarado (`auto_required:
false`) e o assessment histórico está registrado como `status: fail`, não
apagado pelo rebuild.

### 3.6 A-02 — carimbo do compilador

`corda-v4-verification.json.compiler` no rebuild:

```json
{
  "version": "corda-compiler/4.0.0-candidate",
  "build_universe_sha256": "cdc0bd890c734f6e9b98eab98c059c64e46b3d7aa599d62ba89cfc68ec494026",
  "derive_cast_sha256": "3bbbe30f075251213053fd5ba69348511851b23e08a247c247c0f5fc963482de",
  "render_corda_sha256": "57e1434e19479988a458837caa5433970dbe36d0c3c5185603253747ebb51d1d"
}
```

Os três hashes foram recomputados diretamente sobre os fontes e conferem. O
ledger contém:

```text
## Compilador (A-02: carimbo)

- Versão: `corda-compiler/4.0.0-candidate`
- build_universe sha256: `cdc0bd890c734f6e…`
- derive_cast sha256: `3bbbe30f07525121…`
- render_corda sha256: `57e1434e19479988…`
```

**Resultado:** passa.

## 4. Ataque livre

### N-05 — Alta — IDs falsy furam N-01 e voltam a inflar a métrica

**Sonda.** Contrato com um holdout `expected`; resultado esperado `false`; 99
entradas adicionais com `case_id: ""` e `success: true`; baseline somente com o
caso esperado em `false`; relatório real content-addressed.

```python
candidate = [case("expected", False)] + [
    case("", True) for _ in range(99)
]
baseline = [{"case_id": "expected", "success": False}]
candidate_metrics = {"task_success": 0.99}
baseline_metrics = {"task_success": 0.0}
```

**Observado:** `rc=0`; stdout termina em `Status: promotion_candidate`;
EVALUATION ganha o run e `promotion.status` vira
`awaiting_human_acceptance`.

**Causa.** `recompute_task_success()` conta todo objeto em `case_results`
(`record_evaluation.py`, linhas 73–77), enquanto validação e coverage ignoram
IDs falsy (`record_evaluation.py`, linhas 152–160 e 196–205). `None`, `0`, lista
vazia e outros valores falsy pertencem à mesma classe; o vazio textual basta
para a prova.

**Impacto.** A candidata pode satisfazer o limiar com o único holdout esperado
falhando. É bypass direto da fronteira de promoção.

**Correção/gate sugerido — owner: mantenedor de avaliação/contrato.** Validar
cada item antes de recomputar: objeto exato, `case_id` string não vazia após
`strip`, `success` booleano e referências obrigatórias; rejeitar qualquer item
inválido. Recomputar somente a coleção já validada e exigir cardinalidade e
multiconjunto exatos. Adicionar esta sonda com `""`, `0`, `null`, whitespace e
tipos compostos.

### N-06 — Média — STATE estruturalmente inválido ainda deixa efeito parcial

**Sonda.** Run válido + relatório real + STATE JSON válido:

```json
{"schema_version": "corda-state/1.5", "evaluation": {}, "events": {}}
```

**Observado:** `rc=1`, traceback termina em
`AttributeError: 'dict' object has no attribute 'append'`; antes do crash o
stdout já contém `Status: evaluated_inconclusive`. EVALUATION foi alterada;
STATE ficou byte-idêntico.

**Causa.** `load_object()` valida apenas o objeto top-level. A EVALUATION é
substituída na linha 385; somente depois `state["evaluation"]` é tratado como
dict e `events` como lista nas linhas 392–408. Além disso, `os.replace` é
atômico por arquivo, não para o par de arquivos.

**Impacto.** Reabre a divergência EVALUATION↔STATE de N-03 por uma entrada que
é JSON perfeitamente legível; retries e observadores podem ver estados
contraditórios.

**Correção/gate sugerido — owner: mantenedor de estado/transações.** Validar o
schema mutável completo e construir ambos os payloads antes de qualquer
replace. Para atomicidade lógica entre dois arquivos, usar journal/commit
marker ou fonte única derivável; testar também falha no segundo replace e
lost-update concorrente.

### N-07 — Média — A-01 é denylist lexical, não owner exercível

**Sonda.** O mesmo manifesto canônico passou por `validate_manifest()` e
`assess_applicability()` com owners alternativos:

| owner | schema | `veto_owner` | em `requirements_unsatisfied` |
|---|---|---|---|
| `a nomear` | pass | `missing` | sim |
| `pendente` | pass | `present` | não |
| `por nomear` | pass | `present` | não |
| `unknown` | pass | `present` | não |
| `-` | pass | `present` | não |

**Causa.** `build_universe.py`, linhas 691–700, só rejeita vazio ou substring
em cinco marcadores. Qualquer placeholder não enumerado é declarado
“exercível”.

**Impacto.** Um veto operacionalmente morto volta a ficar invisível na
superfície que A-01 pretendia fechar. Isto é distinto do caveat permanente P4:
não estou exigindo autenticação criptográfica, apenas que placeholder não seja
classificado como owner exercível.

**Correção/gate sugerido — owner: mantenedor do schema/governança.** Trocar a
inferência lexical por referência estruturada a um ator/role declarado e
resolúvel, ou assumir honestamente o status `owner_declared` sem alegar
exercibilidade. Se mantida heurística textual, ela não deve controlar um gate
material.

### N-08 — Alta — benchmark com IDs duplicados colapsa e pode promover

**Sonda.** Contrato com dois itens de mesmo `id`, truths e splits distintos; o
último é holdout. Run e baseline contêm uma única entrada `same`, com relatório
JSON real e SHA correto.

```python
benchmark = [
    {"id": "same", "split": "validation", "ground_truth_ref": "truth-validation"},
    {"id": "same", "split": "holdout", "ground_truth_ref": "truth-holdout"},
]
case_results = [case("same", True, "truth-holdout")]
```

**Observado:** `rc=0`, `Status: promotion_candidate` e:

```json
{
  "complete": true,
  "expected_case_count": 1,
  "observed_case_count": 1,
  "holdout_case_ids": ["same"],
  "holdout_covered": true
}
```

**Causa.** A validação transforma o benchmark em `set` e o coverage em `dict`
sem antes rejeitar duplicatas (`record_evaluation.py`, linhas 152–156 e
196–200). O último item vence silenciosamente.

**Impacto.** Cardinalidade, split e truth do contrato podem ser apagados por
colisão de ID, e um único resultado satisfaz dois casos declarados. O efeito
alcança a fronteira de promoção.

**Correção/gate sugerido — owner: mantenedor de avaliação/schema.** Validar o
contrato antes do run: benchmark deve ser lista não vazia de objetos, IDs
strings canônicas e globalmente únicos, split enumerado, truth não vazia; a
cardinalidade original deve sobreviver à validação. Adicionar esta reprodução
nas duas ordens dos itens.

### Ataques que não viraram achado novo

- **Relatório apontando para conteúdo manipulado:** um run apontando para o
  `README.md`, com SHA-256 correto, foi aceito e chegou a
  `promotion_candidate`. Isto prova que content-addressing garante identidade
  dos bytes, não que os bytes são um relatório nem que sustentam
  `case_results`. Não numerei como defeito novo porque o próprio artefato
  declara que a validade do oracle/scorer é externa. É caveat material: o
  aceite humano ou um gate futuro precisa autenticar formato, producer e
  vínculo semântico; `source_ref` textual não faz isso.
- **Abuso de `evidence_root`:** com a raiz declarada em
  `runs/v4-development`, `content_path: "../../README.md"` foi lido e recebeu
  exatamente o hash do README. A opção resolve caminhos, mas não é sandbox nem
  confinamento. É variante do caveat já registrado para paths absolutos/fora
  do repo e não refuta o fechamento específico de N-02, que era falhar duro em
  ausência e fechar o bundle por rebuild.
- **Corrida/atomicidade:** não foi necessário depender de timing para produzir
  divergência; N-06 a reproduz deterministicamente. O código também não tem
  lock, versão esperada ou commit conjunto, portanto a hipótese de lost update
  concorrente permanece aberta e deve entrar no teste da correção.

## 5. Cruzamento pós-achados com caveats conhecidos

| Caveat do REGISTRO | Marca após o gate |
|---|---|
| `canonical_registry` lê path absoluto fora do repo / relativo dependia do CWD | **confirmo, com variante:** `--evidence-root` estabiliza a resolução e o rebuild, mas não confina `..`; não é N-05+ porque a ausência de sandbox já era conhecida e path absoluto é admitido pelo contrato. |
| P4 é atribuição, não autenticação | **confirmo:** A-01 nominal não autentica owner. N-07 é mais estreito: a própria classificação declarativa de “exercível” aceita placeholders triviais. |
| Amostras pequenas e avaliação coautoral | **confirmo:** 4 CAST, 9 conformidade e o contrato de avaliação não provam generalização. O presente gate é cross-model, mas não torna as amostras independentes na origem. |
| Todos os pares internos `weak` | **confirmo historicamente:** este executor oferece independência de modelo/contexto para o gate externo; como o resultado é `fail`, ele invalida a promoção, não a corrobora. |
| Holdout selado e visual review pendentes | **confirmo sem inspeção do holdout:** ambos continuam fora deste gate e pendentes. |
| Scorer `exists`/`find.where` latente | **não reabri neste gate:** N-05/N-08 são falhas de fronteira no registrador e independem desses operadores. |
| `downgrade_state.py` tinha efeito parcial | **recorrência em outro componente:** N-06 encontra a mesma classe transacional em `record_evaluation.py`, apesar do fechamento nominal de N-03. |

## 6. Precedências para elegibilidade e promoção

A lista “holdout selado + visual_review + aceite humano” está incompleta diante
do objeto efetivamente testado.

Antes de considerar a candidata **elegível**, minha leitura exige:

1. corrigir N-05, N-06, N-07 e N-08, com regressões determinísticas para as
   sondas acima;
2. congelar nova tag e repetir o gate isolado sobre o objeto exato, em worktree
   limpo ou arquivo Git imutável igualmente identificado;
3. gerar e executar o holdout selado pelo caminho autorizado, inclusive fechar
   a pendência de o runner ainda não o descobrir automaticamente;
4. realizar a revisão humana visual/de interação/acessibilidade;
5. dar disposição humana explícita ao `mast_validation.status: fail` que a tag
   preserva e a quaisquer caveats residuais, sem reescrever o histórico;
6. obter EVALUATION/STATE concordantes em estado mecanicamente elegível — a tag
   atual registra `evaluated_inconclusive` / `not_eligible`.

Somente depois vem o **aceite humano explícito**, que é a decisão de promoção,
não um substituto para elegibilidade. Licença continua sendo precedente de
publicação, não evidência técnica de elegibilidade.

## 7. Conclusão operacional

O ciclo 07 corrigiu materialmente as reproduções originais: rebuild fecha byte
a byte, os quatro ataques nominais de N-01 recusam sem mutar, JSON malformado
não produz efeito parcial, A-01 nominal aparece, MAST é autoexigido e o
compilador se carimba. Isso é evidência positiva real.

Não basta para passar o gate. N-05 mostra que a mesma inflação retorna por
valores falsy; N-08 mostra que o contrato pode perder casos antes da comparação;
N-06 reabre a divergência transacional; N-07 enfraquece a fronteira de veto.
Por isso o veredito externo sobre `954565f64c856825b4aef2a345c5d7846002a1c7`
é **`fail`**, sem decisão de promoção e sem leitura do holdout selado ou do
[field-project].
