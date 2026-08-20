# Auditoria externa da CORDA v4 — Codex Sol

## Identidade, objeto e escopo

- **Auditor:** Sol, executado por **OpenAI `gpt-5.6-sol` (Codex)**, esforço de
  raciocínio `xhigh`.
- **Data:** 2026-07-29, Europe/Lisbon.
- **Natureza da revisão:** `agent-reviewed` por família de modelo distinta da
  usada no desenvolvimento. Não constitui aceite humano nem auditoria humana
  independente.
- **HEAD auditado:** `79ef9e1b8fd73dc672c71231ac884699550bce15`.
- **Descrição Git:** `v4-ciclo-04-adjusted-3-g79ef9e1`.
- **Tag de referência:** `v4-ciclo-04-adjusted`, commit
  `35fd75119d618af47cb24bf894a4acf510ceb373`; o HEAD contém três commits
  posteriores de preparação e solicitação de auditoria.
- **Estado inicial da worktree:** um diretório não rastreado, `_to_delete/`,
  preexistia e não foi lido nem alterado.
- **Restrição cumprida:** os achados independentes abaixo foram fechados antes
  da leitura de `docs/audits/REGISTRO-caveats-conhecidos-v4.md`. Os arquivos
  `authority-forged-*` não foram lidos nem executados em nenhuma fase.

## Veredito integrado

**REPROVADA para promoção v3→v4 no objeto auditado.**

[fact] O núcleo executável passou nos gates publicados: 32/32 testes, CAST 4/4,
conformidade 9/9 e avaliação mecânica baseline 0/3 versus candidata 3/3.

[inference] Esses resultados não superam quatro bloqueadores: a lei de elenco
não é invariante à ordem e sua implementação de dano ortogonal diverge da
especificação; a comparação chamada “baseline v3” não executa uma implementação
v3 pinada; a elegibilidade aceita métricas autodeclaradas desconectadas dos
resultados por caso; e os artefatos de `runs/v4-development/build/` não são a
recomputação do HEAD canônico. Há ainda falhas de validação de schema/data que
permitem projeção semanticamente enganosa e registros de aceite malformados.

[inference] “Reprovada” aqui significa **não promover**. Não significa que o
protótipo não tenha valor: as propriedades estreitas C5, C6, C7, C8, C9 e C10
foram reproduzidas nos limites declarados.

## Tabela de execuções

| Execução | Esperado | Observado | Resultado |
| --- | --- | --- | --- |
| `git rev-parse HEAD` | objeto pinado | `79ef9e1b8fd73dc672c71231ac884699550bce15` | PASS |
| `git describe --tags --always --dirty` | tag + commits de preparação | `v4-ciclo-04-adjusted-3-g79ef9e1` | PASS |
| `python3 scripts/verify_repo.py` | PASS | `CORDA standalone verification: PASS` | PASS com ressalva de isolamento |
| `python3 gerar-corda/scripts/test_build_universe.py` | 32 testes | 32 executados, `OK` | PASS |
| `run_cast_benchmark.py` | 4/4 | 4/4; 100% na amostra sintética | PASS |
| `run_conformance_benchmark.py` | candidata conforme | baseline: aplicabilidade `0,6667`, false-open `0,4286`, invariantes `0,7719`; candidata `1,0 / 0,0 / 1,0`; 9 casos | PASS |
| `run_evaluation_cases.py && score_cases.py` | baseline 0/3; candidata 3/3 | baseline 0/3; candidata 3/3 | PASS mecânico |
| build do manifesto v4 em dois diretórios | derivados puros byte-idênticos | 14/14 artefatos independentes de localização idênticos; `ledger.md` diferiu somente pelos caminhos absolutos do diretório de saída | PASS restrito |
| build com/sem `projection` | mesmo ID, STATE e BOOTSTRAP | ID `...6ff48fb07b2e` em ambos; STATE, BOOTSTRAP e os outros 10 outputs comuns inspecionados idênticos | PASS |
| rebuild do HEAD versus build versionado | deveria fechar se o build fosse corrente | HEAD recompilado `...6ff48fb07b2e`; build versionado `...c4f555d7086c` | FAIL de coerência do objeto |

