# Versioning

**Public releases start at 1.** This repository's first public release is
**CORDA 1.0.0-rc.1**; the current release candidate is **1.0.0-rc.2**
(cycle-10 repair of finding R-04 from the cross-model article review, plus
the mechanical chain-merge warning for R-03). Nothing was ever published
before this line.

## Why you will see "v3" and "v4" in the audit trail

Before publication, the compiler went through **four internal iterations**
(v1–v4) inside the maintainer's private archive, whose development journal is
not public. The audit documents in `docs/audits/` are preserved evidence and
therefore keep the internal names they were written with:

| Internal name (audit trail) | Meaning | Public identity |
|---|---|---|
| v2.2.1 / v2.2.3 | early internal compiler line (conformance baseline; early external audit) | pre-history, private |
| v3 | previous internal iteration; pinned by hash as the executable baseline the candidate is measured against (0/3 vs 3/3 on the authored acceptance cases) | pre-history, private |
| v4 (candidate) | the internal iteration this code descends from — the one audited, failed, repaired and gated in `docs/audits/` | **this code → 1.0.0-rc.x** |

Evidence is not rewritten: the internal names stay in the trail. New public
work uses public versions only.

## Why "-rc"

By this project's own governance, promotion requires gates that are still
open: a cross-model re-gate of the latest repair, a sealed holdout generated
by the owner outside any agent context, human visual review, and **explicit
human acceptance**. The `-rc` suffix drops when the owner records that
acceptance — not before, and never by an agent's decision.

The compiler stamps its version and source hashes into every
`*-verification.json` and ledger it produces (`compiler` field).
