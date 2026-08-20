# Registro de caveats conhecidos — v4 (para a fase de cruzamento da auditoria)

> **Auditor: não leia antes de emitir seus achados independentes.** Este
> registro consolida o que o processo interno já sabe sobre si mesmo, para você
> marcar `confirmo` / `refuto` / `novo para mim` — e para que achados novos de
> verdade se destaquem.

## Estruturais (escalonados e tratados)

- Z1 (corrigido no ciclo 04): prazos derivavam de `observed_at` — o painel
  temporal não acumulava tensão entre builds. Correção: `due_at` absoluto (R8).
- Z3 (mitigado): rebuilds zeram STATE/verification; mutações agora reaplicadas
  por scripts sancionados após rebuild; candidata pinada por tag git. MAST dos
  ciclos 03–04 registra `fail` (FM-1.4) por honestidade sobre as recorrências.
- Z4 (resolvido por decisão): mudanças do ciclo 03 incluídas no aceite
  *adjusted* por inclusão declarada do owner.
- Bypass do P1 (corrigido no ciclo 02→03): o guard era denylist; virou
  allowlist estrito com casos adversariais no teste R2.

## Abertos (fila do ciclo 05)

- Runner não descobre/executa `authority-forged-*` (holdout selado) ainda.
- Caso authority: baseline parcialmente afirmada pelo runner
  (`mechanism_available: false`) e 1 asserção verifica prosa do runner — não
  muda o 0/3 vs 3/3, mas o claim "nada pré-computado" não é 100% literal.
- Rótulo "baseline v3" = ablação (pipeline v4 sem `projection`), não o
  compilador v3 real reexecutado.
- Scorer: fraquezas latentes (`exists` com path vazio passa vácuo; `find.where`
  vazio casa o primeiro elemento) — não exploradas pelos truths atuais.
- `downgrade_state.py`: `events` malformado crasha após escrever o arquivo
  morto (efeito parcial; retry duplica export); `--owner` não confrontado com o
  owner da decisão.
- `canonical_registry`: id com `\n` injeta linha no stderr; `content_path`
  absoluto fora do repo é lido sem aviso; relativo resolve contra CWD.
- Suíte v3 provada por contagem (24+8), não nome a nome (sem baseline nominal).
- Sem caminho sancionado de re-upgrade STATE 1.4→1.5.
- Render: inversões de ranking no desenho 2D (stress 0.2521 — mitigado por
  disclaimer/tabela); tooltips só mouse; sem teste com usuários.

## Limites permanentes declarados

- P4 é atribuição declarativa, não autenticação criptográfica.
- Amostras pequenas (9 conformidade, 4 cast, 3 avaliação): conformidade nesses
  casos, não generalização; n=3 torna o limiar 0,05 discreto ("um caso a mais").
- Avaliação valida o enquadramento dos 3 painéis (Z7); casos autorados pelo
  mesmo processo que implementou.
- Nenhum uso real fora do self-hosting; nenhum usuário além do owner; sem
  medição de custo single vs multi-agente.
- Todos os pares internos `weak` (mesmo modelo-base): gates internos invalidam,
  não corroboram. Esta auditoria é a primeira revisão cross-model.
- Licença pendente; holdout selado pendente de geração pelo owner;
  visual_review humana pendente.
