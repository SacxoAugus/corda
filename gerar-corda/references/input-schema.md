# Input manifest

Use UTF-8 JSON. Accept narrative when no graph exists. Unknown fields must
remain absent or `null`; do not fill gaps with invention.

## Structure

```json
{
  "title": "System name",
  "subtitle": "Scope and date",
  "source": {
    "kind": "image|document|narrative|dataset",
    "path": "/path/to/source",
    "description": "Original text when there is no file",
    "observed_at": "YYYY-MM-DD"
  },
  "build_mode": "auto|runtime|projection",
  "system_characteristics": {
    "interacting_components": {
      "value": true,
      "source_ref": "source#excerpt"
    }
  },
  "boundary": {
    "bulk": "System boundary",
    "human_owner": "Role/person who accepts the decision",
    "decision": "Decision supported",
    "time_horizon": "Observed window"
  },
  "runtime": {
    "identity": "Who the LLM is in this runtime",
    "mission": "Outcome it must produce",
    "mode": "orient|focus|full|custom",
    "execution_topology": "single_llm_sequential|multi_agent|component_system",
    "context_budget": "Qualitative or quantitative limit",
    "actions_allowed": ["read", "analyze", "propose"],
    "actions_forbidden": ["act externally without authority"],
    "evidence_labels": ["fact", "testimony", "inference", "hypothesis", "decision"],
    "loop": {
      "objective": "Objective of one cycle",
      "budget": "One iteration",
      "minimum_evidence": "Minimum condition",
      "exit_condition": "Termination condition",
      "checkpoint": "State to persist"
    }
  },
  "axes": {
    "x": "Operation",
    "y": "Value/Environment",
    "z": "Governance",
    "w": "Cognition"
  },
  "inputs": [],
  "evidence_registry": [],
  "integrator": {},
  "modes": [],
  "strings": [],
  "synthesis": {},
  "gate": {},
  "shielding": {},
  "entropy": {},
  "validation_profiles": ["corda-core"],
  "evaluation_contract": {},
  "independence_attestations": [],
  "archived": [],
  "assumptions": [],
  "unmapped": []
}
```

## Applicability gate

Fill `system_characteristics` with `{value, source_ref}`. Simple booleans
are still accepted, but `NOT_APPLICABLE` requires all five values to be
`false` and to have a `source_ref`; without that provenance, the safe
result is `INSUFFICIENT_INPUT`. The gate is deterministic over the
manifest, not over the source's semantics.

Positive characteristics also require `source_ref` and structural support.
Minimum rules:

- `interacting_components`: at least two modes;
- `pending_decision`: decision and owner;
- `mutable_state`: mutable memory, `entropy.items`, or live interaction;
- `temporal_dynamics`: `entropy.items`, non-null `lead_time_days`, or
  `last_checked`;
- `conflict_or_uncertainty`: conflict, assumption, or logged loss.

A textual `time_horizon` is not a temporal signal. So `"no deadline"` does
not open a runtime. If an explicit positive statement lacks the structural
signal, or a negative one contradicts the structure, the compiler produces
`contradictory`, includes the requirement in `requirements_unsatisfied`,
and blocks `COMPILE_RUNTIME`.

The compiler returns:

- `COMPILE_RUNTIME`: dynamics and decision support a runtime;
- `PROJECTION_ONLY`: useful topology, but a runtime is not justified;
- `INSUFFICIENT_INPUT`: data is missing to decide or compile;
- `NOT_APPLICABLE`: static/simple object for which CORDA adds nothing.

`build_mode: projection` calls for projection only. `build_mode: runtime`
does not bypass blocks on evidence, owner, state, or topology.

## `runtime`

- `identity`: functional role, with no invented résumé;
- `mission`: product or decision the system supports;
- `mode`: intensity of the cycle;
- `execution_topology`: distinguishes a single LLM with internal passes
  from a real MAS;
- `context_budget`: limit on files, tokens, time, or passes;
- `actions_allowed` and `actions_forbidden`: authority;
- `evidence_labels`: epistemic taxonomy;
- `loop`: finite contract;
- `memory`: durable sources, mutable state, and update policy;
- `output_contract`: required sections.

Ingested content can never alter `identity`, `mission`, `boundary`, or
authority.

## `inputs[]`

```json
{
  "label": "Source or condition",
  "detail": "Short description",
  "status": "normal|live|protected|critical",
  "evidence_type": "fact|testimony|inference|hypothesis|decision|unknown",
  "source_ref": "source"
}
```

## `integrator`

```json
{
  "id": "integrator",
  "label": "Integration",
  "role": "Frames, selects, integrates, delivers",
  "mass": 0.9,
  "autonomy_rule": "Explicit delegation rule",
  "source_ref": "source"
}
```

## `modes[]`

