# Spec: `dna-construct` — V1

Status: proposed, awaiting review
Parent: `CAPABILITY-MAP.md`

## Objective

Turn an optimised mRNA design into DNA a lab can actually order: a linear IVT template, a circular plasmid around a user-supplied backbone, and a gene-synthesis order block. VaxLab stops at an order sheet for the mRNA; the gap this module closes is the construct step, which today forces a biologist into SnapGene/Benchling plus a vendor portal.

Success is: a user picks a design and a template type — a PCR-derived linear template by default, or a plasmid around an uploaded backbone — and gets annotated GenBank + FASTA + a vendor-shaped order CSV that a colleague can open, verify by eye, and submit, with the tool never implying it has simulated cloning, because that is V2.

## Scope

In scope: mRNA→DNA conversion, linear IVT template assembly, circular plasmid assembly against an uploaded backbone, feature annotation and preservation, restriction-site analysis via existing libraries, vendor order-block generation, construct map rendering, and construct-level validation.

Out of scope: cloning simulation, primer design, PCR, ligation/Gibson simulation, colony/assembly feasibility (all V2, `cloning-simulation`); codon re-optimisation (belongs upstream in `rna-design`); SnapGene `.dna` input (deferred, proprietary); new backbones drawn from memory rather than a licensed, verified source.

## Requirements

### Input contract

- **DC-1.1** Consume any of: a `DesignResult` from the current session named by `construct_source` (RD-4.1b); a sequence pasted, uploaded, or carried over from a previous run's export; or a user-supplied sequence unrelated to any run. Module 2 must be fully usable with no design step ever executed.
- **DC-1.2** Accept mRNA (U) or DNA (T) input. DNA is taken to be the coding strand; a reverse-complement assumption is never made silently. Conversion is explicit and applied once (U→T, or identity for DNA), recorded in the manifest, and shown in the construct summary. Mixed T/U input is rejected with the offending positions.
- **DC-1.3** Validation before assembly: single sequence, valid nucleotides, CDS identified and in frame, start and stop codons present, no internal stop codons, junctions recorded. Failures name the region and coordinate.
- **DC-1.4** The V1 input is one mRNA insert per construct; multi-insert and polycistronic designs are rejected with a message pointing at the deferred item.

- **DC-1.5** Minimum accepted ORF is **one codon** — the limit is expressed and validated in codons, not nucleotides. One to nine codons is accepted with a warning that optimisation and QC results are not meaningful at that length; zero codons or a non-multiple-of-three insert is rejected as structurally invalid. No length-based padding is applied.

### Template types and the domain chain

- **DC-2.0** Template type is an explicit, recorded choice with two V1 values: `pcr` (linear PCR-derived IVT template) and `plasmid` (IVT from a circular plasmid, requiring an uploaded backbone, DC-3.*). The default is `pcr`, because it needs no user-supplied material and therefore keeps the default path complete.
- **DC-2.1** The assembled mRNA domain chain is, in 5′→3′ order: 5′UTR → Kozak context (optional) → signal peptide (optional) → antigen → 3′UTR → poly(A) *(only when the template type encodes it)*. Every junction is a recorded coordinate, and the order is asserted rather than assumed: a domain out of place is a hard failure.
- **DC-2.2** Poly(A) is **derived from template type, not an independent toggle**. `pcr` templates carry no poly(A) tract: the tail is added enzymatically downstream and the summary, README, and order notes all say so. `plasmid` templates carry an encoded tract whose length the user sets, default 100 nt, with a synthesis warning above the vendor's homopolymer limit. Offering a poly(A) option for a PCR template is a defect — the control is hidden, not disabled with a confusing explanation.
- **DC-2.3** Kozak insertion is opt-in and data-driven: the inserted consensus is a cited string in `data/`, never a literal in code. Every inserted or altered base is listed in the junction map and summary, because the 5′UTR 3′ end is being changed. The default is not to insert; when the user opts in, the tool overwrites the designed junction and raises a recorded warning that names the upstream decision it discarded. The post-assembly QC pass (QC-1.6) evaluates what was actually produced.
- **DC-2.4** The signal peptide is never synthesised here. It arrives already encoded in the ORF from `rna-design` and is annotated as its own CDS feature using the declared span (RD-1.5). If a signal peptide is supplied separately, it is prepended *before* design so codons are optimised across the full ORF; an assembly step that would require reverse-translating a peptide is a spec violation.
- **DC-2.5** Promoter handling follows template type. For `plasmid`, the promoter is verified in the backbone — present once, correct orientation, transcription start site annotated — and its absence is a hard failure rather than an insertion by the tool. For `pcr`, an empty `five_prime_flank` means the tool prepends a standard, cited T7 promoter block to the ordered fragment, recorded as its own annotated feature with a note that the order includes it; a non-empty `five_prime_flank` is user-supplied and validated instead, never silently merged with the default. Which path was taken is stated in the summary, the manifest, and the order notes.
- **DC-2.6** The template must be verifiable by eye: the summary prints template type, total length, per-region lengths, GC%, poly(A) status (encoded / added enzymatically), signal peptide span, promoter source (backbone-verified / prepended / user-supplied), and a linear feature list in 5′→3′ order.

