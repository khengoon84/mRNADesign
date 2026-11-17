# Decision log — mRNADesign

Append-only. Newest last. Never edit or delete an entry; if a decision is overturned, add a new entry that supersedes it and says which one it replaces.

Format per entry: date, id, decision, why, what it rules out. Dates are ISO. IDs are `D-<n>` and are never reused.

---

## D-001 — 2026-11-16 — No new algorithms

Decision: the project is an orchestrator. Every capability comes from an existing open-source tool behind an adapter or plugin; no codon optimiser, UTR model, structure predictor, signal-peptide predictor, or recoding loop is written in this repo.

Why: the claim "an orchestrator over proven tools" is the whole reason a non-programmer can trust the output. Writing one small optimiser would make that claim unverifiable.

Rules out: QC performing recoding (it measures only), in-house "lightweight" predictors, and any fix that starts with "it would be easy to just compute...".

## D-002 — 2026-11-16 — Colab-only, single notebook, two modules

Decision: one public Colab notebook; Module 1 (`rna-design`) and Module 2 (`dna-construct`) are independently runnable in the same flow. No local install, no CLI prerequisite, no standalone web app.

Why: the target user is a molecular biologist without a terminal. Every additional surface is another thing that can fail without a recovery path.

Rules out: a packaged Python library as the primary deliverable, a hosted web service, and a "run locally if Colab is slow" escape hatch.

## D-003 — 2026-11-16 — LinearDesign is CDS-only

Decision: LinearDesign performs no UTR optimisation. The adapter is declared as a CDS engine, and UTRs come from elsewhere.

Why: confirmed from upstream. A spec that assumed joint 5′UTR+CDS design would have silently produced mRNA records with absent UTRs while claiming a complete design.

Rules out: presenting LinearDesign output as a whole-mRNA optimum; cross-adapter "best mRNA" rankings.

## D-004 — 2026-11-16 — UTRs: reference library + Optimus 5-Prime

Decision: V1 ships a cited reference-UTR library as data (`data/utrs/`), each entry carrying sequence, region, source, licence, and the label *reference, not optimised*. Optimus 5-Prime supplies 5′UTRs when it fits the CPU budget; the library is the fallback. Users may override either region.

Why: no V1 engine designs a 3′UTR, so without the library "Run all" cannot produce a complete mRNA. Inventing placeholder UTRs was the alternative and it is worse than a labelled reference.

Rules out: placeholder sequences, and treating a reference 3′UTR as a designed one in any report.

## D-005 — 2026-11-16 — Engines are plugins; selection is per step

Decision: engines live behind a versioned plugin contract and are selected per step (5′UTR, CDS, 3′UTR, each QC predictor). Mixing engines is normal.

Why: the user asked for the option to choose one tool or another throughout the workflow. Per-step is what makes that meaningful — a single global tool choice would make a mixed record impossible.

Rules out: fetch-and-execute plugin loading from a URL. Plugins come from pinned installs or local files only, because a public notebook that runs arbitrary remote code cannot make a reliability claim.

## D-006 — 2026-11-16 — Project licence MIT; research restriction sits on the dependency

Decision: the project's own code is MIT. LinearDesign's research-only / non-commercial restriction is recorded as an attribute of that dependency, not as a narrowing of the project licence.

Why: MIT cannot be restricted to research use without ceasing to be MIT. Putting the restriction where it actually applies keeps the licence honest and makes the constraint visible at the point of use.

Rules out: a project licence that claims to be MIT while forbidding commercial use, and silence about the restricted default engine.

Consequence: the default path is research-only because LinearDesign is on it. The notebook requires acknowledgement, and the README states that commercial use requires replacing or separately licensing that engine.

## D-007 — 2026-11-16 — DNAChisel is the only route to depletion

Decision: CpG/UpA depletion, forbidden-motif avoidance, and restriction-site removal are expressed as DNAChisel constraints at the design step. RNA QC measures and never recodes.

Why: it satisfies D-001 without a recoder, and it separates "what the design was asked to satisfy" from "what QC observed" — which is the distinction a reviewer will look for.