### Nota sobre `verify_repo.py`

[fact] `scripts/verify_repo.py#L57-L65` percorre recursivamente todo o root e lê
qualquer `.md`, `.py`, `.json`, `.yaml` ou `.yml`, inclusive arquivos não
rastreados e materiais selados. Para cumprir o contrato de não leitura, o
comando foi executado numa cópia byte-equivalente do HEAD com o REGISTRO e os
dois padrões `evaluation/{cases,truth}/authority-forged-*.json` excluídos pelo
`rsync`. Nenhum arquivo do núcleo foi modificado.

## Achados independentes

Os achados S-01 a S-09 foram redigidos e selados antes da fase de cruzamento.

### S-01 — Alta — derivação de elenco depende da ordem e viola a própria regra de dano ortogonal

[fact] A lei afirma que o elenco é o número de subespaços separáveis e que dano
ortogonal exige **evidência disjunta E owner distinto**
(`gerar-corda/references/cast-derivation.md#L22-L36` e `#L48-L61`).

[fact] A fusão é um passe guloso sobre a ordem de entrada e não reavalia
sobreviventes após ampliar o escopo de um deles
(`gerar-corda/scripts/derive_cast.py#L98-L169`). A implementação de adversários
só funde quando há **mesmo owner E evidência sobreposta**
(`gerar-corda/scripts/derive_cast.py#L176-L217`), que não é o complemento da
condição declarada.

**Reprodução:**

```bash
PYTHONPATH=gerar-corda/scripts python3 - <<'PY'
from derive_cast import merge_concerns, derive_adversaries
c = [
 {"id":"a","evidence_scope":{"private":["a"]}},
 {"id":"b","evidence_scope":{"private":["b"]}},
 {"id":"c","evidence_scope":{"private":["a","b"]}},
]
print([x["id"] for x in merge_concerns(c)[0]])
print([x["id"] for x in merge_concerns(list(reversed(c)))[0]])
for h in (
 [{"id":"h1","owner":"x","evidence":["a"]},{"id":"h2","owner":"x","evidence":["b"]}],
 [{"id":"h1","owner":"x","evidence":["a"]},{"id":"h2","owner":"y","evidence":["a"]}],
):
    print(len(derive_adversaries(h)[0]))
PY
```

**Observado:** `['a', 'b']`, depois `['c']`; os dois cenários de dano retornam
dois adversários, embora cada um falhe uma das duas condições declaradas para
ortogonalidade.

[inference] O tamanho do elenco não é função apenas do assunto/evidência; também
é função da ordenação do JSON. Isso derruba a lei como invariante operacional e
não é coberto pelos quatro casos autorais.

### S-02 — Alta — `record_evaluation.py` aceita elegibilidade a partir de métricas autodeclaradas

[fact] `validate_run` verifica presença e tipos, não a existência ou hash das
evidências (`gerar-corda/scripts/record_evaluation.py#L27-L57`).
`assess_case_coverage` não consulta `case_results[].success`
(`#L60-L98`), e `score_thresholds` usa diretamente
`baseline_metrics`/`candidate_metrics` fornecidas pelo chamador
(`#L101-L164`). A decisão de candidatura combina essas três superfícies
(`#L204-L219`).

**Reprodução:** copiar `corda-v4-EVALUATION.json` para `/tmp`, construir um
`run-result.json` com os quatro IDs/`ground_truth_ref` esperados, marcar todos
os `success: false`, usar referências inexistentes, declarar
`baseline.task_success=0.0` e `candidate.task_success=1.0`, e executar:

```bash
python3 gerar-corda/scripts/record_evaluation.py \
  --evaluation /tmp/evaluation.json \
  --run-result /tmp/run-result.json
```

**Observado:** retorno `0`, `status: promotion_candidate`,
`promotion.status: awaiting_human_acceptance`, cobertura completa e threshold
`pass`, apesar de os quatro casos declararem `success: false`.

[fact] O script ainda não preenche `accepted_by` nem conclui aceite humano.
[inference] A fronteira humana final permanece, mas o artefato apresentado ao
humano como elegível pode ser fabricado sem executar o scorer. Isso é um
bloqueador de promoção, não uma falha meramente documental.

