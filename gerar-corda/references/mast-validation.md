# MAST 2025 Profile v2

## Scope

Apply only to execution traces of genuinely multi-agent LLM systems.
Do not apply to projections, organizational components, or internal
sequential passes of a single LLM.

Versioned source: Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*,
NeurIPS 2025, version associated with the expanded MAST-Data dataset.

MAST is a diagnostic taxonomy, not proof of correctness. The published
proportions describe the corpus studied and must not be presented as a
universal failure rate.

The compiler separately applies `corda-design-v1` to every artifact: task,
roles, repetition, history, termination, and verification. This static
adaptation uses MAST-inspired categories, but is not labeled as a MAST
result and does not replace trace inspection.

## Checklist

### System design

| ID | Failure | Inspection question |
| --- | --- | --- |
| FM-1.1 | Task disobedience | Did any agent violate an explicit goal or constraint? |
| FM-1.2 | Role disobedience | Did any agent perform a function outside its contract? |
| FM-1.3 | Step repetition | Did the trace repeat an action without a change of state or evidence? |
| FM-1.4 | Loss of history | Did necessary information disappear between handoffs? |
| FM-1.5 | Ignored termination condition | Did the system continue or stop without respecting the gate? |

### Inter-agent misalignment

| ID | Failure | Inspection question |
| --- | --- | --- |
| FM-2.1 | Conversation reset | Did an agent restart while ignoring already-established state? |
| FM-2.2 | Failure to clarify | Was material ambiguity filled in without a question or a label? |
| FM-2.3 | Task derailment | Did coordination abandon the contracted goal? |
| FM-2.4 | Information withholding | Did available evidence fail to reach whoever needed it? |
| FM-2.5 | Ignored input | Was received input discarded without a recorded reason? |
| FM-2.6 | Reasoning-action divergence | Did the action contradict an issued conclusion, constraint, or evidence? |

### Task verification

| ID | Failure | Inspection question |
| --- | --- | --- |
| FM-3.1 | Premature termination | Did the system declare completion before the exit criteria were met? |
| FM-3.2 | Incomplete verification | Was a deterministic test or goal check missing? |
| FM-3.3 | Incorrect verification | Did the system claim success despite contrary evidence? |

## Recording

For each ID, use:

- `not_observed`: the trace contains sufficient evidence of absence;
- `observed`: the failure appears, with a reference;
- `uncertain`: insufficient or conflicting evidence;
- `not_applicable`: the mode does not apply to the run.

`observed` and `not_observed` require `evidence_ref`. Do not fill in the 14
items by inference. Record with:

```bash
python3 scripts/record_mast_review.py \
  --verification /path/corda-verification.json \
  --assessment /path/mast-assessment.json \
  --reviewer "name or agent" \
  --date YYYY-MM-DD
```

A single `observed` makes the profile `fail`. Items marked `uncertain` or
not assessed keep it at `pass_with_caveats`.
