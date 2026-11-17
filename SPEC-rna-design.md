# Spec: `rna-design` — V1

Status: proposed, awaiting review
Parent: `CAPABILITY-MAP.md`

## Objective

Turn a protein sequence into one or more candidate mRNA designs by orchestrating proven upstream tools, and define the single data contract every other module consumes. This module is where the project's hard constraint lives: it is an adapter layer, not a research project. Its value is that a user stops tool-hopping and gets comparable outputs from LinearDesign, CodonBERT, CUSTOM, GEMORNA and Optimus 5-Prime — with ViennaRNA as QC, never as a designer.

Success is: the same protein, run through any supported adapter, yields a `DesignResult` that provably translates back to that protein, is annotated with exactly which tool and version produced it, and can be compared with any other adapter's result on the same terms.

## Scope

In scope: input intake and validation, the adapter registry, six adapters, the `DesignRequest`/`DesignResult` contract, cross-adapter comparison outputs, length/memory guards, and per-adapter determinism declarations.

Out of scope: QC beyond basic translation/format validation (owned by `rna-qc-additions`), DNA constructs (`dna-construct`), generative UTR and epitope models (`experimental-tier`, V2), any in-house optimiser or baseline algorithm — including a "simple" codon optimiser; CUSTOM and LinearDesign cover the baseline role.

## Requirements

### Inputs

- **RD-1.1** Accept protein input as FASTA (single record in V1), a bare sequence with whitespace/newlines, or a UniProt accession; paste and upload both work in the notebook.
- **RD-1.2** Reject with actionable messages: empty input, multiple FASTA records, characters outside the 20 standard residues, sequences containing `U`/ambiguous `X`/`B`/`Z` (state the offending positions and what to do), and empty/zero-length input. The floor is **one codon**, matching DC-1.5 and expressed in codons rather than nucleotides; 1–9 codons is accepted with a warning that optimisation and QC output is not meaningful at that length.
- **RD-1.3** Enforce a configurable maximum length (default 5,000 aa) with a message that names the limit and the config field, rather than an out-of-memory failure.
- **RD-1.4** Record the input as typed plus a normalised upper-case form; the hash used for provenance is over the normalised form.
- **RD-1.5** The ORF is always designed and optimised end-to-end: an optional N-terminal signal peptide sits upstream of the antigen and is part of the same ORF — never stripped, never appended after design. Where the user declares the signal peptide span, or supplies it as a separate sequence prepended *before* design, the span is carried through to QC and to construct annotation (DC-2.4). A supplied signal peptide duplicating a prefix already present in the protein is rejected, not silently concatenated.

### Adapter registry

- **RD-2.1** Adapters are discovered from a registry; each declares: `id`, upstream source, pinned revision, `gpu_required`, `deterministic` (`seeded` | `snapshot` | `deterministic`), supported length range, which regions it produces (CDS, 5′UTR, 3′UTR) and whether it is QC-only, `licence` class, and a one-line plain-language description for the notebook.
- **RD-2.2** Availability is runtime-aware: an adapter that cannot run on the current runtime is reported as unavailable with the reason (e.g. "requires GPU"), never hidden and never attempted speculatively.
- **RD-2.3** Every registered adapter MUST pass the shared adapter contract suite (RD-3.*) and the plugin contract (RD-6.*); a test asserts the registry and the contract suite's parametrisation are the same set, so a new adapter cannot ship untested.
- **RD-2.4** Adding an adapter is a data-plus-module change with no edits to the notebook; adding a *tool* requires the licence review in `SPEC-notebook-shell.md` NS-3.4.

### Adapter inventory (V1)

Engines are plugins (RD-6.*); this table is the first-party set shipped and pinned in V1. Licence status is a declared attribute, not an assumption.

