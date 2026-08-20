> **REDACTED PUBLIC COPY** — names and paths of the field-test subject were replaced by a declared mechanical map (see PUBLIC-CUT-NOTE.md). The canonical original lives in the maintainer's private archive; original sha256 (first 16): `97b0951c635abe52`.

# Crítica adversarial cross-model — artigo CORDA, revisão 2 (parecer #4)

> **Proveniência:** recebido do dono por colagem na sessão Cowork em
> 2026-08-20 e salvo verbatim pelo integrador no caminho combinado na
> solicitação (`SOLICITACAO-critica-artigo-rev2-codex-sol.md`). A estrutura
> de títulos foi re-marcada em Markdown pelo integrador (a colagem chegou
> achatada) e caminhos absolutos locais da máquina do dono foram
> normalizados para referências neutras (gate de portabilidade e
> privacidade — mesmo tratamento do briefing de campo); nenhuma outra
> alteração. **Autor:** Codex Sol (gpt-5.6-sol). **Engajamento:** #4 da
> série cross-model.

---

## Resposta direta

Há uma combinação de ideias interessante, mas o artigo não demonstra que ela
seja uma contribuição técnica realmente diferente.

O elemento mais promissor é a combinação de:

* poda de papéis pelo escopo declarado de evidência;
* recusas `SINGLE_LENS`/`NO_UNIVERSE`;
* autoridade, aceitação e proveniência transformadas em artefatos verificáveis.

Mas o texto vende algo mais forte: derivação do elenco, compilação de um
runtime multiagente e um método adversarial novo. Hoje:

1. a "derivação" começa de papéis, perguntas, danos e escopos já autorados;
2. o algoritmo central admite — e reproduz — colapsos que contradizem sua própria regra;
3. geração automática de equipes, otimização de topologias, contratos de runtime e red teaming de agentes já têm antecedentes diretos que o artigo não discute;
4. a evidência empírica sustenta um relato de engenharia, não a tese geral anunciada.

VEREDITO: `não submeter` na forma atual.

Nenhum arquivo foi modificado.

## 1. Identidade e ambiente

Sessão executada no Codex Desktop, em macOS, com cwd na raiz do repositório
privado (caminho local normalizado: `~/…/CORDA` — ver nota de proveniência).

O repositório privado estava fisicamente acessível; portanto, o isolamento
foi declarativo, não físico. Não li o repositório privado, exceto os três
objetos do artigo expressamente autorizados em `paper/`. Não li journal,
`runs/`, projeto de campo nem qualquer `authority-forged-*`.

Clone público limpo: `/tmp/corda-artigo-review.FMwbAt/public-corda`, tornado
somente leitura antes das execuções.

* Tag anotada: `v1.0.0-rc.1`
* Objeto da tag: `8290b30e86335d1832d453d270d4acfb0b7b489d`
* Commit: `59ab2bd975de15141899abc4952b002c9e84b3c8`

Hashes conferidos:

* `paper/main.tex`: `28e748fb18644a7f2f1ef6dfabb421417b36aa2c2b891ac86fae5acaf44dbe3a`
* `paper/references.bib`: `9d71d32b47935d46b3e7497f7de618cea3caad29b96d7d1eece03efbfeac7a93`
* PDF: `ba92ed074b4eb9858469ca13751e1dc7353dbc9a852693306fc4ae1b75ff3d42`

Li o fonte integral, a bibliografia e as 14 páginas do PDF `main.pdf`.

## 2. Achados

### R-01 — `bloqueante-submissão` — A novidade é afirmada contra comparadores inadequados

Citação: "CORDA is upstream and orthogonal" e, nos frameworks selecionados,
"cast size [...] remain author choices" (linhas 630–639 do `main.tex`).

Ataque: AutoGen, MetaGPT, CAMEL, CrewAI e LangGraph não são o conjunto
relevante para testar a novidade da derivação de equipes. O artigo ignora
trabalhos diretamente voltados à geração ou seleção automática de agentes e
topologias:

