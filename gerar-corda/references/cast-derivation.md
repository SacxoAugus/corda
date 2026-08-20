# Cast derivation

Step that runs **before** the compiler. The pipeline stops being
`manifest → preflight → compile` and becomes:

```
subject + evidence → CAST DERIVATION → manifest → preflight → compile
```

Additive: it does not change evidence identity, independence, round
admission, or the compiler's conformance benchmark.

## The problem

Until now, the cast was input. Someone typed eight lenses and the compiler
compiled eight lenses. The number of agents was a matter of taste, and taste
tends toward the same error: inflating the cast to look complete.

In physics, no one chooses how many normal modes a bridge has. The number is
the dimension of the state space — you find it, you don't decide it.

## Cast derivation rule

**The cast is the number of separable evidence subspaces, plus the roles
required by the topology.**

Two mechanical consequences, not aesthetic ones:

- two lenses that observe the same thing **are the same lens** — merge them;
- a lens with no evidence of its own and no tool of its own **is not a
  lens** — it is an echo of the briefing; convening it produces a copy of
  the framing.

The machine that decides this already exists and is already validated.
`compare_observers` classifies pairs of observers by evidence topology. The
derivation runs it **in reverse**: not to measure corroboration, but to
discover that two proposed lenses are the same. Correlated there means
redundant here.

## Structural roles

They enter through the topology, independent of the subject:

| Role | When | Why |
| --- | --- | --- |
| Human boundary condition | always | who accepts, rejects, or alters; the universe does not create authority |
| Integrator | ≥2 lenses | one lens needs no integration |
| Adversary | 1 per orthogonal harm domain | see below |

### One adversary per orthogonal harm domain

Orthogonal = **disjoint evidence AND a distinct owner**. Domains that
overlap are the same harm seen from two angles and get a single adversary.

This is not invention: real systems arrive at this by hand. A product
derived from a licensed work and aimed at a vulnerable user has two harms
that do not reduce to one another — harm to the work (owner: licensor) and
harm to the user (owner: clinical advisory). Each needs its own veto,
because whoever protects the work has no way to assess risk to the child,
and vice versa.

A universe with a single adversary for two orthogonal harms has one harm
left unguarded — and no one notices, because the existing adversary always
returns a verdict.

### Adversary power

Required field: `advisory`, `veto`, or `escalation`. These are different
authorities, and the difference changes the outcome. An adversary with
advisory power returns a verdict and the integration proceeds regardless;
one with veto stops it. Hand-written systems tend to decide this by
accident of wording. Here it is declared.

Without declaration, the default is `advisory`, and the omission is
recorded.

## Subject boundary ≠ evidence boundary

`boundary.bulk` states **which sources** the universe reads. It does not
state **which subjects** it can address. These are distinct things, and the
second is usually the bigger risk: silent territory creep is how a focused
product turns into a generic chatbot.

`subject_boundary` has `included` and `excluded`. Absence goes into
`requirements_unsatisfied`.

## Strings: fit and residual

An actor is not a point — it is a state to which different observables
apply. The same lens, under different observables, **sees different
things**.

- **Fit string** — what the available evidence supports. Every lens has
  one.
- **Residual string** — what the lens does *not* explain. It emits the
  structured remainder.

They are not opposites: fit + residual return the whole datum. It is
decomposition, not negation — and so it conserves rather than annihilates.

The test this enables is mechanical: **if the residual has structure, the
fit is wrong.** The residual string does not argue with the fit string; it
shows that the fit left a pattern behind. No one debates a residual plot.

### Why this matters more than it looks

Corroboration requires independence. Falsification does not.

Most agent systems cannot afford independence: one corpus, one model, one
briefing — every observer comes out correlated, and agreement among them is
worth nothing. But **self-confrontation comes free**, and a conclusion that
survives its own residual has produced something real.

For systems with shared evidence, this is the only rigorous move available.

### Admission criterion

The residual string costs a pass. It is not worth it for every lens.

Model the analogy properly: an open string with endpoints on two branes has
tension proportional to the separation between them. Large separation,
heavy string — expensive and informative. Small separation, light string —
cheap and redundant.

**Separation = fraction of the universe's evidence that the lens does not
have in scope.**

A narrow lens leaves a large remainder: the residual is where the value
lives. A lens that sees almost everything has an empty residual: the loop
would be noise. Default threshold 0.34 — a compiler parameter, not a
per-lens number.

The confrontation loop lives **between the strings**, with its own devil's
advocate, blind to the fit's intended conclusion. Local confrontation
happens *before* collapse, where it can still change something — unlike a
terminal gate, which can only reject.

### The global adversary does not dissolve

A devil's advocate per loop catches what that lens got wrong. It does not
catch what all the lenses got wrong **together** — shared briefing, corpus
with a common hole, single framing. Global correlation is invisible from
inside a loop.

So the global adversary survives, with a changed function: it stops
checking claims — the loops do that better and earlier — and starts
hunting for **common mode**. It is the only post from which this can be
seen.

## Cold start

Most subjects arrive with no corpus. If the echo rule ran there, it would
wipe out the entire cast of every project that is just starting.

When there is no `evidence_registry` and no private scope, the derivation
enters `structure_derived_provisional`:

- separability is instead judged by the **declared observable** (domain +
  question); the same question about the same domain is the same lens,
  under different names;
- nothing is cut for lack of private evidence;
- every lens comes out labeled `hypothesis` and the contract carries the
  warning;
- `separation` comes out `null` — with no corpus there is no observable
  separation, and inventing a number would be worse than having none;
- the residual string is admitted anyway: the start is where the most is
  learned, fastest.

Re-derive when the first real evidence comes in.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `DERIVE_CAST` | ≥2 separable lenses; proceeds to manifest |
| `SINGLE_LENS` | one lens: nothing to integrate or confront — answer directly |
| `NO_UNIVERSE` | no lens survived: this calls for an answer, not a universe |

`SINGLE_LENS` and `NO_UNIVERSE` are refusals, and refusing is the most
valuable function of this step. A one-mode universe is expensive theater.

## Limits

- The derivation measures separation of **declared evidence**. It does not
  measure whether the evidence is sufficient, true, or well chosen.
- **A systematic hole in the corpus does not produce a lens.** The
  derivation cannot see what the entire source omits — it is the same
  common-mode problem, one level up, and no operator resolves it. Only a
  human can lift that floor.
- Merging correlated lenses removes redundancy, not shared bias.
- The 0.34 separation threshold is a project choice, calibrated on a small
  sample. It is not a constant of nature.