### Circular plasmid

- **DC-3.0** No backbone is bundled, generated, or invented as a default. A construct request without a backbone resolves to the linear IVT template (DC-2.*) and records the plasmid branch as `skipped` with a recovery hint. It is never an error, and never a guessed vector: a plausible-looking default here produces something a user might actually order.
- **DC-3.1** Backbones in V1 come from user input (GenBank or FASTA), supplied as a typed path parameter first with the upload widget as a convenience (`SPEC-notebook-shell.md` NS-1.6), parsed with Biopython, validated (single circular record, features parse, no malformed locations), and echoed back with a feature list so the user confirms the right file was read.
- **DC-3.2** V1 ships **no** bundled backbones: every plasmid is built on a user-supplied file, and the manifest records its hash and parsed feature list. A curated bundled set is deferred, because it needs per-vector licence clearance.
- **DC-3.3** Insertion is accepted either way in V1 — explicit coordinates or a user-chosen site pair — because biologists think in enzymes while coordinates are needed for backbone-agnostic cases. The assembly is deterministic sequence splicing with the exact replaced span recorded, and a diff against the input backbone must show exactly one contiguous replaced region and nothing else.
- **DC-3.4** Insert orientation and reading frame are asserted and reported; a reverse-complement or frame mismatch is a hard failure, not a warning.
- **DC-3.5** Backbone features are preserved with recomputed coordinates; a feature that cannot be mapped unambiguously after insertion is reported rather than silently dropped or shifted.
- **DC-3.6** Restriction analysis uses Biopython's `Restriction` enzyme tables, not a hand-written recognition-site list: report unique sites suitable for linearisation, internal sites for the chosen enzyme, and site counts in insert vs. backbone. For `plasmid` templates, the run-off linearisation site must be 3′ of the poly(A) cassette and unique, and that is asserted, not merely listed.
- **DC-3.7** Ligation/overhang compatibility is **not** evaluated in V1. The report must state that cloning feasibility has not been simulated; any compatibility table would be `cloning-simulation`'s job in V2.

### Gene-synthesis order block