### S-03 — Alta — a “baseline v3” não é uma implementação v3 pinada

[fact] O runner importa o `build_universe.py` corrente
(`runs/v4-development/evaluation/run_evaluation_cases.py#L22-L27`) e representa
a baseline chamando as mesmas funções com `with_projection=False`
(`#L52-L91`, `#L228-L236`). Para `authority-boundary`, a baseline é um objeto
hardcoded, não uma execução (`#L180-L187`).

[fact] Não há tag pré-v4 no repositório. A única tag listada é
`v4-ciclo-04-adjusted`. Em contraste, a auditoria v2.2.3 registrava uma baseline
preservada e seu hash (`docs/audits/v2.2.3-external-audit.md#L46-L58`).

**Reprodução:**

```bash
cd runs/v4-development/evaluation
python3 run_evaluation_cases.py
python3 score_cases.py
```

**Observado:** 0/3 versus 3/3, exatamente como publicado.

[inference] O número é reprodutível, mas mede “feature v4 ligada versus
desligada no código v4” sobre asserções escritas para a feature. Não demonstra
regressão ou ganho sobre um executável v3 histórico. O claim mecânico C7 é
estreito e verdadeiro; usar 0/3→3/3 como evidência comparativa de produto seria
exagero.

### S-04 — Média — allowlist/schema de projeção não é semanticamente estrito

[fact] O schema versionado enumera três painéis e fixa `dimensions: 2`
(`runs/v4-development/cycles/ciclo-01/schema/projection-extension.schema.json#L7-L29`).
O preflight aceita qualquer string em `panels`, qualquer string em `algorithm`,
qualquer inteiro em `dimensions/iterations` e também booleanos, pois `bool` é
subclasse de `int` em Python
(`gerar-corda/scripts/build_universe.py#L716-L780`).

[fact] O layout sempre executa o mesmo algoritmo 2D. `algorithm` é apenas
ecoado; `dimensions` não é consumido
(`gerar-corda/scripts/build_universe.py#L1777-L1861`).

**Reprodução:** uma projeção com
`panels=["unknown-panel"]`, `algorithm="not-implemented"`, `seed=true`,
`dimensions=7`, `iterations=-1` retornou `COMPILE_RUNTIME`, sem contradições e
sem qualquer painel derivado. Duas compilações com rótulos
`algorithm-a`/`algorithm-b`, mesma semente e iterações, produziram coordenadas e
stress idênticos, mudando somente o rótulo.

[inference] P1 bloqueia chaves derivadas autoradas, mas o claim composto de
“allowlist estrito” é falso. O output pode declarar um algoritmo que não foi
executado.

### S-05 — Média — datas malformadas são aceitas ou descartadas silenciosamente

[fact] O validador de manifesto verifica apenas endpoints de `strings[]`, não
tipo/formato de `due_at` (`gerar-corda/scripts/render_corda.py#L193-L203`).
`_parse_iso_date` retorna `None` em erro e um item sem `lead_time_days` é
silenciosamente omitido da projeção temporal
(`gerar-corda/scripts/build_universe.py#L1768-L1774` e `#L1954-L1977`).

**Reprodução temporal:** `due_at: "not-a-date"` com `observed_at` válido
produziu `COMPILE_RUNTIME`, nenhuma contradição e nenhum item datado no painel.

[fact] `record_acceptance.py` exige apenas texto não vazio para `date`
(`#L41-L45`) e persiste o valor sem parsing (`#L60-L82`), embora o schema exija
formato `date`
(`runs/v4-development/cycles/ciclo-01/schema/projection-extension.schema.json#L176-L187`).

**Reprodução de aceite:**

```bash
python3 gerar-corda/scripts/record_acceptance.py \
  --state /tmp/state.json --outcome accepted --owner owner \
  --date not-a-date --statement ok --source-ref x
```

**Observado:** retorno `0`, `decision.state: accepted`,
`decided_at: "not-a-date"`.

[inference] C5 funciona para datas ISO válidas, mas P4 não assegura um registro
“completo” segundo o próprio schema.

