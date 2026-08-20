> **REDACTED PUBLIC COPY** — names and paths of the field-test subject were replaced by a declared mechanical map (see PUBLIC-CUT-NOTE.md). The canonical original lives in the maintainer's private archive; original sha256 (first 16): `24bb12aa61c35d81`.

# Parecer da CORDA v4 pós-correções e pós-campo — Codex Sol

## Identidade, natureza e escopo

- **Parecerista:** Sol, OpenAI `gpt-5.6-sol` (Codex), 2026-08-19.
- **Objeto principal:** candidata `v4-ciclo-05-pos-sol` (`d28cade`) e evidência
  posterior do ciclo 06/implantação `[field-project]/[field-install]/`.
- **Natureza:** parecer sobre mudança de estado desde a auditoria de 2026-07-29;
  não é uma re-auditoria completa nem aceite humano.
- **Classe de revisão:** `agent-reviewed` por família de modelo distinta da usada
  na implementação e no campo. As sondas pontuais abaixo são
  `deterministically verified`; a conclusão não é auditoria humana independente.
- **Escopo respeitado:** li o repo CORDA e, no [field-project], somente
  `[field-project]/[field-install]/**`. Não li `authority-forged-*`, `LEGADO/`,
  `!_[field-project]_V5/` nem dossiês externos a essa pasta. Formei O1–O5 antes de ler
  `docs/audits/REGISTRO-caveats-conhecidos-v4.md`.

## Veredito executivo

**O estado mudou materialmente a favor da candidata, mas ela ainda não é
elegível para promoção.** As correções S-01, S-04 no código executável, S-05,
S-08 e S-09 estão demonstradas por propriedades locais reproduzíveis; a nova
baseline elimina a ablação como substituto de uma execução v3; e o campo
fornece a primeira evidência real de utilidade operacional estreita.

Todavia, três condições centrais da reprovação não fecharam de ponta a ponta:

1. **S-02 continua contornável:** `task_success` é recomputado, mas sobre uma
   lista que aceita casos fora do contrato; uma sonda com o único holdout
   esperado em `false` e 99 casos estranhos em `true` produziu
   `promotion_candidate`/`awaiting_human_acceptance`.
2. **S-06 recorre no objeto pinado:** o rebuild de `d28cade` preserva o
   `universe_id`, mas não reproduz EVIDENCE/projection/universe byte a byte. O
   build versionado degrada `auditoria-codex-sol` para `id:`; o rebuild a partir
   da raiz resolve o arquivo e usa seu SHA-256, mudando o snapshot de evidência.
3. **S-07 é best-effort, não transacional:** EVALUATION é gravado antes de STATE;
   STATE inválido faz o comando retornar 2 depois de EVALUATION já ter mudado.

Minha recomendação é **não promover `d28cade`**. Corrigir essas fronteiras,
resolver os achados operacionais de campo, congelar uma nova candidata e só
então executar holdout, gate isolado e aceite humano.

## O1 — Correções

**Resposta:** as condições da reprovação foram **materialmente reduzidas, mas
não integralmente endereçadas**. Eu não endosso a frase “9/9 corrigidas” como
claim de fechamento; endosso “9/9 receberam implementação, e as reproduções
originais deixaram de reproduzir”. A distinção importa porque as sondas novas
atingem a mesma fronteira de promoção por caminhos diferentes.

### O que considero resolvido

- **S-01:** a partição passou a ser fechamento por componentes, com
  representante derivado do conteúdo, e ganhou testes metamórficos. O campo
  acrescentou uma partição única em seis permutações reais e reprodução exata
  da partição v3.x (`ciclo-05-sintese.md#L16`; relatório de campo
  `#L18-L20`). Isto resolve o defeito de ordem observado, não transforma a
  heurística em lei.
