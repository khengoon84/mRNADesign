# Statement of Intent — mRNADesign

## mRNADesign — mRNA Sequence & Vaccine Design Tool

- **Outcome:** A public, open-source Google Colab notebook orchestrating proven open-source tools through a form-driven, guided workflow. Two modules:
  - **Module 1 — RNA sequence design & optimisation:** Core (LinearDesign, CodonBERT, CUSTOM, GEMORNA, Optimus 5-Prime, ViennaRNA QC, LinearFold QC) + DNAChisel (constraint-based CDS optimisation: CpG/UpA, forbidden motifs, restriction sites) + additions 1–6 (λ trade-off visualisation, CpG/UpA depletion, m1Ψ slippery-sequence avoidance, motif scan suite, Kozak/signal-peptide/TM checks, consolidated QC report) + an experimental tier (generative UTR models, epitope/antigen prediction) that users opt into per workflow.
  - **Module 2 — DNA construct/plasmid design:** Linear IVT template, circular plasmid, gene-synthesis order block, user-uploaded backbone, and — in V2 — cloning simulation (primer design + PCR) as adapters over OpenCloning/Primer3.
- **User:** Molecular biologists, vaccine developers, and scientists without command-line/Linux skills — one guided flow instead of tool-hopping.
- **Why now:** Proven tools exist but are CLI-only and fragmented; steps get lost between tools; VaxLab proves the Colab model but lacks a plasmid module.
- **Success:** GitHub release + paper; a biologist completes protein sequence in → optimised mRNA + construct/order outputs out in one Colab session with no terminal.
- **Constraint:** No new algorithms — adapters/wrappers over reliable open-source software only; runs on Colab with GPU as an option for deep-learning tools.
- **Out of scope:** New algorithm development, local/CLI installation, standalone web app, clinical/wet-lab validation, and commercial-use clearance for research-only dependencies (users obtain their own licences).

## Reference model

- [VaxLab (ChangLabSNU)](https://github.com/ChangLabSNU/VaxLab) — integrated Colab platform for mRNA vaccine design: form fields + Run-all UX; covers UTR optimisation (GEMORNA, Optimus 5-Prime), CDS optimisation (LinearDesign, CodonBERT, simple codon optimizer, CUSTOM), quality report, Twist order sheet. mRNADesign builds from scratch using VaxLab as a UX/architecture model, adding the plasmid/construct module VaxLab lacks.

## Scope decisions (spec interviews, 2026-11-16)

Confirmed while drafting `CAPABILITY-MAP.md` and the `SPEC-*.md` set. The specs are authoritative for detail; this section records the intent-level decisions the original statement did not yet contain.

**Versions**
- V1 ships Module 1 and Module 2. The experimental tier and cloning simulation (primer/PCR) are V2.
- One public notebook. The two modules are independently runnable, and Module 2 accepts either Module 1 output or a user-supplied sequence.

**Engines and what they may do**
- LinearDesign optimises the CDS only — it performs no UTR optimisation. CodonBERT (MIT) and CUSTOM also produce CDS.
- GEMORNA and Optimus 5-Prime generate 5′UTRs.
- No V1 engine generates a 3′UTR. V1 uses a cited reference-UTR library labelled *reference, not optimised*; PARADE (MIT, verified) is the intended V2 3′UTR engine.
- DNAChisel is the only sanctioned route to CpG/UpA depletion, forbidden-motif avoidance, and restriction-site removal. QC never recodes — it measures.
- ViennaRNA and LinearFold report structure metrics only. Their MFE values are engine-attributed and never compared across engines, because the energy models differ.
- Signal peptide is predicted with DeepSig or PEFT-SP (open source). SignalP is excluded: a licence-gated predictor would leave the check unusable for most users. Transmembrane prediction waits for an open engine.

**Licensing**
- The project's own code is **MIT**. MIT cannot be narrowed to "research only" without ceasing to be MIT, so the research restriction is recorded where it actually applies — on the dependency — not on the project licence.
- LinearDesign is research use only, not for commercial use. Because it is the default CDS engine, the default path is research-only: the notebook states this, requires acknowledgement, and `README` explains that commercial use requires replacing that engine or licensing it separately.
- Other engines are permissively licensed where stated (CodonBERT and PARADE are MIT) and otherwise verified before pinning.
- No clinical or wet-lab validation is claimed anywhere.

**Limits**
- Minimum ORF is one codon; fewer than 10 codons is accepted with a warning. Maximum 5,000 aa.
- One global default seed, overridable per engine.

**Construct**
- Template types: `pcr` (default, needs no user material) and `plasmid` (requires an uploaded backbone). No bundled backbones in V1.
- Domain chain: 5′UTR → Kozak (optional) → signal peptide (optional) → antigen → 3′UTR → poly(A).
- Poly(A) follows template type: none encoded in `pcr` (added enzymatically), encoded in `plasmid` with a 100 nt default.
- Order output is vendor-neutral CSV. No synthesis vendor has been selected, so no vendor-specific format or synthesis limit is claimed.

**Architecture**
- Engines are plugins behind a versioned contract, selectable per step (5′UTR, CDS, 3′UTR, each QC predictor). Mixing engines across steps is normal.
- Plugins come from pinned installs or local files only. Code is never fetched and executed from a URL.
- "Run all" guarantees the default path only. Anything needing material the tool cannot invent resolves to a declared skip with a one-step recovery hint — never an invented default.

## Confirmed

User confirmed this statement of intent explicitly on 2026-11-16.

Scope decisions above were confirmed on 2026-11-16 during the spec interviews. Module boundaries and build order are recorded in `CAPABILITY-MAP.md`, and the approved specifications are `SPEC-notebook-shell.md`, `SPEC-rna-design.md`, `SPEC-rna-qc-additions.md`, `SPEC-dna-construct.md`, plus the V2-deferred `SPEC-experimental-tier.md`.