### S-06 — Alta — o build versionado não fecha sobre a fonte canônica do HEAD

[fact] `gerar-corda/` é a fonte canônica. O commit de preparação `b8a9afe`
alterou `gerar-corda/SKILL.md`, que é também evidência por conteúdo do manifesto,
sem regenerar `runs/v4-development/build/`.

**Reprodução:**

```bash
python3 gerar-corda/scripts/build_universe.py \
  --spec runs/v4-development/manifest/corda-v4-manifest.json \
  --out-dir /tmp/sol-current --basename corda-v4
jq -r .universe_id /tmp/sol-current/corda-v4-universe.json
jq -r .universe_id runs/v4-development/build/corda-v4-universe.json
```

**Observado:** o HEAD recompilado gera
`corda-v4-universo-de-desenvolvimento-6ff48fb07b2e`; o build versionado contém
`...c4f555d7086c`. A identidade de `skill-canonica` mudou de
`sha256:7443...83f6b` para `sha256:097c...650c5`; o snapshot de evidência e
`projection_data` também mudam.

[fact] O aceite `adjusted` e a avaliação `evaluated_inconclusive` versionados
estão ligados ao universo `...c4f555d7086c`. A tag `35fd751` preserva esse
objeto histórico.

[inference] A tag continua útil como pin histórico, mas o HEAD solicitado não é
um bundle autoconsistente “fonte canônica + derivados + estado”. Antes de
promoção é necessário escolher um único objeto candidato, recompilar e reaplicar
ou migrar os registros mutáveis com vínculo explícito.

### S-07 — Média — STATE/BOOTSTRAP e EVALUATION divergem sobre o estado da avaliação

[fact] `runs/v4-development/build/corda-v4-EVALUATION.json#status` é
`evaluated_inconclusive` e sua promoção é `not_eligible`.
`runs/v4-development/build/corda-v4-STATE.json#evaluation.status` continua
`compiled_unevaluated`; esse STATE é incorporado no BOOTSTRAP.

[fact] `record_evaluation.py` só muta EVALUATION e não emite delta ou evento
para STATE (`gerar-corda/scripts/record_evaluation.py#L167-L227`).

**Reprodução:**

```bash
jq '.status,.promotion.status' \
  runs/v4-development/build/corda-v4-EVALUATION.json
jq '.evaluation' runs/v4-development/build/corda-v4-STATE.json
```

[inference] Um runtime carregado pelo caminho recomendado recebe um checkpoint
que contradiz a fonte de avaliação. O contrato precisa definir autoridade e
sincronização entre esses dois estados.

### S-08 — Média — o gate de portabilidade atravessa a fronteira do holdout

[fact] `scan_private_coupling()` usa `ROOT.rglob("*")` e lê conteúdo de todos os
arquivos com extensões selecionadas, inclusive ignored/untracked
(`scripts/verify_repo.py#L51-L69`).

**Reprodução:** inspeção estática das linhas acima; executar o verificador no
objeto completo violaria a restrição de não leitura, por isso a reprodução foi
feita na cópia filtrada descrita na tabela.

[inference] Um gate do núcleo não deve depender de, nem ler, holdout selado,
registro de caveats ou outputs do usuário. O scanner deve ter allowlist do
núcleo auditado ou exclusões executáveis.

### S-09 — Baixa — determinismo é de conteúdo, não de localização

[fact] Dois builds em diretórios distintos produziram hashes idênticos para
14/14 artefatos puramente derivados inspecionados. O único diff foi
`corda-v4-ledger.md`, que incorpora caminhos absolutos do diretório de saída
(`gerar-corda/scripts/build_universe.py#L2517-L2554`).

**Reprodução:**

```bash
python3 gerar-corda/scripts/build_universe.py --spec \
  runs/v4-development/manifest/corda-v4-manifest.json \
  --out-dir /tmp/sol-a --basename corda-v4
python3 gerar-corda/scripts/build_universe.py --spec \
  runs/v4-development/manifest/corda-v4-manifest.json \
  --out-dir /tmp/sol-b --basename corda-v4
diff -qr /tmp/sol-a /tmp/sol-b
```