- **S-04 no executável:** painéis, algoritmo, dimensões, inteiros estritos e
  limites são agora rejeitados na fronteira do compilador
  (`gerar-corda/scripts/build_universe.py`, função
  `assess_projection_integrity`; síntese C05 `#L19`).
- **S-05:** datas malformadas viram contradição no build ou recusa nos mutadores
  (`ciclo-05-sintese.md#L20`).
- **S-08:** o verificador tem exclusões executáveis para material selado/fora de
  escopo (`scripts/verify_repo.py`, `_is_sealed_or_out_of_scope`).
- **S-09:** o ledger passou a registrar basenames, não caminhos absolutos
  (`gerar-corda/scripts/render_corda.py`, renderização do ledger).

Essas são propriedades mecânicas locais. A perda de isolamento do ciclo 05
reduz corroboração, mas não apaga o valor das execuções determinísticas; o
próprio ciclo descreve corretamente essa limitação
(`ciclo-05-sintese.md#L32-L54`).

### O que está apenas parcialmente resolvido

- **S-02:** o recomputo declarado em `record_evaluation.py#L68-L114` fecha a
  minha forja original, porém `assess_case_coverage` constrói mapas sem rejeitar
  IDs inesperados/duplicados (`#L137-L175`), enquanto o recomputo usa todos os
  itens da lista. Como a elegibilidade só consulta `coverage.complete`,
  `holdout_covered` e threshold (`#L281-L290`), casos extras podem inflar a
  métrica. Antes da promoção, exigir igualdade exata e unicidade entre casos do
  contrato e resultados, rejeitar extras/duplicatas, validar a baseline pelo
  mesmo conjunto e tornar obrigatório o relatório content-addressed do scorer.
- **S-06:** o procedimento foi escrito (`ciclo-05-sintese.md#L21`), mas o objeto
  `d28cade` não fecha por rebuild. O build versionado contém
  `identity_token: id:auditoria-codex-sol` (o mesmo padrão ainda aparece no
  build corrente em `corda-v4-EVIDENCE.json#L23-L42`); no rebuild a partir da
  raiz, o token é `sha256:a5eead8e...`. O snapshot muda de
  `d28a5dbb...` para `f175f92f...`, propagando a diferença a EVIDENCE,
  `projection_data` e `universe.json`, embora o ID estável permaneça
  `...fe5a3c39eae1`. É preciso resolver `content_path` contra uma raiz canônica,
  falhar quando evidência esperada degrada de hash para id e adicionar um gate
  de rebuild do bundle candidato.
- **S-07:** `--state` é opcional e EVALUATION é escrita em
  `record_evaluation.py#L298-L303` antes de STATE ser lido em `#L305-L332`.
  Minha sonda com STATE malformado retornou 2, mas deixou EVALUATION com um run
  novo e status alterado. Validar todos os destinos antes de qualquer escrita e
  fazer commit atômico/recuperável; quando o contrato declara STATE associado,
  a sincronização não pode ser opcional.
- **S-04 como pacote documental:** o código é estrito, mas a fonte canônica da
  skill ainda chama o enforcement de “pendência aberta”
  (`gerar-corda/SKILL.md#L200-L205`), e o schema JSON histórico aceita qualquer
  string em `algorithm` e nem declara `iterations`
  (`projection-extension.schema.json#L19-L28`). Código, schema e texto devem
  convergir antes de a versão ser promovida.

### Exigência antes de elegibilidade

Corrigir S-02/S-06/S-07 acima; reconciliar schema e documentação; fechar A-01
(veto sem owner) e o registro MAST de execução real; gerar um novo objeto
candidato autoconsistente. Só depois fazem sentido holdout e gate final.

## O2 — C1 e a baseline v3

**Resposta:** a nova baseline satisfaz a lacuna de **executabilidade e pinagem
operacional**, mas não completa, sozinha, C1 nem transforma 0/3→3/3 em prova de
superioridade.

