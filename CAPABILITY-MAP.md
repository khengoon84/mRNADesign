# Capability Map: mRNADesign — V1

Status: proposed, awaiting review
Source of truth for intent: `mRNADesign.md`
Per-module specs: `SPEC-<module-id>.md` (this map is the index; module ids are stable and never renamed)

## Modules

| Module id | Version | Responsibility | Depends on |
|---|---|---|---|
| `notebook-shell` | V1 | Single Colab entrypoint, form-driven config, pinned tool bootstrap + provenance, run ledger, artifact packaging, human-readable failure handling | — |
| `rna-design` | V1 | Adapters over LinearDesign, CodonBERT, CUSTOM, GEMORNA, Optimus 5-Prime, and ViennaRNA; unified `DesignRequest`/`DesignResult` contract | `notebook-shell` |
| `rna-qc-additions` | V1 | Additions 1–6 as pure checks over `DesignResult`: λ trade-off, CpG/UpA, m1Ψ slippery sites, motif scan suite, Kozak/SP/TM, consolidated QC report | `rna-design` |
| `dna-construct` | V1 | Linear IVT template, circular plasmid, gene-synthesis order block, user-uploaded backbone | `rna-design` |
| `experimental-tier` | V1 (PARADE only) + V2 | Opt-in experimental engines. **V1: PARADE** (5′/3′UTR generation + prediction), never on the default path. V2: UTRGAN, Smart5UTR, epitope/antigen prediction | `rna-design` |
| `cloning-simulation` | V2 (deferred) | Primer3 primer design + PCR/cloning simulation via OpenCloning | `dna-construct` |

Build order: `notebook-shell` → `rna-design` → `rna-qc-additions` → `dna-construct` → *(V2)* `cloning-simulation`.
`experimental-tier` is built after `rna-design` and is never on the default path: V1 ships PARADE as an opt-in engine only; the rest of the tier is V2.

## Dependency rules

- Arrows point one way. Two modules needing each other are one module.
- The `DesignRequest`/`DesignResult` contract lives in `SPEC-rna-design.md`; `rna-qc-additions` and `dna-construct` consume it and may not widen it without a delta spec.
- The only plausible future cycle is epitope prediction (V2) feeding polyepitope construct design. It must route through the `rna-design` request contract, never by `experimental-tier` writing into `dna-construct` internals. Flagged now so V2 does not have to unwind it.
- QC has two invocation points: the design record (`rna-design`) and, when present, the assembled mRNA (`dna-construct`, QC-1.6). The second is a runtime edge, not a build-order change — construct never depends on QC — and it is what lets the report describe the sequence as it will actually be ordered.
- `rna-design` and `dna-construct` are independently *usable* but not independently *buildable*. Module 2 accepts a user-supplied or previously exported sequence with no design step run (NS-1.7, DC-1.1), yet it still consumes the `MrnaRecord` contract owned by `rna-design`. Skipping the design step skips work, not the dependency — so the build order stands.
- `notebook-shell` owns scaffolding, layout, commands, and the shared test harness. Other specs list only their own paths and add only module-specific commands.

## V1 definition of done

A molecular biologist with no command-line skills opens the public Colab notebook in a fresh session, enters a protein sequence, presses Run all, and — with every other field left at its default — receives optimised mRNA for the default adapter set, a consolidated QC report, a linear (PCR-derived) IVT template, a vendor-neutral gene-synthesis order block, and a downloadable run bundle. No terminal, no local install, no further input.

**"Run all" is a promise about the default path, not about every feature.** Anything needing material the tool cannot invent — a backbone, a design choice — resolves by presence: absent input yields a declared skip with a one-step recovery hint, never an error and never a plausible-but-wrong default. Circular plasmid, additional adapters, and vendor-specific export profiles are therefore branches, not defaults.

Verified once per release on the golden case plus the invariants in `SPEC-rna-design.md` §Success Criteria, and continuously by the headless end-to-end test.

## V2 backlog

| Item | Why deferred |
|---|---|
| `experimental-tier` — UTRGAN, Smart5UTR, epitope/antigen | Research-grade. PARADE is the exception: it ships in V1 as an opt-in engine because it is the fallback when Optimus 5-Prime cannot fit the Colab free tier. Everything else needs the reliability contract proved on PARADE first, and must not contaminate V1's "proven tools only" claim. |
| `cloning-simulation` (Primer3 primers, PCR simulation) | Agreed sequencing: it consumes construct outputs, so it is only meaningful once `dna-construct` is solid. |
| SnapGene `.dna` backbone import | Proprietary format; V1 accepts GenBank/FASTA only. |
| Multiple golden cases across antigen length classes | V1 pins one canonical case to keep the regression suite cheap; more can be added without a spec change only if they stay fixtures. |

## Notes

- **Core engine set expanded by decision (2026-11-16):** DNAChisel (constraint-based CDS optimisation, and the only sanctioned route to CpG/UpA depletion) and LinearFold (second structure-metrics engine) are now recorded in `mRNADesign.md` under *Scope decisions*, so the intent document and this spec set describe the same toolset.
- **PARADE verified** (`autosome-ru/parade`, MIT): 5′ and 3′UTR generation plus activity/stability prediction. It is the intended V2 answer to the 3′UTR gap that V1 fills with the reference library.
- **UTR gap closed for V1** (RD-4.1c): a cited reference-UTR library as data, with Optimus 5-Prime supplying 5′UTRs when it fits the CPU budget. Per-region provenance (RD-3.7) means a report never implies a reference 3′UTR was designed.
- **Depletion is no longer backlog:** CpG/UpA and forbidden-motif avoidance are reachable through DNAChisel as an opt-in design engine (RD-2.8). QC still only measures (QC-3.3), so the "no new algorithms" rule holds by construction rather than by omission.
- **No VCS yet, by decision.** History is kept as dated immutable snapshots (`scripts/snapshot.sh`, archives in `backups/`) plus an append-only `DECISIONS.md`. Snapshots are taken *before and after* each significant session change and are stored in the workspace; copying them off-machine is not required (D-020), with the resulting exposure to disk failure recorded and accepted there. Local `git init` publishes nothing (no account, no network) and remains the expected floor once implementation starts.
- `agent-skills/` in this workspace is tooling for the agent, not part of the mRNADesign deliverable.