| Adapter id | Upstream | Designs | Runtime | Determinism | Licence |
|---|---|---|---|---|---|
| `lineardesign` | LinearDesign (pinned) | **CDS only** — upstream performs no UTR optimisation | CPU | `snapshot` | Research use only; not for commercial use |
| `codonbert` | CodonBERT + pinned weights | CDS | CPU, GPU recommended | `seeded` or `snapshot` | MIT (weights: verify at pin time) |
| `custom` | CUSTOM | CDS | CPU | `deterministic` | Verify before pinning |
| `gemorna` | GEMORNA | 5′UTR | GPU | `seeded` or `snapshot` | Verify before pinning |
| `optimus5` | Optimus 5-Prime | 5′UTR | CPU/GPU per upstream | `seeded` or `snapshot` | Verify before pinning |
| `viennarna-qc` | ViennaRNA | none — structure metrics only (MFE, ensemble diversity) | CPU | `deterministic` | Verify before pinning |
| `dnachisel` | DNAChisel (pinned) | CDS with constraint-based optimisation (GC, CpG/UpA, forbidden motifs, restriction sites) | CPU | `deterministic` | MIT (verify) |
| `linearfold` | LinearFold (pinned) | none — structure metrics only (fast folding) | CPU, GPU optional | `deterministic` | Verify before pinning |
| `parade` | PARADE (pinned) | 5′UTR and 3′UTR generation; UTR activity/stability prediction | GPU recommended | `seeded` or `snapshot` | MIT |

- **RD-2.5** `viennarna-qc` and `linearfold` are exposed only as QC/metrics steps and cannot be selected as design methods; attempting one is a validation error, not a silent no-op.
- **RD-2.6** Region coverage is per-region truth. No V1 engine designs a 3′UTR, and LinearDesign designs no UTR at all, so an absent region is the normal case rather than an error: it is recorded `absent` with the reason and, when the template needs it, resolved from user input or a cited reference library. It is never filled with a placeholder sequence invented here.
- **RD-2.7** Licence status is a first-class adapter attribute: `research_only` or `permissive`. A `research_only` engine runs only after a per-session acknowledgement, and every run bundle records the restriction plus a statement that commercial use requires separate licensing. The project README states this too — a public notebook whose default path depends on a research-only engine must not imply otherwise.
- **RD-2.8** A constraint-based engine (`dnachisel`) must report the constraints it was given, whether each was satisfied, and the objective value. A constraint the engine could not satisfy is surfaced as a warning naming the constraint and its location — never silently relaxed, and never reported as met. This engine is the only sanctioned route to CpG/UpA depletion or forbidden-motif avoidance (QC-3.3, QC-4.3).
- **RD-2.9** Structure metrics are engine-attributed: every MFE/diversity value names the folder that produced it (ViennaRNA or LinearFold). Values from different folders are never placed in one series or compared as equivalent, because their energy models differ — a lower MFE from another engine is not a better design.
- **RD-2.10** Every adapter declares a `maturity` of `proven` or `experimental`. Only adapters registered in `SPEC-experimental-tier.md` may be `experimental`, and an `experimental` adapter can never appear in any `default_adapters` set or in a default-path fallback chain. Selecting one is always an explicit user action, and its output is labelled per XT-1.4.
- **RD-2.11** The 5′UTR resolution order is fixed and monotone in maturity: the user's pasted 5′UTR, then a selected proven engine (`optimus5`), then the cited reference library (RD-4.1c). An experimental engine (`parade`) is never reached automatically, even when every proven source is unavailable — that case resolves to `absent` with a recovery hint naming PARADE as an opt-in option. Substituting a research-grade model into a failed default path would silently convert a proven-path run into an unlabelled experimental one.

### Data contract

