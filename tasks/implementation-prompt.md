# Implementation session prompt — mRNADesign V1

Copy everything below this line into the new session.

---

Use the **incremental-implementation** skill for this entire session: deliver the work in thin,
verifiable slices, one increment at a time, and never move to the next increment until the current
one's Verify command passes.

## Your job

Implement V1 of mRNADesign strictly per the approved Phase-2 deliverables in this workspace:

- `tasks/plan.md` — architecture, decision record, gate register, checkpoints CP0–CP6, spec defects
- `tasks/todo.md` — 75 dependency-ordered tasks (T01–T69 + T37A, T41A–T41C, T42A; T32A cancelled)
- `DECISIONS.md` — append-only decision log
- Specs: `SPEC-notebook-shell.md`, `SPEC-rna-design.md`, `SPEC-rna-qc-additions.md`,
  `SPEC-dna-construct.md`, `SPEC-experimental-tier.md` (binding for the PARADE slice only)
- `mRNADesign.md`, `CAPABILITY-MAP.md` — intent and scope

Read `tasks/plan.md` and `tasks/todo.md` fully before writing any code.

## First actions, before any implementation

1. Run `scripts/snapshot.sh pre-implementation`; archives are stored in `backups/` in the workspace (off-machine copy not required — `DECISIONS.md` D-020).
2. Append the deferred decision entries to `DECISIONS.md` (D-013 onward, per plan §Decision record):
   MIT with blank holder; git deferred until V1 completes (T69); G25 = option B (`codonbert` default
   CDS engine, `lineardesign`/`custom` opt-in, per-engine licence responsibility sits with the user);
   G26 = engine-selective printed notice, no click gate; G27 = ViennaRNA/LinearFold conditions
   accepted; CUSTOM ships as a separate GPL-3.0 package (`mrna-design-custom`); licence wording rule —
   every restricted dependency says "contact the rights holder", never promising a licence exists.
3. Start with **T01**, then **T02**, then **T04**, in that order. Gate tasks T17–T25 are research
   tasks with no product code; slot them in as their outputs unblock adapter work.

## Hard rules (violate none)

- **No new algorithms.** Every scientific step wraps a pinned upstream tool through an adapter. Do not
  reimplement, patch or fork engine logic. RD-SC7's grep test stays and must pass.
- **Colab-only runtime; one notebook** (`notebooks/mRNADesign.ipynb`); the default path must complete
  with only the protein sequence entered — no dialogs, no questions (NS-SC1/NS-SC7).
- **Pinned dependencies** with licence and provenance in `mrna_design/tools/manifest.yaml`.
- **`not_run` is not `pass`.** Skipped branches carry recovery hints naming real, shipped fields.
  **No auto-ranking** — the comparison table never picks a winner.
- **Never invent a default for a material choice** (backbone, construct source, vendor profile,
  tissue, UTR beyond the decided reference library). Absent → `unavailable` with a reason.
- A task marked 🔒 BLOCKED waits for its gate. Do not start it, and do not pick a default to unblock it.
- Tasks are sized to one focused session, ≤5 files each, each with Acceptance / Verify / Files.
  Do not renumber; record deviations in `DECISIONS.md`.
- If you find a spec contradiction, **report it with both requirement IDs and stop** — do not choose a
  winner.
- Default CDS engine is `codonbert` (G25-B). G2 (weights licence) is its remaining gate: build T36,
  but do not claim the default's commercial usability until G2's verdict is recorded. Its CPU/RAM
  measurement is a hard gate — a measured free-tier failure is reported back, never silently swapped.
- `custom` ships **only** as the separate GPL-3.0 package `packages/mrna-design-custom/` (T35); a core
  test asserts `mrna_design/` never imports it.
- **No git.** The repository starts at T69 after V1 is complete. Use `scripts/snapshot.sh` before and
  after each significant change; archives stay in `backups/` in the workspace (D-020).
- Report progress per increment: what was implemented, the Verify output, which tasks closed, what
  unblocked, and wait for my review before the next increment. Stop for review at every checkpoint
  CP0–CP6.

## Increment discipline (incremental-implementation skill)

- Pick the lowest-numbered task whose dependencies are all closed.
- One task per increment (or a dependency-locked pair when the second is trivial).
- End every increment with: the task's Verify command run green, the acceptance bullets checked off in
  `tasks/todo.md`, and a one-paragraph status note.
- If an increment cannot verify green, stop, diagnose, and report — do not widen the slice.