Os dois arquivos preservados têm hashes que conferem com `BASELINE.md#L8-L11`;
o driver executa o módulo em subprocesso e mede a ausência dos mecanismos v4,
em vez de hardcodá-la (`BASELINE.md#L13-L19`). Isto é muito melhor que a antiga
ablação: o resultado passa a significar **“a candidata implementa três
capacidades que o snapshot v3 não implementa, nos três casos autorais deste
contrato”**.

Mantenho duas reservas:

1. A proveniência histórica ainda é **atestada pelo owner**, não verificável por
   uma tag/commit pré-v4. `BASELINE.md#L3-L6` diz que o snapshot veio do disco no
   início da sessão; o repo não contém um objeto Git v3 anterior que permita a
   um terceiro provar essa origem. Portanto, a formulação rigorosa é “snapshot
   v3 histórico atestado pelo owner e agora pinado”, não “baseline histórica
   provada pelo repositório”.
2. C1 é retrocompatibilidade, não presença de feature. O runner adiciona
   `projection` apenas quando `with_projection=True`
   (`run_evaluation_cases.py#L56-L91`); logo baseline e candidata não recebem
   manifestos byte-idênticos nesse comparativo. O 0/3→3/3 não compara todos os
   outputs comuns da v3 contra a v4 sem bloco. Essa prova continua sendo a
   suíte nominal/goldens v3 e um diferencial de outputs comuns. O campo cobre
   um exemplar real forte — manifesto v3-era preservou duas exigências e a
   independência 6/4 (`relatorio-teste-campo.md#L18-L24`) —, não todo o domínio
   de regressão.

Assim, **mudo** minha leitura de “ablação” para “comparação executável contra
snapshot v3 atestado”; **não mudo** a conclusão sobre superioridade. A prova
nominal da suíte v3 permanece bloqueador correto.

## O3 — Campo e utilidade

**Resposta:** sim, este é o tipo de evidência que eu tinha em mente, e ele
permite afirmar **utilidade demonstrada neste episódio**, com atribuição
estreita.

Há três sinais reais:

- os critérios foram pré-registrados antes da execução e congelaram a referência
  (`criterios-teste-campo.md#L1-L12`, `#L35-L76`);
- o painel v4 tornou visíveis um prazo absoluto real e a entropia vencida em 44
  dias (`[field-install]/README.md#L15-L20`);
- o gate reprovou D1 por contornar a governança e D5 por ordenar tratamento de
  dado pessoal sem base, devolveu somente o §7 e o reparo passou
  (`gate-veredito.md#L19-L31`, `#L35-L49`;
  `gate-veredito-v2.md#L9-L29`). Isso é uma intervenção de qualidade de decisão,
  não mera executabilidade.

O limite é causal. Os nove testes do gate já estavam no manifesto operacional;
a execução foi manualmente orquestrada; lentes, Mesa, adversários e gate
compartilharam modelo-base; e o próprio MAST marca FM-3.1/FM-3.2 como observados
(`mast-assessment-rodada-01.json#L17-L20`). Portanto:

- **utilidade do loop/gate CORDA neste caso:** demonstrada;
- **utilidade incremental do painel temporal v4:** demonstrada como sinal útil;
- **v4 melhor que v3, utilidade geral ou efeito organizacional durável:** não
  demonstrados.

Para ampliar o claim, ainda faltam: decisão/feedback explícito do owner dizendo
como o artefato mudou uma decisão real; acompanhamento do desfecho; custo,
latência e retrabalho comparados ao fluxo anterior; mais execuções reais em
outros assuntos (incluindo exceções); e ao menos um gate/reviewer de outro
modelo-base ou humano com poder de rejeição. Para chamar o mecanismo de estável,
eu usaria o gate operacional de cinco execuções reais, incluindo uma com
reparo/exceção; a rodada 01 já satisfaz justamente o exemplar difícil dessa
série.

## O4 — Enquadramento da promoção

