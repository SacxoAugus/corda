# Precedence and collisions

## Invoking CORDA

Use it when there is an explicit request for CORDA/SGM or when the work is
to design an LLM runtime for a system with:

- two or more interdependent components/agents;
- mutable state or temporal dynamics;
- a pending human decision;
- conflict, uncertainty, a gate, or a need for synthesis.

## Do not invoke

Do not use it for:

- drafting a simple system prompt;
- summarizing or improving a static document;
- a single-step task;
- visualization without a runtime, unless a CORDA projection is explicitly requested;
- operating a system already covered by a domain skill.

## Domain skills

If a skill already knows how to load state and run the system, it takes
precedence for the operation. CORDA only takes precedence to:

1. assess whether the system warrants a runtime;
2. design/review its topology;
3. compile or migrate the universe.

The external router must know this rule. Until then, keep
`allow_implicit_invocation: false` and invoke with `$gerar-corda`.
