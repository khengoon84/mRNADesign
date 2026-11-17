# Spec: `rna-qc-additions` — V1

Status: proposed, awaiting review
Parent: `CAPABILITY-MAP.md`

## Objective

Deliver additions 1–6 as a layer of pure, individually testable checks over `DesignResult`, and consolidate them into one report a biologist can act on. The upstream tools optimise; nothing in the field tells a user "this design is strong, but it has three U-homopolymer runs and a cryptic polyadenylation signal — fix those first". That gap is this module's reason to exist.

Success is: every check is a function of (design, reference data) with no hidden state, every result carries status plus the source of its threshold, and a check that could not run is visibly `not_run` rather than quietly passing.

## Scope

In scope: additions 1–6, the check-result data model, the threshold/motif/vendor data files with citations, the consolidated report renderer, and per-region metrics.

Out of scope: designing or recoding sequences (any mitigation must be performed by an upstream tool's own parameters), candidate ranking, DNA-level checks (`dna-construct`), experimental-tier results (rendered separately in V2, never affecting status).

## Requirements

### Check model (applies to all six additions)

- **QC-1.1** Every check is a pure function `(record: MrnaRecord) -> CheckResult`, with no I/O beyond loading versioned data files, no global state, and no randomness.
- **QC-1.2** `CheckResult` = `id`, `addition`, `region` (`mrna` | `utr5` | `cds` | `utr3`), `status` ∈ {`pass`, `warn`, `fail`, `not_run`}, `value`, `unit`, `threshold_ref`, `message`, `evidence` (coordinates/spans). `not_run` is mandatory and distinct from `pass`.
- **QC-1.3** Every threshold, motif, and severity lives in a versioned data file under `data/` with a citation and an effective-date; no threshold is hard-coded in Python. Changing a threshold is a data diff a reviewer can see.
- **QC-1.4** The report states, per check, whether it evaluates the full mRNA or a region, because region-scoped results must not be read as whole-molecule claims. "Full mRNA" means 5′UTR → poly(A) by definition (the sequence the user actually has), but the poly(A) tract is its own region and is excluded from dinucleotide/GC/homopolymer density metrics — including it would swamp every count. Poly(A) length and integrity are reported separately.
- **QC-1.8** Where no validated threshold exists, a check may instead be **reference-derived**: the data file records a cited reference set, the statistic used (e.g. a percentile of CpG density across licensed vaccine sequences), and the version of that set. The report labels such rows *reference-derived, not a safety threshold*, and never presents the number as a pass/fail biological boundary. This is the only acceptable way to produce a threshold for vaccine-context CpG/UpA guidance — there is no published validated cut-off to cite.
- **QC-1.5** Checks never mutate the design and never recommend a specific recoding unless an upstream tool can be invoked with parameters to achieve it (QC-3.3, QC-4.3).
- **QC-1.6** The check set is invoked at two points where an assembled template exists: on the design record (pre-assembly) and on the assembled mRNA (post-assembly), so inserted Kozak bases and junction changes are evaluated as they will be ordered. The report labels which invocation produced each result and never merges the two into one status. If assembly did not run, only the design-record pass is reported and the gap is stated.
- **QC-1.7** Checks accept any `MrnaRecord` that satisfies the sequence contract, whether it came from a design or from assembly; this is what makes the post-assembly pass (QC-1.6) possible without a second implementation.

### Addition 1 — λ trade-off visualisation

- **QC-2.1** Where the adapter supports a λ sweep (LinearDesign), run a bounded sweep (configurable point count, default 8, with a pre-flight time estimate) and emit: `lambda_sweep.csv` (λ, MFE, CAI, GC, chosen flag) and `lambda_tradeoff.png`/`.svg`. The sweep is **ORF-scoped**: LinearDesign optimises the CDS only, so every plotted point is labelled CDS-only and must not be read as a whole-mRNA trade-off.
- **QC-2.2** Where no sweep exists, emit a cross-adapter trade-off plot (MFE vs CAI, one point per adapter, labelled, with region scope) instead of an empty figure.
- **QC-2.3** The chosen operating point is marked, and its selection rule is printed (`user-selected` in V1; no automatic knee-point heuristic).
- **QC-2.4** Plot output must be legible in the report at 100% zoom: axis units, adapter/λ labels, and a caption naming the tool that produced each series.
- **QC-2.5** Every MFE/diversity value names the folding engine that produced it (ViennaRNA or LinearFold), including the λ sweep's MFE column. Two folders' values are never merged into one series or ranked against each other: their energy models differ, so a cross-engine "lower MFE" is a change of ruler, not an improvement.

### Addition 2 — CpG / UpA analysis

- **QC-3.1** Report CpG and UpA counts, density per 100 nt, longest CpG/UpA run, and per-region breakdown (5′UTR, CDS, 3′UTR, poly(A)-excluded).
- **QC-3.2** Report thresholds as configurable, source-backed ranges — reference-derived where no validated cut-off exists (QC-1.8) — and mark `warn`/`fail` accordingly; the same metrics are reported for every engine so candidates are comparable.
- **QC-3.3** **This module measures and reports only.** Depletion happens, if at all, by selecting the constraint-based design engine (`dnachisel`, RD-2.8) with explicit CpG/UpA constraints at the *design* step — never by a recoding loop here. When such an engine ran, the report shows which constraints were applied and the before/after measurements, and states that constraint selection was the user's design decision, not a QC recommendation.
- **QC-3.4** Any synonymous-recoding loop written in this module is a spec violation, regardless of how simple it looks.

### Addition 3 — m1Ψ slippery-sequence and U-run analysis

- **QC-4.1** Scan for: U homopolymer runs ≥4, the slippery-heptamer class associated with −1 ribosomal frameshifting (U-rich run followed by a downstream stimulator motif; exact consensus patterns in `data/motifs/slippery.yaml` with citations), and report position, length, region, and distance from the CDS start.
- **QC-4.2** Report results per reading frame context, because a U-run's risk depends on where the ribosome is, not just its existence; the report must not imply a quantitative frameshift rate.
- **QC-4.3** Mitigation is out of scope for this module: it reports and warns only. Slippery-site avoidance, if wanted, is expressed as a forbidden-motif constraint on the constraint-based design engine (RD-2.8) at design time; the report then shows whether the engine satisfied it.
- **QC-4.4** The data file must record which modification context (m1Ψ-replaced uridine) each entry is justified for, and the report must state that the analysis is assumption-based, not measured frameshift efficiency.

### Addition 4 — Motif scan suite

- **QC-5.1** `data/motifs/library.yaml` is the single source of motifs; each entry has `id`, `name`, IUPAC pattern or regex, `regions`, `severity`, `source` (public database with version, or peer-reviewed citation), `notes`, and at least one positive and one negative fixture sequence.
- **QC-5.1a** Database-derived entries are imported as a **versioned snapshot committed to the repo**, never fetched live at run time. The import records the database name, version, retrieval date, and any filtering applied, so a check result can be reproduced a year later.
- **QC-5.2** V1 covers at minimum: AU-rich elements (ARED-Plus class), polyadenylation signals (PolyA_DB / PolyASite class), 5′ and 3′ splice-site-like motifs, Kozak-adjacent AUG contexts outside the intended start, G-quadruplex-prone G-runs (G4Hunter / QuadBase class), and RIG-I/IFN-associated motifs curated from primary literature because no database covers them. Every entry names its source class; a consensus string recalled from memory is not a source. Optional where a clean database exists: RNA-binding-protein motifs (ATtRACT / CISBP-RNA class).
- **QC-5.3** Scanning is overlap-aware (a motif may occur at every offset) and reports all hits with coordinates, not just the first.
- **QC-5.4** A motif entry without fixtures or citation fails validation at load time — the library cannot grow without evidence.
- **QC-5.5** Adding a motif is a data change plus fixtures; no code change, no new test file.

### Addition 5 — Kozak, signal peptide, and transmembrane checks

- **QC-6.1** Kozak: report the nucleotides at the −6..−1 and +4 positions relative to the start codon, the strength classification against the documented consensus, and the deviation; the reference table is data with a citation. Where assembly inserted or substituted Kozak nucleotides, the post-assembly pass (QC-1.6) reports the context actually ordered, and each row states which pass produced it.
- **QC-6.2** Signal peptide prediction uses **DeepSig** or **PEFT-SP**, both open-source and both selectable per step through the plugin contract (RD-6.*). Each is pinned, version-recorded, and cited in the report. A registration- or licence-gated predictor is deliberately excluded from the default path: it would leave most users with an unusable check, and an unusable check rendered as absence is worse than a different engine.
- **QC-6.2a** Transmembrane prediction is a separate engine under the plugin contract (RD-6.*) and may legitimately be unavailable: if no licensed predictor can be installed, the check stays `not_run` with its own reason (QC-6.3). The two checks never share a status or a `not_run` reason.
- **QC-6.3** If no licensed predictor is available on the runtime, both checks return `not_run` with the reason and the report shows the gap prominently; they never return `pass`.
- **QC-6.4** Predictor output is presented as prediction with its upstream confidence semantics preserved (no re-binning invented here), and the report links the protein-level prediction to the nucleotide design so the user understands the check is about the protein, not the codons.
- **QC-6.5** Contradictions between an upstream predictor's call and the user's declared annotation (e.g. user states a signal peptide, predictor finds none) are surfaced as `warn` with both claims, never auto-resolved.

### Addition 6 — Consolidated QC report

- **QC-7.1** One self-contained HTML file per run (no external CSS/JS/fonts, opens from the Colab file browser) plus `qc_summary.csv` with one row per check result.
- **QC-7.2** Report structure: run identity and provenance, headline warnings ordered by severity then region, per-addition sections, full result table with thresholds and citations, and a separate clearly-labelled section reserved for experimental-tier results (empty in V1).
- **QC-7.3** Every result shows: check id, region, status, observed value, threshold with `threshold_ref`, and the citation. A result without a citation is a render-time error.
- **QC-7.4** The report never presents a composite score or an automatic "recommended design". Cross-candidate comparison is a table; the decision is the user's.
- **QC-7.5** A fixed, non-dismissible disclaimer states: research use only; no clinical, regulatory, or wet-lab validation; predictions are not measurements.
- **QC-7.6** Report generation is deterministic: same inputs and data-file versions produce byte-identical HTML except for the run id/timestamp fields, which are isolated in one header block.

## Tech Stack

Python 3.11, Biopython (sequence handling), pandas, matplotlib (PNG/SVG), Jinja2 (HTML from a single template), PyYAML (data files). No sequence-design code, no new predictors.

## Commands

```bash
pytest tests/unit/qc -q
pytest tests/unit/qc/test_motif_library.py -q          # library validation + fixtures
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --qc-only
python -m mrna_design.report --run outputs/<run_id> --out /tmp/report.html
```

## Project Structure

```
mrna_design/qc/model.py            CheckResult, severity ordering, registry of checks
mrna_design/qc/lambda_tradeoff.py  addition 1
mrna_design/qc/cpg_upa.py          addition 2
mrna_design/qc/m1psi.py            addition 3
mrna_design/qc/motifs.py           addition 4 (scanner; library is data)
mrna_design/qc/kz_sp_tm.py         addition 5
mrna_design/report/render.py       addition 6 (Jinja2)
mrna_design/report/templates/qc.html.j2
data/motifs/library.yaml           motif entries + fixtures + citations
data/motifs/slippery.yaml
data/thresholds/qc.yaml            all numeric thresholds with citations
docs/qc-checks.md                  per-check rationale, assumptions, limitations
tests/unit/qc/                     one test module per addition + library validation
```

## Code Style

Checks are pure and return a value object; thresholds come from data:

```python
def scan_slippery(design: DesignResult, ref: QcReference) -> list[CheckResult]:
    """Report U-homopolymer and slippery-heptamer sites. Never edits the sequence."""
    hits = _scan(design.cds, ref.motifs["slippery"])
    return [
        CheckResult(
            id="slippery.u_run", addition=3, region="cds", status=_status(hit, ref),
            value=hit.length, unit="nt", threshold_ref=f"slippery.u_run.min_len@{ref.version}",
            message=..., evidence=hit.span,
        )
        for hit in hits
    ] or [_not_run("slippery.u_run", reason="region absent")]
```

Conventions: one module per addition; `CheckResult` construction only through helpers that demand `threshold_ref`; requirement IDs in test names; no `print`; data-file schema validated by pydantic at load.

## Testing Strategy

- **Unit per addition:** crafted inputs with known answers (a sequence with exactly three CpG sites; a U-run at a known offset; a motif with two overlapping hits); boundary cases at every threshold; `not_run` paths.
- **Library validation:** every motif entry has fixtures, citation, and passes its own positive/negative cases; an entry with a typo'd IUPAC code fails.
- **Report tests:** snapshot the HTML for a fixed run with timestamps normalised; assert every rendered result has a citation; assert the disclaimer is present; assert the experimental section is present but empty.
- **Cross-adapter:** the same check suite runs over every adapter's `DesignResult` from the golden run, proving the checks are contract-shaped rather than LinearDesign-shaped.
- **Determinism:** run the report twice, diff.
- Coverage ≥85% for `mrna_design/qc/` and `mrna_design/report/`; no test may assert a biological conclusion (e.g. "this design is safe") — only mechanism.

## Boundaries

- **Always:** source every threshold from a cited data file; keep checks pure and order-independent; report `not_run` honestly; label predictions as predictions; keep the disclaimer.
- **Ask first:** adding or changing a threshold; adding a motif to the library; adding a predictor dependency (licence review required); changing report structure or file names; changing severity semantics.
- **Never:** implement a recoding/mitigation algorithm; implement a signal-peptide, TM, or structure predictor; hide a `not_run` or an unavailable tool; emit a composite score or auto-recommendation; present QC as validation or a safety claim; assert a quantitative frameshift or immunogenicity rate that was not measured.

## Success Criteria

| # | Criterion | Verification |
|---|---|---|
| QC-SC1 | All six additions exist as pure functions covered by unit tests with known-answer fixtures | `pytest tests/unit/qc` |
| QC-SC2 | Every `CheckResult` carries a resolvable `threshold_ref`; rendering fails otherwise | Report test + validation test |
| QC-SC3 | Motif library fails to load if any entry lacks fixtures or citation | Library validation test |
| QC-SC4 | Report is self-contained, deterministic, and contains the fixed disclaimer | Snapshot + double-render diff + asset scan |
| QC-SC5 | Checks run unchanged against every adapter's result from the golden run | Cross-adapter test |
| QC-SC6 | Unavailable predictors produce `not_run` with reason, never `pass` | Injected-unavailability test |
| QC-SC7 | λ sweep and cross-adapter trade-off plots both render for the golden run, with labels and captions | Report snapshot + plot data assertions |

## Out of Scope (Deferred)

- CpG/UpA depletion by recoding — see Open Question 1; measurement + upstream-parameter re-run only in V1.
- Codon-pair / tRNA-pool analyses, codon harmonisation scoring — no proven adapter in V1 inventory; would be a new metric.
- Secondary-structure visualisation beyond the MFE/diversity numbers — ViennaRNA already reports; custom plotting is V2 polish.
- Immunogenicity or expression prediction — that is experimental-tier territory and stays there.
- PDF export — HTML plus CSV is sufficient and avoids a fragile rendering dependency in Colab.

## Open Questions

1. **Motif database selection and curation:** the DB classes are named in QC-5.2, but each import needs a decision — which release, which filters, and who signs off an entry. Snapshots are committed (QC-5.1a), so the cost is per-import, not per-run.
2. **Transmembrane predictor:** DeepSig and PEFT-SP settle the signal peptide and are signal-peptide-specific, so TM still needs an engine (Phobius, a DeepTMHMM API call, or another). Is `not_run` acceptable for V1, or is TM a must-have that justifies a server dependency?
3. **Reference panel for CpG/UpA:** which published vaccine sequences form the reference set, under what licence, and which percentile becomes the default warning line? This is the only defensible source for a "vaccine range" (QC-1.8).
4. **Splice-site strength:** consensus-motif scanning is data; a strength score (MaxEntScan class) is a predictor with its own licence and engine decision. Does V1 scan only, or add a scoring engine?
5. **Poly(A) reporting:** length and synthesis warnings are defined; is integrity (homopolymer/heterogeneity risk) worth reporting separately, or does that overstate what a sequence check can claim?
