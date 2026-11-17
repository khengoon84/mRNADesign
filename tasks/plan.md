# Implementation Plan: mRNADesign — V1

**Status:** proposed, awaiting review. **G25 is decided (2026-11-16): option B** — `codonbert` is the
default CDS engine; `lineardesign` and `custom` remain available as explicit user selections. **Licence
model decided with it:** the tool is developed for research *and* commercial use, and the only commercial
limitation is the one attached to the engines the user chooses — selecting `lineardesign` makes obtaining
a commercial licence the **user's responsibility** if the output is commercialised. **G26 is decided** by
the same logic: an engine-selective printed notice, no click gate on the default path. **G27's
conditions are accepted** for V1's free distribution. Remaining gates: **G1** (LinearDesign
terms/fetch), **G2** (CodonBERT weights — now the critical path for the default), G3, G9, G8 curation.
The CUSTOM shipping boundary is **resolved: a separate GPL-3.0 adapter package**; and a uniform
licence-wording rule applies to every dependency (§Licence wording rule): the tool never promises that a
commercial licence exists — restricted tools say "contact the rights holder". Version control is
decided: deferred until V1 is complete (T69).
**Source specs (approved, Phase 1):**
`mRNADesign.md` (intent) · `CAPABILITY-MAP.md` · `SPEC-notebook-shell.md` · `SPEC-rna-design.md` ·
`SPEC-rna-qc-additions.md` · `SPEC-dna-construct.md` · `SPEC-experimental-tier.md` (binding for the
PARADE slice only)

**In scope:** `notebook-shell` → `rna-design` → `rna-qc-additions` → `dna-construct`, plus the V1 slice of
`experimental-tier` — **PARADE only**, as an opt-in UTR engine (`CAPABILITY-MAP.md` already places it in V1).
**Out of scope:** the rest of `experimental-tier` (UTRGAN, Smart5UTR, epitope/antigen prediction),
`cloning-simulation`, and every item on the specs' Deferred lists.

---

## Overview

V1 is a single Colab notebook that turns a protein sequence into an optimised mRNA, a QC report, a DNA
construct, and a downloadable run bundle, with no terminal and no install. Everything scientific is
outsourced to pinned upstream tools behind a versioned plugin contract; this repository contributes
orchestration, validation, provenance, and reporting — never an algorithm.

The plan is built around four moves:

1. **The shell carries the promise.** Config schema, contracts scaffolding, bootstrap, ledger, error
   rendering and the test harness are built and proven before any adapter is written, because none of
   the other modules can be verified without them (`CAPABILITY-MAP.md` §Dependency rules).
2. **One thin vertical slice early.** Shell + fixture adapter → a complete, downloadable run bundle with
   manifest, README, skip hints and error handling (CP1). Then the first real upstream adapter through
   the same path (CP3). Everything after that widens an already-working path rather than assembling one.
3. **Gates are tasks, not assumptions.** Every open question in the specs becomes an explicit, blocked
   task with a decision recorded before dependent code starts. The critical path still runs through
   licence questions: G25 (default CDS engine — G27's factual half is already answered from source, so
   the weights question G2 is what separates options A and B), then G1–G5 (engine licences), G9 (vendor
   profile) and the engineering gates G16/G17/G23/G24. G8 closed with the UTR decision, G21/G22 closed
   as spec fixes. A cleared gate unblocks work, an unclear gate leaves it blocked.
4. **Honesty is a build artefact.** `not_run` ≠ `pass`, skips carry recovery hints naming real fields,
   nothing is auto-ranked, and no material choice gets an invented default. These are enforced by tests
   (NS-SC8, QC-SC6, DC-SC8/9/10, RD-SC15), not by review vigilance.

Contract-first ordering is non-negotiable: `DesignRequest` / `DesignResult` / `MrnaRecord` (RD-3.1–3.7)
are defined and tested (T07) before the registry (T08) and before any adapter (T26+), because every
module downstream — QC, construct, report — is a consumer of those shapes.

---

## Decision record — review of 2026-11-16

