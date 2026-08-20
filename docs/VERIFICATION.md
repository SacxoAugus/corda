# Estado de verificação

## Núcleo do compilador

A linha v2.2.3 foi auditada externamente antes desta extração. O escopo
verificado incluiu:

- validação de atestados na fronteira de decisão;
- integridade de hashes inline;
- aplicabilidade e abortos;
- isolamento do overlay;
- benchmark de conformidade com nove casos;
- 24 testes unitários.

A auditoria não demonstra generalização em distribuição desconhecida.

## Derivação de elenco v3

Estado atual:

- quatro casos sintéticos;
- dois holdouts;
- quatro casos conformes;
- autoria compartilhada entre código e dataset;
- sem auditoria externa.

Consequentemente, a derivação é candidata e experimental. Ela mede separação de
evidência declarada; não mede suficiência, verdade ou ausência de vieses comuns.

## Extensões v4 (ciclos 01–04, 2026-07-28)

Estado por superfície, na linguagem restrita abaixo:

- Compilador com extensões (projection_data, P1–P6, STATE 1.5, due_at
  absoluto): `deterministically verified` (32 testes; conformidade 9/9; cast
  4/4; rebuild byte-idêntico reproduzido por gate isolado) e `agent-reviewed`
  (lentes, gates adversariais e adversário global — todos com o mesmo
  modelo-base do produtor; invalidam, não corroboram).
- Decisões de arquitetura (ADR-001, topologia multi_agent, ACCEPTANCE v1.1):
  `human accepted` como *adjusted* (registro em
  `runs/v4-development/build/corda-v4-STATE.json#decision`).
- MAST 2025 v2 sobre traces reais: `fail` registrado com honestidade
  (FM-1.4: rebuilds apagavam registros de revisão; mitigação procedural +
  pinagem por tag).
- Auditoria cross-model (Codex Sol, OpenAI gpt-5.6-sol, 2026-07-29;
  `docs/audits/v4-audit-codex-sol.md`): **REPROVADA para promoção v3→v4** no
  objeto auditado. C5–C10 confirmados nos limites declarados; **C2–C4
  refutados** (enforcement de schema da projeção não é estrito; registro de
  aceite admite data malformada; `algorithm` é rótulo e o build versionado não
  fechava sobre o HEAD); C1 não verificável sem baseline v3 executável pinada.
  Achados novos S-01/S-02/S-04/S-05/S-08/S-09 — destaque: derivação de elenco
  dependente da ordem de entrada (S-01) e elegibilidade fabricável por métricas
  autodeclaradas (S-02). Classe da revisão: `agent-reviewed` por família de
  modelo distinta — primeira do run; não constitui aceite humano.
- Nenhuma superfície v4 é `externally audited` por humano/organização. O claim
  externo permanece restrito ao núcleo herdado da v2.2.3.

## Linguagem de revisão

Usar somente:

- `self-checked`;
- `agent-reviewed`;
- `deterministically verified`;
- `externally audited`;
- `human accepted`.

Não chamar o repositório inteiro de auditado. O claim externo aplica-se ao
núcleo herdado da v2.2.3, não automaticamente à derivação v3 ou a mudanças
futuras.