**Resposta:** reformulo. “Superconjunto compatível da v3, sem regressão” ainda é
amplo demais, porque “sem regressão” soa universal e “superconjunto” pode ser
lido como equivalência comportamental provada.

A afirmação sustentável hoje é:

> **A candidata v4 implementa uma extensão opcional e aditiva da v3. Na suíte
> publicada e em um universo v3-era não sintético, não foram observadas
> regressões nos comportamentos comparados; as capacidades novas executaram nos
> três casos autorais de aceitação e em uma implantação de campo. Superioridade
> e generalização não estão demonstradas.**

Isto endossa o espírito do enquadramento do integrador, mas restringe o alcance
de “compatível” e “sem regressão” ao conjunto observado. O próprio relatório de
campo já reconhece que não demonstra “melhor” (`relatorio-teste-campo.md#L70-L79`).

**Sim, a “lei do elenco” deve ser rebaixada antes da promoção.** O fecho
transitivo agora fornece uma regra determinística bem definida, mas as premissas
continuam sendo uma modelagem: igualdade de evidência declarada não implica
igualdade de pergunta, ferramenta, função de perda ou autoridade; e uma cadeia
de sobreposições pode fundir lentes cujos extremos são separáveis. A skill ainda
afirma categoricamente “o número de agentes não se escolhe”
(`gerar-corda/SKILL.md#L3`, `#L26-L34`). Eu usaria **“heurística/regra operacional
de derivação do elenco sob o grafo de evidência declarado”**, deixando explícito
que o resultado é candidato a revisão por buracos de corpus, custo, autoridade
e dano. Rebaixar agora evita promover linguagem epistemicamente mais forte que
a evidência.

## O5 — Bloqueadores restantes e ordem

**Resposta:** a lista proposta contém bloqueadores corretos, mas está incompleta
e na ordem errada. O gate isolado não deve rodar sobre `d28cade` se as correções
abaixo criarão uma candidata nova.

Ordem recomendada:

1. **Fechar as fronteiras de promoção:** corrigir padding/duplicatas e tornar o
   scorer content-addressed obrigatório; tornar EVALUATION↔STATE transacional.
2. **Fechar os achados de campo que afetam autoridade/observabilidade:** A-01
   (veto sem owner deve bloquear ou degradar explicitamente); selecionar/registrar
   MAST quando a execução realizada for multiagente; adicionar carimbo de
   compilador ou vínculo automático equivalente. O campo registra o veto morto e
   a ausência de carimbo em `relatorio-teste-campo.md#L45-L62`, e o trace registra
   que a execução real não acionou MAST automaticamente
   (`rodada-01-trace.json#L33-L37`).
3. **Congelar uma nova candidata autoconsistente:** resolver paths contra raiz
   canônica, reconstruir de localizações distintas, exigir hashes idênticos dos
   derivados definidos como portáveis, reaplicar mutações por caminho sancionado
   e alinhar SKILL/schema/README/VERIFICATION. Reexecutar a bateria S-01…S-09.
4. **Compatibilidade/migração:** rodar a suíte nominal v3 sobre a baseline pinada,
   comparar outputs comuns v3↔v4 sem `projection` e testar round-trip
   STATE 1.4→1.5→1.4 (incluindo registros, recuperação e confronto do owner no
   downgrade). O próprio ciclo 06
   mantém re-upgrade na fila (`ciclo-06-trace.json#L46-L52`).
5. **Preparar o holdout antes de revelá-lo:** fazer o runner descobrir exatamente
   os casos selados, rejeitar extras/duplicatas e registrar hashes; só então o
   owner gera o holdout fora de contexto e o executa sobre a candidata final.
6. **Gate adversarial isolado e cross-model sobre a candidata final**, não sobre
   `d28cade`; incluir minhas reproduções novas, fechamento do bundle, migração e
   os achados A-01/MAST. A reprovação interna foi sinal forte, mas a aprovação
   interna permaneceu fraca por declaração do próprio gate
   (`gate-veredito-v2.md#L3-L7`, `#L27-L39`).