| # | Question | Decision | Effect |
|---|---|---|---|
| 1 | Project licence (G0) | **MIT** for this repo's code; dependency terms disclosed separately in `THIRD-PARTY-NOTICES.md`, never by narrowing MIT | G0 closed apart from the holder/year line; T03 rewritten |
| 2 | Reference model (VaxLab) | Answered in review; notes recorded below | No plan change; two lessons fold into existing tasks |
| 3 | G19 + G20 | **Approved** as proposed | T05 unblocked; taxonomy is now fixed, not a proposal |
| 4 | G18 | **Approved**: adapter executes the sweep, QC renders it | T41/T50 unblocked; AD-4 is now binding |
| 5 | G7 DNAChisel seed | **Recommended**: seed from a named upstream adapter, via a small delta spec | T38 gains prerequisite T37A; **approved in the second review (#11)** |
| 6 | G6 Optimus budget | **Optimus 5-Prime stays the default 5′UTR engine; measure later.** Demotion, if needed, is a delta spec — never a silent swap | T22 becomes a non-blocking measurement; T34 unblocked except G3. **Superseded by #12** (reference library becomes default) |
| 7 | G15 PARADE | **In scope** as an explicit opt-in UTR option; never on the default path or in a fallback chain | New Phase 3b (T41A–T41C); T39/T40 hints may now name a real option |
| 8 | G10–G14 | **Deferred.** Gates stay open, dependent tasks stay blocked | Consequence flagged in §Still open D5 — needs confirmation |

**Notes on the reference model (VaxLab, `ChangLabSNU/VaxLab`, MIT, *Exp Mol Med* 2026).**
VaxLab is one 26-cell Colab notebook (11 markdown + 15 code) whose cells carry real logic: installs,
`if/elif` dispatch on the chosen engine, parsing of upstream stdout with string surgery, HTML assembly,
and a vendored OVE sequence editor. Installation clones upstream repositories **from `main`** (unpinned)
and `wget`s a prebuilt LinearDesign binary from the project's own `resources/` directory; the Twist order
sheet is a vendored XLSX and the QC report needs an external forna server. UTRs from BNT162b2/Moderna sit
inline in the notebook. The repo is MIT with no per-dependency licence surface, and the research-only
status of LinearDesign is not acknowledged to the user.

That is the model we deliberately diverge from on four points (NS-1.1 thin cells, NS-3.6 no vendoring,
NS-3.2/3.5 pinned+verified installs, NS-3.8 surfaced licence notices), and deliberately copy on two
(one notebook, form-driven "Run all", in-notebook guidance). Two hard data points are relevant to us:

- LinearDesign peaked at **52 GB** on full-length SARS-CoV-2 spike and fits the 12.7 GB Colab tier only
  up to **~566 aa**. RD-1.3's 5,000 aa cap is a validation limit, not an engine capability; per-adapter
  length ranges (RD-2.1) and the pre-flight estimate (RD-5.1) are what keep this honest.
- Optimus 5-Prime and GEMORNA each need a conda environment in VaxLab, which is why Optimus is now
  opt-in (item 12) rather than the default 5′UTR source: heavy, but demonstrably Colab-runnable when
  a user asks for it.

Note also that VaxLab's practice of redistributing a LinearDesign binary from its own repository is
evidence that someone does it, **not** evidence that it is permitted. G1 remains a licence question.

---

## Decision record — second review, 2026-11-16

| # | Question | Decision | Effect |
|---|---|---|---|
| 9 | Licence holder line | **Left blank**; the user fills it in manually later | G0 closed; T03 records the decision and notice surface, and T69 writes `Copyright (c) 2026` with no name when the repo starts |
| 10 | Default CDS engine | **Resolved: option B.** `codonbert` is the default CDS engine; `lineardesign` and `custom` ship as explicit user selections. Licence model: research **and** commercial; per-engine responsibility — a `lineardesign` run's commercial use is the user's licence obligation, stated in a printed notice at selection | G25 closed; G2 (CodonBERT weights) is now the critical path; T32A cancelled; T32 demoted to opt-in; T36 is the default-engine task |
| 11 | G7 DNAChisel seed | **Approved**: seed from a named upstream adapter via delta spec | T37A unblocked; T38 waits only on G4 |
| 12 | G8 reference UTRs | **Resolved**: the vaccine UTRs VaxLab exposes become the default reference library, with BNT162b2's 5′+3′ pair as the default and mRNA-1273 et al. selectable; expand in V2 | T24 unblocked with primary-source provenance; default UTR flips to the library |
| 13 | G10–G14 deferral | **Agreed**: V1 ships additions 2/4/5 as `not_run` with reasons | New QC delta task T42A; QC-SC1 is partial by decision |
| 14 | G21 LinearDesign regions | **Resolved by domain fact**: LinearDesign designs the CDS only, never UTRs; the code sample's `utr5` is a spec bug | T32 unblocked from G21; spec fix recorded |
| 15 | G22 poly(A) | **Resolved**: poly(A) is a fixed construct element, not an optimisation target; no independent toggle | T55 encodes poly(A) per `template_type`; T13 has no poly(A) flag |
| 16 | Version control | **Deferred until V1 is complete** (item 7) | T01 is now a snapshot baseline with no repo/.gitignore; T03 records the licence without a `LICENSE` file; git init + `LICENSE` + notices move to T69 |

**Consequences of the UTR decision (item 12).** The default path no longer needs Optimus 5-Prime, so the
default 5′UTR source is a cited reference sequence and `optimus5` becomes opt-in (supersedes G6's
"Optimus stays default"). This removes a conda install from the path a first-time user takes, and makes
the 3′UTR possible at all — no V1 engine designs one. `optimus5` and `parade` remain selectable, never
automatic. RD-2.11's order (user → proven engine → reference) must be inverted for the default set by a
delta spec, which T24 writes: **user → reference library → opt-in engine**, with the substitution
labelled either way.

**Licence caveat on that decision.** VaxLab is a pointer, not a source of permission. The UTR sequences
must be taken from the primary sources (the BNT162b2 and mRNA-1273 publication/patent sequence
listings), each library entry carrying its own citation and a note that vaccine UTR sequences may be
covered by patent claims. That is a research-use caveat on the data, separate from this repo's MIT
grant. Curating them from VaxLab's notebook would copy an unattributed sequence table and inherit an
unclear provenance.

**What changed in DECISIONS.md (to append at implementation start, append-only — not written now):**
D-013 licence holder blank; D-014 reference-first UTR default (supersedes D-004's ordering, keeps
D-006's licence structure); D-015 LinearDesign CDS-only and poly(A) as a fixed element (confirms
D-003/D-007); D-016 version control deferred until V1 completes; D-017 the G25/G26/G27 resolutions above.

---

## CUSTOM licence finding — correction to item 2 (blocks G25)

> **Resolved 2026-11-16 (G25 = option B):** CUSTOM is **not** the default and the project stays MIT.
> `codonbert` is the default CDS engine; `custom` remains available as an explicit user selection —
> shipped per §CUSTOM adapter boundary (resolved 2026-11-16: separate GPL-3.0 package). The finding is retained as the
> evidence for why T35 is blocked and why the repo licence does not change.

You proposed CUSTOM (`hexavier/CUSTOM`) as the default codon-optimisation engine on the understanding
that it is MIT and therefore commercial-use friendly. **The repository is GPL-3.0, not MIT.** Checked at
source on 2026-11-16:

- GitHub licence metadata: `gpl-3.0`, "GNU General Public License v3.0".
- `LICENSE` is the GPLv3 text; `setup.py` declares `license="GPLv3"`; PyPI `custom-optimizer 0.0.1`
  declares `GPLv3`; `readme.md` says "CUSTOM is under a common GNU GENERAL PUBLIC LICENSE".
- The package is a Python library (`from custom import TissueOptimizer`), and its `install_requires`
  includes `ViennaRNA` (`import RNA`).

Three consequences, none of which are legal opinions but all of which are engineering blockers:

1. **Copyleft, not permissive.** GPLv3 does permit commercial use, but if we distribute a work that
   combines it with our code, that combined work must be GPLv3. An adapter that `import`s a GPL library
   is the conservative case for a combined work. So "MIT repository with CUSTOM as default" is not a
   coherent licence position: the distributed notebook/code would have to be GPLv3.
2. **It needs a tissue parameter.** `TissueOptimizer("<tissue>", n_pool=…)` — there is no zero-input
   path. A default tissue is a scientific parameter, and this project forbids inventing one.
3. **It pulls ViennaRNA in.** CUSTOM imports `RNA`. ViennaRNA's licence is **not** permissive and
   **not** GPL: it is a custom licence permitting research, educational and commercial use with
   conditions (credit; no-fee redistribution; contact the authors to embed in a commercial product —
   verified from tbi.univie.ac.at/RNA/license.html and the repo's `license.txt`, 2026-11-16; see D9/G27).
   So choosing C adds a copyleft obligation without removing the folding-engine conditions.

There is also a determinism problem: the API builds a probabilistic pool and then selects, and exposes
no seed. RD-2.4's table calls `custom` `deterministic`; on this source reading it is at best `seeded`
with a seed we would have to add, so the spec claim is a defect (see §Spec defects, item 10).

**A caveat that applies to every option, not just C.** The default QC path reports MFE/ensemble
diversity (RD-3.2 "where available", QC-2.2's cross-adapter plot, QC-2.5's engine attribution), and the
only two folding engines in V1 are ViennaRNA and LinearFold. Verified at source on 2026-11-16: **both**
carry the same style of custom licence — permission for research, educational and commercial use and
modification, conditional on (1) no-fee redistribution beyond media costs, (2) visible credit/citation,
and (3) for ViennaRNA, contacting the authors before inclusion in a commercial product; LinearFold's
file is tagged `Other/NOASSERTION` on GitHub. So the folding engines do **not** block commercial use of
the default path outright — an earlier draft of this plan wrongly called ViennaRNA "GPL-licensed,
non-commercial" — but they add notice conditions that `docs/licence-claims.md`, the manifest and T67's
README wording must state. The residual question is whether you accept operating under those conditions,
not whether permission exists.

**Options, for your decision (G25):**

| | Default CDS engine | Repo licence | Default path usable commercially? | Cost |
|---|---|---|---|---|
| **A** | `lineardesign` (current plan) | MIT | No — LinearDesign is research-only; folding engines add credit/redistribution conditions | already planned; envelope work in T32A |
| **B** | `codonbert` | MIT | Yes if the **weights** licence clears (G2); folding-engine conditions (credit, no-fee redistribution) still apply | CPU speed to measure; GPU recommended |
| **C** | `custom` (CUSTOM) | **GPL-3.0** for the combined work | Yes for the engine (copyleft, share-alike); folding-engine conditions still apply | abandons MIT; needs a declared tissue default; GPL + ViennaRNA conditions |
| **D** | `custom` as a separate GPL plugin, shipped outside the MIT core | MIT core + GPL plugin | depends on the legal boundary | legal review; not a zero-input default |

**Recommendation.** Check the licence boundary you actually need before choosing:

- If the goal is *usable commercially at all, copyleft acceptable*: **C** is the cleanest and most
  honest option — the whole project becomes GPL-3.0, one licence, one notice. The blocker is the tissue
  parameter (a scientific choice, not a licensing one) and ViennaRNA's terms (G4).
- If the goal is *no copyleft and no research-only restriction on the default path*: **B**, but only if
  the CodonBERT **weights** licence permits it (G2) — G27 no longer blocks this, since ViennaRNA's
  verified terms permit commercial QC use with conditions.
- **A** is the fallback when the weights do not clear: MIT repo, research-only default path, already
  disclosed.
- **D** (CUSTOM as a separate GPL plugin) is a legal-boundary argument I should not settle for you.

**Ordering that avoids redoing work:** G2 for CodonBERT weights is now the licence question that decides
between A and B (G27 is answered); then a short measurement of whichever of B or C you prefer (CPU speed
and peak RAM for CodonBERT; tissue default and determinism for CUSTOM).

**Resolved 2026-11-16: you picked row B** — the findings above stand as evidence; the decision and its
consequences are recorded in D3 and §CUSTOM adapter boundary. T32A is cancelled, T32 demotes to opt-in,
T36 becomes the default-engine task gated on G2, and T35 ships the adapter in its separate GPL-3.0
package (§CUSTOM adapter boundary, resolved the same day).

---

## CUSTOM adapter boundary — resolved: separate GPL-3.0 adapter package (2026-11-16)

G25 chose option B, so the repo stays MIT and `custom` is an **opt-in** engine. **Your decision: option
1** — the adapter ships as its own GPL-3.0-licensed package (`mrna-design-custom`), installing the MIT
core as a dependency; users who want CUSTOM opt in by installing it, and the MIT core never imports GPL
code. Rejected alternatives, for the record: docs-only external use (worst UX) and an adapter inside the
MIT core (conservative combined-work case, legal review). T35 implements the package; its GPL-3.0
licence is declared in the package metadata from the start, while the `LICENSE` file itself is written
at T69 with the repository. The evaluation order in the notebook lists `mrna-design-custom` adapters as
unavailable-with-reason until the package is installed, never silently absent.

---

## Licence wording rule — "contact the rights holder" everywhere (2026-11-16)

Your decision, generalised: **the same rule applies to every tool and package this project uses.** No
document, notice, report footer or README ever promises that a commercial licence path exists or is
obtainable. For every dependency whose terms restrict commercial use (research-only, conditional, or
silent on the question), the wording is exactly:

> *"Commercial use of this engine's output is not granted by this project. Contact the rights holder
> before using the output commercially."*

Recorded per dependency as a manifest attribute (`commercial_use`: `permitted` / `conditional` /
`contact-rights-holder` / `excluded`), surfaced in `docs/tool-licences.md`, the selection-time notice,
the report footer and T67's README. G1 keeps its factual work — recording LinearDesign's actual terms
verbatim with source — but no longer owes a verdict on whether a licensing path exists, because none is
promised.

---

## Default CDS engine: the reliability question (G25)

*This section analysed the engine-reliability half of G25 under the pre-decision assumption (option A).
**The decision is option B** — `codonbert` default. The envelope argument is retained because
`lineardesign` still ships as an opt-in engine, but its measured-envelope work (T32A) is cancelled: an
opt-in engine declares its length range from upstream documentation, and the user who selects it owns the
runtime risk. The licence argument resolved the other way: the user accepted per-engine responsibility
instead of keeping a research-only default.*

You asked what to default to if LinearDesign is not reliable, and whether to demote it. The constraint
is that this repo may not write a baseline optimiser (RD §Out of Scope; RD-SC7's grep test), so the
default must be an upstream engine. In the V1 inventory only three engines produce a CDS:

| Engine | Zero-input? | Runtime | Determinism | Licence | Real risk |
|---|---|---|---|---|---|
| `lineardesign` | yes | CPU | `snapshot` | research-only | peak RAM grows steeply with length (52 GB at 1,273 aa; ~566 aa at 12.7 GB) |
| `custom` (CUSTOM) | **no, per its upstream interface** — tissue-targeted | CPU | `deterministic` | unverified (G2) | an extra material choice; tissue default would be an invented scientific parameter |
| `codonbert` | yes | CPU (GPU recommended) | `seeded`/`snapshot` | MIT + weight terms (G2) | weights licence; CPU speed on long proteins |

So "make LinearDesign non-default" has no clean landing place: `custom` cannot complete with only a
protein entered without a spec-declared tissue, and `codonbert` trades a memory ceiling for a
weight-licence and CPU-time risk. The
defensible answer is **keep LinearDesign as the default CDS engine and make its envelope explicit**,
rather than swap one unverified default for another:

1. **Declare the envelope from measurement, not from the paper.** T32A measures peak RSS against protein
   length on both Colab tiers (12.7 GB and 51 GB), records the ceiling per tier, and feeds `length_range`
   (RD-2.1) and the pre-flight estimate (RD-5.1). The 5,000 aa validation cap stops being implied as an
   engine capability.
2. **Route by envelope, not by hope.** Within the ceiling, LinearDesign runs. Above it, the run states
   the measured limit and the config field, and offers the real options in the hint: switch to the
   high-RAM runtime, shorten the antigen, or select `custom`/`codonbert` explicitly. An explicit
   substitution is allowed and surfaced (RD-4.1b, RD-SC8); a silent one is not.
3. **Never page the session to death.** RD-5.1's ceiling abort runs before the engine starts, using the
   declared class; the message names the limit, the estimate and the alternative. A 52 GB attempt on a
   12.7 GB tier is a bug in our estimate, not a user error.
4. **Keep the λ sweep off the default path.** The sweep multiplies runtime and is a QC addition; the
   default run designs once. T41 keeps it bounded and opt-in.
5. **Licence responsibility follows the engine choice.** The tool itself is built for research **and**
   commercial use; the only commercial limitation is the one attached to the engine the user selects.
   Selecting `lineardesign` (research-only terms) makes obtaining a commercial licence the **user's**
   responsibility, stated in a printed notice at selection time — never a click gate on the default
   path. G1 must still verify that a commercial-licence path for LinearDesign actually exists; if it
   does not, the notice says "contact the rights holder" rather than promising a licence.

**Decision (G25 = option B):** `codonbert` is the default CDS engine. Its CPU speed/RAM measurement
(T36) is now a **hard gate** — if it cannot finish the golden protein on the free tier, that is reported
back to you as a measured failure; the default is not silently switched back. `lineardesign` ships
opt-in (T32) with a declared length range from upstream documentation; T32A is cancelled.

---

## Architecture decisions

**AD-1 — `mrna_design/run.py` is the composition root.**
The shell "depends on nothing" (`CAPABILITY-MAP.md`), yet a run must reach design, QC and construct.
Resolution: module-to-module imports stay one-way (`rna-qc-additions` → `rna-design`;
`dna-construct` → `rna-design`; neither imports QC), and `run.py` — which lives in the shell — is the
single place that imports all modules and wires the pipeline. It is an orchestrator, not a dependency:
it may call modules in order, never reach into their internals. QC-1.6's post-assembly pass (T53) is
wired here, which is exactly why `dna-construct` never depends on QC.

**AD-2 — Contracts are frozen-then-additive.**
T07 lands the full V1 shape, including `region_bounds`, per-region provenance (RD-3.7) and the
junction map, before anything consumes it. Widening them later is an "Ask first" boundary (RD §Boundaries),
so the plan pays the design cost once. `DesignResult.validated()` (RD-3.3/3.4) is implemented with T07
and exercised with synthetic fixtures, so no adapter can be written against an unvalidated shape.

**AD-3 — The contract suite is capability-scoped, not one-size.**
RD-2.3 requires every registered adapter to pass "the shared adapter contract suite", but RD-2.1
declares which regions an adapter produces and whether it is QC-only, and QC-6.2 requires
signal-peptide/TM predictors to be registered engines that produce no CDS at all. Resolution: the suite
derives its assertions from `capabilities()` — CDS adapters get translation fidelity (RD-3.4),
metrics-only engines get determinism and attribution (RD-2.9), predictors get determinism plus
confidence pass-through (QC-6.4). RD-SC2's "registry and parametrisation are the same set" is asserted
over the whole registry, so capability classes cannot become an escape hatch.

**AD-4 — Engines execute; QC measures and renders.** *(G18 approved 2026-11-16 — binding.)*
QC-1.1 makes every check a pure function; QC-2.1 asks for a λ sweep to be *run*. Resolution: the sweep
executes inside the design adapter (it is a property of LinearDesign's API, RD-2.1 `capabilities()`), its
points land as a design artifact, and `qc/lambda_tradeoff.py` only formats and plots them. This keeps QC
free of engine execution and keeps recoding/sweeping out of the QC module (QC-3.4).

**AD-5 — Everything citable is data, never a Python literal.**
Thresholds, motifs, reference UTRs, Kozak consensus, T7 promoter block, vendor profile, and the tool
manifest all live under `data/` or `mrna_design/tools/manifest.yaml` with citation, version and effective
date (QC-1.3, QC-5.1, RD-4.1c, DC-2.3, DC-4.2, NS-3.1). Loading is pydantic-validated and fails closed,
so a missing citation is a load error rather than a silently weaker check (QC-5.4, RD-SC12).

**AD-6 — One bundle layout, defined once.**
`outputs/<run_id>/` is owned by `ledger.py` (NS-4.1). Other modules write into declared subpaths
(`designs/<adapter_id>/…` RD-4.2, construct files DC-5.1, `report.html` QC-7.1). Layout is fixed in T09
and asserted centrally (T16), so no module invents a filename and NS-SC4/NS-SC5 stay testable.

**AD-7 — Ports and adapters for every upstream tool.**
One module per tool in `mrna_design/adapters/`, each a class with `id`, `capabilities()`, `run()`,
`determinism`, `licence`, plus a subprocess/API wrapper that parses only documented output. No upstream
algorithm source is copied, and RD-SC7's grep test (T30) forbids reverse-translation helpers outside
adapter modules.

**AD-8 — Snapshot testing is a quality gate with a written tolerance.**
RD-3.5 requires a declared determinism class and, for `snapshot` adapters, "an explicit tolerance and a
documented reason". T31 builds the harness and records the tolerance *before* the first snapshot
(G24), and `--snapshot-update` requires a reviewed rationale in the commit body (RD §Testing Strategy).

**AD-9 — The notebook is thin and machine-checked.**
`notebooks/mRNADesign.ipynb` holds parameter declarations and calls only (NS-1.1). It is authored
directly (no generator, to avoid inventing structure the specs do not have) and is executed by
`nbconvert` on every commit (NS-6.3, T15), which is the only thing that keeps hand-edited JSON honest.

**AD-10 — Determinism is scoped to content.**
Report HTML is byte-identical except run-id/timestamp in one header block (QC-7.6); manifests are
compared on content not byte order (NS-SC5). Non-deterministic GPU adapters declare `snapshot` or
`seeded` and are never compared to CPU output.

**AD-11 — Sandbox boundaries for third-party code.**
Installs are pinned, verified post-install, and confined to `/content/tools/<name>` on Colab
(NS-3.2/3.3/3.5/3.6). For CI/headless runs the location is overridable by one environment variable
(G17) — the default stays `/content/tools` so the Colab path is the tested path.

**AD-12 — The default UTR source is the cited reference library, not an engine.** *(item 12, 2026-11-16.)*
No V1 engine designs a 3′UTR, and making the 5′UTR depend on a conda-installed model put the heaviest
step on the first-run path. Default resolution is therefore user-supplied → reference library →
opt-in engine, with the library entry's citation and *reference, not optimised* label carried into the
record, the report and the manifest. This is a deliberate inversion of RD-2.11's stated order and is
implemented only through T24's delta spec, so the spec and the code cannot disagree.

---

## Component dependency graph

```
                    ┌──────────────────────────────┐
                    │ P0 repoTooling  T01–T04      │
                    │ git · licence · CI · fixture │
                    └──────────────┬───────────────┘
                                   │
             ┌─────────────────────▼──────────────────────┐
             │ notebook-shell (P1) T05–T16                │
             │ RunConfig → contracts → registry → ledger  │
             │ → errors → tool manifest/bootstrap → run.py│
             │ → notebook → Slice A e2e                   │
             └───────┬──────────────────────────┬─────────┘
                     │                          │
     ┌───────────────▼────────────┐   ┌─────────▼───────────────┐
     │ GATES (P2) T17–T25         │   │ rna-design (P3) T26–T41 │
     │ licence · pin · budget ·   │──▶│ registry · adapters     │
     │ UTR lib · vendor · spike   │   │ contract suite          │
     └────────────────────────────┘   │ comparison · MrnaRecord │
                                      └───────┬──────────┬──────┘
                                              │          │
                            ┌─────────────────▼──┐   ┌───▼──────────────────────┐
                            │ rna-qc-additions   │   │ experimental-tier (P3b)  │
                            │ (P4) T42–T53       │   │ PARADE — opt-in only     │
                            │ CheckResult · 6    │   │ gate · labels · weights  │
                            │ additions · report │   │ snapshot · isolation     │
                            └─────────┬──────────┘   └──────────────────────────┘
                                      │ (runtime edge, wired by run.py)
                            ┌─────────▼──────────┐
                            │ dna-construct      │
                            │ (P5) T54–T63       │
                            │ rna→dna · linear   │
                            │ plasmid · order    │
                            └─────────┬──────────┘
                                      │
                            ┌─────────▼──────────────────────────────┐
                            │ Integration & release (P6) T64–T69     │
                            └────────────────────────────────────────┘
```

Edges that must exist: config → contracts → registry → adapters → comparison → QC → report → construct.
`experimental-tier` consumes `rna-design` and writes nothing into `dna-construct` internals (XT-3.4).
Edges that must **not** exist (asserted by an import test in T30): `dna-construct` → `qc`,
`qc` → `adapters/*` execution, `dna-construct` → `experimental`, `mrna_design/*` → `notebooks/*`.

---

## Implementation order

### Phase 0 — Foundation (T01–T04)
Working-tree snapshot baseline, tooling config, licence decision and notice surface, golden fixture
citation. Nothing scientific, and no repository: git starts at T69 after V1 (item 7).

### Phase 1 — Shell + Slice A (T05–T16)
Build order within the shell: field taxonomy → resolved config → contracts → plugin contract/registry →
ledger → error handling → tool manifest/bootstrap → composition root → fixture adapter → notebook.

**Slice A (CP1)** is deliberately *not* a product claim: shell + a fixture plugin (RD-SC10's sanctioned
test plugin) produces a real bundle — `config.resolved.yaml`, `manifest.json`, `run.log`, artifacts,
`README.txt`, zip — with skips, recovery hints, an injected failure rendered without a traceback, and a
Module-2-only run recorded `not run`. It proves the harness before real science arrives. Slice B (T32)
replaces the fixture with LinearDesign the moment G1 clears.

### Phase 2 — Gates (T17–T25), overlapping Phase 1 and 3
Eight research/decision tasks, no product code. They run in parallel with Phase 1/3 work and are the
reason the plan can fail fast: G1 decides whether the advertised default path exists at all. After the
three 2026-11-16 rounds, G0/G6/G7/G8/G18/G19/G20/G21/G22 are closed and version control is deferred until V1; 75 tasks in total.
G10–G14 are deferred with the consequence agreed (T42A). **G27 is answered from source** and its
conditions are accepted (D9). **G25 is decided: option B** — `codonbert` default, `lineardesign`/`custom`
opt-in, per-engine licence responsibility (D3). **G26 is decided:** engine-selective printed notice, no
click gate (D8). Still open: **G1** (including whether a LinearDesign commercial-licence path exists),
**G2** (CodonBERT weights — critical path for the default engine), **G3**, **G9** and G8 curation. The
CUSTOM shipping boundary is resolved (separate GPL-3.0 package, T35) and the licence wording rule
("contact the rights holder", every dependency) is recorded. T22 is now a *measurement* for the opt-in
Optimus engine.

### Phase 3 — rna-design (T26–T41)
Input validation and guards parallel with the contract suite and comparison layer; then adapters. The
G25-decided default CDS engine `codonbert` first (T36; its CPU/RAM measurement is a hard gate on the
default claim), then the opt-in engines (`lineardesign` T32, `custom` T35 in its separate
GPL-3.0 package), then metric engines, then the reference UTR library (T24/T39), then the opt-in `optimus5`,
then the gated engines. T39/T40 close the default path,
the reference-first UTR order and the construct-source substitution rules.

**Checkpoint CP3** is the scientific truth gate: ≥2 adapters on the golden protein, every output
translating back to the input protein, determinism matching declarations, snapshot recorded, and the
LinearDesign envelope abort demonstrated at a length past the measured ceiling.

### Phase 3b — experimental-tier, PARADE only (T41A–T41C)
Added by the 2026-11-16 review and consistent with `CAPABILITY-MAP.md`, which has always placed PARADE
in V1. PARADE is an **opt-in** UTR engine: it can never appear in `default_adapters`, a fallback chain,
a saved profile, or `config.resolved.yaml` without an in-run user action (XT-1.1, RD-2.11). The
reliability contract is binding from its first implementation — opt-in gate, hard labelling, weights hash,
reproducibility snapshot, `not_run` on missing GPU/weights — because a research-grade model beside
LinearDesign must be labelled and isolated from the moment it is selectable.

**Checkpoint CP3b** proves isolation, not biological quality: default-off in every path,
`experimental_derived` propagates, and no experimental value can reach `qc_summary.csv` status columns.

### Phase 4 — rna-qc-additions (T42–T53)
Delta spec for deferred additions (T42A) first, then model and data loaders (T42/T43), then each
addition independently (T46–T51), then the report (T52) and the post-assembly edge (T53). Additions
2/3/5 need no design-engine execution, so they parallelise cleanly once the model exists. Motif
curation (T44/T45) is a data task on the critical path for addition 4 only, and stays blocked while
G12/G13 are deferred.

### Phase 5 — dna-construct (T54–T63)
Conversion and linear assembly first (the default path), assertions and round-trip next, plasmid and
order block after. The plasmid branch is explicitly *not* on the default path (DC-3.0), so its tasks
never block CP5's default-path proof, though both must pass before release.

### Phase 6 — Integration and release (T64–T69)
Stitch the default path end-to-end, run the multi-adapter golden case, refresh-manifest CI, docs,
quality gate, Colab manual release check.

---

## Parallel vs sequential

| Must be sequential | Why |
|---|---|
| T05 → T06 → T07 → T08 | Config resolves contracts; contracts precede registry; registry precedes adapters |
| T07 → any adapter | RD-3.4 fidelity contract must exist before an adapter can be validated against it |
| T09 → T16 (bundle assertions) | Layout is ledger-owned |
| T08 + T30 → adapter tasks | Contract suite must be runnable before adapters are claimed tested (RD-2.3) |
| T31 → T32 (first snapshot) | Tolerance policy precedes first recorded snapshot (G24) |
| T42 → T42A → T52 | Model first, then the deferred-check delta, then the report that renders it |
| Upstream docs → T32 (`length_range`) | With T32A cancelled (G25 = B), the opt-in `lineardesign` declares its range from upstream documentation |
| T41A → T41B → T41C | Weights/install spike before the gate, gate before the adapter (XT-2.4) |
| T55 → T57 → T62 | Assembly → assertions → emitted artifacts |
| CP1 → anything needing a bundle | The harness is the verification substrate |

| Safe to parallelise | Notes |
|---|---|
| T01/T02/T04 | Repo, tooling, fixture |
| T09, T10, T11, T26, T27, T28 | Disjoint files, depend only on T05–T08 |
| T17–T25 (all gates) | Research/decision only; no product code (T32A cancelled) |
| T32, T33, T35, T36, T37, T38 | One adapter module each; blocked individually by their gates |
| T44/T45 with T46/T47/T48 | Data curation vs pure checks |
| T58, T60, T61, T62 | Disjoint construct submodules after T55/T57 |
| T67 docs with T64–T66 | Docs follow implemented behaviour; write late, review with it |

| Needs coordination | Notes |
|---|---|
| T07 vs T38 (DNAChisel seed) | G7 resolved: a `DesignRequest` field is required, so T37A's delta spec lands before T38 — widening is still "Ask first", satisfied by the written delta |
| T41 vs T50 (λ sweep) | G18 **resolved**: adapter executes, QC renders — no coordination left, only the artifact shape |
| T30 vs all adapters | Capability classes must be agreed once, in T30, not per adapter |
| T52 vs T53 | Report must label the two invocations distinctly (QC-1.6) before the edge is wired |

---

## Gate register

Unresolved gates leave dependent tasks **blocked**. No default is chosen on the user's behalf.

| Gate | Question | Decides | Status | Blocks | Task |
|---|---|---|---|---|---|
| **G0** | Project licence — MIT confirmed; the user fills the copyright holder in manually later | `LICENSE`, README claim | **resolved**: MIT, blank holder | — | T03 |
| **G1** | LinearDesign licence terms **and** whether the pinned binary may be fetched by bootstrap (RD OQ4) | existence of the advertised default path | open | T32, T40, T64 | T17 |
| **G2** | CodonBERT licence + weights redistribution; CUSTOM is **GPL-3.0** (found 2026-11-16, see §CUSTOM licence finding) | adapters available **and** the repo's licence position | open | T35, T36 | T18 |
| **G3** | GEMORNA and Optimus 5-Prime licences | adapter availability | open | T34, T37 | T19 |
| **G4** | ViennaRNA (incl. commercial use, G27), LinearFold, DNAChisel licences (and pin revisions) | metric engines + constraint engine + the default-path commercial claim | open | T33, T38, T64 | T20 |
| **G5** | DeepSig / PEFT-SP licences | addition 5 usability | open | T49 | T21 |
| **G6** | Does Optimus 5-Prime fit the Colab CPU budget? (RD OQ2) | default 5′UTR = engine or reference library | **superseded 2026-11-16**: reference library is default, `optimus5` opt-in (item 12) | — | T22 |
| **G7** | How DNAChisel obtains a seed CDS without in-repo reverse translation | RD-2.8 viability, contract boundary | **resolved**: named-adapter seed + delta spec (T37A) | — | T23 |
| **G8** | Which reference 5′/3′UTRs, on what licence, curated by whom? (RD OQ1) | whether V1 has any 3′UTR content | **resolved**: VaxLab's vaccine-UTR set, BNT162b2 pair as default, primary-source citations | — | T24 |
| **G9** | Source for each `generic` synthesis rule, or explicitly `unspecified` (DC-4.2) | order-block warnings | open | T60 | T25 |
| **G10** | Is `not_run` acceptable for TM in V1, or is a server dependency justified? (QC OQ2) | addition 5 status | **deferred, agreed**: `not_run` with reason | T49 | T21 |
| **G11** | Reference panel + percentile for CpG/UpA "vaccine range" (QC OQ3) | addition 2 warn/fail | **deferred, agreed**: `not_run` with reason | T46 | T46 |
| **G12** | Motif DB releases/filters/sign-off (QC OQ1) | addition 4 coverage | **deferred, agreed**: `not_run` with reason | T44, T45 | T44 |
| **G13** | Splice-site strength: consensus scan only, or a scoring engine? (QC OQ4) | addition 4 scope | **deferred, agreed**: `not_run` with reason | T44 | T44 |
| **G14** | Is poly(A) integrity worth reporting separately? (QC OQ5) | addition 2/6 scope | **deferred, agreed**: length reported, integrity judgement `not_run` | T51 | T51 |
| **G15** | PARADE scope and the RD-2.11 hint | RD-2.11 vs NS-1.5 honesty | **resolved**: PARADE in scope, opt-in only | — | T41A–C |
| **G16** | Construct map rendering library (pinned) — dependency addition | DC-5.3 | open | T61 | T61 |
| **G17** | Tools install root override for CI while defaulting to `/content/tools` | NS-3.2 vs NS-6.1 | **resolved 2026-11-17**: `MRNA_DESIGN_TOOLS_ROOT` (primary; documented) overrides `/content/tools`; aliases accepted, primary wins | T12 | T12 |
| **G18** | λ sweep ownership: adapter capability vs QC-executed (QC-1.1 vs QC-2.1) | module boundary | **resolved**: adapter executes, QC renders | — | T41 |
| **G19** | Material vs representation field taxonomy (NS-1.2a vs RD-4.1b/DC-2.0) | `RunConfig` classification | **resolved**: taxonomy approved | — | T05 |
| **G20** | Protein required only when `run_modules` includes design? (NS-1.2 vs NS-1.7/DC-1.1) | validation rule | **resolved**: conditional, approved | — | T05 |
| **G21** | LinearDesign capabilities contradiction (RD-2.4/RD-2.6 vs code sample) — spec fix | default 5′UTR resolution | **resolved**: LinearDesign is CDS-only; sample's `utr5` is the bug | — | T32 |
| **G22** | CLI template vocabulary + no poly(A) toggle (DC-2.0/DC-2.2/DC-SC10 vs Commands) — spec fix | CLI surface | **resolved**: poly(A) is a fixed element, no optimisation toggle; `pcr`/`plasmid` vocabulary | — | T55 |
| **G23** | Golden fixture provenance: exact RBD residue span/citation; pUC19 test-backbone source and licence | fixture legitimacy | open | T04 | T04 |
| **G24** | Snapshot tolerance value and written reason per `snapshot` adapter (RD-3.5) | snapshot gate validity | open | T31, T32 | T31 |
| **G25** | Default CDS engine — reopened by the CUSTOM licence finding (CUSTOM is GPL-3.0, not MIT; needs a tissue; pulls ViennaRNA) | default engine, repo licence and default-path commercial status | **resolved (2026-11-16): option B.** `codonbert` default; `lineardesign`/`custom` opt-in; the tool targets research **and** commercial use and per-engine licence responsibility sits with the user (selecting `lineardesign` ⇒ the user obtains a commercial licence if commercialising). Repo stays MIT. G2 (weights) is the remaining factual gate for the default's commercial claim. CUSTOM shipping boundary **resolved: separate GPL-3.0 package** | T32 (opt-in), T35 (package), T36 (default), T40 | T36 |
| **G26** | **Spec contradiction:** RD-2.7/NS-3.8 require a per-session research-only acknowledgement before LinearDesign runs, while NS-1.1/NS-SC1/NS-SC7 require the default path to complete with only the sequence entered and no step asking a question | whether the default path has a click gate | **resolved (2026-11-16):** engine-selective printed notice — the default path (`codonbert`) asks nothing; selecting a research-only engine is an explicit action that renders the responsibility notice, and the restriction is recorded in the bundle/report. Spec delta to RD-2.7/NS-3.8 tracked with the other deltas | T15, T16, T32, T64 | T32 |
| **G27** | ViennaRNA's terms for a **QC** dependency (and for CUSTOM's import of it) (RD-2.4, RD-2.9) | default-path commercial claim and notice wording | **answered from source 2026-11-16**: both ViennaRNA and LinearFold permit research/educational/**commercial** use under custom conditions — no-fee redistribution, credit, author contact for commercial-product embedding; **not** GPL. Conditions **accepted by you (2026-11-16)** for V1's free distribution; the embedding clause applies to shipping the engines inside a commercial product, not to design outputs. Conditions recorded in the manifest and honoured in `docs/licence-claims.md` (D9) | T20, T33, T36, T64 | T20 |

G21 and G22 are **specification fixes** confirmed by review on 2026-11-16: LinearDesign designs the
CDS only, and poly(A) is a fixed construct element rather than an optimisation target. The spec text
still needs the corresponding delta (T32/T55), but the engineering reading is settled.

**Deferral consequence (G10–G14, agreed).** With these open, additions 2 (threshold judgement), 4
(library content) and 5 (predictor engines) cannot reach a `pass`/`fail` state, and QC-SC1's "all six
additions exist, covered by known-answer fixtures" cannot be signed off. V1 ships a consolidated report
in which those checks are present as `not_run` with reasons and recovery hints. That requires the delta
to QC-1.2/QC-3.2/QC-7.3 written by T42A, because the current text assumes a cited threshold exists.
QC-SC1 is therefore partial **by recorded decision**, not by omission.

---

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| G1 fails (LinearDesign cannot be fetched/allowed) | **High** for option A only — the default path and the research-only claim change shape | G1 is run first, in parallel with Phase 1; Slice A does not depend on it; fallback ordering (reference CDS? CUSTOM?) becomes a *user decision*, never a silent swap |
| A pinned engine turns out non-redistributable (NS-3.4) | Med | Gate task records exclusion + reason in manifest and user summary; adapter simply absent, with the reason shown (RD-6.6) |
| Colab runtime drifts off Python 3.11 / pinned torch | **High** — every adapter can break at once | NS-3.5 drift detection, pinned-runtime assumption is an "Ask first" change, notebook smoke on the real runtime (T68), manifest freshness job (T66) |
| Optimus 5-Prime too slow on CPU | Low after item 12 — it is now opt-in | G6 superseded: default 5′UTR is the reference library; T22 measures the opt-in engine so the pre-flight estimate is honest |
| LinearDesign memory blow-up on long proteins (VaxLab measured 52 GB on full spike; ~566 aa ceiling at 12.7 GB) | **Medium** — it is no longer the default (G25 = B), so the default run cannot trigger it | Opt-in only: declared `length_range` from upstream documentation (T32A cancelled), pre-flight estimate where the tool provides one, RD-5.1 abort with the real alternatives; the selecting user owns the runtime risk |
| CodonBERT cannot finish the golden protein on the free-tier CPU | **Medium** — it is now the default engine | T36 measures CPU/RAM as a hard gate; a measured failure is reported to you with the numbers and the default is re-decided explicitly, never silently swapped (RD-5.1) |
| Reference UTR sequences (BNT162b2/mRNA-1273) carry patent claims | Med — users may assume a freedom-to-operate claim | Per-entry citation + explicit research-use caveat in the library, report and README; VaxLab is cited as a pointer only, never as the licence source (T24) |
| PARADE is not installable from pip / weights unavailable | Med | T41A spike first (conda→pip re-pin, Zenodo weights hash); if it fails, PARADE ships as documented `unavailable` with reason and the reference UTR library remains the fallback — never a silent checkpoint swap (XT-1.6, XT-1.7) |
| PARADE leaks into the default path or changes run status | **High** (V1's "proven tools only" claim) | XT-1.1/1.3 gate tests in T41B/T41C, `default_adapters` assertion, `qc_summary.csv` isolation test, CP3b |
| A GPL dependency (CUSTOM) imported from MIT-distributed code | **Low** — resolved: the adapter ships as a separate GPL-3.0 package that depends on the MIT core; the core never imports GPL code | T35 implements `mrna-design-custom`; a test asserts no module under `mrna_design/` imports the package |
| Licence notices drift from the pinned set | Med | `docs/tool-licences.md` is generated/validated from `tools/manifest.yaml` (T03 + T11) and becomes `THIRD-PARTY-NOTICES.md` at T69; a test fails when an entry has no notice line |
| DNAChisel needs a seed CDS → `DesignRequest` widening | Med | G7 resolved; the widening is the approved T37A delta spec, not a quiet code change |
| λ sweep blurs the QC/engine boundary | Med | AD-4 + G18; QC-SC5 ensures checks stay contract-shaped |
| Reference data curation (UTRs, motifs, thresholds, vendor rules) exceeds estimate | **High** — data tasks are the long pole | Each is its own gated task with a citation-completeness test; checks degrade to `not_run`/`reference-derived` rather than inventing numbers (QC-1.8) |
| Snapshot churn from upstream or GPU nondeterminism | Med | Written tolerance (G24), review-gated updates, `seeded`/`snapshot` declarations rather than re-recording silently |
| Report not byte-identical, or embeds external assets | Med | Single Jinja2 template, inline CSS, timestamps isolated, double-render diff test (QC-7.6, QC-SC4) |
| Hand-edited notebook JSON breaks | Med | Thin cells, `nbconvert` smoke per commit, notebook rebuild instructions in docs |
| Bootstrap network flakiness / upstream disappearance | Med | Retries in bootstrap (not silent downgrade), recorded SHA + documented re-pin procedure (NS-3.6), nightly `-m network` run |
| Coverage targets collide with data-heavy code | Low | Coverage config per package; data validated by load tests, excluded from statement coverage with a documented rationale |
| `not_run` drifts into `pass` under refactoring | **High** (product-integrity) | Status is a closed enum, rendering demands a reason for `not_run`, injected-unavailability tests (QC-SC6), bundle assertions (NS-SC8) |
| Material default invented under time pressure (backbone, construct source, vendor) | **High** (user could order the wrong thing) | DC-SC9/DC-SC10 tests, branch_resolution states, review checklist item in every construct task |
| New-algorithm creep (a "small" reverse translation or recoder) | **High** (project premise) | RD-SC7 grep test from T30, QC-3.4 test forbidding recoding paths, adapter boundaries in review |
| pUC19 fixture licence unclear | Low | T04 records source/GenBank accession and licence; if unclear, use a synthetic test backbone instead |

---

## Verification checkpoints

Each checkpoint is a stop-and-review gate. Commands are the ones the specs already define.

### CP0 — Foundation
- [ ] `ruff check . && ruff format --check .` and `mypy mrna_design` clean on an empty package
- [ ] The CI command sequence passes locally; the workflow file activates at T69 when the repository exists
- [ ] `DECISIONS.md` records G0 (MIT, holder intentionally blank) and `docs/tool-licences.md` exists; no `LICENSE` file yet — it is created at T69 with the repository
- [ ] Golden fixture file exists with a recorded citation in `docs/fixtures.md`

### CP1 — Slice A (shell complete, no upstream engine)
- [ ] `python -m mrna_design.tools.bootstrap --profile v1 --verify` works against a fixture tool (network marker separated)
- [ ] `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --out /tmp/run` produces the NS-4.1 file set and a complete NS-4.2 manifest
- [ ] Skipped branches appear in summary + manifest + `README.txt` with a real field name (NS-SC8)
- [ ] Injected failures (bad install, missing GPU, bad input, length cap) render without traceback (NS-SC2)
- [ ] `run_modules=["construct"]` bundle records design as `not run` (NS-SC9 shape only)
- [ ] `jupyter nbconvert --to notebook --execute notebooks/mRNADesign.ipynb --output-dir /tmp/nb --ExecutePreprocessor.timeout=3600` green
- [ ] Coverage of `tools/` and `ledger.py` near-total

### CP2 — Gates closed
- [ ] Every gate in the register has `resolved` + decision text in `DECISIONS.md`, or is explicitly deferred with its tasks still blocked (G1, G2, G3, G4, G5, G9, G16, G17, G23, G24; G25/G26/G27 and the CUSTOM shipping boundary are resolved, with the wording rule recorded via T20)
- [ ] `mrna_design/tools/manifest.yaml` validates; every entry has licence, revision, `last_verified`
- [ ] Excluded tools appear with a reason (NS-3.4)

### CP3 — rna-design golden
- [ ] `pytest tests/unit/design -q` and `pytest tests/integration/test_adapter_contract.py -q` green
- [ ] The default pair — `codonbert` CDS + reference UTRs — yields one design, and adding `lineardesign` as an explicit second adapter yields two designs, a comparison table, and a `MrnaRecord` whose junction map reconstructs
- [ ] Every CDS retranslates exactly to the input protein (RD-3.4)
- [ ] Registry set == contract-suite parametrisation (RD-SC2); GPU-only adapters unavailable-with-reason on CPU (RD-SC5)
- [ ] `default_adapters` contains no `experimental` and no GPU adapter (RD-SC9, RD-SC15)
- [ ] Snapshot recorded with tolerance and reason (RD-3.5, G24)
- [ ] LinearDesign's declared `length_range` (from upstream documentation; T32A cancelled by the G25-B decision) aborts a past-range request with the limit and the real alternatives before the engine starts (RD-2.1, RD-5.1)
- [ ] Default 5′ and 3′UTR come from the cited reference library, labelled *reference, not optimised*, with per-entry source (RD-4.1c, RD-SC12, G8)

### CP3b — PARADE (experimental tier)
- [ ] Opt-in is off by default in notebook, headless and every config path; enabling it is recorded (XT-1.1, XT-SC1)
- [ ] Every PARADE artifact carries marker, model name, pinned version, citation and the fixed no-validation sentence (XT-1.4, XT-SC4)
- [ ] Snapshot/reproducibility gate passes with the written tolerance, or PARADE reports `not_run`/`unavailable` with a reason (XT-1.5, XT-1.7)
- [ ] No PARADE value appears in `qc_summary.csv` status columns or changes run status (XT-1.3, XT-SC3); report-section isolation is re-verified at CP4, where the report exists
- [ ] `experimental_derived` propagation is wired and unit-tested here; the end-to-end construct/order-CSV propagation is verified at CP5 (XT-1.2)
- [ ] No import path from `dna-construct` or `qc` into `mrna_design/experimental/` (XT-SC6, XT-3.4)

### CP4 — QC report
- [ ] `pytest tests/unit/qc -q` green; `pytest tests/unit/qc/test_motif_library.py -q` green
- [ ] `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --qc-only` emits `qc_summary.csv` + one self-contained HTML
- [ ] `python -m mrna_design.report --run outputs/<run_id> --out /tmp/report.html` renders; double render is byte-identical
- [ ] Every row has `threshold_ref` + citation; `not_run` rows have reasons (QC-SC2, QC-SC6)
- [ ] Two-engine run keeps MFE series separate (RD-SC14)
- [ ] Additions 2, 4 and 5 render `not_run` with their reasons and recovery hints, by recorded decision — never `pass` (QC-SC2, T42A)
- [ ] With PARADE opted in, its results render only in the experimental section and touch no `qc_summary.csv` status column (XT-1.3, XT-SC3)

### CP5 — Construct
- [ ] `pytest tests/unit/construct -q` and `pytest tests/integration/test_construct_roundtrip.py -q` green
- [ ] `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml` (no backbone) emits linear template + order block, zero errors, `backbone_path` hint (DC-SC8)
- [ ] Backbone run emits GenBank that round-trips; diff shows exactly one replaced span (DC-SC2/3)
- [ ] Export blocked when a construct assertion fails (DC-SC5)
- [ ] Summary states cloning was not simulated (DC-SC6)
- [ ] With a PARADE-derived UTR, construct and order CSV are flagged `experimental_derived` (XT-1.2, DC-5.5)

### CP6 — Release
- [ ] `pytest -m e2e`, `pytest -m network`, `pytest -m gpu` results recorded per runtime
- [ ] `pytest --cov=mrna_design --cov-report=term-missing --cov-fail-under=80` green, module minimums met
- [ ] `ruff check . && ruff format --check .`, `mypy mrna_design` clean
- [ ] Manual Colab CPU check: fresh session, only the sequence entered, Run all, full bundle (NS-SC1/SC7)
- [ ] Docs complete: metrics, QC checks, construct formats, re-pin, known limitations, research-only licence map

---

## Traceability: success criteria → tasks

| Module | Criteria | Tasks |
|---|---|---|
| `notebook-shell` | NS-SC1/2/4/5/6/7/8/9 | T05–T16 (harness), T64/T68 (release) |
| `rna-design` | RD-SC1–15 | T07, T08, T30, T32–T41, T65 — G25 resolved (option B); T32A cancelled |
| `rna-qc-additions` | QC-SC1–7 | T42–T53 (incl. T42A), T65 — QC-SC1 partial by recorded decision (G10–G14) |
| `dna-construct` | DC-SC1–14 | T54–T63, T64 |
| `experimental-tier` (PARADE) | XT-SC1–6 | T41A–T41C, T64 (flag propagation) |
| Cross-cutting | V1 definition of done | CP6, T64, T68; CP6 cannot claim "consolidated QC report" while QC additions 2/4/5 are `not_run` |

---

## Spec defects found while planning (reported, not resolved)

These are recorded as gates above; the plan does not choose a winner.

1. **LinearDesign capability contradiction (G21).** `SPEC-rna-design.md` RD-2.4 (table: "CDS only") and
   RD-2.6 ("LinearDesign designs no UTR at all") agree with `mRNADesign.md` §Scope decisions, but the
   spec's own Code Style sample declares `Capabilities(designs=("cds", "utr5"))`. The sample also omits
   fields RD-2.1 requires. Taken literally, it would put a 5′UTR on the default CDS engine and contradict
   RD-4.1a/RD-SC15. **Resolved 2026-11-16**: the sample is wrong; LinearDesign is CDS-only. The spec
   delta is still owed, and the adapter must not encode the sample's claim.
2. **Poly(A) as a CLI toggle (G22).** `SPEC-dna-construct.md` DC-2.2 and DC-SC10 forbid poly(A) as an
   independent toggle and require the control be hidden for `pcr`; the spec's Commands section shows
   `--construct linear --poly-a encoded`. It also uses `linear` where DC-2.0 defines `pcr`/`plasmid`.
   **Resolved 2026-11-16**: poly(A) is a fixed element, never optimised; the flag does not exist, and
   `pcr`/`plasmid` is the vocabulary.
3. **Required-field contradiction (G20).** NS-1.2/NS-1.2a make the protein sequence the one required
   field; NS-1.7, NS-SC9 and DC-1.1 require a Module-2-only run with no protein at all.
   **Resolved by review 2026-11-16** — conditional requirement; a spec delta still needs to be written so
   the text matches the behaviour.
4. **Material-field contradiction (G19).** NS-1.2a lists *construct source* as material ("no default may
   be invented"), while RD-4.1b declares `construct_source` default `lineardesign` and DC-2.0 declares
   `template_type` default `pcr`.
   **Resolved by review 2026-11-16** — taxonomy approved; `construct_source` is treated as a *named
   selection over results this run produced* with a spec-declared default and a surfaced substitution,
   not as a material input. Same delta as (3).
5. **QC purity vs sweep execution (G18).** QC-1.1 requires pure functions with no I/O; QC-2.1 requires a
   sweep to be run with a pre-flight estimate.
   **Resolved by review 2026-11-16** — adapter executes, QC renders (AD-4).
6. **Install-root vs headless reproduction (G17).** NS-3.2 fixes `/content/tools/<name>`; NS-6.1 and
   NS-SC5 require headless reproduction outside Colab.
7. **PARADE hint with no PARADE (G15).** RD-2.11 requires the absent-5′UTR recovery hint to name PARADE
   as an opt-in, and NS-1.5 requires hints to name something real.
   **Resolved by review 2026-11-16** — PARADE is in scope, so the hint names a shipped option.
8. **Undocumented CLI surface.** `--only`, `--qc-only`, `--construct`, `--backbone`, `--insert-at`,
   `--snapshot-update` appear in the specs' Commands but NS-6.1 defines only `--config`/`--out`.
   Non-blocking: the CLI is developer-only (NS §Out of Scope), so T13 treats the specs' Commands as the
   authoritative flag list and assigns each flag to its owning module's task.
9. **`data/backbones/` vs DC-3.2.** The structure lists a backbones data directory while DC-3.2 ships
   none. Non-blocking: create it with a README explaining it is empty by decision.
10. **CUSTOM determinism claim (RD-2.4 vs upstream source).** RD-2.4's adapter table declares `custom`
    `deterministic`, but the upstream API (`TissueOptimizer`, `n_pool=…`, `select_best`) builds a
    probabilistic pool and selects from it, and exposes no seed. It is at best `seeded` once a seed is
    added. Non-blocking for planning, blocking for T35's determinism declaration and RD-3.5's snapshot
    policy; reported rather than resolved.

---

## Decisions I need from you (after three rounds, 2026-11-16)

D1. **Licence holder line (G0).** Closed as instructed: MIT with the holder left blank for you to fill
in manually. Because git starts only after V1 (D7), the `LICENSE` file itself is written at T69; until
then the decision lives in `DECISIONS.md` and the dependency notices live in `docs/tool-licences.md`.
The GPL finding below (D3) may still change *which* licence that file carries.

D2. **G1 — LinearDesign terms and fetch permission.** Still the gate that decides whether the default
path exists as specified. VaxLab redistributing a binary from its own repo is not permission. If the
terms forbid bootstrap fetching, the documented alternative is "point at the upstream release and ask
the user to supply the binary", which keeps LinearDesign selectable without redistributing it.

D3. **G25 — default CDS engine: closed (option B, 2026-11-16).** Your decision: **`codonbert` is the
default** CDS engine; `lineardesign` and `custom` remain available as explicit user selections. The
licence model decided with it: the tool is developed for research **and** commercial purpose, and the
only commercial limitation is the one attached to the engines the user chooses — if the user selects
`lineardesign` and intends the output for commercialization, **obtaining a commercial licence is the
user's responsibility**, stated in a printed notice at selection time. The repo stays MIT. Consequences
encoded in the tasks: T36 becomes the default-engine task and its CPU/RAM measurement is a **hard gate**
(a measured free-tier failure is reported back, not silently swapped away); T32 demotes to opt-in with a
length range declared from upstream documentation; **T32A is cancelled**; T40's `default_adapters` is
`codonbert` CDS + reference UTRs; T32A's cancellation removes the measured-envelope guarantee for
`lineardesign` opt-in runs (accepted risk). One caveat this decision does not settle: **G1 must still
verify that a LinearDesign commercial-licence path exists** — the notice promises the user can obtain
one; if the terms offer no such path, the notice says "contact the rights holder" instead. And **G2**
(CodonBERT weights) is now the critical path for the default's commercial claim: if the weights turn out
non-commercial, that is reported to you before release, and the engine default is re-decided explicitly.
The CUSTOM opt-in adapter ships as a separate GPL-3.0 package (§CUSTOM adapter boundary, resolved) —
T35 is no longer decision-blocked.

D4. **G8 resolution needs curation, not just a decision.** The sequences are chosen (VaxLab's
vaccine-UTR set; default pair BNT162b2), but T24 must still take them from primary sources with
per-entry citations and the patent caveat. Until it does, the default path has no 3′UTR and the construct's 3′UTR domain is
empty-by-decision. G9 (vendor `generic` rules) is unchanged and still open.

D5. **Deferred QC gates (G10–G14) — closed as agreed.** V1 ships additions 2/4/5 as `not_run` with
reasons; T42A writes the delta to QC-1.2/QC-3.2/QC-7.3 and QC-SC1 is partial by recorded decision.

D6. **G16/G17/G23/G24** are engineering-level and can clear inside their own tasks (map library choice,
tools-root override, fixture provenance, snapshot tolerance). They block only the task that raises them.

D7. **Version control — closed: deferred until V1 is complete (item 7).** T01 is a snapshot baseline
and must not create a repository, `.gitignore`, or commit; T03 records the licence without writing
`LICENSE`; T69 performs `git init`, the first commit, `LICENSE`, `.gitignore` and
`THIRD-PARTY-NOTICES.md` after V1 is signed off. `PHASE2-PROMPT.md` §Version control and `DECISIONS.md`
D-011 are now consistent with the plan — no superseding entry is needed. Snapshots remain the working
backup and are stored in `backups/` in the workspace; **copying them off-machine is not required**
(amended 2026-11-17 by `DECISIONS.md` D-020, which records the accepted risk).

D8. **G26 — acknowledgement vs one-field promise: closed (2026-11-16), by the G25-B decision.** The
contradiction between RD-2.7/NS-3.8 (acknowledgement before a `research_only` engine runs) and
NS-1.1/NS-SC1/NS-SC7 (default path completes with only the protein entered) dissolves once the default
path carries no research-only engine: **the default (`codonbert`) path asks nothing.** Selecting
`lineardesign` or `custom` is an explicit user action; that selection **renders a printed notice** with
the engine's licence class and the user-responsibility statement (for `lineardesign`: obtaining a
commercial licence for commercialized output is the user's obligation), and the restriction is recorded
in the bundle/report and manifest. No checkbox, no click gate — reading (a), now with a concrete trigger
the earlier spec lacked. This is a **spec delta** to RD-2.7/NS-3.8: the per-session acknowledgement
becomes an engine-selection notice; T15/T16 implement the notice text from a single source. If a future
config makes a research-only engine the default again, this decision reopens automatically.

D9. **G27 — ViennaRNA/LinearFold terms: answered from source, correcting an earlier draft.** An earlier
draft of this plan called ViennaRNA "GPL-licensed, non-commercial". That is **wrong**. Verified at source
on 2026-11-16: ViennaRNA's licence (tbi.univie.ac.at/RNA/license.html, repo `license.txt`) grants
permission for **research, educational, and commercial use and modification**, conditional on (1) no-fee
redistribution other than media costs, (2) proper credit to the authors and the Institute of Theoretical
Chemistry, University of Vienna, and (3) contacting the authors before inclusion in a **commercial
product**. LinearFold's licence file (GitHub `Other/NOASSERTION`) is the same style: research,
educational and commercial use permitted, no-fee redistribution, paper citation required.
Consequences: (a) the folding engines do not make the default path research-only — the earlier claim
that "no V1 option produces a commercially clean default path" for that reason is **withdrawn**; the
honest V1 claim is now driven by LinearDesign's own research-only terms (option A) or the CodonBERT
weights (option B), not by the QC engines; (b) the conditions are real and must be recorded as
dependency attributes in `manifest.yaml`/`docs/tool-licences.md` and honoured in
`docs/licence-claims.md` and T67's README; (c) the commercial-product-embedding clause is the one that
could still matter for an opt-in CUSTOM run (GPL'd CUSTOM+ViennaRNA inside a distributed product would
trigger it) — covered by the §CUSTOM adapter boundary decision, not by this one. G27's factual half is closed; your acceptance of the conditions is folded
into the G25 decision.

D10. **Licence responsibility model — recorded with G25 (2026-11-16).** The tool is developed for
research **and** commercial purpose. The project's own code is MIT. A run's commercial usability is
determined entirely by the engines the user selects, disclosed per engine in the notice, report footer
and manifest: `codonbert` (default) — subject to G2's weights verdict; `lineardesign` — research-only
terms, commercial use requires a licence **the user obtains**; `custom` — GPL-3.0 obligations carried by its
separate `mrna-design-custom` package; ViennaRNA/LinearFold — conditions accepted (D9). **The same wording rule applies to every
dependency** (§Licence wording rule): no notice, footer or README ever promises that a commercial
licence exists — restricted tools say "contact the rights holder", uniformly. This model is the
substance of `docs/licence-claims.md` and T67's README section.

