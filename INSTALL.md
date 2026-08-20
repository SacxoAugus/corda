# Installation

## Requirements

- Python 3.10 or higher;
- Pillow optional for PNG;
- no mandatory dependency for SVG, Markdown, and JSON.

## Verify the copy

At the project root:

```bash
python3 scripts/verify_repo.py
```

The command runs:

1. structural validation of the skill;
2. cast derivation benchmark;
3. compiler conformance benchmark;
4. 24 unit tests;
5. a scan for private couplings and absolute paths.

## Use as a CLI

Derivation:

```bash
python3 gerar-corda/scripts/derive_cast.py \
  --brief /path/brief.json \
  --out-dir /path/output \
  --basename universe
```

Compilation:

```bash
python3 gerar-corda/scripts/build_universe.py \
  --spec /path/manifest.json \
  --out-dir /path/output \
  --basename universe
```

## Install in Codex

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R gerar-corda "$CODEX_SKILLS_DIR/gerar-corda"
```

Open a new Codex task to update the skill catalog.

## Use in other LLMs

The generated runtime is provider-independent. Load:

1. `<basename>-BOOTSTRAP.md`;
2. `<basename>-STATE.json`;
3. authorized sources for the run.

The host must implement persistence, tools, and permissions. CORDA must not
claim to have recorded state or executed actions if the integration does not
offer those capabilities.
