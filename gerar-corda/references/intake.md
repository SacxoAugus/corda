# Intake without graph dependency

## Rule

Accept a narrative description, document, dataset, image, or graph. The
graph is one possible piece of evidence, not the mandatory input model. The
compiler still receives JSON; when the source is narrative, the LLM must
produce a draft manifest before preflight.

## Narrative description

Treat each statement as:

- `fact`: only when accompanied by verifiable evidence;
- `testimony`: an account attributed to a person/source;
- `inference`: a relationship constructed by the compiler;
- `hypothesis`: a plausible fill-in that requires testing;
- `decision`: a direction explicitly accepted by whoever holds authority;
- `unknown`: absence, ambiguity, or contradiction not yet resolved.

Do not automatically convert first person into `fact`. Preserve the original
description in `source.description` or by reference in `source.path`.

## Extraction

Produce the draft manifest with:

1. boundary, owner, and decision;
2. system characteristics;
3. components/modes explicitly mentioned;
4. observed interactions;
5. mutable state and time;
6. conflicts and uncertainties;
7. origin of each material statement;
8. canonical evidence record, common/private/tooling/`prior` scope;
9. task, oracle, ground truth, baseline, and success criteria, when they exist;
10. missing fields as `unknown`.

Do not create modes merely to fill out the topology. If the source does not
support components or relationships, leave them absent and allow
`INSUFFICIENT_INPUT`, `PROJECTION_ONLY`, or `NOT_APPLICABLE`.

Do not artificially split a common source to simulate independence. Mark
evidence as `private` only when access or observation is genuinely
exclusive. If there is no benchmark, compile as `compiled_unevaluated`.

## Characteristics for the gate

Fill in `system_characteristics` with value and origin:

```json
{
  "interacting_components": {
    "value": true,
    "source_ref": "narrative#paragraph-2"
  }
}
```

Use `false` only when the source supports the absence and record
`source_ref`. Use `null` when it cannot be known. `NOT_APPLICABLE` cannot be
decided by mere absence of fields.

Do not infer temporal dynamics from the presence of text in `time_horizon`.
Expressions such as `"no deadline"` are negative, not signals. Require
structure: `entropy.items`, a non-null `lead_time_days`, or `last_checked`.
Cross-check each explicit statement against these signals and record
`contradictory` in case of divergence.
