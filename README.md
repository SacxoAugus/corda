# CORDA

> 🇧🇷 [Versão em português](README.pt-BR.md)

Auditable universe compiler for LLMs, with cast derivation via evidence
topology.

> **Version:** `1.0.0-rc.1` — first public release; nothing was published
> before it. Internal lineage names (v3/v4) appear only in the preserved
> audit trail — see [VERSIONING.md](VERSIONING.md).
>
> **Status:** release candidate. The tool is an optional, additive extension
> of its private predecessor (explorable projection, computable human
> acceptance, absolute deadlines, deterministic-oracle evaluation), measured
> against that predecessor pinned by hash: 0/3 vs 3/3 on the authored
> acceptance cases — capability presence, **not superiority**. It survived
> two cross-model audits and one isolated cross-model adversarial gate whose
> free attack failed a candidate the full nominal battery had approved (see
> [docs/audits/README.md](docs/audits/README.md)); every finding was
> reproduced, fixed, and re-tested (70 unit tests, byte-level rebuild gate).
> The `-rc` drops only upon explicit human acceptance, still pending —
> together with a sealed holdout and human visual review. Claims are narrow
> by design: no superiority, no generalization, no external human audit of
> the extensions.

## What it does

CORDA turns a description, documents, data, or an optional graph into an
operational LLM runtime:

```text
subject + evidence
→ cast derivation
→ manifest
→ preflight
→ neutral runtime + state + evidence + optional projection
```

The system:

- derives how many modes/agents the subject supports;
- merges observers with correlated evidence;
- refuses artificial single-lens universes;
- separates facts, inferences, hypotheses, recommendations, and decisions;
- blocks rounds without new evidence;
- keeps decision-making authority with the human owner;
- generates `SYSTEM`, `UNIVERSE`, `STATE`, `EVIDENCE`, and `BOOTSTRAP`;
- keeps the physical metaphor in an optional overlay.

A graph can be used as a source, but it is never a prerequisite.

## Quick start

Requires Python 3.10 or higher. Pillow is optional and enables PNG output.

```bash
python3 -m pip install Pillow
python3 scripts/verify_repo.py
```

Derive a cast:

```bash
python3 gerar-corda/scripts/derive_cast.py \
  --brief gerar-corda/assets/cast-benchmark/cases/dois-danos-ortogonais.json \
  --out-dir build/cast-demo \
  --basename demo
```

Compile a narrative universe without a graph:

```bash
python3 gerar-corda/scripts/build_universe.py \
  --spec gerar-corda/assets/conformance-benchmark/cases/dynamic-runtime.json \
  --out-dir build/runtime-demo \
  --basename demo
```

To operate the universe in an LLM, first load
`build/runtime-demo/demo-BOOTSTRAP.md` and preserve
`build/runtime-demo/demo-STATE.json` as a checkpoint.

## Install as a Codex skill

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R gerar-corda "$CODEX_SKILLS_DIR/gerar-corda"
```

Then, invoke it explicitly:

```text
Use $gerar-corda to derive and compile a universe for this decision: [...]
```

The skill has no implicit invocation, to avoid conflicting with domain
skills. Other LLMs can consume the generated artifacts; the `SKILL.md`
packaging is Codex-specific.

## Structure

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

## Available evidence

| Surface | Current evidence |
| --- | --- |
| Compiler | 70 unit tests, including metamorphic cast tests and re-derived adversarial probes from every audit finding; byte-level bundle rebuild gate |
| Conformance | 9 cases; 3 holdouts; 9/9 conformant |
| Cast derivation | 4 synthetic cases; 2 holdouts; 4/4 conformant (order-invariant: single partition across input permutations) |
| Evaluation (ACCEPTANCE v1.2) | deterministic oracle with mandatory content-addressed scorer report; measured against the **hash-pinned executable predecessor**: 0/3 vs 3/3 on the authored cases — capability presence, not superiority; `evaluated_inconclusive` until the sealed holdout runs |
| Cross-model audit #1 (2026-07-29) | **rejected for promotion**; findings S-01…S-09, all reproduced and fixed ([report](docs/audits/v4-audit-codex-sol.md)) |
| Cross-model review #2 (2026-08-19) | material progress, utility demonstrated in one field episode, **do not promote**; findings N-01…N-04, all reproduced and fixed |
| Isolated cross-model gate (2026-08-20) | nominal battery fully PASS, **free attack failed the candidate** (N-05…N-08), all reproduced and fixed — see [docs/audits/README.md](docs/audits/README.md) |
| Field use | one real deployment; one real multi-agent round where the universe's gate rejected a defective recommendation and forced repair; one external session where round admission correctly refused redundant work |
| Generalization | Not demonstrated |
| Human acceptance | Recorded mechanically (`record_acceptance.py`); promotion still requires explicit human acceptance — pending |

See [docs/VERIFICATION.md](docs/VERIFICATION.md) for the exact boundary of
the claims, and [the v2.2.3 external audit report](docs/audits/v2.2.3-external-audit.md)
for inherited evidence.

## Security

CORDA organizes context and evidence; it does not create a security boundary
on its own. Permissions, isolation, secrets, and external actions remain the
host's responsibility. See [SECURITY.md](SECURITY.md).

## License

**Apache License 2.0** (maintainer's decision, 2026-08-20) — file
[`LICENSE`](LICENSE), attribution in [`NOTICE`](NOTICE). In summary: free
use, copying, modification, and distribution (including commercial),
preserving the notice of authorship and NOTICE; explicit patent grant with a
retaliation clause; **no rights over the name "CORDA"** (§6 — the mark
belongs to the author). External contributions: until a published CLA
exists, contributions are accepted only under the terms of Apache-2.0 itself
(§5).
