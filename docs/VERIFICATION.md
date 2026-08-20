# Verification status

Restricted language only — each surface carries the strongest claim its
evidence supports, and nothing stronger:
`deterministically verified` · `agent-reviewed` (same base model: invalidates,
never corroborates) · `agent-reviewed, cross-model` · `human accepted` ·
`externally audited` · `not demonstrated`.

## Compiler core (inherited line)

The early internal line (audit-trail name "v2.2.3") was externally audited
before extraction: attestation validation at the decision boundary, inline
hash integrity, applicability and aborts, overlay isolation, the nine-case
conformance benchmark. That audit does not demonstrate generalization on an
unknown distribution. Inherited evidence: `externally audited` (scope above,
nothing more).

## Cast derivation

Order-invariant (transitive closure with content-derived representatives;
metamorphic tests: permutation, idempotence, duplication, transitivity). Four
synthetic cases, two holdouts, 4/4 conformant. Authorship of code and dataset
is shared — the benchmark proves sample conformance, not truth, sufficiency
or absence of common bias. Since cycle 10 (article-review finding R-04,
reproduced): adversary seats follow declared harm owners — distinct owners
never merge, so orthogonal harm domains provably never share a seat and no
named owner can vanish from the cast; and the declared lens chain-merge
limit (R-03) now emits a mechanical `chain_merge_warning` instead of merging
silently. Status: `deterministically verified` on the published sample; the
derivation rule is an **operational heuristic** with declared limits (see
SKILL), and every derived cast is a candidate.

## Extensions (introduced in the internal iteration named "v4")

- Compiler with extensions (projection_data, invariants P1–P6, STATE 1.5,
  absolute deadlines, compiler stamp, MAST auto-required for multi-agent
  topology): `deterministically verified` — 79 unit tests, conformance 9/9,
  cast 4/4, byte-level bundle rebuild gate, and re-derived adversarial probes
  from every audit finding (S-01…S-09, N-01…N-08, R-03/R-04) asserting each
  one no longer reproduces (or, for the declared R-03 limit, warns).
- Architecture decisions (ADR-001, multi_agent topology, ACCEPTANCE v1.2 with
  deterministic oracle, mandatory content-addressed scorer report, exact
  contract-case matching, transactional evaluation↔state writes):
  `human accepted` as *adjusted* (recorded via `record_acceptance.py`;
  the acceptance record lives in the private development journal).
- Evaluation against the predecessor: the internal "v3" iteration is pinned
  by hash as an executable baseline and run by the same procedure: 0/3 vs
  3/3 on the three authored acceptance cases. This is capability presence
  under an authored contract — **not superiority**, and not the nominal
  test-suite proof, which remains queued.
- MAST 2025 v2 over real traces: honest `fail` records preserved (state-loss
  and verifier-independence findings, with mitigations declared). A passing
  MAST was never claimed.

## Adversarial trail (cross-model)

- Audit #1 (2026-07-29): promotion **rejected**; three internal claims
  refuted; findings S-01…S-09 — all later reproduced by the maintainer's
  integrator and fixed. `agent-reviewed, cross-model`.
- Review #2 (2026-08-19): material progress; "utility demonstrated in this
  episode" for one real field round; **do not promote**; findings N-01…N-04
  — reproduced and fixed.
- Isolated adversarial gate (2026-08-20): executed by the cross-model
  reviewer from a clean `git archive` of the frozen candidate. The nominal
  battery passed integrally; the **free attack failed the candidate**
  (N-05…N-08) — reproduced and fixed. This is the project's central
  empirical result: a completed checklist is not an adversary.
- Article review #4 (2026-08-20): the same cross-model reviewer
  adversarially reviewed the project's preprint (revision 2) with reviewer's
  eyes (public materials only; prior exposure declared). Verdict: **do not
  submit** in that form; findings R-01…R-13, including two executable
  counterexamples against the published code — both reproduced by the
  integrator; R-04 fixed in cycle 10, R-03's declared limit now warns.
  `agent-reviewed, cross-model`.
- No extension surface is `externally audited` by a human/organization. The
  external-audit claim remains restricted to the inherited core.

## Field use

One real deployment of a compiled universe on a real pre-existing project
from the maintainer's own practice — not authored for this evaluation; the
field project's human owner is the maintainer himself, which is disclosed
wherever the deployment is claimed (subject redacted in the public cut): a genuine multi-agent round in which
the universe's own gate rejected a defective recommendation (governance
bypass + personal-data processing without legal basis), forced a repair, and
only then passed it; and one external session in which round admission
correctly **refused** redundant work and escalated two real defects instead
of fabricating novelty. Status: utility demonstrated in these episodes —
attribution narrow, generalization `not demonstrated`.

## Still open before promotion

Cross-model re-gate of the latest repairs (cycles 08 and 10); sealed holdout generated by the
owner outside any agent context and executed by the runner; nominal
predecessor test-suite proof; human visual review; **explicit human
acceptance** — which no agent can give.
