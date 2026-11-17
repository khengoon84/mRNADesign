# Design contracts — `mrna_design.design.contracts`

This document is the prose mirror of the models in
`mrna_design/design/contracts.py` (T07, `SPEC-rna-design.md` RD-3.*). The two must
agree; a change to either is a specification change, not a cleanup, and is
recorded in `DECISIONS.md` (AD-2 — contracts are frozen-then-additive).

## Why these models exist first

T07 lands the full V1 shape — `region_bounds`, per-region provenance (RD-3.7)
and the junction map (RD-4.3) — before anything consumes it (AD-2). Widening
them later is an *Ask first* boundary, so the design cost is paid once.
`DesignResult.validated()` runs for every engine, including third-party ones
(RD-6.5), and a plugin that returns an invalid result is rejected and reported
as a plugin defect, never as a bad input.

## `DesignRequest` (RD-3.1)

What an adapter receives. Normalisation is owned here so an adapter never has to
interpret biology on its own.

| Field | Type | Rule |
| --- | --- | --- |
| `protein` | `str` | Normalised: whitespace removed, uppercased, one trailing `*` removed, every letter one of the 20 unambiguous codes. Ambiguity codes (`B J X Z U O`) are rejected — RD-3.4 requires exact Biopython retranslation. |
| `signal_peptide_span` | `Span \| None` | 1-based inclusive (`start`..`end`) over `protein`; `end` must not exceed the protein length. |
| `seed` | `int \| None` | Optional resolved seed (RD-3.6). `None` means the adapter has no seed to apply. |
| `host_codon_usage_profile` | `str \| None` | Identifier of a codon-usage profile shipped as data (AD-5), never an inline table. |
| `gc_bounds` | `GcBounds \| None` | Target GC fraction bounds in `[0, 1]` with `maximum >= minimum`. |
| `constraint_hints` | `dict[str, dict[str, Any]]` | Adapter id -> hints, passed through verbatim; only adapters whose upstream tool accepts them may use them (RD-3.1, RD-2.8). |
| `adapter_params` | `dict[str, dict[str, Any]]` | Adapter id -> documented parameters; resolved values land in `DesignResult.resolved_params` (RD-3.2). |

Unknown keys are rejected (`extra="forbid"`). Validation failures are field-level
messages, never a traceback (NS-2.2).

## `DesignResult` (RD-3.2)

What an adapter returns.

| Field | Type | Rule |
| --- | --- | --- |
| `protein` | `str` | The protein this design encodes (normalised). |
| `cds` | `str` | The designed coding sequence, **DNA** (`A/C/G/T`). |
| `has_start` | `bool` | Declared: `cds` begins with `ATG`. |
| `has_stop` | `bool` | Declared: `cds` ends with `TAA`/`TAG`/`TGA`. |
| `region_bounds` | `dict[str, RegionBounds]` | Declared bounds per carried region, contiguous in export order. Keys are exactly the present regions: `cds` always; `utr5`/`utr3` when the result carries them. |
| `utr5` | `str \| None` | Optional 5'UTR, DNA. |
| `utr3` | `str \| None` | Optional 3'UTR, DNA. |
| `adapter_id` | `str` | The designing adapter. |
| `tool_version` | `str` | Upstream tool version. |
| `resolved_params` | `dict[str, Any]` | The parameters actually applied. |
| `seed` | `int \| None` | The seed this adapter ran with (RD-3.6). |
| `metrics` | `dict[str, float]` | Metrics computed by the upstream tool or a named, cited helper (RD-3.8); keys are documented in `docs/metrics.md`. |
| `warnings` | `tuple[AdapterWarning, ...]` | Upstream warnings, verbatim and tool-attributed (RD-4.4). |
| `provenance` | `dict[str, str]` | Tool provenance (source URL, weights revision, ...), manifest-recorded. |

### `validated()` (RD-3.3, RD-3.4)

Enforces, raising a typed `AdapterDefectError` listing every violated clause:

- RD-3.3 — start codon present (`ATG`), in frame (`len(cds) % 3 == 0`), a
  terminating stop (`TAA`/`TAG`/`TGA`), no internal stop codons, and the
  declared `has_start`/`has_stop`/`region_bounds` match the sequences.
- RD-3.4 — Biopython retranslation of `cds` under the standard genetic code
  (table 1) reproduces the input protein exactly (one terminating `*`
  stripped). A violation is a defect in the adapter, never in the input.

The standard genetic code is the V1 contract; a host with a non-standard code
would need its own specification first. Retranslation only runs when the frame is
whole — retranslating a partial codon proves nothing.

## `MrnaRecord` (RD-3.7, RD-4.3)

The exported whole-mRNA view: `5'UTR + CDS + 3'UTR` concatenated in that
order, with an explicit junction map, for downstream construct building. Absent
regions (RD-2.6) are simply not carried — the record never invents a
placeholder sequence.

| Field | Type | Rule |
| --- | --- | --- |
| `sequence` | `str` | The full record, DNA, in export order. |
| `region_bounds` | `dict[str, RegionBounds]` | Explicit per-region coordinates; present regions must tile `sequence` exactly in export order. |
| `provenance` | `dict[str, str]` | Region -> source token, for exactly the present regions. |

Per-region provenance (RD-3.7) takes one of three forms:

- `adapter:<id>` — produced by that adapter,
- `user` — pasted by the user,
- `reference:<id>` — taken from the cited reference-UTR library (RD-4.1c).

A record built from more than one engine is normal, not a special case; the
report names the source of each region.

### Junction map (RD-4.3)

`region_bounds` are 0-based half-open, so
`record.sequence[bounds.start:bounds.end]` returns exactly the region (RD-SC6).
Adjacent regions share a coordinate — that shared coordinate *is* the junction.
`MrnaRecord.junctions` returns one `Junction(left, right, position)` between
each pair of adjacent present regions; `MrnaRecord.region(name)` reconstructs a
region's sequence from the map.

## Conventions

- **Protein normalisation** (RD-3.1): whitespace removed, uppercased, one
  trailing `*` removed; ambiguity codes rejected.
- **Nucleotide alphabet** (DNA, `A/C/G/T`): every upstream engine designs in
  DNA codons and `dna-construct` consumes DNA, so no adapter transcribes
  between alphabets at the contract boundary. `U` is rejected with a pointed
  message instead of being silently converted.
- **Spans vs bounds**: `Span` is 1-based inclusive (UniProt convention) for
  `DesignRequest.signal_peptide_span`; `RegionBounds` is 0-based half-open for
  everything that slices a sequence.
- **Standard genetic code** (table 1) is the V1 contract for `validated()`.
- **Biopython** is the retranslation engine (RD-3.4); it is a dependency of
  this module, not of any adapter.

## Coverage

T07's verify gate is `pytest --cov=mrna_design.design.contracts --cov-fail-under=95`
against `tests/unit/design/`.
EOF
echo done