- **RD-3.1** `DesignRequest` = normalised protein, optional `signal_peptide_span`, optional seed, host codon-usage profile, target GC bounds or constraint hints *only where the upstream tool accepts them*, and adapter parameters. No field exists that an adapter would have to interpret biologically on its own.
- **RD-3.2** `DesignResult` = `protein`, `cds` (with explicit `has_start`, `has_stop`, `region_bounds`), optional `utr5`/`utr3`, `adapter_id`, `tool_version`, `resolved_params`, `seed`, `metrics` (CAI, GC, MFE, ensemble diversity where available), `warnings`, `provenance`.
- **RD-3.3** The CDS is always FASTA-checkable: start codon present, in-frame, terminating stop codon, length exactly `3*n`, no internal stop codons.
- **RD-3.4** **Translation fidelity is a hard contract:** retranslating `cds` with Biopython MUST reproduce the input protein exactly, for every adapter, every run. A violation is a defect in the adapter, never in the input.
- **RD-3.5** Determinism is declared, not assumed. `deterministic` adapters must produce identical output across runs on the same runtime; `seeded` adapters must produce identical output for a fixed seed on the same runtime/GPU model; `snapshot` adapters are validated against a recorded reference output with an explicit tolerance and a documented reason (e.g. GPU nondeterminism).
- **RD-3.6** **Seeding policy:** one global default seed, overridable per adapter. The resolved seed for each adapter is recorded in the manifest, so a run can be repeated without guessing which engine used which seed.
- **RD-3.7** `MrnaRecord` carries per-region provenance: the 5′UTR, CDS, and 3′UTR each record their own source (`adapter:<id>` | `user` | `reference:<id>`). A record built from more than one engine is normal, not a special case, and the report names the source of each region.
- **RD-3.8** Every metric an adapter reports is either computed by the upstream tool or by a named, cited helper; this repo does not invent metrics. CAI/GC/MFE definitions are documented in `docs/metrics.md` with their source.

### Comparison and outputs

- **RD-4.1** Running N adapters yields a comparison table over the same `DesignResult` fields, plus a per-adapter section; the module never picks or ranks a winner — candidate selection is the user's decision.
- **RD-4.1a** The default set is declared in config (`default_adapters`, per-step) and covers the regions the default template needs: `lineardesign` for the CDS and `optimus5` for the 5′UTR, with the reference library (RD-4.1c) as fallback when the 5′UTR engine is unavailable or does not fit the runtime budget. Because LinearDesign is CDS-only, a default set of CDS engines alone cannot produce a complete mRNA. CodonBERT, GEMORNA and additional engines are opt-in.
- **RD-4.1c** A cited reference-UTR library ships as data (`data/utrs/`): each entry carries sequence, region (5′UTR or 3′UTR), source (paper or accession), licence, and the label *reference, not optimised*. It is used when no engine was selected for a region or the selected engine is unavailable; that region's provenance becomes `reference:<id>`, and the report and `README.txt` state that it is a reference sequence the user must confirm for their application. Adding an entry is a data change with a citation, never a code change.
- **RD-4.1b** The construct source is a *named* adapter (`construct_source`, default `lineardesign`), not "the first result" and not a ranking. If the named adapter is unavailable or yielded no CDS, the run falls back to the next successful adapter in the declared set and states the substitution prominently in the summary, manifest, and report. The user can change the source without recomputing.
- **RD-4.2** Outputs per run: `designs/<adapter_id>/{cds.fasta, utr5.fasta, utr3.fasta, metrics.json}` and a run-level `designs/comparison.csv`; filenames are stable so `dna-construct` can consume the named source design by id.
- **RD-4.3** The chosen design can be exported as a single mRNA record (5′UTR + CDS + 3′UTR, concatenated in that order with an explicit junction map) for downstream construct building, with the junction coordinates recorded so QC can report per-region results.
- **RD-4.4** Warnings from upstream tools are surfaced verbatim (with tool attribution) and never swallowed; if an upstream tool printed a licence or citation notice, it is copied into the run bundle.

### Resource behaviour

- **RD-5.1** Each adapter declares an expected runtime/peak-memory class; the pre-flight summary uses it, and exceeding a configured ceiling aborts the adapter with a message instead of killing the session.
- **RD-5.2** Adapter results are cached within a session keyed by (input hash, adapter id, resolved params, seed, tool revision), so re-running the notebook does not repeat expensive work and a later failure does not force recomputation.

### Plugin contract and engine selection

- **RD-6.1** Adapters are plugins behind a versioned contract: `id`, `capabilities()`, `run()`, `determinism`, `licence`, `provenance`, plus a declared contract version. An engine declaring an incompatible contract version is refused with a message naming both versions — never coerced into running.
- **RD-6.2** Registration is not editing: an engine is added by registering it (manifest entry or entry point); neither the notebook nor the core registry is modified. This is what makes "use tool A or tool B for this step" a configuration change rather than a code change.
- **RD-6.3** Engine selection is per step, not global: CDS optimisation, 5′UTR, 3′UTR, and each QC predictor each expose a choice among available engines. The resolved engine per step is recorded in the manifest and printed in the summary, so a run never leaves the user guessing which tool produced which region.
- **RD-6.4** Third-party plugins are permitted only from a pinned install or a locally supplied file — never fetched and executed implicitly from a URL. They must declare licence and provenance, and are marked `unverified` in the report when the contract suite was not run in that session.
- **RD-6.5** A plugin cannot bypass validation: `DesignResult.validated()` runs for every engine including third-party ones, and a plugin that mutates a request or returns an invalid result is rejected and reported as a plugin defect.
- **RD-6.6** An engine can be disabled but not hidden: a disabled or unavailable engine still appears in the list with the reason, so the user learns the option exists and why it is off.