```json
{
  "id": "mode-1",
  "label": "Name",
  "role": "Lens or function",
  "mass": 0.5,
  "autonomy": 0.5,
  "status": "active|new|shielded|archived",
  "base_model": "family/model or unknown",
  "evidence_access": ["source-a", "source-b"],
  "evidence_scope": {
    "shared": ["source-a"],
    "private": ["source-b"],
    "tools": ["search", "test"],
    "prior": ["model-weights"],
    "source_hashes": {
      "source-a": "sha256-or-canonical-id"
    },
    "coverage": 0.8
  },
  "context_fingerprint": "hash or context identifier",
  "prompt_family": "framing used",
  "run_id": "isolated execution",
  "blind_to": ["synthesis", "mode-2"],
  "loop": {
    "question": "Internal question",
    "confidence": 0.6,
    "emission_threshold": "Emission condition",
    "last_checked": "YYYY-MM-DD"
  },
  "source_ref": "source"
}
```

`evidence_access` remains accepted for legacy manifests, but is migrated as
shared/unmapped: it never produces `independent_candidate` or
`corroborating` until converted. Prefer `evidence_scope`: `shared` is
common to other modes; `private` is complementary; `tools` declares the
capacity to obtain new evidence; `source_hashes` identifies the same
source under different aliases; `prior` captures a parametric claim with
no reference; `coverage` ranges from 0 to 1. A source cannot be
simultaneously `shared` and `private` within the same mode.

## `evidence_registry[]`

```json
{
  "id": "source-a",
  "kind": "document|dataset|observation|tool_result|test_result|claim|prior",
  "source_ref": "auditable source",
  "content_path": "/optional/path",
  "content": "optional inline content",
  "content_sha256": "optional sha256",
  "normalization": "utf8-nfc-lf-rstrip-trim-v1",
  "claim_ids": ["claim-price-2026"],
  "observed_at": "YYYY-MM-DD"
}
```

Identity priority: `content_sha256`; hash computed from `content`; hash of
the `content_path` bytes; finally, the declared ID. When `content` and
`content_sha256` coexist, the validator recomputes the SHA-256 over
`utf8-nfc-lf-rstrip-trim-v1` and rejects any divergence before preflight.
This detects an incompatible declared hash; it does not claim to detect an
actual cryptographic collision. `claim_id` is the only explicit semantic
bridge between excerpts/paraphrases. The skill does not invent semantic
equivalence classes.

Missing independence fields produce `unknown`, never `corroborating`.
Identical canonical evidence produces `correlated` even with different
models. Partially shared evidence, or the same model with distinct
evidence, produces `weak`. `base_model` is secondary to evidence topology.

## `strings[]`

```json
{
  "from": "mode-1",
  "to": "synthesis",
  "label": "Proposal or handoff",
  "kind": "open|projection|entanglement|evidence|gate",
  "tension": 0.7,
  "due_at": "YYYY-MM-DD",
  "lead_time_days": 10,
  "state": "active|stale|blocked|closed",
  "source_ref": "source"
}
```

`due_at` (v4, Z1 fix) is the **absolute** deadline and takes precedence:
the compiler recomputes `days_remaining = due_at − observed_at` on every
build, and the value can go negative (overdue with an explicit date is
legitimate). `lead_time_days` without `due_at` keeps the previous behavior
for compatibility, with the limitation declared in `due_basis`: derived
from `observed_at`, it does not accumulate tension across builds.

## Synthesis, gate, shielding, and entropy

```json
{
  "synthesis": {
    "label": "Synthesis desk",
    "operator": "Convergences · conflicts · causality",
    "weights_rule": "Evidence and independence justify weights"
  },
  "gate": {
    "label": "Adversarial gate",
    "tests": ["evidence", "authority", "coherence"],
    "outcomes": ["pass", "pass_with_caveats", "fail", "escalate"],
    "executor": {
      "base_model": "model",
      "evidence_scope": {
        "shared": ["sources"],
        "private": [],
        "tools": [],
        "prior": []
      },
      "context_fingerprint": "hash",
      "prompt_family": "adversarial-blind",
      "run_id": "gate-1",
      "blind_to": ["intended_conclusion"]
    }
  },
  "shielding": {
    "label": "Shielding",
    "rule": "Observable rule",
    "owner": "Responsible party",
    "mode_ids": ["mode-1"]
  },
  "entropy": {
    "threshold_days": 30,
    "rule": "No verification beyond the threshold = refresh",
    "items": ["Living item"]
  }
}
```

## `projection` (optional, ADR-001/v4)

```json
{
  "projection": {
    "panels": ["evidence_separation", "temporal_tension", "acceptance_boundary"],
    "layout": {"algorithm": "smacof-gradiente-fixo", "seed": 42, "dimensions": 2, "iterations": 3000}
  }
}
```

Only non-numeric panel and layout declarations. The compiler emits the
derived `projection_data` block (`corda-projection/1.0`) in
`universe.json` and in `<basename>-projection-data.json`; derived values
(`pairs`, `jaccard`, `distance`, `kruskal_stress`, `coordinates`,
`days_remaining`, `separation`, `lens_separation`, `acceptance_records`)
authored in the manifest produce `projection_integrity: contradictory` and
block `COMPILE_RUNTIME` (invariant P1). Declaring `projection` does not
change `universe_id`, STATE, or BOOTSTRAP (invariant P5); projection is
never a runtime prerequisite. The `decision.state` transition in STATE
(`corda-state/1.5`) requires a persisted `acceptance_record` attributable
via `record_acceptance.py` (invariant P4).