Rules out: a recoding loop in QC; silent relaxation of unsatisfiable constraints (they must be reported by name and location).

## D-008 — 2026-11-16 — Structure metrics are engine-attributed

Decision: ViennaRNA and LinearFold both report MFE/ensemble metrics, and every value names the engine that produced it. Two engines' values are never merged into one series or ranked against each other.

Why: the energy models differ. Comparing them would look like a design improvement when it is only a change of ruler.

## D-009 — 2026-11-16 — Signal peptide via DeepSig / PEFT-SP

Decision: signal-peptide prediction uses DeepSig or PEFT-SP. SignalP is excluded.

Why: a licence-gated predictor leaves most users with a permanent `not_run`, which reads as a broken check. Both replacements are open source and installable.

Open: transmembrane prediction has no chosen engine yet and stays `not_run` with its own reason.

## D-010 — 2026-11-16 — PARADE ships in V1, opt-in only

Decision: PARADE (MIT, `autosome-ru/parade`) is registered in V1 as the single experimental engine, offering 5′/3′UTR generation and UTR activity/stability prediction. It is never in `default_adapters`, never in a fallback chain, and never reachable without an explicit user action in that run. Maturity `best_effort` until its conda-only environment is repinned to pip.

Why: it is the only viable 3′UTR engine, and the user asked for it to be selectable when Optimus 5-Prime cannot fit the Colab free tier. Shipping it with the full reliability contract binding is cheaper than retrofitting the contract later.

Rules out: substituting PARADE automatically when proven UTR sources fail (RD-2.11); any experimental result affecting run status or QC status columns.

## D-011 — 2026-11-16 — No version control yet; dated snapshots instead

Decision: the workspace is not a git repository. History is kept as dated immutable snapshots (`scripts/snapshot.sh`, `snapshots/`) plus this append-only log.

Why: the user asked not to start git yet. Snapshots give a recoverable state without committing to a repository layout, a licence file, or a `.gitignore` that would be decided prematurely.

Rules out: treating the working directory as recoverable. A snapshot on the same disk does not survive the failure it protects against, so snapshots must be copied off-machine.

Note: `git init` publishes nothing (no account, no network) and remains the expected floor once implementation starts. This entry records a deliberate deferral, not a rejection of version control.

## D-012 — 2026-11-16 — Phase 1 approved; Phase 2 in a separate session

Decision: the specification set (`CAPABILITY-MAP.md` + six `SPEC-*.md`) is the Phase 1 deliverable and is approved. Planning and task breakdown happen in a new session with `PHASE2-PROMPT.md`.

Why: spec and plan are different modes of thinking, and the planning session needs the specs, not the history of drafting them.

## D-013 — 2026-11-17 — Project licence MIT; copyright holder line intentionally blank (G0)

Decision: this repository's own code is MIT. The copyright holder line is left deliberately blank for the user to fill in manually. Because no `LICENSE` file is written until T69 (see D-016), the decision is recorded here, and will be surfaced in `docs/tool-licences.md` when T03 creates it; T69 writes `Copyright (c) 2026` with no name.

Why: MIT cannot be narrowed to research-only without ceasing to be MIT, and the project's only commercial limitation belongs to the engines a user selects (D-017). Leaving the holder blank is the user's explicit instruction; inventing a holder would assert authorship the project cannot verify.

Rules out: a research-only project licence; a licence claim in `README.md` before T69; putting a holder name in the metadata.

Requirement ids: `mRNADesign.md` §Licensing; NS-3.8; plan G0.

## D-014 — 2026-11-17 — Reference-first UTR default (supersedes D-004's ordering; G8)

Decision: the default UTR source is the **cited reference library** (`data/utrs/`), with the BNT162b2 5′+3′ pair as the default and the other vaccine entries selectable. Resolution order for the default set is **user-supplied → reference library → selected opt-in proven engine**, with any substitution labelled. `optimus5` and `parade` are opt-in only, never automatic. Each entry carries its primary-source citation and the label *reference, not optimised*.