* [AutoAgents](https://arxiv.org/abs/2309.17288) gera equipes especializadas a partir da tarefa;
* [DyLAN](https://arxiv.org/abs/2310.02170), publicado no COLM 2024, seleciona equipes e estruturas dinâmicas;
* [Captain Agent](https://arxiv.org/abs/2405.19425) forma equipes adaptativamente durante a conversa;
* [GPTSwarm](https://arxiv.org/abs/2402.16823), ICML 2024, otimiza conectividade de grafos de agentes;
* [AgentSpec](https://arxiv.org/abs/2503.18666), aceito no ICSE 2026, fornece uma DSL para restrições executáveis de runtime;
* [Agent Behavioral Contracts](https://arxiv.org/abs/2602.22302) cobre precondições, invariantes, governança e recuperação em cadeias multiagente.

Sem esses comparadores, "upstream and orthogonal" é posicionamento autoral,
não resultado.

Correção proposta: incluir uma matriz técnica comparando input exigido,
mecanismo de formação, objeto otimizado, autoridade, enforcement, recusa,
garantias e integração. A novidade deve ser reduzida ao delta que sobreviver
a essa comparação.

### R-02 — `bloqueante-submissão` — O elenco não é derivado do assunto e da evidência

Citação: "the number of agents is derived as the number of separable
evidence subspaces" (linhas 69–73).

Ataque: o executável não descobre subespaços a partir de documentos ou
dados. O input já contém:

* `concerns`;
* pergunta, domínio e papel de cada concern;
* `evidence_scope.private`;
* ferramentas;
* `harm_domains`, donos e poderes.

O algoritmo público então remove concerns sem evidência privada/ferramentas
e une escopos iguais ou contidos. Isso é poda e consolidação de um elenco
candidato já autorado, não derivação do elenco a partir da evidência bruta.
A etapa cognitivamente difícil — propor os concerns e atribuir fontes —
continua sendo feita pelo autor/LLM antes do algoritmo.

Correção proposta: ou renomear a contribuição para `evidence-scoped cast
pruning/consolidation`, ou apresentar e avaliar um método que extraia os
candidatos e os escopos diretamente do corpus, com erro de extração e
concordância humana medidos.

### R-03 — `bloqueante-submissão` — O fechamento transitivo contradiz a regra central

Citação: a implementação usa "a transitive closure over pairwise
mergeability" (linhas 211–214), embora o próprio artigo admita que a cadeia
"can merge lenses whose endpoints are separable" (linhas 219–223).

Ataque: executei um contraexemplo no código público:

* lente A observa `{a}`;
* lente B observa `{b}`;
* lente bridge observa `{a,b}`.

A e B são separáveis pela própria definição. Entretanto, ambas são fundidas
ao bridge e o resultado é:

```
surviving_lenses = 1
verdict = SINGLE_LENS
```

Isto não é apenas uma limitação periférica. É a negação operacional da tese
"número de subespaços separáveis". O artigo reconhece o defeito e,
simultaneamente, apresenta o resultado como contribuição mecânica.

Correção proposta: definir formalmente a relação que deve preservar
separabilidade, provar o invariante "endpoints separáveis nunca desaparecem
por uma ponte" e adicionar o contraexemplo à avaliação. Enquanto isso não
existir, a saída deve ser "candidato para revisão", nunca "o número
derivado".

### R-04 — `bloqueante-submissão` — A mesma falha pode apagar adversários ortogonais

Citação: "one adversary per orthogonal harm domain", com ortogonalidade
definida por evidência disjunta e dono distinto (linhas 228–240).

Ataque: o código toma componentes conexos da relação "mesmo dono OU
evidência sobreposta". Testei:

* dano A: dono 1, evidência `{a}`;
* dano B: dono 2, evidência `{b}`;
* bridge: dono 1, evidência `{b}`.

A e B são ortogonais, mas as duas pontes de não-ortogonalidade colocam tudo
no mesmo componente. O executável retorna um único adversário, apagando uma
fronteira de dano que a regra afirma preservar.

Esse defeito é mais grave que R-03 porque a consequência é perda de um
veto/owner independente.

Correção proposta: não usar fechamento transitivo do complemento da
ortogonalidade. Modelar explicitamente o problema de cobertura dos domínios,
preservar todos os pares ortogonais e demonstrar essa propriedade por testes
gerativos ou prova.

### R-05 — `maior` — "Compiler/runtime" descreve um objeto mais forte que o entregue

Citação: CORDA "emits an operational runtime for LLMs" (linhas 121–129).

Ataque: a execução pública produz Markdown, JSON, SVG/PNG, estado e scripts
mutadores. O `BOOTSTRAP` instrui um LLM a atuar como orquestrador. Não há
scheduler, protocolo de mensagens executável, backend para
AutoGen/LangGraph/CrewAI ou enforcement no ponto de ação. O próprio artigo
admite que a orquestração de campo foi manual (linhas 677–681).

Portanto, o objeto é um bundle de especificação/prompt e governança, não um
runtime multiagente no sentido usual.

Correção proposta: renomear para "compiler of auditable runtime
specifications/bundles" ou implementar ao menos um backend executável que
faça os gates, poderes e transições valerem durante a execução.

### R-06 — `bloqueante-submissão` — "A completed checklist is not an adversary" é ilustrado, não demonstrado

Citação: o texto chama isso de "central empirical claim" e diz que foi
"demonstrated" (linhas 504–510).

Ataque: houve um episódio, com um sistema, um owner, um revisor externo e
uma sequência adaptativa. Não há comparação controlada entre:

* checklist sem ataque livre;
* mesmo modelo com ataque livre;
* modelo diferente sem ataque livre;
* modelos diferentes, budgets e prompts equiparados;
* revisores humanos ou múltiplos revisores.

O episódio mostra que aquele checklist não continha quatro classes de bypass
que aquele ataque encontrou. Não mostra que o ganho veio da família de
modelo, da liberdade de ataque, do contexto isolado ou simplesmente de uma
nova rodada de revisão.

Além disso, red teaming executável de agentes já é uma área estabelecida:
[Agent Security Bench](https://arxiv.org/abs/2410.02644),
[Agent-SafetyBench](https://arxiv.org/abs/2412.14470) e o
[ART benchmark](https://arxiv.org/abs/2507.20526). Logo, "an adversarial
loop the field lacks" (linhas 79–86) é falso sem qualificação estreita.

Correção proposta: transformar a frase em conclusão do caso — "in this
episode, the enumerated battery missed four bypasses found under free
attack" — ou executar estudo comparativo pré-registrado.

### R-07 — `maior` — O 0/3 versus 3/3 evita a ablação, mas continua sendo um teste de presença quase tautológico

Citação: "the candidate implements three capabilities that the pinned
predecessor does not, on the three authored cases" (linhas 601–610).

Ataque: trocar a ablação pelo predecessor histórico é uma correção real.
Porém:

* os três casos foram escritos para capacidades novas;
* o predecessor não possuía essas capacidades;
* os casos e o scorer foram autorados pelo processo que criou a candidata;
* o executável do predecessor e sua proveniência não estão públicos;
* a suíte nominal do predecessor não foi executada contra ele.

O resultado demonstra presença de features, nada sobre qualidade, utilidade,
regressão total ou valor incremental. Chamar essa seção de "Evaluation"
infla um smoke test de compatibilidade funcional.

Correção proposta: executar a suíte nominal preservada do predecessor, casos
externos ou pré-registrados, medir custo e resultados de tarefa e publicar o
baseline executável para o referee.

### R-08 — `maior` — O artigo atribui revisão cross-model ao objeto errado

Citação: "The extensions are [...] agent-reviewed, cross-model" (linhas
663–669).

Ataque: o gate cross-model falhou o commit `954565f...`, do ciclo 07.
N-05…N-08 foram corrigidos depois, no ciclo 08. A release pública atual
contém essas correções, mas o próprio corte público declara pendente o
re-gate da latest repair.

A Tabela 2 agrava a confusão: sua legenda diz que a coluna externa é o
veredito "on the cycle's output" (linhas 384–389), mas coloca o gate que
testou o ciclo 07 na linha do ciclo 08 (linhas 407–414). O mesmo padrão
desloca auditorias para o ciclo que respondeu a elas.

Correção proposta: cada claim de revisão deve carregar commit/tag exato. O
estado correto da release é: `latest code deterministically tested;
predecessor object cross-model attacked; latest repairs not yet cross-model
re-gated`.

### R-09 — `maior` — O Apêndice D reproduz o software, não o estudo

Citação: "Every quantitative claim is recomputable from the public
repository or attributable to the private journal" (linhas 719–723).

Ataque: os comandos públicos recomputam:

* 70 testes;
* cast 4/4;
* conformidade 9/9;
* verificação standalone.

Não recomputam:

* rebuild byte a byte do universo de desenvolvimento — retorna `SKIP`;
* nove ciclos e suas datas;
* execução 0/3 versus 3/3 do predecessor;
* campo, gate de nove testes, primeira síntese ou reparo;
* prazo e janela de 44 dias;
* registros MAST;
* reprodução cronológica de todos os achados;
* identidades dos modelos internos;
* decisões `human accepted as adjusted`.

Attribution não é verificação. A política de acesso ao journal ainda está
pendente.

Correção proposta: criar uma tabela claim→objeto→hash→public/private→comando.
Claims privados devem ser chamados de `owner-attested case records` até
revisão sob acordo.

### R-10 — `maior` — "Externally audited" do núcleo não é verificável pelo referee

Citação: "The inherited early compiler core is externally audited" (linhas
660–662).

Ataque: o relatório público afirma que a identidade do auditor não acompanha
o repositório e que o bundle original só poderá ser conferido se
disponibilizado separadamente. Para o referee, "external" é uma declaração
do mantenedor sobre um relatório fornecido pelo próprio mantenedor.

Correção proposta: publicar identidade ou atestação verificável e o bundle
auditado; caso contrário, usar "owner-supplied report of a prior external
audit".

### R-11 — `maior` — Família de modelo diferente não equivale a independência

Citação: "The strongest verification available before a human expert is a
reviewer from a different model family" (linhas 455–460).

Ataque: mudar a família reduz uma fonte de correlação, mas não resolve:

* corpora e práticas de treinamento sobrepostos;
* mesma especificação e framing;
* mesmo owner e critérios;
* mesmo revisor usado três vezes;
* ausência de múltiplas amostras;
* adaptação dos reparos aos achados anteriores.

Não há evidência para ordenar isso como "the strongest verification
available".

Correção proposta: dizer "one additional model-family diversity dimension" e
separar diversidade de independência. Um experimento com múltiplos modelos,
prompts e revisores seria necessário para o claim mais forte.

### R-12 — `maior` — O campo contém uma conclusão jurídica e uma lacuna ética

Citação: o abstract chama a recomendação de "an unlawful data-processing
order" (linhas 87–90); a seção de campo repete que não havia base legal
(linhas 529–539).

Ataque: o material sustenta que o gate encontrou ausência de base legal
documentada segundo a regra do projeto. Não sustenta a conclusão jurídica
objetiva "unlawful".

Além disso, um episódio real envolvendo terceiro, dados pessoais e uma
alegação de intervenção em qualidade decisória exige uma declaração
explícita sobre:

* autorização do owner do projeto de campo;
* se dados pessoais foram ou não processados;
* consentimento, ética institucional ou fundamento de dispensa;
* retenção e acesso aos artefatos;
* ausência de impacto operacional ou decisão automatizada sobre pessoas.

A AI disclosure não cobre isso.

Correção proposta: substituir "unlawful" por "lacking a documented legal
basis under the project's gate" e adicionar seção de ética/dados do campo.

### R-13 — `maior` — O abstract transforma a taxonomia MAST em causalidade

Citação: "Multi-agent LLM systems fail mostly at the specification level"
(linhas 64–67) e "most breakdowns are not model-capacity problems" (linhas
102–110).

Ataque: MAST reporta 14 modos encontrados em 1.600+ traces de sete
frameworks e 150 traces usados no desenvolvimento da taxonomia; esses
números estão corretos na [fonte primária](https://arxiv.org/abs/2503.13657).
Mas uma taxonomia observacional não estabelece que sistemas "fail mostly"
por especificação nem identifica contrafactualmente que capacidade do modelo
não é a causa.

Correção proposta: "MAST documents recurring specification, coordination,
and verification failures in the studied traces."

## 3. O que tentei e não quebrou

* Os três hashes conferem exatamente.
* A identidade da release pública está clara.
* `python3 scripts/verify_repo.py` passou com 70 testes.
* Cast: 4/4.
* Conformidade: 9/9.
* O clone permaneceu limpo e somente leitura.
* P1–P6, contagem MAST de 14 modos e os IDs apresentados são internamente legíveis.
* O artigo declara honestamente `n=3`, caso de campo único, orquestração manual, holdout pendente, ausência de generalização e ausência de superioridade.
* O trail público preserva reprovações, inclusive o gate fatal.
* A divulgação de IA é uma boa base: identifica participação material de LLMs e responsabilidade humana.
* Não encontrei vazamento do nome real do projeto de campo no artigo ou na varredura textual do artefato público.

Esses méritos tornam o material aproveitável como relato técnico. Não
resolvem a pergunta da novidade científica.

## 4. O que não pode ser verificado sem o journal

Sem acesso ao journal, um referee não consegue validar a evidência primária
dos ciclos, campo, avaliação histórica, decisões humanas ou modelos
internos. Os documentos públicos são relatos redigidos e cópias redigidas
dos pareceres; não substituem os traces e objetos originais.

Um referee poderia aceitar isso para:

* preprint narrativo claramente rotulado;
* experience report com evidência privada declarada;
* workshop, se o journal for oferecido aos revisores sob acordo.

Não deveria aceitar para:

* artifact evaluation que alegue reprodução integral;
* conferência principal com a contribuição empírica atual;
* claims fortes de método, eficácia ou independência.

## 5. Título

* Candidato A: não sustentado. O usuário/LLM ainda escolhe os concerns e seus escopos; o sistema poda a lista.
* Candidato B: é o mais fiel ao episódio, mas apresenta uma observação conhecida de assurance como novidade central.
* Candidato C: é o mais próximo de um experience report, mas "runtime/compiler" e o estado de revisão do objeto atual continuam inflados.

Título recomendado:

**Evidence-Scoped Cast Pruning and Executable Governance for Multi-Agent LLM
Workflows: A Self-Hosting Experience Report**

Ele diz o que o artefato realmente faz e não promete derivação automática
nem superioridade científica.

## VEREDITO

`não submeter` na forma atual.

* arXiv: chance real após corrigir os claims factualmente falsos e rotular como technical/experience report.
* Workshop/tool paper: chance razoável após corrigir R-02–R-04, fazer comparação direta de novidade e abrir uma matriz de evidência.
* Conferência principal cs.MA/cs.SE: chance baixa sem validação externa pré-registrada, baseline público, comparação com formação automática de equipes e uma definição formal que sobreviva aos contraexemplos.
* Trilha de artefatos: não enquanto o público reproduzir apenas 70/9/4 e os resultados centrais dependerem do journal privado.

A resposta honesta à pergunta do owner é: há uma engenharia diferenciada na
combinação, mas o artigo ainda não demonstra uma contribuição nova; e o
único mecanismo que poderia sustentá-la falha hoje em dois contraexemplos
centrais.