7. **Revisão humana visual/de interação/acessibilidade**, incluindo teclado,
   toque, ranking e legibilidade; depois **aceite humano explícito** da promoção.

Licença e decisão sobre anonimização/remoção do caso [field-project] são bloqueadores de
**publicação**, não necessariamente da promoção interna; o próprio relatório
marca essa fronteira (`relatorio-teste-campo.md#L84-L88`).

## Achados novos

### N-01 — Alta — cobertura permite inflar `task_success` com casos fora do contrato

**Sonda:** contrato com um holdout esperado; resultado desse holdout `false`;
99 casos não previstos `true`; baseline 0,0; candidata 0,99.

**Observado:** retorno 0, `case_coverage.complete=true`,
`holdout_covered=true`, `observed_case_count=100` para
`expected_case_count=1`, status `promotion_candidate` e
`awaiting_human_acceptance`.

**Causa:** o recomputo usa toda a lista (`record_evaluation.py#L73-L77`), mas a
cobertura não rejeita `actual - expected` nem duplicatas (`#L137-L175`).

### N-02 — Alta — `d28cade` não fecha por rebuild da evidência

**Sonda:** `git archive d28cade`; build a partir da raiz extraída; comparação
dos derivados com `runs/v4-development/build/` da mesma tag.

**Observado:** mesmo `universe_id` (`...fe5a3c39eae1`), porém:

| Artefato | SHA-256 versionado | SHA-256 rebuild | Igual |
|---|---|---|---|
| `corda-v4-universe.json` | `007a3434...` | `62325d0f...` | não |
| `corda-v4-projection-data.json` | `fd911cb6...` | `d48eabd4...` | não |
| `corda-v4-EVIDENCE.json` | `15722ed5...` | `605f5bf8...` | não |

A diferença causal é a evidência `auditoria-codex-sol`: `id:` no build
versionado versus hash de conteúdo no rebuild; snapshot `d28a5dbb...` versus
`f175f92f...`. Isto refuta o fechamento de S-06 no objeto pinado.

### N-03 — Média — sincronização EVALUATION→STATE deixa efeito parcial

**Sonda:** run válido com `--state` apontando para JSON malformado.

**Observado:** retorno 2 e STATE intacto, mas EVALUATION já ganhou o run e mudou
para `evaluated_inconclusive`. A ordem de escrita está em
`record_evaluation.py#L298-L332`.

### N-04 — Média — contrato documental de projeção diverge do executável

O código corrigido aplica enum/bounds, mas a skill ainda registra S-04 como
pendência (`gerar-corda/SKILL.md#L200-L205`) e o schema JSON não enumera algoritmo
nem admite `iterations` (`projection-extension.schema.json#L19-L28`). Antes da
promoção, existe uma única verdade normativa a escolher e versionar.

## Cruzamento com o REGISTRO de caveats conhecidos

O REGISTRO foi lido somente depois de O1–O5 e N-01…N-04 estarem redigidos.