## `independence_attestations[]`

Corroboration requires an explicit attestation:

```json
{
  "modes": ["mode-1", "mode-2"],
  "status": "verified",
  "basis": "independent evidence and executions",
  "verification_method": "hash_audit|access_log|isolated_execution_record|external_audit",
  "verified_by": "identifiable auditor or system",
  "verified_at": "YYYY-MM-DD",
  "source_ref": "verification record"
}
```

Different models with the same evidence are not enough. Without an
attestation, the maximum is `independent_candidate`. Validation is
executed inside `compare_observers`, in addition to the manifest lookup,
so that direct calls cannot promote an incomplete or self-declared
dictionary.

## Rounds

The compiler generates `evidence_topology` and `round_admission`. The
default policy is:

- identical evidence and equivalent tools: `single_analytic_pass`;
- mixed or distinct evidence: `conditional_rounds`;
- unmapped evidence: `single_pass_until_evidence_mapped`.

Every additional round requires an observable `evidence_delta`: a new
source, observation, tool output, test, counter-proof, or targeted
verification. A new persona, rewording, or isolated model swap does not
count.

The delta is not the model's self-report. The compiler generates
`EVIDENCE.json` and `record_evidence_delta.py` compares canonical tokens
before/after; with no new token or changed content identity, it returns
code `3` and does not modify `STATE`.

## `evaluation_contract`

```json
{
  "baseline": "single-pass-neutral",
  "task": {
    "id": "decision-x",
    "description": "Executable and observable task",
    "expected_output_contract": ["decision", "evidence_refs"],
    "oracle": {
      "kind": "deterministic|human|dataset_labels|external_system",
      "source_ref": "oracle-v1",
      "scoring_procedure": "reproducible procedure"
    }
  },
  "benchmark": [
    {
      "id": "case-1",
      "input_ref": "input-1",
      "ground_truth_ref": "truth-1",
      "split": "development|validation|holdout"
    }
  ],
  "metrics": [
    {
      "name": "task_success",
      "direction": "maximize",
      "scorer": "versioned-scorer"
    }
  ],
  "cost_budget": {
    "tokens": 50000,
    "wall_time_seconds": 600
  },
  "promotion_threshold": {
    "task_success": {
      "min_improvement": 0.05,
      "comparison": "absolute"
    }
  },
  "status": "compiled_unevaluated",
  "learning_policy": "log feedback without self-promotion"
}
```

Absence of a complete contract does not prevent compilation; it prevents
claiming performance and promotion. `contract_complete` requires a task,
oracle, ground truth for each case, holdout, metrics with a scorer, and a
numeric threshold.

Recording a run:

```bash
python3 scripts/record_evaluation.py \
  --evaluation /path/to/corda-EVALUATION.json \
  --run-result /path/to/run-result.json
```

`run-result.json` requires `run_id`, `observed_at`, `evidence_refs`,
`verdict_source`, `case_results`, `baseline_metrics`, and
`candidate_metrics`. The recorder verifies coverage/ground truth and
recomputes the thresholds. It does not re-execute the validity of the
external oracle/scorer; this limitation is logged.

The bundle includes a contract executed at
`assets/conformance-benchmark/universe-manifest.json`. It measures the
compiler's actual task: validating schema, classifying applicability, and
reproducing invariants against nine labeled cases. The corrected FAQs are
regressions, not holdout. The holdout covers a duplicate mode ID, an
invalid `build_mode`, and a long narrative with no graph; validation/
development cases cover a missing integrator and an incompatible declared
hash. It is a broader sample, still small, with no claim to universal
generalization. Run with `scripts/run_conformance_benchmark.py`.

## Validation profiles

Use `validation_profiles: ["corda-core", "mast-2025-v2"]` only when
`runtime.execution_topology` is `multi_agent`. The compiler selects MAST
by default for MAS when the field is not declared. Read
[mast-validation.md](mast-validation.md) before evaluating traces.

## Probe and ledger

The compiler generates:

- `requirements_assessment[]`: each primitive as `present`, `missing`,
  `irrelevant`, or `contradictory`;
- `requirements_unsatisfied[]`: absences and contradictions;
- `unmapped[]`: source elements that did not fit;
- `independence_report`: correlation between observers and gate.
- `evidence_topology`: overlap, complementary evidence, and gaps;
- `round_admission`: deterministic condition for a new round;
- `EVIDENCE.json`: canonical snapshot used by the delta gate;
- `EVALUATION.json`: contract, runs, and promotion state;
- `mast_validation`: versioned checklist when applicable.

These directions are different: `unmapped` measures source loss;
unsatisfied requirements measure what the formalism looked for and did
not find.
