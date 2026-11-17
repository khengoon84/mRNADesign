# Phase 2 prompt — paste into a new session

You are continuing the **mRNADesign** project at `/home/khengoon/projects/mRNADesign` — a public open-source Google Colab notebook that orchestrates proven open-source tools for mRNA sequence design and DNA construct design. Phase 1 (specification) is complete and approved. Your job is **Phase 2 only: produce an implementation plan and a task breakdown.** Do not write product code.

## Read first, in this order

1. `mRNADesign.md` — statement of intent + scope decisions (source of truth for scope, users, constraints, out-of-scope)
2. `DECISIONS.md` — append-only decision log; the record of *why* the specs say what they say. Do not re-litigate an entry; if one looks wrong, raise it rather than working around it.
3. `CAPABILITY-MAP.md` — module ids, dependency direction, build order, V1/V2 line
4. `SPEC-notebook-shell.md`
5. `SPEC-rna-design.md`
6. `SPEC-rna-qc-additions.md`
7. `SPEC-dna-construct.md`
8. `SPEC-experimental-tier.md` — V1 registers **PARADE only**; read it for that engine's obligations and to confirm everything else stays out of V1

Then load the `planning-and-task-breakdown` skill and follow spec-driven-development Phase 2.

## Scope

- **In:** V1 — `notebook-shell` → `rna-design` → `rna-qc-additions` → `dna-construct`, plus **PARADE as a single opt-in engine** in `experimental-tier` (RD-2.10, RD-2.11, XT-1.1, XT-1.11, XT-2.4).
- **Out:** everything else in `experimental-tier` (UTRGAN, Smart5UTR, epitope/antigen), `cloning-simulation`, and everything on the specs' Deferred lists.

PARADE is in scope because it is the fallback when Optimus 5-Prime cannot fit the Colab free tier. It is **never** on the default path: not in `default_adapters`, not in a fallback chain, not reachable without an explicit user action in that run. Plan its adapter and its labelling, not its promotion.

## Produce

- `tasks/plan.md` — component dependency graph, implementation order, what can be parallel vs must be sequential, risks with mitigations, verification checkpoints between phases.
- `tasks/todo.md` — tasks sized to one focused session, ≤5 files each, each with **Acceptance / Verify / Files**, ordered by dependency rather than perceived importance.

Prefer vertical slices: get `notebook-shell` + one adapter producing a real run bundle early, then widen. The golden case is the SARS-CoV-2 spike RBD fixture referenced by the specs; each spec's Commands section already defines its verification commands.

## Hard constraints — do not relax

- **No new algorithms.** Adapters and wrappers only. No codon optimiser, UTR model, signal-peptide/TM predictor, or recoding loop written here. RD-SC7's grep test stays.
- **Colab-only runtime.** No local install for users, no web app, no terminal step.
- **Pinned dependencies** at exact revisions, with licence and provenance recorded in `mrna_design/tools/manifest.yaml`.
- **One notebook.** The default path must complete with only the protein sequence entered.
- `not_run` is a distinct status from `pass`; skipped branches carry a recovery hint; no auto-ranking of candidates.
- **Never invent a default for a material choice** (backbone, construct source, vendor profile).

## Licensing position — settled, do not reopen

- The project's own code is **MIT**. MIT cannot be narrowed to research-only, so do not attempt it and do not describe the project as "MIT for research purposes only".
- LinearDesign is research-use-only / non-commercial. It is the default CDS engine, so the **default path** is research-only. That restriction lives on the dependency (RD-2.7, NS-3.8), is surfaced with a per-session acknowledgement, and is stated in the README and the report footer.
- Commercial use requires replacing or separately licensing that engine. The tool does not grant commercial clearance for anything.

## Version control — no git yet

The user has deliberately not started git (DECISIONS.md D-011). Do **not** make `git init`, a licence file, or a first commit a task.

- Current practice: dated immutable snapshots via `scripts/snapshot.sh` (writes `snapshots/<name>.tar.gz`, a sidecar README, and appends to `snapshots/SHA256SUMS`), plus the append-only `DECISIONS.md`.
- Plan should treat a snapshot before each significant change as the working baseline, and note that snapshots must be copied off-machine to be worth anything.
- Do **not** propose a repository layout, `.gitignore`, or branching model. Raising git as a later recommendation is fine; acting on it is not.

## Planning constraints

- `notebook-shell` comes first: it owns the config schema, contracts scaffolding, bootstrap, run ledger, and test harness. Nothing else can be verified without it.
- Define `DesignRequest` / `DesignResult` / `MrnaRecord` before implementing any adapter.
- QC's post-assembly pass (QC-1.6) is a runtime edge, not a build-order change — `dna-construct` never depends on QC.
- PARADE's adapter is gated on its **pip repin** (XT-2.4): plan it as a task with a gate, not as a certainty. If the repin fails, PARADE ships `unavailable` with a reason, and V1's 3′UTR story is the reference library alone.
- Turn the specs' Open Questions into **explicit tasks with gates**, not silent assumptions. At minimum: LinearDesign redistribution terms; licence verification for every pinned engine; Optimus 5-Prime CPU budget (decides whether the engine or the reference library is the default 5′UTR source, and whether PARADE takes a 5′UTR role); reference UTR curation and permission; vendor/generic profile sourcing; transmembrane predictor choice. If a gate is unresolved, mark the task blocked — do not pick a default on the user's behalf.

## Stop conditions

- Do not create source files, notebook cells, adapters, or tests.
- If two specs contradict each other, stop and report both requirement IDs; do not choose a winner.
- Finish by summarising the plan, listing what can start immediately, and listing decisions you need from me.
- Then wait for review — do not begin implementation.