| Item do REGISTRO | Marca | Cruzamento pós-campo |
|---|---|---|
| Z1 / `due_at` absoluto | **confirmo** | O painel do [field-project] materializou `2026-08-28` como prazo absoluto e −44 dias de entropia (`[field-install]/README.md#L15-L18`). |
| Z3 / rebuild + reaplicação de mutações | **confirmo como mitigação, refuto como fechamento** | N-02 mostra nova recorrência no próprio `d28cade`: mesma identidade estável, snapshot de evidência divergente. |
| Bypass P1 virou allowlist estrito | **confirmo no código, restrinjo no contrato** | O executável agora tem enum/tipos/bounds (`build_universe.py#L738-L818`); SKILL e schema continuam divergentes (N-04). |
| Runner não descobre holdout | **confirmo** | Continua explicitamente na fila do ciclo 06 (`ciclo-06-trace.json#L46-L50`). |
| Baseline era ablação / authority parcialmente afirmado | **obsoleto em parte** | A baseline agora é um snapshot executável; ausência de mecanismo é medida. Ainda resta uma string de requisito produzida pelo harness e o comparativo não usa manifesto byte-idêntico. |
| Fraquezas `exists`/`find.where` do scorer | **confirmo como abertas; N-01 é distinto** | N-01 não depende desses operadores: explora a fronteira entre coverage e recomputo em `record_evaluation.py`. É novo para o REGISTRO. |
| `downgrade_state.py` com efeito parcial / owner não confrontado | **parcialmente corrigido** | O script agora valida `events` antes de escrever, mas ainda só exige owner não vazio; incluir confronto de autoridade e round-trip no gate de migração. |
| `canonical_registry` resolve path relativo contra CWD | **confirmo; recorrência nova** | O mecanismo já era conhecido (`REGISTRO#L33-L34`); o fato novo é que ele contaminou o bundle declarado corrigido da tag `d28cade` (N-02). |
| Suíte v3 não nominal; sem re-upgrade; render sem teste humano | **confirmo** | Os três continuam na fila, agora acompanhados por uma baseline executável. |
| P4 é atribuição, não autenticação | **confirmo** | Nada neste parecer eleva a fronteira a autenticação. |
| Amostras pequenas / avaliação coautoral | **confirmo** | Limita 0/3→3/3 a conformidade/capacidade no contrato publicado. |
| Nenhum uso real fora do self-hosting | **refuto por obsolescência temporal** | O ciclo 06 e `[field-install]/rodada-01` são uso real pós-REGISTRO, embora ainda sem independência organizacional/model-diversa e sem custo comparado. |
| Todos os pares internos weak | **confirmo** | O gate de campo declara aprovação fraca e o MAST mantém FM-3.2 observado. |
| Licença, holdout e visual review pendentes | **confirmo** | Licença bloqueia publicação; holdout e visual review bloqueiam promoção. |

O cruzamento não elimina nenhum achado independente. Ele muda apenas a origem
de N-02: a fragilidade de CWD já era conhecida, mas sua recorrência no pacote
que se declarava autoconsistente não constava do REGISTRO.

## Claims que refuto ou restrinjo

- **“9/9 constatações corrigidas” — refuto como fechamento.** Aceito “9/9
  receberam correção e as sondas originais ficaram verdes”; N-01/N-02/N-03
  mostram S-02/S-06/S-07 ainda abertas em propriedades materiais.
- **“Baseline e candidata rodam o mesmo manifesto” — restrinjo.** Rodam o mesmo
  conteúdo-base e scorer, mas `minimal_manifest(..., with_projection)` inclui a
  seção apenas para a candidata (`run_evaluation_cases.py#L56-L91`).
- **“0/3→3/3 prova superioridade” — refuto.** Prova disponibilidade/conformidade
  das extensões nos três casos autorais contra um snapshot v3 executável.
- **“Superconjunto compatível sem regressão” — restrinjo ao escopo observado.**
  Não houve regressão na suíte publicada e no caso [field-team] comparado; não existe
  prova universal.
- **“O campo ainda prova só executabilidade” — refuto.** O fail devolutivo em
  governança/LGPD e o reparo demonstram utilidade do gate neste episódio; não
  demonstram superioridade geral da v4.
- **“Gate isolado sobre `d28cade` é o próximo passo” — refuto.** As correções
  materiais exigem nova candidata; o gate final deve avaliar esse objeto.

## Limite inferencial

Este parecer não valida a verdade do corpus [field-project], não leu dados pessoais fora da
pasta autorizada, não executou o holdout selado, não constitui decisão jurídica
sobre LGPD, não prova generalização, não realiza inspeção visual humana e não
aceita nem promove a versão. O owner continua sendo a única autoridade para a
promoção.