Why: no V1 engine designs a 3′UTR, and making the 5′UTR depend on a conda-installed model put the heaviest step on the first-run path. D-004's ordering (engine first, library as fallback) described a default the user could not reach on a free Colab tier within a useful time.

Supersedes: D-004's *ordering* only ("Optimus 5-Prime supplies 5′UTRs when it fits the CPU budget; the library is the fallback"). D-004's structure — library as cited data, labelled *reference, not optimised*, no placeholders — stands unchanged. D-006's licence structure is unchanged.

Rules out: Optimus or PARADE on the default path; cross-vaccine mixing in the default record; treating a reference 3′UTR as designed.

Requirement ids: RD-2.11, RD-4.1a, RD-4.1c; plan item 12 / G8.

## D-015 — 2026-11-17 — LinearDesign is CDS-only; poly(A) is a fixed construct element (G21, G22)

Decision: LinearDesign designs the CDS only and never a UTR. The `Capabilities(designs=("cds", "utr5"))` sample in `SPEC-rna-design.md` is a specification defect, not an implementation target. Separately, poly(A) is a fixed construct element driven by `template_type`: `pcr` encodes none and states the tail is added enzymatically; `plasmid` encodes a user-set length (default 100 nt). No poly(A) optimisation toggle or CLI flag exists.

Why: both are domain facts confirmed at source on 2026-11-16. Implementing the sample literally would put a 5′UTR on the CDS engine and contradict RD-4.1a/RD-SC15; exposing poly(A) as a toggle would present a fixed element as an optimisation target and contradict DC-2.2/DC-SC10.