## Tech Stack

Python 3.11, Biopython (translation, FASTA/GenBank IO), pandas (comparison tables), pydantic (contracts), numpy. Upstream tools via pinned installs per the manifest; ViennaRNA Python bindings. No custom optimisation code.

## Commands

```bash
pytest tests/unit/design -q
pytest -m "network and not gpu" -q
pytest -m gpu -q
pytest tests/integration/test_adapter_contract.py -q
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only lineardesign custom
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --snapshot-update
```

## Project Structure

```
mrna_design/design/contracts.py     DesignRequest, DesignResult, MetricSet, MrnaRecord
mrna_design/design/plugins.py       versioned plugin contract, entry-point registration
mrna_design/design/registry.py      engine discovery, availability, capabilities, licence flags
mrna_design/design/compare.py       comparison table, mRNA assembly + junction map
mrna_design/design/guards.py        length/memory/time guards, result cache
mrna_design/adapters/base.py        ABC + shared validation helpers
mrna_design/adapters/{lineardesign,codonbert,custom,gemorna,optimus5,viennarna,dnachisel,linearfold}.py
tests/unit/design/                  contract + comparison tests
tests/integration/test_adapter_contract.py   parametrised over the registry
tests/fixtures/golden_rbd/          reference protein + recorded snapshots
docs/metrics.md                     metric definitions and citations
data/utrs/                          cited reference 5′/3′UTR entries with provenance
data/utrs/README.md                 what each entry is, why it is there, what it is not
```

## Code Style

Adapters are uniform, self-describing, and free of shared mutable state:

```python
class LinearDesignAdapter:
    id = "lineardesign"
    deterministic = "snapshot"

    def capabilities(self) -> Capabilities:
        return Capabilities(designs=("cds", "utr5"), gpu_required=False, max_aa=5000)

    def run(self, request: DesignRequest, guard: Guard) -> DesignResult:
        """Call the pinned upstream tool. Validates its own output before returning."""
        with guard.budget(tool=self.id):
            raw = upstream.design(request.protein, **request.adapter_params)
        return self._to_result(raw, request).validated()   # raises AdapterDefect, never returns silently
```

Conventions: one adapter = one class with `id`, `capabilities()`, `run()`; all output validation in `DesignResult.validated()`; requirement IDs in test names; no adapter may mutate a `DesignRequest`.

## Testing Strategy

- **Contract suite (per adapter, the core of this module):** translation fidelity, valid start/stop, correct length, region presence/absence honesty, seed determinism or snapshot agreement, declared capability bounds honoured, warnings preserved.
- **Unit:** validation messages, guards, cache keys, comparison table shapes, FASTA/GenBank round-trip. No network.
- **Integration (`-m network`, `-m gpu`):** real tools on the golden protein; verify pinned revision is what executed.
- **Golden snapshot:** one reference protein (SARS-CoV-2 spike RBD), outputs recorded per adapter. Updating snapshots requires review and a commit message stating *why* the output legitimately changed — snapshot updates are a quality gate, not a test convenience.
- Coverage ≥80%; `adapters/base.py` and `contracts.py` at ≥95%.

## Boundaries

- **Always:** validate every adapter output before returning it; declare determinism honestly; pin and record the exact revision that ran; keep the contract additive-only within V1.
- **Ask first:** adding/removing an adapter; widening `DesignRequest`/`DesignResult`; changing the golden protein or snapshots; changing the length cap; accepting an upstream licence that restricts redistribution.
- **Never:** implement a codon optimiser, UTR model, or structure predictor in this repo (including a "simple baseline"); copy upstream algorithm source into `mrna_design/`; let an adapter return a CDS that does not translate to the input; silently substitute a different tool or a placeholder UTR; rank candidates on the user's behalf.

