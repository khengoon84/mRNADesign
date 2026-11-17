# Fixtures — provenance, boundaries and hashes

The golden case is one protein and one test backbone, pinned so every module's
regression suite compares like with like. Fixture data is an **immutable input**:
changing the golden protein or the backbone is an *Ask first* change
(`SPEC-rna-design.md` §Boundaries of autonomy), and requires a new entry here
plus a `DECISIONS.md` note.

`tests/unit/test_fixtures.py` asserts the hashes below against the files on
disk. A mismatch is a failure, not a warning.

## Frozen files

| File | SHA-256 |
|---|---|
| `tests/fixtures/golden_rbd/protein.fasta` | `93a3ce7dcce4f068975f5d20fa101be483fef156fafb2d0c3707ccd10b957b48` |
| `tests/fixtures/backbones/puc19.gb` | `14b0b5ba06c7e24e0e2c2205c63f58155c17ea74e3ec5806243aba87e8394c22` |

`tests/fixtures/golden_rbd.yaml` is **not** hash-frozen: it is a configuration
fixture validated against `RunConfig` (T05) by
`tests/unit/test_config_schema.py`, with its `default_adapters` placeholder
filled at T40. Its protein string is compared to `protein.fasta` on every test
run, so the two cannot drift.

## Golden protein — SARS-CoV-2 spike receptor-binding domain

| Field | Value |
|---|---|
| File | `tests/fixtures/golden_rbd/protein.fasta` |
| Source | UniProtKB **P0DTC2** (`SPIKE_SARS2`, *Severe acute respiratory syndrome coronavirus 2*, Wuhan-Hu-1) |
| Entry status | reviewed (Swiss-Prot), entry version **32**, sequence version **1**, last annotation update 2026-11-04 |
| Residues | **319–541**, 1-based inclusive, **223 aa** |
| Definition | UniProt feature `Region 319..541 — Receptor-binding domain (RBD)` |
| Retrieved | 2026-11-17 from `https://rest.uniprot.org/uniprotkb/P0DTC2.json` |
| Sequence ends | starts `RVQPTESIVR`, ends `NKCVNF` |

**Why this span.** 319–541 is UniProt's own RBD annotation, so the boundary is
citable and machine-checkable rather than chosen here. The same entry annotates
adjacent constructs: `Domain 334..527` (BetaCoV S1-CTD, the structured core) and
`Region 437..508` (the receptor-binding motif). Those are narrower definitions,
not better ones, and trimming to either would be a scientific choice this task
is not entitled to make. If a construct-specific span is ever needed, it becomes
a **new** golden case rather than an edit to this one.

The fixture is the mature domain only: no signal peptide, no purification tag,
no linker. Adding any of those would change the protein the optimiser sees, so
they are a caller's decision, not a fixture default.

## Test backbone — pUC19

| Field | Value |
|---|---|
| File | `tests/fixtures/backbones/puc19.gb` |
| Record | NCBI Nucleotide **M77789.2**, "Cloning vector pUC19, complete sequence" |
| Length / topology | **2,686 bp**, circular |
| Retrieved | 2026-11-17 via NCBI E-utilities `efetch` (`rettype=gb`) |
| Published source | Yanisch-Perron, Vieira & Messing, *Gene* 33:103–119 (1985); Norrander, Kempe & Messing, *Gene* 26:101–106 (1983) |
| Licence note | Treated as licence-free for test use on the owner's instruction (2026-11-17). The NCBI record carries no separate licence statement; it is stored verbatim, used only as a test fixture, and is **not** a runtime backbone or part of any distributed run bundle. |

The stored file is the unmodified GenBank text, header included, so the hash is
reproducible from the accession and version above.

`data/backbones/README.md` records the separate rule that V1 **ships no bundled
backbones** (`SPEC-dna-construct.md` DC-3.2): a user-supplied `backbone_path` is
the only way a plasmid template is produced. This fixture exists to test the
plasmid branch, not to offer a default.

## Golden configuration fixture

`tests/fixtures/golden_rbd.yaml` parses as a `RunConfig` (T05):

- `protein_sequence` is the 223-aa domain above, inlined so a headless run needs
  no path resolution.
- `backbone_path: null` — absent, so the declared result is a linear PCR
  template and the plasmid branch is a skip with a recovery hint (DC-3.0).
- `default_adapters: null` — the real set is decided at T40 (G25-B: `codonbert`
  CDS + reference UTRs). `null` means *not encoded yet*, never *run nothing*.

## Adding a fixture

A new fixture is only legitimate if it is additive: a new file, a new row in the
table above, a citation, and a test. Editing an existing frozen file is a
breaking change to every snapshot downstream and needs a recorded decision.
