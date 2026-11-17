# mRNADesign

**Status: under construction.** V1 is being implemented from the approved Phase-2 plan
(`tasks/plan.md`, `tasks/todo.md`).

mRNADesign is a public Google Colab notebook that turns a protein sequence into an optimised mRNA,
a quality-control report, and a DNA construct — by orchestrating pinned, proven open-source tools.
Everything scientific is performed by an upstream tool behind an adapter; this repository contributes
orchestration, validation, provenance and reporting only.

- One notebook, no terminal, no local install (`notebooks/mRNADesign.ipynb`).
- Every engine is pinned with its licence and provenance recorded.
- `not_run` is not `pass`: anything skipped is reported with a reason and a recovery hint.
- No candidate is auto-ranked.

## Licence

The licence decision is recorded in `DECISIONS.md` (D-013) and the dependency notices in
`docs/tool-licences.md`. No public licence claim is made here yet; the `LICENSE` file is written when
the repository starts, after V1 is complete (D-016).

## Documentation

- `mRNADesign.md` — intent and scope
- `CAPABILITY-MAP.md` — modules, dependency direction, V1 definition of done
- `DECISIONS.md` — append-only decision log
- `tasks/plan.md`, `tasks/todo.md` — implementation plan and task breakdown
- `SPEC-*.md` — per-module specifications