[inference] O claim de layout/derivados determinísticos está sustentado; a frase
genérica “rebuild byte-idêntico” deve continuar qualificada por artefato e
localização.

## Veredito por claim

| Claim | Veredito | Fundamentação |
| --- | --- | --- |
| C1 | **não verificável** | [fact] No compilador corrente, ausência de `projection` não emite `projection_data`, e o toggle preservou ID/STATE/BOOTSTRAP. [inference] “outputs v3 inalterados” historicamente não pode ser verificado sem executável/tag v3 ou golden outputs completos pinados. |
| C2 | **refutado** | [fact] Chaves derivadas testadas viram `contradictory` e bloqueiam runtime; porém painéis, algoritmo, dimensões e iterações fora do schema passam. Logo o composto “allowlist estrito” é falso (S-04). |
| C3 | **refutado** | [fact] Campos vazios e owner divergente são recusados; atribuição não é autenticação. [fact] `decided_at=not-a-date` é aceito, contrariando a completude/schema do registro (S-05). |
| C4 | **refutado** | [fact] Semente fixa reproduz coordenadas e o stress/escala são publicados. [fact] `algorithm` é só rótulo, `dimensions` é ignorado e o `projection_data` versionado não é a recomputação do HEAD (S-04, S-06). |
| C5 | **confirmado** | [fact] R8 reproduziu `4 → 2 → -2`, com `overdue=true` no negativo, para `due_at` ISO válido. Datas inválidas têm a falha separada S-05. |
| C6 | **confirmado** | [fact] Builds com/sem projeção deram o mesmo `universe_id`, STATE e BOOTSTRAP; `stable_id` remove `projection` e `projection_data` (`build_universe.py#L88-L98`). |
| C7 | **confirmado** | [fact] O scorer versionado reproduziu deterministamente baseline 0/3 e candidata 3/3. [inference] Isso não valida a comparação como baseline histórica v3 (S-03). |
| C8 | **confirmado** | [fact] Busca independente no núcleo não encontrou caminho pessoal, cliente identificável, segredo ou output proprietário. As ocorrências de “cliente” são fixtures sintéticas do CAST. |
| C9 | **confirmado** | [fact] O artefato corrente está `evaluated_inconclusive`/`not_eligible`, e nenhum script observado conclui aceite de promoção sem humano. [inference] A elegibilidade prévia é fabricável (S-02), portanto a confirmação é estrita ao claim de aceite final e ao estado corrente. |
| C10 | **confirmado** | [fact] README e `docs/VERIFICATION.md` distinguem `deterministically verified`, `agent-reviewed`, `human accepted` e limitam `externally audited` ao núcleo v2.2.3. Não alegam generalização. |

## Opinião solicitada

### 1. Lei de derivação de elenco

[inference] A intuição é boa como **heurística de recusa e compressão**:
evidência realmente separável pode justificar observadores distintos; papéis
topológicos não devem nascer de gosto; recusar teatro multiagente é uma função
valiosa.

[inference] Ela ainda não é uma lei sólida:

1. igualdade de acesso a evidência não implica igualdade de pergunta, estimando
   ou função de perda;
2. a relação de fusão precisa ser uma equivalência ou um algoritmo de fechamento
   definido; hoje é gulosa e dependente da ordem;
3. dano ortogonal precisa de semântica consistente para owner, evidência,
   severidade e poder, não apenas dois testes de conjunto;
4. evidência declarada pode ser incompleta, falsa ou facilmente particionada
   para fabricar separabilidade;
5. custo, latência, capacidade de ferramenta e autoridade podem justificar
   decomposição mesmo quando o corpus se sobrepõe;
6. recusa automática não pode apagar uma lente cuja ausência vem de um buraco do
   corpus.

[inference] Eu reformularia a unidade de derivação como
`(pergunta/claim, evidência, ferramenta, domínio de dano, autoridade)` e exigiria
testes metamórficos de permutação, idempotência e fechamento.

### 2. Self-hosting