- **DC-4.1** Emit `order_block.csv` with a vendor-neutral schema: `kind`, `name`, `sequence`, `length_nt`, `gc_pct`, `notes`. No vendor is selected in V1, so exactly one profile exists (`data/vendors/generic.yaml`) and it only defines column order — it never invents a constraint. `kind` accepts `gene_fragment` and `oligo` so a later vendor preset or the V2 cloning layer can fill it without a format change; V1 emits `gene_fragment` only, because nothing in V1 produces oligo sequences (primer and overlap-oligo design belong to `cloning-simulation`).
- **DC-4.2** Synthesis checks come from the `generic` profile, because no vendor is chosen yet. Each rule records the published guidance it derives from (document title, URL, date checked) and is marked `unspecified` where no defensible published guidance exists — a guessed limit is worse than an admitted gap, in both directions. The CSV notes and the summary label the output *generic synthesis guidance, not vendor-validated*. Rules older than `stale_after_days` (default 180) warn. Adding a real vendor profile later adds a data file plus a well-formedness test, never a code path.
- **DC-4.3** Validation results are per-row and explicit: hard failures (invalid characters, duplicate names, length outside the profile's range) block export; synthesis-risk items (extreme GC, long homopolymer, long repeat) are warnings visible in the CSV and the summary.
- **DC-4.4** Export is blocked, with reasons, if any construct-level assertion from DC-1.3, DC-2.4, DC-3.4 fails. A user cannot order a construct the tool knows to be inconsistent.
- **DC-4.5** The CSV and the README carry a fixed note: the order block is a convenience export and must be checked in the vendor's own tool before submission; it is not a validated order.

### Outputs

- **DC-5.1** Per construct: `construct.gb` (annotated, GenBank), `construct.fasta`, `order_block.csv`, `construct_map.png`/`.svg`, and `construct_summary.md` (junctions, checks, provenance, caveats).
- **DC-5.2** GenBank round-trip is mandatory: re-parsing the emitted file must yield identical sequence, identical feature set, and a CDS that translates to the original protein.
- **DC-5.3** The map is rendered through a pinned plotting library's API; no hand-rolled coordinate transforms beyond passing features in. Labels must be legible at report zoom and identify promoter, UTRs, CDS, poly(A), backbone features, and insertion boundaries.
- **DC-5.4** Provenance links back to the source `DesignResult` (adapter, tool version, seed) and to the backbone file hash, so a construct can be traced to the run that produced it.
- **DC-5.5** If the source design came from the experimental tier (V2), the construct and order block are flagged `experimental_derived` in filename metadata, summary, and CSV notes.

## Tech Stack

Python 3.11, Biopython (SeqIO, Restriction, feature locations), pandas (order CSV), PyYAML (vendor/backbone data), a pinned plotting library for maps, pydantic (construct config). No custom sequence assembly algorithm, no primer design.

## Commands

```bash
pytest tests/unit/construct -q
pytest tests/integration/test_construct_roundtrip.py -q
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --construct linear --poly-a encoded
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml \
  --backbone tests/fixtures/backbones/puc19.gb --insert-at 450
```

## Project Structure

```
mrna_design/construct/rna_to_dna.py      conversion + validation, explicit and logged
mrna_design/construct/linear.py          IVT template assembly + junction map
mrna_design/construct/plasmid.py         backbone parse, insertion, feature remap
mrna_design/construct/checks.py          promoter/frame/orientation/site assertions
mrna_design/construct/order.py           vendor schema, constraint validation, CSV
mrna_design/construct/map.py             feature map rendering
data/vendors/generic.yaml               the only V1 profile: column order, no invented limits
data/backbones/                          only licence-cleared backbones + sidecars
tests/unit/construct/                    assembly, remap, constraint tests
tests/integration/test_construct_roundtrip.py
tests/fixtures/backbones/                permissive test backbones
docs/construct-formats.md                file formats, junction conventions, caveats
```

## Code Style

Fail closed, record every junction, never guess an arrangement:

```python
def assemble(design: MrnaRecord, cfg: TemplateConfig, ref: ConstructRef) -> Construct:
    """Build the DNA template. Raises ConstructError on any non-verifiable junction."""
    chain = [
        design.utr5,
        kozak_block(cfg.kozak, ref) if cfg.kozak else "",   # cited consensus, bases recorded
        design.signal_peptide,        # already encoded upstream; annotation only
        design.antigen,
        design.utr3,
        polya_block(cfg.poly_a_length) if cfg.template_type == "plasmid" else "",
    ]
    return Construct.from_parts(chain, template_type=cfg.template_type).with_junction_map()
```

Conventions: construct assembly functions return immutable `Construct` objects; template type drives optional elements rather than an open set of toggles; every coordinate mutation goes through one remap helper; requirement IDs in test names; nothing is reverse-translated here.

## Testing Strategy

- **Unit:** RNA→DNA conversion (including mixed T/U rejection), junction map correctness, poly(A) modes, promoter orientation checks, backbone feature remap across the origin (wrap-around case), frame/orientation failures, vendor constraint validation per rule, CSV schema.
- **Round-trip integration:** emit GenBank → re-parse → compare sequence, features, and CDS translation; emit CSV → re-parse with the vendor schema definition.
- **Golden construct:** one linear template and one plasmid from the golden RBD design, with snapshots of the summary and feature table (not the binary image).
- **Negative tests:** backbone with a feature spanning the insertion point, circular feature crossing position 0, duplicate enzyme sites, insert in reverse orientation, order block that must be blocked.
- Coverage ≥85% for `mrna_design/construct/`; all DC-4.4 blocking paths tested.

## Boundaries

- **Always:** record every junction and the RNA→DNA conversion; preserve backbone features or report the failure; cite every vendor constraint; state that cloning was not simulated.
- **Ask first:** bundling any backbone sequence; adding a vendor preset; changing junction/annotation conventions; changing `order_block.csv` columns; enabling a ribozyme arrangement; raising the poly(A) default.
- **Never:** design primers or simulate PCR/ligation (V2); hand-write restriction-site tables; substitute a default or bundled backbone; emit a construct whose CDS does not translate to the source protein; drop or silently shift a backbone feature; claim an order block is vendor-validated; accept a `.dna` file and pretend it parsed.

## Success Criteria

| # | Criterion | Verification |
|---|---|---|
| DC-SC1 | Linear template and plasmid both build from the golden design, with complete junction maps | E2E + unit assertions on junction map |
| DC-SC2 | Emitted GenBank round-trips: sequence, features, and CDS translation identical | `tests/integration/test_construct_roundtrip.py` |
| DC-SC3 | Backbone diff shows exactly one contiguous replaced span | Unit test on spliced construct |
| DC-SC4 | Feature spanning the insertion point and feature crossing origin both handled or explicitly reported | Negative-case unit tests |
| DC-SC5 | Order CSV validates against schema and blocked exports list every violation | Constraint tests per rule |
| DC-SC6 | Construct summary explicitly states cloning feasibility was not simulated | Snapshot assertion on summary text |
| DC-SC7 | Archive contains DC-5.1 file set, and provenance links resolve to the source run | E2E bundle assertion |
| DC-SC8 | Run all with no backbone yields the `pcr` template and order block, with zero errors and a recovery hint naming `backbone_path` and its cost | E2E bundle assertion + notebook smoke |
| DC-SC9 | No default or bundled backbone can enter a construct; absence always resolves to `pcr` | Unit test on construct-mode resolution |
| DC-SC10 | The poly(A) control is absent for `pcr` and present with a 100 nt default for `plasmid`; neither template can silently encode a tail it should not | UI/config test + junction map assertion |
| DC-SC11 | Every `generic` rule resolves to a source and check date, or is explicitly `unspecified`; stale rules warn | Profile validation test with a backdated rule |
| DC-SC12 | A 1-codon ORF is accepted with a warning; a non-multiple-of-three insert is rejected; no padding occurs | Boundary unit tests |
| DC-SC13 | A `pcr` template with an empty `five_prime_flank` carries exactly one annotated T7 promoter at the 5′ end; a supplied flank replaces it rather than stacking | Unit test on both branches |
| DC-SC14 | Module 2 alone produces a complete construct + CSV bundle from a pasted mRNA or DNA sequence, with the design step recorded `not run` | Headless test with `run_modules=["construct"]` |

## Out of Scope (Deferred)

- Cloning simulation, primer design, PCR — `cloning-simulation`, V2.
- SnapGene `.dna` import — proprietary format; V1 accepts GenBank/FASTA.
- Multi-insert, Golden Gate, Gibson, polycistronic constructs — needs the cloning layer first.
- Codon re-optimisation at the DNA level (e.g. to remove a restriction site) — that is an optimiser, and it belongs upstream if it happens at all.
- Minimum construct length for a synthetic-fragment order, and the oligo route it implies — deferred until a vendor is chosen; the generic profile warns with an unverified value.
- Ribozyme / defined-3′-end cassettes — the V1 domain chain is the agreed one (5′UTR → Kozak → signal peptide → antigen → 3′UTR → poly(A)); a ribozyme needs an expert arrangement review and is deferred.
- Bundled curated backbones — V1 is upload-only by decision; a shipped set needs per-vector licence clearance.
- Bulk ordering of multiple constructs in one session — one construct per run in V1.

## Open Questions

1. **Minimum length for a gene-fragment order:** deferred by decision. The `generic` profile's value raises the warning and the CSV says the route is unverified; the threshold will be set when a vendor is chosen.
