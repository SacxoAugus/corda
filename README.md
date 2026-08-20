# CORDA

> 🇧🇷 [Versão em português](README.pt-BR.md)

Auditable universe compiler for LLMs, with cast derivation via evidence
topology.

> **Status:** candidate based on CORDA v3 with additive v4 extensions
> (explorable projection, computable acceptance, absolute deadlines,
> evaluation with a deterministic oracle), accepted by the owner as
> *adjusted* on 2026-07-28 and pinned at tag `v4-ciclo-04-adjusted`. The
> compiler core was externally audited at v2.2.3; the v3/v4 extensions have
> deterministic verification and agent review (same base model — declared),
> but have **not** been externally audited nor validated on an unknown
> distribution.

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
| Compiler | 32 unit tests (24 v3 + 8 from the v4 extensions) |
| Conformance | 9 cases; 3 holdouts; 9/9 conformant |
| Cast derivation | 4 synthetic cases; 2 holdouts; 4/4 conformant |
| v4 evaluation (ACCEPTANCE v1.1) | deterministic oracle; ablation 0/3 vs 3/3 (not the historical v3 baseline — Sol audit S-03); `evaluated_inconclusive` |
| Cross-model audit (Codex Sol, 2026-07-29) | **rejected for promotion**: C2–C4 refuted, 6 new findings; C5–C10 confirmed ([report](docs/audits/v4-audit-codex-sol.md)) |
| Generalization | Not demonstrated |
| Human acceptance | Recorded mechanically (`record_acceptance.py`); promotion still requires explicit acceptance |

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