Confirms: D-003 (LinearDesign CDS-only) and D-007 (depletion is DNAChisel's job; QC only measures). The corresponding spec deltas are still owed (T32, T55).

Rules out: any `--poly-a` flag; `linear` as a template vocabulary word (the vocabulary is `pcr`/`plasmid`); a UTR capability on LinearDesign's adapter.

Requirement ids: RD-2.4, RD-2.6, RD-4.1a, RD-SC15; DC-2.0, DC-2.2, DC-SC10.

## D-016 — 2026-11-17 — Version control deferred until V1 is complete (T69)

Decision: no git repository, no `.gitignore`, no `LICENSE` file and no commit exists until V1 is complete. History is dated immutable snapshots (`scripts/snapshot.sh`) plus this append-only log. `git init`, the first commit, `LICENSE`, `.gitignore` and `THIRD-PARTY-NOTICES.md` are written at T69, after release sign-off.

Why: the user asked not to start git yet; starting it would force an early repository-layout decision and a licence file whose holder line is still blank (D-013).

Supersedes: the final sentence of D-011's note ("`git init` ... remains the expected floor once implementation starts"), which is now timed to T69 rather than to the start of implementation. D-011's reasoning and its off-machine snapshot rule stand.

Rules out: using git history as the recovery mechanism during V1; proposing a repository layout, branching model or `.gitignore` early.

Requirement ids: plan item 7 and item 16; T01, T03, T69.

## D-017 — 2026-11-17 — G25/G26/G27: `codonbert` is the default CDS engine; engine-selective notice; folding-engine conditions accepted

Decision: **G25 = option B.** `codonbert` is the default CDS engine; `lineardesign` and `custom` remain explicit user selections. The tool is built for research **and** commercial use: the project code stays MIT, and the only commercial limitation is the one attached to the engine the user selects — a `lineardesign` run's commercial use requires a licence the **user** obtains, stated in a printed notice at selection time and recorded in bundle, report and manifest.

**G26** is resolved by the same logic: an engine-selective **printed notice**, not a click gate. The default path (`codonbert`) asks nothing; selecting a restricted engine renders the responsibility notice. No per-session acknowledgement step exists.

**G27** conditions are accepted: ViennaRNA and LinearFold permit research, educational and commercial use under custom conditions (no-fee redistribution, visible credit/citation, and for ViennaRNA author contact before embedding in a commercial product). These are notice obligations, not a research-only restriction; they do not make the default path research-only.

Why: the default must be an upstream engine (D-001), `custom` cannot complete without a tissue target that the project forbids inventing, and a research-only default conflicts with the stated research-and-commercial intent.

Open consequence: **G2** (CodonBERT weights licence) is the remaining factual gate for the default's commercial claim. T36 may be built, but the default's commercial usability is not claimed until G2's verdict is recorded. T36's CPU/RAM measurement on the golden protein is a hard gate: a measured free-tier failure is reported to the user with the numbers, never silently swapped.

Rules out: a click gate on the default path; a research-only default path; promising that a commercial licence exists for any restricted engine (D-019); promoting `lineardesign` back to default without a new entry.

Requirement ids: RD-2.7, RD-2.9, RD-2.10, RD-4.1a, RD-SC9, RD-SC15; NS-1.1, NS-1.5, NS-3.8, NS-SC1, NS-SC7; plan G25/G26/G27.

## D-018 — 2026-11-17 — `custom` ships only as the separate GPL-3.0 package `mrna-design-custom`

Decision: upstream `hexavier/CUSTOM` is GPL-3.0, not MIT (verified at source 2026-11-16: `LICENSE`, `setup.py`, PyPI metadata). The adapter ships as its own GPL-3.0-licensed package at `packages/mrna-design-custom/`, declaring `license = "GPL-3.0"` in its metadata and depending on the MIT core. The MIT core never imports it; a core test asserts that. In the notebook, `custom` is listed as **unavailable-with-reason, naming the package**, until the package is installed — never silently absent. No `LICENSE` file is written before T69 (D-016).

Why: an adapter that imports a GPL library is the conservative combined-work case. Keeping it out of the MIT distribution preserves the project's licence position while still letting a user opt in explicitly.

Rules out: `custom` inside `mrna_design/`; `custom` as a default or fallback; a distribution that silently carries GPL code into an MIT claim; a default tissue value.

Requirement ids: RD-2.2, RD-2.4, RD-2.10, RD-4.4, RD-6.6, NS-1.2a; plan §CUSTOM adapter boundary, T35.

## D-019 — 2026-11-17 — Licence wording rule: restricted dependencies say "contact the rights holder"

Decision: no document, notice, report footer, manifest line or README ever promises or implies that a commercial-licence path exists or is obtainable. For every dependency whose terms restrict commercial use (research-only, conditional, or silent), the notice uses exactly:

> *Commercial use of this engine's output is not granted by this project. Contact the rights holder before using the output commercially.*

This applies uniformly, including `lineardesign`. Each dependency records a machine-readable `commercial_use` attribute in `mrna_design/tools/manifest.yaml` with one of `permitted` / `conditional` / `contact-rights-holder` / `excluded`, surfaced in `docs/tool-licences.md`, the selection-time notice, the report footer and the README at T67.

Why: the project cannot verify that a licence is available, and a notice that assumes one would be a factual claim the project cannot support. A single wording removes per-dependency drift.

Rules out: per-engine bespoke licence promises; "may be available", "licence can be obtained" and similar phrasings; a notice that names a fee, a term or a vendor as certain.

Requirement ids: NS-3.8; RD-2.7; plan §Licence wording rule; T17, T20, T67.

## D-020 — 2026-11-17 — Off-machine snapshot rule withdrawn; snapshots live in `backups/` in the workspace

Decision: **the requirement to copy snapshot archives off-machine is withdrawn** by the user. Snapshot archives, their sidecar READMEs and `SHA256SUMS` are stored in `backups/` inside the workspace. `scripts/snapshot.sh` writes there and `scripts/snapshot.sh --list` reads there. The user has explicitly accepted the risk this carries: an archive on the same disk does not survive disk failure, filesystem corruption, loss or re-registration of the WSL distribution, or deletion of the workspace.

Why: the user judged the off-machine step not worth its friction and asked for the rule to be removed. Recording the withdrawal keeps the decision log honest; the project may not silently keep a requirement the owner has dropped, nor silently drop one without a record.

Supersedes: D-011's rules-out clause ("snapshots must be copied off-machine"); the off-machine sentence D-016 left standing; the same instruction in `tasks/implementation-prompt.md` and `PHASE2-PROMPT.md`; and `CAPABILITY-MAP.md` §Notes. D-011's other content stands: there is still no repository, and snapshots plus this append-only log remain the only history.

Deviation recorded (task text not renumbered): T01's acceptance bullet changes from *"output copied off-machine, copy instructions recorded"* to *"archives stored in `backups/` in the workspace; off-machine copy not required by decision (D-020)"*. T01 is otherwise unchanged.

Rules out: claiming that an in-workspace archive is a disaster-recovery copy; treating `backups/` as protection against hardware loss; any later "restore from backup" procedure that assumes the copy survived.

Consequence accepted: if this disk fails or the workspace is deleted before T69, the project is lost. That is the user's stated position, not an oversight, and this entry is the record of it.

Requirement ids: T01; plan D7; CAPABILITY-MAP §Notes.

## D-021 — 2026-11-17 — T03 dependency notice surface: derived seed set, class vocabulary, no inferred permissions

Decision: `docs/tool-licences.md` is the dependency notice surface from T03 onward, and `docs/licence-claims.md` holds the public claims drafted for publication at T69. This repository's own code is MIT with the holder intentionally blank (D-013); no `LICENSE` file exists before T69 (D-016), so no public licence claim is published and `README.md` keeps its stub.

Because `mrna_design/tools/manifest.yaml` does not exist until T11, the T03 row set is **derived** from `SPEC-rna-design.md` RD-2.4, `mRNADesign.md` §Scope decisions, the gate register and `pyproject.toml`: LinearDesign; CodonBERT code and CodonBERT **weights as separate rows**; CUSTOM; GEMORNA; Optimus 5-Prime; ViennaRNA; LinearFold; DNAChisel; PARADE; DeepSig; PEFT-SP; SignalP (excluded); the undecided transmembrane options; the reference-UTR sequence data; CPython and the libraries/tooling that `pyproject.toml` pins or the specs name; the two library choices not yet made (G16 construct map; the QC plot renderer); and the Google Colab runtime. Revisions read `unpinned — gate Gx` wherever the gate is open; no revision is guessed. Once T11 lands, this file is generated/validated from `tools/manifest.yaml`, and a hand edit is a defect.

Class vocabulary: the task's `permissive` / `research_only` / `copyleft` / `excluded`, plus **`conditional`** and **`unverified`**. Reason: G27's verified ViennaRNA/LinearFold terms permit research, educational and commercial use *subject to conditions*, so `permissive` would understate the obligations and `research_only` would be false; an open gate is likewise a fact the four values cannot express, and T11 already requires an `unverified` licence class (RD-2.7). This is a wording extension, not a new gate: no dependency is recorded as `permissive` or `commercial_use: permitted` by inference from a plan sentence alone.

`commercial_use` is fixed to `permitted` / `conditional` / `contact-rights-holder` / `excluded` (D-019). Restricted, conditional or silent rows are never `permitted`; they carry the exact D-019 sentence. Classes recorded as of this entry: `permissive` — CodonBERT **code**, CPython 3.11.16, PyYAML 6.0.3, hatchling 1.33.0, ruff 0.17.5, mypy 2.4.1, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3 (Apache-2.0); `conditional` — ViennaRNA, LinearFold, CUSTOM, `mrna-design-custom`, reference-UTR data; `research_only` — LinearDesign; `excluded` — SignalP. Every other row is `unverified` pending its gate or the task that adds it (CodonBERT weights, GEMORNA, Optimus 5-Prime, DNAChisel, PARADE, DeepSig, PEFT-SP, the TM options, the planned Python libraries, the two unchosen plotting libraries, and the Colab runtime).

Why: T03 is the one task where a licence table could quietly become a set of assumptions. Recording open gates as `unverified` and refusing to infer permission from the plan keeps the notice surface truthful, and gives T17–T21 a precise set of rows to close rather than a prose document to rewrite.

Rules out: treating a plan or spec sentence as a licence verification; hiding an open gate behind `permissive`; writing a revision no gate has fixed; a `commercial_use: permitted` that no gate or verified licence supports; publishing any claim before T69.

Requirement ids: NS-3.1, NS-3.4, NS-3.8; RD-2.4, RD-2.7, RD-2.9, RD-6.6; D-013, D-017, D-018, D-019; T03, T11, T17–T21, T69.

## D-022 — 2026-11-17 — T03 public licence claims drafted for T69; `README.md` unchanged

Decision: `docs/licence-claims.md` contains the T69 claim text, unpublished until then: MIT for this repository's code with the holder line filled at T69 (D-013); the tool targets research **and** commercial use; the sole commercial limitation attaches to the engine the user selects; the default `codonbert` is not claimed commercially usable until G2's weights verdict (D-017); `lineardesign` is research-restricted and carries the exact D-019 sentence; `custom` ships as the separate GPL-3.0 `mrna-design-custom` package (D-018); ViennaRNA/LinearFold carry their accepted credit/redistribution/embedding conditions (D-017); the reference-UTR data may carry patent claims and is outside the MIT grant; no clinical, regulatory or wet-lab validation is claimed. `README.md` is left unchanged and makes no licence claim; its existing "Licence" section only points at the decision record.

Stale intent text noted, not reopened: `mRNADesign.md` §Licensing still says LinearDesign is the default and the default path is research-only. That is the pre-G25 intent, superseded by D-017 (G25-B: `codonbert` is the default). The drafted claims follow D-017. T67/T69 must not copy the stale sentence, and this entry is not permission to revise the intent document inside T03.

Why: the claims have to be reviewable and grep-able before they are published, and T69 is too late to discover that a sentence promises a licence the project cannot verify. Drafting them now also makes the wording rule (D-019) testable against a concrete text rather than an intention.

Rules out: a licence claim in `README.md` before T69; any claim that a commercial licence exists or is obtainable; presenting the pre-G25 intent text as the current licence model; a claim of clinical, regulatory or wet-lab validation.

Requirement ids: NS-3.8; `mRNADesign.md` §Licensing; plan §Licence wording rule; D-013, D-017, D-019; T03, T67, T69.

## D-023 — 2026-11-17 — CP0 (Foundation) signed off

Decision: the owner signed off **CP0 — Foundation** on 2026-11-17. All four checkpoint items passed on the tree recorded by snapshot `mrnadesign-20261117T033032Z-t03-licence-notice`:

1. `ruff check .`, `ruff format --check .` and `mypy mrna_design` clean.
2. The local CI sequence green: **12 passed** under `pytest -m "not network and not gpu and not e2e"`. The remote run still waits for the repository that starts at T69 (D-016), so "CI" means the identical command sequence run locally.
3. `DECISIONS.md` records G0 as MIT with the copyright holder line intentionally blank (D-013) and `docs/tool-licences.md` exists as the notice surface (D-021); **no `LICENSE` file** exists and none is written before T69.
4. The golden fixture exists with its citation in `docs/fixtures.md` (UniProtKB P0DTC2, residues 319–541) and the hash tests pass.

Why: CP0 is a stop-and-review gate. The sign-off is the owner's explicit decision after reading the evidence, not an agent's inference from a green test run.

Unblocks: **T05** (field taxonomy and `RunConfig` schema) and, behind it, Phase 1. T01–T04 and T03 are closed.

Rules out: treating this sign-off as approval of any public licence claim (the claims stay unpublished until T69, D-022) or as permission to create `LICENSE`, `.gitignore` or a repository early (D-016); re-running CP0 evidence from memory — a later checkpoint re-runs its own commands.

Requirement ids: plan §Verification checkpoints CP0; T01–T04; D-013, D-016, D-020, D-021.

## D-024 — 2026-11-17 — T05 `RunConfig` taxonomy implemented; pydantic pinned; declared representation defaults recorded

Decision: the approved field taxonomy (G19/G20 resolved 2026-11-16) is implemented in `mrna_design/config.py` and recorded in `docs/config-fields.md`, with a drift test asserting that the prose table and `RunConfig.field_specs()` name exactly the same fields and classes. The taxonomy is exactly the approved one: `required` = `protein_sequence` when `run_modules` includes `design` and `sequence_input` when it does not; `material` = `backbone_path` only, with no value default; `representation` = `run_modules`, `template_type`, `poly_a_length`, `construct_source`, `default_adapters`, `seed`, `adapter_seeds`, `report_title`, `run_label`.

Declared values that no earlier task fixed, recorded here rather than left in code: the global default seed is **42** (a convention, overridable per adapter via `adapter_seeds`; `adapter_seeds` defaults empty); `report_title` defaults to `"mRNADesign run report"`; `run_label` defaults `None` and, when supplied, must be a filename-safe component (`^[A-Za-z0-9][A-Za-z0-9._-]*$`), otherwise the ledger-generated run id names the output (T09); `poly_a_length` defaults `None` and is **not** defaulted in the schema — T06 resolves a plasmid template to 100 nt and writes it explicitly (DC-2.2); `construct_source` defaults to `"codonbert"` (G25-B; RD-4.1b delta); `default_adapters` stays `None` until T40. The schema rejects unknown keys (`extra="forbid"`), rejects a backbone supplied with `template_type="pcr"`, rejects `poly_a_length` on a `pcr` template, and rejects `template_type="plasmid"` without a backbone. Validation raises `ConfigValidationError` with field-level `.messages` (`"field: reason"`); the pydantic exception is retained only for `run.log` diagnostics at T10 (NS-5.2), never rendered (NS-2.2).

Dependency decision: **pydantic 2.14.3** is added to `pyproject.toml` as the schema engine (MIT; installed metadata checked 2026-11-17), with its transitive runtime components `pydantic-core` 2.50.4, `annotated-types` 0.8.0 and `typing-inspection` 0.4.5 recorded in `docs/tool-licences.md` as `permissive` / `permitted`. Those rows replace the T03 `unverified` pydantic row; the uniform-restriction list loses `pydantic` accordingly, because no condition or open gate remains.

Why: the schema is where an invented material default or a silently dropped field would be hardest to see later. Tagging each field in its JSON schema and failing closed when a class is missing makes NS-2.3 machine-checkable instead of a review habit, and fixing the arbitrary representation values now means T06 resolution and T09 manifest recording have one list to consume rather than three competing ones.

Rules out: any value default on `backbone_path`; accepting or ignoring unknown config keys; rendering a raw pydantic `ValidationError` or traceback to the user; classifying `construct_source` as material; accepting `poly_a_length` on a PCR template; treating the seed default as a biological or optimiser claim; choosing an adapter set before T40; requiring a new dependency pin without updating the notice rows.

Requirement ids: NS-1.2, NS-1.2a, NS-2.1, NS-2.2, NS-2.3, NS-5.4; RD-3.6, RD-4.1a, RD-4.1b (delta); DC-2.0, DC-2.2, DC-3.0; G19, G20, G25-B; D-013, D-017, D-019, D-021; T05, T06, T09, T10, T40.

## D-025 — 2026-11-17 — T06 resolution branch set, skip-proof summary, and pre-flight probe choices

Decision: `resolve_config()` turns a validated `RunConfig` into a `ResolvedConfig` whose flat `as_dict()`/`to_yaml()` payload is `config.resolved.yaml`: every `RunConfig` field explicit plus `branch_resolution`, `resolved_seeds` and `sequence_source`. Seeds resolve from the adapters passed by the caller, else from `default_adapters`, with per-adapter overrides applied and duplicate ids collapsed; a blank adapter id is refused. The plasmid poly(A) default of 100 nt is resolved into the written value; a PCR template leaves `poly_a_length` null. YAML is emitted with sorted keys so a re-run is comparable (NS-SC5).

`branch_resolution` has one entry per optional branch in the current schema: `design_module`, `construct_module`, `plasmid` and `encoded_poly_a`. States are `supplied` (the user or run supplied it), `defaulted` (a declared representation default was applied — currently only the plasmid poly(A) length) and `skipped` (not produced). Every skipped entry must carry a `recovery_hint` naming a real `RunConfig` field **and** a `cost_of_inclusion`; `BranchResolution` refuses the entry otherwise, and `PreflightSummary` checks the same invariant again so a model built from a bypassed nested object is still rejected (NS-1.5, NS-5.4, NS-SC8). A non-skipped branch cannot carry a stale hint or cost. The PCR poly(A) branch is recorded as skipped with a hint naming `template_type` and `backbone_path`, because an encoded tract is genuinely not produced in that run (DC-2.2) even though no poly(A) control exists for PCR.

`sequence_source` accepts exactly the NS-2.5 vocabulary — `user`, `design:<adapter_id>`, `run:<previous_run_id>` — and is set only when `run_modules` excludes `design`; supplying it for a design run is refused rather than ignored, and the default for a Module-2-only run is `user`. The caller supplies the provenance label from session state; T13 owns carrying a previous bundle forward.

Pre-flight (`mrna_design/notebook_ui.py`) is a model (`PreflightSummary`) plus one renderer. Adapter plans arrive as `StepEstimate(step, adapter_id, gpu_required, runtime_class, memory_class)`; runtime and memory class are **non-empty free-text declarations** from the adapter (RD-5.1), not an invented enum, because no spec fixes the vocabulary and T23 records the real adapter contracts. GPU presence is a best-effort `shutil.which("nvidia-smi")` probe, injectable for tests and replaceable at T13/T68; it never imports torch or changes the pipeline. Duplicate step/adapter pairs are refused, while one adapter may serve two distinct steps.

Why: NS-2.4 and NS-SC8 are integrity requirements, so the skip rule belongs in a constructor rather than in a renderer that a later caller might bypass. Recording the branch set explicitly now also fixes the vocabulary the manifest, README and report must reuse at T09/T16, and prevents a second, differently named branch list appearing later.

Rules out: writing a resolved config with an implicit field or unresolved seed; a skip without a field-level hint and cost; a summary rendered from an unvalidated branch list; inventing a runtime/memory-class enum before adapters declare their contracts; importing a deep-learning stack to probe for a GPU; treating a Module-2-only run, or a design/construct module omitted by `run_modules`, as a failure rather than a recorded state.

Requirement ids: NS-1.4, NS-1.5, NS-1.7, NS-2.1, NS-2.3, NS-2.4, NS-2.5, NS-2.6, NS-5.4, NS-SC8; RD-3.6, RD-5.1; DC-2.2, DC-3.0; D-017, D-024; T06, T08, T09, T13, T16, T23, T68.

## D-026 — 2026-11-17 — T12 tools root override and bootstrap contract (G17 resolved)

Decision: The tools install root defaults to `/content/tools` (the tested Colab path,
NS-3.2) and is overridable for CI/headless runs by exactly one documented
environment variable, `MRNA_DESIGN_TOOLS_ROOT` (G17). Alias variables are accepted for
convenience (`MRNA_TOOLS_ROOT`, `MRA_TOOLS_ROOT`, `TOOLS_ROOT`, ...) but the primary
variable always wins when several are set, so the override remains effectively single.

`mrna_design/tools/bootstrap.py` installs each non-excluded manifest entry at its pinned
revision into `<root>/<name>`, records the revision in marker files (`.revision`,
`REVISION`, `revision.txt`, `version.txt`, ...), re-verifies after install, and raises
`RevisionMismatchError` loudly on any mismatch instead of overwriting a differing
revision. A second run is a no-op when the recorded revision already matches
(NS-3.3). Imported-module drift is detected by `check_imported_version`, which raises
`VersionDriftError` when the module's `__version__`/`VERSION` differs from the manifest
pin (NS-3.5). Nothing is vendored; the re-pin procedure is documented in
`docs/re-pin.md` (NS-3.6).

Why: G17 is engineering-level and clears inside its own task (plan D6); keeping the
default at `/content/tools` preserves the Colab-tested path while the documented env var
makes headless reproduction possible (NS-6.1).

Rules out: overwriting a mismatched installed revision silently; treating an
unimportable module as drift failure during bootstrap; a second documented override
variable.

Requirement ids: NS-3.2, NS-3.3, NS-3.5, NS-3.6, NS-6.1; G17; T11, T12.
