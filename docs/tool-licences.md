# Third-party licences and notices

**Status:** T03 seed surface, 2026-11-17. This file is the project's dependency notice surface
(`SPEC-notebook-shell.md` NS-3.8, `SPEC-rna-design.md` RD-2.7). It is **not** a licence for this
repository's code: that is MIT with the copyright holder line intentionally blank (`DECISIONS.md`
D-013), and no `LICENSE` file exists until T69 (`DECISIONS.md` D-016).

**Why this row set exists before the manifest.** `mrna_design/tools/manifest.yaml` lands at T11, so
T03 derives its rows from `SPEC-rna-design.md` RD-2.4, `mRNADesign.md` §Scope decisions, the gate
register in `tasks/plan.md`, and `pyproject.toml`. **From T11 this file is generated or validated
from that manifest** (`DECISIONS.md` D-021); every manifest dependency must have a row here and every
row must exist in the manifest. After T11, editing this file by hand is a defect, not a maintenance
chore.

**A missing row is a defect in this task, not evidence that no licence applies.** The set below is the
T03 seed set. It is not a claim that the list is complete for all future work.

---

## How to read the table

**Class** (`licence class`) is one of:

| Class | Meaning |
|---|---|
| `permissive` | Use, modification and redistribution permitted with attribution-style conditions only. |
| `research_only` | The terms restrict or exclude commercial use of the output. |
| `copyleft` | The terms permit commercial use but impose share-alike/source obligations on a distributed combination. |
| `conditional` | Commercial use is permitted subject to conditions that must be honoured in notices or redistribution (G27's folding-engine terms), or the data carries an unresolved use condition. |
| `unverified` | No licence decision exists yet: the gate is open, or the dependency has not been added. This is the honest state, never a synonym for `permissive`. |
| `excluded` | The dependency is not shipped, with the reason recorded. |

`conditional` and `unverified` extend the four classes named in the T03 task text; the reason is
recorded in `DECISIONS.md` D-021. The vocabulary exists so that a verified conditional licence and an
open question cannot be forced into `permissive`.

**`commercial_use`** is the machine-readable enum from `DECISIONS.md` D-019:
`permitted` / `conditional` / `contact-rights-holder` / `excluded`. It describes the commercial status
of output produced using the component. Where an engine has more than one component row (CodonBERT
code and weights), the engine-level status is the **conjunction** of its rows: `permitted` on the code
row does not make a `codonbert` run commercially usable while the weights row reads
`contact-rights-holder`.

**Imported or fetched.** *Imported* means the component is installed and loaded in-process.
*Fetched at run time* means bootstrap downloads the pinned upstream revision during the run; nothing is
vendored (`SPEC-notebook-shell.md` NS-3.6). *Distributed as data* means the files ship in the
repository and are read, not executed.

**Revision.** `unpinned — gate Gx` is a legitimate value. No revision is guessed: an open gate is a
fact the table records, not an omission to paper over.

---

## Dependency rows

| Component (adapter id where one exists) | Upstream / source | Revision | Licence as recorded | Class | `commercial_use` | Imported / fetched | Gate or note |
|---|---|---|---|---|---|---|---|
| `lineardesign` | LinearDesign (pinned upstream binary) | unpinned — gate G1 | Research use only; not for commercial use (RD-2.4). Verbatim terms and fetch permission recorded at T17 | `research_only` | `contact-rights-holder` | fetched at run time by bootstrap; whether the binary may be fetched at all is part of G1 | Opt-in engine (G25-B). Selection prints the responsibility notice (G26). No promise that a commercial licence exists |
| `codonbert` (code) | CodonBERT upstream code | unpinned — gate G2 | MIT (declared in RD-2.4; verified against the pinned revision at T18) | `permissive` | `permitted` | imported at run time after a pinned fetch | **Code only.** A `codonbert` run is not commercially usable while the weights row below is unresolved |
| `codonbert-weights` | CodonBERT model weights | unpinned — gate G2 | Not established; weights terms may differ from the code licence | `unverified` | `contact-rights-holder` | fetched at run time from the pinned, licence-cleared source with a checksum (T36) | G2 is the critical path for the default engine's commercial claim (D-017) |
| `custom` | CUSTOM (`hexavier/CUSTOM`) | unpinned — gate G2 (exact revision recorded at T18) | GPL-3.0 (verified at source 2026-11-16: `LICENSE`, `setup.py`, PyPI metadata; D-018) | `copyleft` | `conditional` | fetched at run time only by installing the opt-in `mrna-design-custom` package; the MIT core never imports it | Opt-in; requires a tissue target and has no invented default. Copyleft consequence stated below |
| `mrna-design-custom` | This project's separate adapter package (`packages/mrna-design-custom/`) | not yet written — T35 | GPL-3.0 declared in package metadata; the `LICENSE` file itself is written at T69 | `copyleft` | `conditional` | imported only when the user installs the package | The MIT core does not import it, and a core test asserts that (D-018) |
| `gemorna` | GEMORNA | unpinned — gate G3 | Not yet verified | `unverified` | `contact-rights-holder` | fetched at run time (GPU) | Opt-in; unavailable-with-reason on CPU |
| `optimus5` | Optimus 5-Prime | unpinned — gate G3 | Not yet verified | `unverified` | `contact-rights-holder` | fetched at run time (install method confirmed at T19) | Opt-in 5′UTR engine; never the default (D-014) |
| `viennarna-qc` | ViennaRNA | unpinned — gate G4 | Custom licence, verified at source 2026-11-16 (`tbi.univie.ac.at/RNA/license.html`; repository `license.txt`): research, educational and commercial use and modification permitted, conditional on no-fee redistribution, visible credit, and contacting the authors before embedding in a commercial product (G27, D-017) | `conditional` | `conditional` | imported at run time (Python bindings) | Conditions accepted for V1's free distribution. Notice obligations below |
| `linearfold` | LinearFold | unpinned — gate G4 | Custom terms in the same style, GitHub `Other/NOASSERTION`: research, educational and commercial use, no-fee redistribution, paper citation (G27, D-017) | `conditional` | `conditional` | fetched at run time | Exact terms recorded verbatim at T20 |
| `dnachisel` | DNAChisel | unpinned — gate G4 | MIT declared upstream; not yet verified against a pinned revision | `unverified` | `contact-rights-holder` | imported at run time | Opt-in constraint engine only (D-007) |
| `parade` | PARADE (`autosome-ru/parade`) | unpinned — pin and verification at T41A | MIT declared upstream (D-010); not yet re-verified at the pinned revision | `unverified` | `contact-rights-holder` | fetched at run time (upstream is conda-only; the pip re-pin is T41A) | Experimental, opt-in only; never default or fallback (D-010) |
| `deepsig` | DeepSig | unpinned — gate G5 | Not yet verified | `unverified` | `contact-rights-holder` | fetched at run time | Signal-peptide predictor (D-009) |
| `peft-sp` | PEFT-SP | unpinned — gate G5 | Not yet verified; upstream `environment.yml` is conda-based (T21) | `unverified` | `contact-rights-holder` | fetched at run time | Signal-peptide predictor (D-009) |
| `signalp` | SignalP | not applicable | Proprietary, licence-gated | `excluded` | `excluded` | not imported or fetched | Excluded by D-009 and QC-6.2: a licence-gated predictor would leave most users with a permanent `not_run` |
| `tm-predictor` | Transmembrane options assessed at T21 (Phobius, DeepTMHMM API, other) | not selected — G10 deferred, agreed | Not selected, therefore not verified | `unverified` | `contact-rights-holder` | not fetched: no engine chosen | TM ships `not_run` with its own reason (QC-6.2a); no placeholder engine |
| `reference-utr-library` | Vaccine UTR sequence data (BNT162b2, mRNA-1273 and the other entries curated at T24) | not yet curated — T24 | Per-entry primary-source citation; sequences may be covered by patent claims, and this project's MIT grant does not extend to them (RD-2.7) | `conditional` | `contact-rights-holder` | distributed as data in `data/utrs/`, read not executed | Entries are *reference, not optimised*; research-use caveat per entry (G8, D-014) |
| `python` | CPython | 3.11.16 | PSF-2.0 (`LICENSE.txt` shipped with the interpreter; checked 2026-11-17) | `permissive` | `permitted` | runtime | Pinned by `requires-python = ">=3.11,<3.12"`; Colab drift is an NS-3.5 risk |
| `pyyaml` | PyYAML | 6.0.3 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (config loading and the T04 fixture test) | Pinned in `pyproject.toml` |
| `pydantic` | pydantic | 2.14.3 | MIT (`License-Expression: MIT` in installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (validated `RunConfig` schema, NS-2.1) | Pinned in `pyproject.toml` at T05 |
| `pydantic-core` | pydantic-core | 2.50.4 | MIT (`License-Expression: MIT` in installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (transitive dependency of pydantic) | Revision follows pydantic 2.14.3; re-check when pydantic is re-pinned |
| `annotated-types` | annotated-types | 0.8.0 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (transitive dependency of pydantic) | Revision follows pydantic 2.14.3 |
| `typing-inspection` | typing-inspection | 0.4.5 | MIT (`License-Expression: MIT` in installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (transitive dependency of pydantic) | Revision follows pydantic 2.14.3 |
| `biopython` | Biopython | 1.88 | `LicenseRef-Biopython-License-Agreement` (installed distribution metadata, checked 2026-11-17) — BSD-style, free for commercial use | `permissive` | `permitted` | imported (translation fidelity in the design contracts, T07/RD-3.4; FASTA/GenBank IO later) | Pinned in `pyproject.toml` at T07 |
| `numpy` | numpy | 2.4.6 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (transitive dependency of Biopython) | Revision follows Biopython 1.88; re-check when Biopython is re-pinned |
| `pandas` | pandas | not yet added — T28 | Not yet verified at the pin | `unverified` | `contact-rights-holder` | imported once added | Comparison tables |
| `numpy` | numpy | 2.4.6 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | imported (transitive dependency of Biopython) | Revision follows Biopython 1.88; re-check when Biopython is re-pinned; its own first importer will pin it if ever used directly |
| `jinja2` | Jinja2 | not yet added — T52 | Not yet verified at the pin | `unverified` | `contact-rights-holder` | imported once added | Single self-contained QC report template |
| `qc-plot-library` | Not selected | not selected — T50 | Not selected, therefore not verified | `unverified` | `contact-rights-holder` | imported once selected | QC-2.4 requires legible PNG/SVG; no spec names the library |
| `construct-map-library` | Not selected | not selected — gate G16 | Not selected, therefore not verified | `unverified` | `contact-rights-holder` | imported once selected | T61 renders the construct map through a pinned library |
| `hatchling` | hatchling | 1.33.0 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | build time only | Build backend; not part of the run bundle |
| `ruff` | ruff | 0.17.5 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | developer tool, not distributed | Lint and format gate |
| `mypy` | mypy | 2.4.1 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | developer tool, not distributed | Type gate |
| `pytest` | pytest | 9.2.0 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | developer tool, not distributed | Test runner |
| `pytest-cov` | pytest-cov | 7.1.0 | MIT (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | developer tool, not distributed | Coverage plugin |
| `coverage` | coverage.py | 7.17.3 | Apache-2.0 (installed distribution metadata, checked 2026-11-17) | `permissive` | `permitted` | developer tool, not distributed | Transitive dependency of pytest-cov |
| `jupyter-nbconvert` | Jupyter nbconvert | not yet added — T15 | Not yet verified at the pin | `unverified` | `contact-rights-holder` | developer tool, not distributed | Executes the notebook smoke test |
| `google-colab` | Google Colab hosted runtime | service, not versioned like a package | Google Colab Terms of Service; a service contract, not a software licence granted to this project, and not reviewed in T03 | `unverified` | `contact-rights-holder` | hosted platform at run time | No V1 gate covers Colab's service terms. Users running the notebook in Colab are subject to them; this project makes no claim about them |

---

## Uniform commercial-use notice (D-019)

No document, notice, report footer or README promises or implies that a commercial licence exists or
is obtainable for a restricted dependency. Every row above whose `commercial_use` is
`contact-rights-holder` or `conditional` carries exactly this sentence at the point of use:

> *Commercial use of this engine's output is not granted by this project. Contact the rights holder
> before using the output commercially.*

Rows carrying it: `lineardesign`, `codonbert-weights`, `custom`, `mrna-design-custom`, `gemorna`,
`optimus5`, `viennarna-qc`, `linearfold`, `dnachisel`, `parade`, `deepsig`, `peft-sp`,
`tm-predictor`, `reference-utr-library`, `biopython`, `pandas`, `numpy`, `jinja2`,
`qc-plot-library`, `construct-map-library`, `jupyter-nbconvert`, `google-colab`.

For `custom` and `mrna-design-custom` the sentence is required because the terms are conditional; the
binding condition is the copyleft obligation stated below, not doubt about whether GPL-3.0 permits
commercial use. For `reference-utr-library`, "this engine's output" is read as the designed mRNA that
contains the reference sequence. For `google-colab`, the row is a hosted service rather than an engine
or library; the sentence is included because its service terms have not been reviewed here, not
because Colab's terms are asserted to restrict the output.

Permitted phrasings stop there. The following are forbidden by D-019: "licence available", "can be
obtained", "may be available", any fee, term or vendor stated as certain, and any sentence that turns
"contact the rights holder" into an assurance that contact will produce a licence.

---

## The file does not relicense upstream code

This file is a notice surface. It **does not relicense** any upstream code, model weights, sequence
data or service, and it grants the reader no rights beyond the upstream terms. The upstream licence
text governs each component; where this table summarises terms, the summary is for orientation and the
verbatim text recorded at the owning gate (T17–T21, T41A) prevails.

The MIT grant applies only to code written in this repository. It does not extend to upstream tools,
CodonBERT or PARADE weights, reference UTR sequences, Colab, or any other row above.

## Copyleft changes the distributed combination, not just its notice

A `copyleft` dependency changes the licence of the **distributed combination**, not merely the notice
text attached to it. If GPL-3.0 code were imported into code distributed as part of the MIT core, the
combined distribution would have to be GPL-3.0; a notice line saying "this component is GPL-3.0" would
not preserve the MIT position for the combination.

The project avoids that with the boundary recorded in `DECISIONS.md` D-018: CUSTOM ships only as the
separate GPL-3.0 package `mrna-design-custom`, which depends on the MIT core. The MIT core never
imports it, a core test asserts that, and the notebook lists `custom` as unavailable-with-reason
naming the package until a user installs it. A user who installs it receives a GPL-3.0 package; the
obligations attach to that package and to any distribution of a combination containing it.

Any future `copyleft` dependency must be handled the same way or the project licence must change. The
`copyleft` class in this table is a warning, not a solution.

---

## Gates that will change these rows

| Gate | Rows it decides | What changes |
|---|---|---|
| **G1** (T17) | `lineardesign` | Verbatim terms, fetch/redistribution permission, final class confirmation |
| **G2** (T18) | `codonbert`, `codonbert-weights`, `custom` | Code and weights recorded separately; exact CUSTOM revision; the default engine's commercial claim becomes decidable |
| **G3** (T19) | `gemorna`, `optimus5` | Licences at the pinned revision; install method and weight availability |
| **G4** (T20) | `viennarna-qc`, `linearfold`, `dnachisel` | Verbatim folding-engine terms already verified under G27; pins and DNAChisel verification close the rows |
| **G5** (T21) | `deepsig`, `peft-sp` | Licences, install method and runtime class |
| **G10** (deferred, agreed) | `tm-predictor` | Stays unselected; `not_run` with a reason, not a placeholder engine |
| **G16** (T61) | `construct-map-library` | Pinned library chosen and recorded |
| **G9** (T25) | vendor profile data | Adds a row only if a cited synthesis-guidance source requires attribution |
| **T41A** | `parade` | Pin, weights source/hash and licence re-verified at the pinned revision |
| **T11** | all rows | This file becomes manifest-generated/validated; derivation from prose ends |

Rows with no gate (`python`, the pinned Python tooling, the planned runtime libraries, the QC plot
library, `google-colab`) close when the task that first imports or uses them records the pin. Until
then they stay `unverified`.

---

## Boundaries and test data

The golden protein is UniProtKB P0DTC2 residues 319–541; the test backbone is NCBI M77789.2 (pUC19).
Both are test fixtures only. Their provenance and the pUC19 licence note are recorded in
`docs/fixtures.md`; neither is a runtime input or part of a distributed run bundle, and V1 ships no
bundled backbones (`SPEC-dna-construct.md` DC-3.2).

## Maintenance

- Before T11: a change to this file needs a gate decision or a task that added a dependency, recorded
  in `DECISIONS.md`.
- From T11: the file is generated/validated from `mrna_design/tools/manifest.yaml`. A test fails when a
  manifest entry has no notice line, and an entry here without a manifest row is equally a defect.
- At T69: this table becomes `THIRD-PARTY-NOTICES.md`, generated from the manifest, published with the
  `LICENSE` file. No claim in `docs/licence-claims.md` may be published until then.
