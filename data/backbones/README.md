# `data/backbones/` — intentionally empty

**V1 ships no backbones.** `SPEC-dna-construct.md` DC-3.2 makes this explicit,
and DC-SC9 asserts it: no default or bundled backbone can enter a construct.

Why:

- A backbone is a **material** choice (`SPEC-notebook-shell.md` NS-1.2a). It
  changes what a user would order, so the tool may not invent one.
- With `backbone_path` absent, the construct resolves to a linear PCR-derived
  IVT template and the plasmid branch is recorded `skipped` with a recovery hint
  naming the field (`DC-3.0`, `NS-5.4`). That is a complete, valid run.
- Shipping a "convenience" vector would silently decide a cloning strategy,
  a selection marker and a vendor's catalogue item on the user's behalf.

A user supplies their own backbone via `backbone_path` (GenBank or FASTA,
DC-3.1). The test backbone at `tests/fixtures/backbones/puc19.gb` is a
**test-only** fixture for the plasmid branch; it is not a runtime default, is
never offered as one, and is not copied into run outputs.

This directory stays empty in V1. If a future release ever bundles a backbone,
it needs a licence record, a provenance entry and an explicit decision, not a
file dropped in here.
