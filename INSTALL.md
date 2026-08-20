# Installation

CORDA is three things, and you can adopt any subset:

1. a **CLI** (plain Python scripts — works anywhere, no framework);
2. an **agent skill** (the `gerar-corda/` folder: `SKILL.md` is the operating
   contract, `references/` the method, `scripts/` the tools) — installable in
   Claude Code, Claude apps, Codex, or any runner that reads files and runs
   Python;
3. a **universe compiler** whose output (`BOOTSTRAP.md` + `STATE.json`) runs
   in **any** LLM, with no framework at all.

## Requirements

- Python 3.10 or higher;
- Pillow optional for PNG;
- no mandatory dependency for SVG, Markdown, and JSON.

## Verify the copy

At the project root:

```bash
python3 scripts/verify_repo.py
```

The command runs: structural validation of the skill; the cast-derivation
benchmark; the compiler conformance benchmark; the full unit-test suite
(79 tests at v1.0.0-rc.2, including re-derived adversarial probes from every
audit finding); a scan for private couplings and absolute paths; and — when a
development universe is present — a byte-level bundle rebuild gate (reported
as `SKIP` in this public cut, whose development journal is private).

## Use as a CLI (no framework)

Cast derivation:

```bash
python3 gerar-corda/scripts/derive_cast.py \
  --brief /path/brief.json \
  --out-dir /path/output \
  --basename universe
```

Compilation (always pass `--evidence-root` pointing at the directory your
manifest's `content_path` entries are relative to — unresolved evidence
refuses to compile, by design):

```bash
python3 gerar-corda/scripts/build_universe.py \
  --spec /path/manifest.json \
  --out-dir /path/output \
  --basename universe \
  --evidence-root /path
```

State mutations go only through the sanctioned scripts
(`record_evidence_delta.py`, `record_acceptance.py`, `record_round.py`,
`record_mast_review.py`, `downgrade_state.py`) — never edit generated
outputs by hand.

## Install as a skill

### Claude Code

Per project (the skill applies inside that repository):

```bash
mkdir -p .claude/skills
cp -R gerar-corda .claude/skills/gerar-corda
```

Or per user (available in every project):

```bash
mkdir -p ~/.claude/skills
cp -R gerar-corda ~/.claude/skills/gerar-corda
```

Start a new Claude Code session; ask for CORDA/SGM or cast derivation, or
invoke it directly with `/gerar-corda`.

### Claude apps (Cowork / claude.ai)

Package the skill folder as a zip and add it through the app's skills
settings:

```bash
cd gerar-corda && zip -r ../gerar-corda.skill . && cd ..
```

Upload `gerar-corda.skill` where your plan's settings accept custom skills
(naming and location vary by plan and platform version).

### Codex

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
cp -R gerar-corda "$CODEX_SKILLS_DIR/gerar-corda"
```

Open a new Codex task to refresh the skill catalog. (`gerar-corda/agents/openai.yaml`
carries the Codex-side metadata.)

### Any other agent runner

The skill has no runtime dependency on any vendor: `SKILL.md` is a plain
operating contract, `references/` are plain Markdown, `scripts/` are plain
Python. Any agent that can read files and execute Python can follow it —
point your runner's instruction mechanism at `gerar-corda/SKILL.md`.

## Use the compiled universe in any LLM

The generated runtime is provider-independent. Load, in order:

1. `<basename>-BOOTSTRAP.md` (the single neutral load — it embeds a build-time
   STATE snapshot and tells you the disk STATE wins if they diverge);
2. `<basename>-STATE.json` (the current mutable state, source of truth);
3. the authorized sources for the run.

The host must implement persistence, tools, and permissions. CORDA must not
claim to have recorded state or executed actions if the integration does not
offer those capabilities.
