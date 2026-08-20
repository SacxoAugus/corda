> **REDACTED PUBLIC COPY** — names and paths of the field-test subject were replaced by a declared mechanical map (see PUBLIC-CUT-NOTE.md). The canonical original lives in the maintainer's private archive; original sha256 (first 16): `890307397c8e3818`.

# Reprodução do parecer #4 pelo integrador — 2026-08-20

Disciplina da casa: achado não reproduzido é alegação. Status: **13/13
conferem**. Nenhum achado refutado.

## Executáveis (fixtures exatas do parecer, rodadas sobre o código público)

**R-03 — cadeia de lentes.** Brief com lente A (`{ev-a}`), lente B
(`{ev-b}`), lente ponte (`{ev-a, ev-b}`). Resultado:

```
Veredito: SINGLE_LENS
Elenco: {'proposed': 3, 'surviving_lenses': 1, 'adversaries': 0, ...}
```

Reproduzido exatamente como descrito. Observação do integrador: o limite da
cadeia de lentes **está declarado** (`SKILL.md`: "a chain of overlaps can
merge lenses whose endpoints are separable; the derived cast is a
candidate") — o achado do parecer é que o artigo apresenta o mecanismo como
"o número derivado" enquanto o próprio limite declarado nega a tese
operacionalmente. Procede.

**R-04 — cadeia de adversários.** Dano A (Dono 1, `{ev-a}`, veto), dano B
(Dono 2, `{ev-b}`, veto), dano ponte (Dono 1, `{ev-b}`, parecer).
Resultado:

```
adversaries kept: 1
 - dano-a | owner: Dono 1 | power: veto | evidence: [ev-a, ev-b]
```

Reproduzido — e **pior do que o parecer descreve**: o Dono 2 desaparece do
elenco por completo; sua fronteira de dano passa a ser "representada" por um
veto do Dono 1, parte com interesse distinto. Verificação adicional do
integrador: nem `SKILL.md` nem `REGISTRO-caveats-conhecidos-v4.md` declaram
a variante de adversários da cadeia — o limite declarado cobre só lentes.
Logo o componente-ferramenta do R-04 é **defeito novo e não declarado**
contra a regra da própria skill ("um adversário por domínio de dano
ortogonal"). Nota de linhagem: o fecho por componentes conexos é a correção
S-01 (auditoria #1) — introduzida para invariância à ordem; o complemento da
ortogonalidade não é transitivo, e fechá-lo super-funde. As duas correções
puxam em direções opostas; o desenho novo precisa satisfazer ambas
(invariância à ordem E preservação de pares ortogonais).

Fixtures preservadas para virarem testes de regressão no ciclo de reparo.

## Textuais (citações conferidas linha a linha no `main.tex` criticado)

- **R-08**: confere — a legenda da Tabela 2 diz "verdict on the cycle's
  output", mas as linhas 05/07/08 carregam o veredito no ciclo que
  *respondeu*, não no ciclo cujo output foi testado. Erro do integrador na
  revisão 2.
- **R-05, R-06, R-07, R-09, R-10, R-11, R-12, R-13**: todas as citações
  existem nas linhas apontadas, com o sentido que o parecer atribui.
- **R-02**: confirmado por inspeção do schema de brief (concerns com
  pergunta/domínio/papel/escopo e harm_domains com donos/poderes chegam
  autorados; o algoritmo poda e consolida).
- **R-01**: os seis comparadores apontados existem como referências a
  verificar (links arXiv); a checagem de existência/versão de cada um fica
  para a revisão 3, antes de citar.