[inference] Self-hosting é evidência de **executabilidade, dogfooding,
reprodutibilidade local e capacidade de expor falhas próprias**. Não é evidência
independente de utilidade, generalidade ou correção do formalismo; autor,
instrumento, dados, oracle e aceitação continuam correlacionados. Neste objeto,
S-02 e S-03 mostram precisamente esse risco.

[inference] Só uma aplicação externa prospectiva provaria o que falta: domínio
não usado para escrever o sistema, owner com poder real de rejeitar, tarefa e
métricas pré-registradas, baseline executável pinada, dados não autorais,
exceções reais, custo/latência, usuários e reviewer humano ou organização
externa.

### 3. Mudanças antes de promover v3→v4

1. Corrigir a derivação de elenco e adicionar testes metamórficos de permutação,
   fechamento, duplicação e casos-limite de dano/owner.
2. Aplicar o schema na fronteira: enums de painéis/algoritmos, `dimensions=2`,
   bounds de iteração/semente, datas ISO e tipos que excluam booleanos.
3. Executar uma baseline v3 pinada por commit/hash pelo mesmo harness, sem
   hardcode de ausência.
4. Fazer o scorer emitir um relatório content-addressed e fazer
   `record_evaluation.py` recomputar métricas/cobertura a partir desse relatório,
   verificar hashes, commit e existência das evidências.
5. Separar estado gerado de ledger mutável append-only ou definir merge
   determinístico; sincronizar STATE, EVALUATION e BOOTSTRAP.
6. Montar um único bundle candidato no mesmo commit: fonte canônica, manifesto,
   derivados, testes e registros migrados; só então taguear.
7. Restringir `verify_repo.py` ao núcleo e manter o holdout fora de qualquer scan
   geral ou contexto de agente.
8. Realizar teste externo de uso/visual/acessibilidade antes de qualquer claim de
   decisão pronta.

### 4. Preprint

[inference] Sim, o material sustenta um preprint honesto como **framework
executável + estudo de caso self-hosted**, desde que o texto não venda eficácia
ou generalização. Claims defensáveis: formalização compilável, separação
runtime/overlay, invariantes executáveis, reprodutibilidade nos benchmarks
autorais e relato de falhas/correções.

[inference] O preprint deve chamar 0/3→3/3 de teste de conformidade da extensão,
não de superioridade; declarar N pequeno, oracle correlacionado, baseline não
pinada, ausência de aplicação externa e os achados desta auditoria. Um estudo
externo pré-registrado deveria ser trabalho futuro ou condição para claims mais
fortes.

## Limite inferencial

Esta auditoria:

- não leu nem executou o holdout `authority-forged-*`;
- não prova generalização, utilidade em produção, segurança de autenticação,
  isolamento do host, acessibilidade, legibilidade ou desempenho;
- não valida a verdade/suficiência dos datasets e ground truths autorais;
- não constitui aceite humano de arquitetura ou promoção;
- reduz monocultura de família de modelo, mas não cria independência humana;
- auditou o HEAD `79ef9e1...` e tratou `35fd751...` como referência histórica,
  não como o mesmo objeto;
- não publicou, não criou release e não escolheu licença.

## Cruzamento com caveats conhecidos

O REGISTRO foi lido somente depois do selamento dos achados S-01 a S-09.
`novo para mim` significa que o item não integrou os achados independentes;
quando possível, ele foi ainda assim verificado após o cruzamento.

