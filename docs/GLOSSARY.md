# CORDA — Canonical Glossary (PT → EN)

Fixed by the maintainer's integrator before any translation (cycle 09). Every
translated document MUST use exactly these terms. The project name **CORDA** is
never translated (Apache-2.0 §6: the name is not granted).

| Português (canônico) | English (canonical) | Nota |
|---|---|---|
| CORDA | CORDA | nome próprio; nunca traduzir |
| corda (objeto do universo) | string | metáfora SGM (string/brane); `strings[]` no manifesto já é EN |
| brana / modo / lente | brane / mode / lens | lens = subespaço de evidência separável |
| elenco | cast | derivação do elenco = cast derivation |
| universo | universe | |
| manifesto | manifest | fonte editável |
| compilador | compiler | |
| aceite | acceptance | aceite humano = human acceptance |
| rodada | round | admissão de rodada = round admission |
| delta de evidência | evidence delta | |
| adversário | adversary | |
| domínio de dano | harm domain | |
| parecer (poder) | advisory (power) | nunca "opinion" como poder |
| veto (poder) | veto (power) | |
| escalonamento (poder) | escalation (power) | |
| dono / dono exercível | owner / exercisable owner | owner_named = asserção estruturada |
| recusa | refusal | SINGLE_LENS / NO_UNIVERSE ficam como estão |
| ajuste + resíduo | fit + residual | decomposição do dado inteiro |
| eco (corte de eco) | echo (echo cut) | cut_echo fica como está |
| fusão por identidade de evidência | merge by evidence identity | |
| separação (métrica) | separation | evidence separation |
| tensão temporal | temporal tension | painel temporal = temporal panel |
| fronteira | boundary | subject_boundary fica como está |
| entropia / revalidação | entropy / revalidation | itens de entropia = entropy items |
| gate | gate | não traduzir de volta |
| verificação / camadas | verification / layers | |
| carimbo do compilador | compiler stamp | |
| pacote autoconsistente | self-consistent bundle | bundle rebuild gate |
| holdout selado | sealed holdout | |
| verdade (ground truth) | ground truth | truth/ dirs ficam |
| oráculo determinístico | deterministic oracle/scorer | |
| elegibilidade | eligibility | promotion eligibility |
| promoção | promotion | sempre gated por human acceptance |
| decisão (do owner) | decision | decision.state fica |
| evidência viva (ferramental) | living evidence (tooling) | |
| diário de desenvolvimento | development journal | permanece em PT como evidência canônica |
| sonda | probe | |
| achado | finding | S-xx/N-xx/A-xx/Z-x preservados |
| lei do elenco → | cast derivation rule (operational heuristic) | NUNCA "law" (rebaixada no c07) |
| declarado vs derivado | declared vs derived | P1: authored derived values are contradictory |
| selado / fora de escopo | sealed / out of scope | |
| mutador sancionado | sanctioned mutator | scripts de mutação do STATE |
| overlay (mítico) | (mythic) overlay | nunca entra no runtime |
| condição de contorno humana | human boundary condition | o owner |

Regras gerais: identificadores de código, campos JSON, nomes de arquivo e
marcadores de achado NÃO mudam (são contrato/evidência). Datas ISO como estão.
"pass_with_caveats", "evaluated_inconclusive" etc. já são EN — intocados.
O diário (docs/audits/, runs/) permanece em português: traduções do diário
seriam artefatos derivados, não evidência.