## Success Criteria

| # | Criterion | Verification |
|---|---|---|
| RD-SC1 | Every registry adapter passes RD-3.3 and RD-3.4 on the golden protein | `tests/integration/test_adapter_contract.py` |
| RD-SC2 | Registry and contract-suite parametrisation are identical sets | Unit test on registry enumeration |
| RD-SC3 | 2+ adapters produce a comparable table with no missing metrics for common fields | Integration assertion on `comparison.csv` |
| RD-SC4 | Determinism behaviour matches the declaration for each adapter | Repeat-run test (deterministic), seed test (seeded), snapshot test (snapshot) |
| RD-SC5 | GPU-only adapters are unavailable-with-reason on a CPU runtime; nothing is attempted | CPU-runtime integration test |
| RD-SC6 | Exported mRNA record round-trips with a junction map whose coordinates reconstruct 5′UTR/CDS/3′UTR | Unit round-trip test |
| RD-SC7 | No adapter code path exists that originates a sequence from this repo's own logic | Code review checklist + grep-based test forbidding reverse-translation helpers outside adapters |
| RD-SC8 | Construct source is resolved by name, and any substitution is recorded and surfaced | Unit test with the named adapter made unavailable |
| RD-SC9 | The default set runs on CPU within the default budget; no GPU adapter is on the default path | CPU-runtime timing + registry assertion on `default_adapters` |
| RD-SC10 | A test plugin registers without touching core code and passes the contract suite; a contract-version mismatch is refused with a stated reason | Plugin fixture tests |
| RD-SC11 | Per-step engine selection is recorded and printed, including mixed-engine records (5′UTR from one engine, CDS from another) | Manifest assertion on a mixed-engine run |
| RD-SC12 | Every reference-UTR entry resolves to a source and licence, and its use is labelled *reference, not optimised* in the report and README | Library validation test + report snapshot |
| RD-SC13 | A deliberately unsatisfiable DNAChisel constraint is reported by name and location, and the run never claims it was met | Negative test with an impossible constraint |
| RD-SC14 | MFE values carry the folding engine, and no output places two folders in one series | Report/manifest assertion on a two-engine run |
| RD-SC15 | No `experimental` adapter appears in any default set or fallback chain; with every proven UTR source removed, the 5′UTR resolves to `absent` with a recovery hint rather than to PARADE | Registry assertion + default-path test with proven UTR sources stubbed unavailable |

## Out of Scope (Deferred)

- In-house baseline codon optimiser — would violate the no-new-algorithms constraint; CUSTOM/LinearDesign cover it.
- Joint 3′UTR design — no proven tool in V1 inventory; generative UTR models are V2.
- Multi-chain / polyprotein handling — V1 assumes a single open reading frame; linker design is V2 at the earliest.
- Batch runs over many proteins — Colab session budget and UI simplicity; one protein per run in V1.
- Codon-usage tables beyond human — host selection arrives with a cited table, not an ad-hoc heuristic.
- Remote/arbitrary plugin loading (fetch-and-execute) — a public notebook that executes code from a URL cannot make any reliability claim; plugins come from pinned installs or local files only (RD-6.4).

## Open Questions

1. **Which reference UTRs, and under what licences?** The library is only as good as its curation: each entry needs a paper or accession, a licence that permits redistribution, and a stated reason for inclusion. A UTR taken from a patented vaccine construct is a licensing question, not a technical one.
2. **5′UTR default engine on CPU:** confirm Optimus 5-Prime runs within the Colab free-tier budget. If it does not, the reference library becomes the default 5′UTR source, `optimus5` becomes opt-in, and PARADE is offered as an explicit opt-in 5′UTR engine for users who want generation over a reference sequence — never as the automatic substitute (RD-2.11).
3. **Third-party plugin policy:** local file and pinned install only (current rule, RD-6.4), or a curated allowlist with a review step? The former is safe but shifts risk to the user; the latter creates a maintenance queue.
4. **LinearDesign redistribution:** the research-only licence covers use, but confirm the pinned binary may be fetched by the bootstrap. If not, point at the upstream release rather than mirroring it.