| Caveat do REGISTRO | Marca | Cruzamento |
| --- | --- | --- |
| Z1: `due_at` absoluto corrige tensão que não acumulava | **confirmo** | R8 e a avaliação temporal reproduziram 4→2→−2 para data absoluta. |
| Z3: rebuild zera STATE/verification; scripts + tag mitigam | **confirmo** | S-06/S-07 reproduzem a consequência no HEAD. A tag preserva o objeto antigo, mas a mitigação não produz um HEAD autoconsistente. |
| Z4: ciclo 03 incluído no aceite `adjusted` | **confirmo** | O `acceptance_record.statement` versionado inclui expressamente ciclo 03/Z1/Z3/Z4 e D1–D3. Isto confirma atribuição declarada, não autenticidade externa. |
| Bypass P1 corrigido por “allowlist estrito” | **refuto** | Há allowlist de chaves, mas não enforcement estrito do schema: painel/algoritmo arbitrário, `dimensions != 2`, booleanos e iterações negativas passam (S-04). |
| Runner não descobre/executa `authority-forged-*` | **confirmo** | O runner enumera exatamente três funções/casos; o holdout não é descoberto. Nenhum arquivo selado foi lido para chegar a essa conclusão. |
| Caso authority contém baseline afirmada e asserção sobre prosa | **confirmo** | S-03: `mechanism_available: false` é hardcoded e `transition_requirement` é texto do runner. |
| “Baseline v3” é ablação v4 sem `projection` | **confirmo** | É o centro de S-03; não há executável/tag v3 pinado. |
| Scorer: `exists` vazio e `find.where={}` passam de modo fraco | **novo para mim** | Verificação pós-cruzamento confirma `resolve(..., "") -> (True,obj)`, `op=exists -> pass` e `all(...)` sobre `where={}` selecionando o primeiro elemento (`score_cases.py#L20-L81`). |
| `downgrade_state.py`: efeito parcial com `events` malformado; owner não confrontado | **novo para mim** | Inspeção pós-cruzamento confirma que o arquivo morto é escrito em `#L48-L90` antes de `state.setdefault("events", []).append` em `#L91-L107`, e que `--owner` só é não vazio, sem comparação com `decision.owner`. |
| `canonical_registry`: newline no ID; path absoluto/CWD | **novo para mim** | Inspeção pós-cruzamento confirma ID apenas com `strip`, `Path(content_path)` sem confinamento e resolução relativa ao CWD (`build_universe.py#L118-L163`). |
| Suíte v3 provada por contagem 24+8, sem baseline nominal | **confirmo** | Fundamenta o `não verificável` de C1: o delta de contagem existe, mas não há lista/golden histórico completo pinado. |
| Sem caminho sancionado de re-upgrade STATE 1.4→1.5 | **novo para mim** | Nenhum script de re-upgrade foi encontrado; o fluxo documentado manda rebuild + reaplicação manual de mutações. |
| Render: stress 0,2521, tooltip só mouse, sem teste com usuário | **confirmo** | Stress 0,2521 foi observado; HTML liga tooltip a `mousemove/mouseleave` sem foco/touch; `visual_review` permanece `not_performed`. |
| P4 é atribuição, não autenticação | **confirmo** | O owner é comparação textual; não há identidade criptográfica ou autorização no host. |
| Amostras pequenas e limiar discreto | **confirmo** | 9/4/3 casos; `task_success` em n=3 tem passo de 1/3. Nenhum claim de generalização foi aceito. |
| Avaliação cobre o enquadramento dos três painéis e é coautoral | **confirmo** | Truths e runner foram escritos no mesmo processo; S-03 limita a interpretação a conformidade. |
| Nenhum uso externo; sem custo single vs multi | **confirmo** | Nenhuma evidência de aplicação externa/custo foi localizada; a seção de opinião trata isso como lacuna necessária. |
| Todos os pares internos `weak` | **confirmo** | Rebuild do HEAD: `independence_report.summary = {"weak": 10}`. Esta revisão cross-model ainda é `agent-reviewed`, não corroboração humana. |
| Licença, holdout selado e `visual_review` pendentes | **confirmo** | README mantém licença pendente; EVALUATION/verification registram holdout e `visual_review` como pendentes. O holdout não foi inspecionado. |

### O que foi realmente novo

[fact] Não constavam do REGISTRO: S-01 (ordem/ortogonalidade do elenco), S-02
(elegibilidade fabricável em `record_evaluation.py`), S-04 (drift entre schema e
allowlist/algoritmo), S-05 (datas inválidas), S-08 (scanner atravessa o holdout)
e S-09 (ledger dependente de localização).

[inference] S-06 e S-07 aprofundam Z3: o caveat conhecido dizia que rebuild
zera estado; esta auditoria demonstrou também que um commit posterior na fonte
canônica mudou `universe_id` sem regenerar o build, deixando HEAD, EVALUATION,
STATE e BOOTSTRAP em planos de identidade/estado diferentes.
