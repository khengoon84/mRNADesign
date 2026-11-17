"""The data contracts shared by every design adapter (T07, RD-3.*).

``DesignRequest`` is what an adapter receives; ``DesignResult`` is what it must
return; ``MrnaRecord`` is the exported whole-mRNA view consumed by downstream
construct building (RD-4.3). All three are pydantic models with ``extra="forbid"``:
a misspelled field must fail loudly rather than vanish from the manifest.

The contracts are frozen-then-additive (AD-2): T07 lands the full V1 shape —
``region_bounds``, per-region provenance (RD-3.7) and the junction map — before
anything consumes it. Widening them is an *Ask first* boundary, so a change to
one of these models is a specification change recorded in ``docs/contracts.md``,
never a cleanup.

Conventions fixed here and documented in ``docs/contracts.md``:

- Protein normalisation (RD-3.1): whitespace is removed, letters are uppercased,
  one trailing ``*`` terminator is removed; every remaining letter must be one of
  the 20 unambiguous amino-acid codes. Ambiguity codes (``B J X Z U O``) are
  rejected because RD-3.4 requires Biopython retranslation to reproduce the
  protein exactly, which an ambiguous letter would make unverifiable.
- ``Span`` and ``RegionBounds`` are integers in fixed bases — spans are 1-based
  inclusive (UniProt convention), region bounds are 0-based half-open, so
  ``record.sequence[start:end]`` returns exactly that region.
- Nucleotide regions carry **DNA** (A/C/G/T): every upstream engine designs in
  DNA codons and ``dna-construct`` consumes DNA, so no adapter should have to
  transcribe between alphabets at the contract boundary. ``U`` is rejected with
  a pointed message instead of being silently converted.
- ``validated()`` enforces RD-3.3 and RD-3.4 and raises a typed
  adapter-defect error (RD-6.5): a violation is a defect in the adapter,
  never in the input.
"""

from __future__ import annotations

import re
from typing import Any

from Bio.Seq import Seq
from pydantic import BaseModel, ConfigDict, Field, model_validator

CANONICAL_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
"""The 20 unambiguous standard amino-acid codes (RD-3.1 normalised protein)."""

DNA_ALPHABET = frozenset("ACGT")
"""The nucleotide alphabet for every region: contracts carry DNA (see below)."""

START_CODON = "ATG"
STOP_CODONS = frozenset({"TAA", "TAG", "TGA"})
"""The standard-code start and stop codons (RD-3.3, table 1)."""

CDS = "cds"
UTR5 = "utr5"
UTR3 = "utr3"
REGIONS = (UTR5, CDS, UTR3)
"""Export order (RD-4.3): 5'UTR, then CDS, then 3'UTR."""

AMBIGUOUS_CODES = frozenset("BJXZUO")
"""IUPAC ambiguity and rare codes; rejected, not silently guessed."""

STOP_STAR = "*"
"""The translation terminator, allowed only as an optional final character."""


def normalise_protein(raw: str) -> str:
    """Normalise a user- or tool-supplied protein string (RD-3.1).

    Strips whitespace (pasted FASTA bodies wrap lines), uppercases, removes one
    trailing ``*`` terminator, and rejects anything that is not an unambiguous
    amino-acid code with a message naming the offending letter and position.
    """
    letters = "".join(raw.split()).upper()
    if letters.endswith(STOP_STAR):
        letters = letters[:-1]
    if not letters:
        raise ValueError(
            "protein: sequence is empty after normalisation; "
            "an empty protein cannot be designed from",
        )
    for position, letter in enumerate(letters, start=1):
        if letter not in CANONICAL_AMINO_ACIDS:
            hint = ""
            if letter in AMBIGUOUS_CODES:
                hint = (
                    f" ({letter} is an ambiguity code; RD-3.4 requires exact "
                    "Biopython retranslation, which ambiguity makes unverifiable)"
                )
            raise ValueError(
                f"protein: letter {position} is '{letter}', which is not one of "
                f"the 20 unambiguous amino-acid codes{hint}",
            )
    return letters


class Span(BaseModel):
    """A 1-based inclusive span over a sequence (UniProt/NCBI convention)."""

    model_config = ConfigDict(extra="forbid")

    start: int = Field(ge=1, description="First residue of the span, 1-based.")
    end: int = Field(description="Last residue of the span, inclusive.")

    @model_validator(mode="after")
    def _ordered(self) -> Span:
        if self.end < self.start:
            raise ValueError(
                f"span: end ({self.end}) must not be before start ({self.start})",
            )
        return self


class GcBounds(BaseModel):
    """Target GC fraction bounds passed through to engines that accept them.

    An engine that cannot honour them reports so per RD-2.8; it never relaxes
    them silently.
    """

    model_config = ConfigDict(extra="forbid")

    minimum: float = Field(ge=0.0, le=1.0)
    maximum: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _ordered(self) -> GcBounds:
        if self.maximum < self.minimum:
            raise ValueError(
                f"gc_bounds: maximum ({self.maximum}) must not be below minimum ({self.minimum})",
            )
        return self


class DesignRequest(BaseModel):
    """What every design adapter receives (RD-3.1).

    No field exists that an adapter would have to interpret biologically on its
    own: the protein is already normalised, spans and bounds are explicit
    numbers, and per-adapter payloads are passed through verbatim — the adapter
    that accepts them owns their meaning (RD-2.8).
    """

    model_config = ConfigDict(extra="forbid")

    protein: str = Field(description="Normalised protein (RD-3.1; see normalise_protein).")
    signal_peptide_span: Span | None = Field(
        default=None,
        description="Optional 1-based inclusive span over protein (RD-3.1).",
    )
    seed: int | None = Field(
        default=None,
        description=(
            "Optional resolved seed for the run (RD-3.6); None means the "
            "adapter has no seed to apply."
        ),
    )
    host_codon_usage_profile: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Identifier of a codon-usage profile shipped as data (AD-5), never an inline table."
        ),
    )
    gc_bounds: GcBounds | None = Field(
        default=None,
        description=(
            "Target GC fraction bounds for engines that accept GC hints (RD-3.1, RD-2.8)."
        ),
    )
    constraint_hints: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Adapter id -> constraint hints, passed through verbatim; only "
            "adapters whose upstream tool accepts them may use them (RD-3.1)."
        ),
    )
    adapter_params: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Adapter id -> documented parameters, passed through verbatim; "
            "the resolved values land in DesignResult.resolved_params (RD-3.2)."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_protein(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("protein"), str):
            data = {**data, "protein": normalise_protein(data["protein"])}
        return data

    @model_validator(mode="after")
    def _span_within_protein(self) -> DesignRequest:
        if self.signal_peptide_span is not None:
            length = len(self.protein)
            if self.signal_peptide_span.end > length:
                raise ValueError(
                    "signal_peptide_span: end "
                    f"({self.signal_peptide_span.end}) is beyond the protein "
                    f"length ({length})",
                )
        return self


def normalise_region(raw: str, field: str) -> str:
    """Normalise a nucleotide region: strip whitespace, uppercase, DNA letters.

    The contracts carry DNA (A/C/G/T), because every upstream engine designs in
    DNA codons and ``dna-construct`` consumes DNA; ``U`` is rejected with a
    pointed message so an adapter handing back RNA must transcribe back first.
    """
    letters = "".join(raw.split()).upper()
    if not letters:
        raise ValueError(f"{field}: region is empty after normalisation")
    for position, letter in enumerate(letters, start=1):
        if letter not in DNA_ALPHABET:
            if letter == "U":
                raise ValueError(
                    f"{field}: letter {position} is 'U'; the contracts carry DNA "
                    "(A/C/G/T) — write the RNA sequence as its DNA form",
                )
            raise ValueError(
                f"{field}: letter {position} is '{letter}', which is not a DNA letter (A/C/G/T)",
            )
    return letters


class RegionBounds(BaseModel):
    """A region's coordinates within the exported record.

    0-based half-open: ``record.sequence[bounds.start:bounds.end]`` returns
    exactly the region, which is what the RD-SC6 round-trip test asserts.
    Adjacent regions share a coordinate — that shared coordinate *is* the
    junction (RD-4.3).
    """

    model_config = ConfigDict(extra="forbid")

    start: int = Field(ge=0, description="0-based inclusive start within the record.")
    end: int = Field(ge=0, description="Exclusive end within the record.")

    @model_validator(mode="after")
    def _ordered(self) -> RegionBounds:
        if self.end < self.start:
            raise ValueError(
                f"region bounds: end ({self.end}) must not be before start ({self.start})",
            )
        return self


class AdapterWarning(BaseModel):
    """One warning from an upstream tool, verbatim and attributed (RD-4.4)."""

    model_config = ConfigDict(extra="forbid")

    tool: str = Field(min_length=1, description="The tool the warning came from.")
    message: str = Field(min_length=1, description="The warning text, unaltered.")


class AdapterDefectError(ValueError):
    """A ``DesignResult`` violated RD-3.3/RD-3.4 (RD-6.5).

    The defect belongs to the adapter, never to the input: ``messages`` name
    each violated clause so the report can state the plugin defect precisely.
    """

    def __init__(self, messages: list[str]) -> None:
        self.messages = tuple(messages)
        super().__init__("; ".join(self.messages))

    def __str__(self) -> str:
        return "; ".join(self.messages)


class DesignResult(BaseModel):
    """What every design adapter returns (RD-3.2).

    ``has_start``/``has_stop``/``region_bounds`` are the adapter's *explicit*
    declarations about its own output; :meth:`validated` cross-checks them
    against the sequences, so a misdeclared result is a plugin defect (RD-6.5)
    rather than something downstream silently guesses.
    """

    model_config = ConfigDict(extra="forbid")

    protein: str = Field(description="The protein this design encodes (RD-3.2).")
    cds: str = Field(description="The designed coding sequence, DNA (RD-3.2).")
    has_start: bool = Field(description="Declared: cds begins with a start codon (RD-3.3).")
    has_stop: bool = Field(
        description="Declared: cds ends with a terminating stop codon (RD-3.3).",
    )
    region_bounds: dict[str, RegionBounds] = Field(
        description=(
            "Declared bounds per carried region, contiguous in export order "
            "(RD-3.2, RD-4.3). Exactly the present regions: 'cds' always; "
            "'utr5'/'utr3' when the result carries them."
        ),
    )
    utr5: str | None = Field(default=None, description="Optional 5'UTR, DNA (RD-3.2).")
    utr3: str | None = Field(default=None, description="Optional 3'UTR, DNA (RD-3.2).")
    adapter_id: str = Field(min_length=1, description="The designing adapter (RD-3.2).")
    tool_version: str = Field(min_length=1, description="Upstream tool version (RD-3.2).")
    resolved_params: dict[str, Any] = Field(
        description="The parameters actually applied, for the manifest (RD-3.2, RD-3.6).",
    )
    seed: int | None = Field(
        default=None,
        description="The seed this adapter ran with (RD-3.6); None when seedless.",
    )
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Metrics computed by the upstream tool or a named, cited helper "
            "(RD-3.8); keys are documented in docs/metrics.md, never invented."
        ),
    )
    warnings: tuple[AdapterWarning, ...] = Field(
        default_factory=tuple,
        description="Upstream warnings, verbatim and attributed (RD-4.4).",
    )
    provenance: dict[str, str] = Field(
        default_factory=dict,
        description="Tool provenance (source URL, weights revision, ...), manifest-recorded.",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_sequences(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if isinstance(data.get("protein"), str):
                data["protein"] = normalise_protein(data["protein"])
            for field in (CDS, UTR5, UTR3):
                if isinstance(data.get(field), str):
                    data[field] = normalise_region(data[field], field)
        return data

    @property
    def _carried_regions(self) -> dict[str, str]:
        carried: dict[str, str] = {CDS: self.cds}
        if self.utr5 is not None:
            carried[UTR5] = self.utr5
        if self.utr3 is not None:
            carried[UTR3] = self.utr3
        return carried

    def validated(self) -> DesignResult:
        """Return ``self`` after enforcing RD-3.3 and RD-3.4.

        RD-3.3 is the FASTA-checkable structure: start codon present, in frame
        (length exactly ``3*n``), a terminating stop codon, no internal stops,
        and the ``has_start``/``has_stop``/``region_bounds`` declarations true.
        RD-3.4 is the hard translation contract: retranslating ``cds`` with
        Biopython (standard genetic code) must reproduce the input protein
        exactly, once its single terminating ``*`` is stripped.

        Every failure is an :class:`AdapterDefectError` listing each violated
        clause — the adapter is broken, the input is not (RD-6.5).
        """
        defects: list[str] = []
        self._check_region_bounds(defects)
        self._check_start_stop(defects)
        self._check_frame_and_stops(defects)
        self._check_translation(defects)
        if defects:
            raise AdapterDefectError(defects)
        return self

    def _check_region_bounds(self, defects: list[str]) -> None:
        """The declared bounds must cover exactly the carried regions, contiguous
        in export order (RD-3.2, RD-4.3)."""
        declared = dict(self.region_bounds)
        for region in REGIONS:
            present = region in self._carried_regions
            declared_present = region in declared
            if present and not declared_present:
                defects.append(
                    f"region_bounds: region '{region}' is present but not declared",
                )
            elif declared_present and not present:
                defects.append(
                    f"region_bounds: region '{region}' is declared but absent from the result",
                )
        offset = 0
        for region in REGIONS:
            sequence = self._carried_regions.get(region)
            if sequence is None:
                continue
            expected = RegionBounds(start=offset, end=offset + len(sequence))
            bounds = declared.get(region)
            if bounds is not None and bounds != expected:
                defects.append(
                    f"region_bounds: '{region}' declares {bounds.start}..{bounds.end} "
                    f"but its place in export order is {expected.start}..{expected.end}",
                )
            offset += len(sequence)

    def _check_start_stop(self, defects: list[str]) -> None:
        """RD-3.3: start codon present, terminating stop present, declarations true."""
        if not self.cds.startswith(START_CODON):
            defects.append(
                f"cds: no start codon ({START_CODON}) at position 1 (RD-3.3)",
            )
        if self.cds[-3:] not in STOP_CODONS:
            defects.append(
                f"cds: no terminating stop codon ({'|'.join(sorted(STOP_CODONS))}) "
                "at the 3' end (RD-3.3)",
            )
        if self.has_start != self.cds.startswith(START_CODON):
            defects.append(
                f"has_start: declared {self.has_start} but the sequence "
                f"{'has' if self.cds.startswith(START_CODON) else 'has no'} "
                f"{START_CODON} at position 1 (RD-3.3)",
            )
        if self.has_stop != (self.cds[-3:] in STOP_CODONS):
            defects.append(
                f"has_stop: declared {self.has_stop} but the sequence "
                f"{'has' if self.cds[-3:] in STOP_CODONS else 'has no'} "
                "terminating stop codon (RD-3.3)",
            )

    def _check_frame_and_stops(self, defects: list[str]) -> None:
        """RD-3.3: length exactly 3*n, no internal stop codon."""
        length = len(self.cds)
        if length % 3 != 0:
            defects.append(
                f"cds: length {length} is not a multiple of 3 (RD-3.3)",
            )
        codons = [self.cds[i : i + 3] for i in range(0, length - length % 3, 3)]
        internal = [
            f"{position}:{codon}"
            for position, codon in enumerate(codons[:-1], start=1)
            if codon in STOP_CODONS
        ]
        if internal:
            defects.append(
                f"cds: internal stop codon(s) at {', '.join(internal)} (RD-3.3)",
            )

    def _check_translation(self, defects: list[str]) -> None:
        """RD-3.4: Biopython retranslation reproduces the protein exactly.

        The standard genetic code (table 1) is the V1 contract; a host with a
        non-standard code would need its own specification first. A broken
        frame is recorded by RD-3.3's check, so this check only runs when the
        frame is whole — retranslating a partial codon proves nothing.
        """
        length = len(self.cds)
        if length % 3 != 0:
            return
        translated = str(Seq(self.cds).translate(to_stop=False))
        if translated.endswith(STOP_STAR):
            translated = translated[:-1]
        else:
            defects.append(
                f"cds: translation ends without a terminating '{STOP_STAR}' (RD-3.4)",
            )
        if translated != self.protein:
            defects.append(
                "translation fidelity: Biopython retranslation of cds is "
                f"'{translated}', which does not reproduce the input protein "
                f"'{self.protein}' — the defect is in the adapter, never in "
                "the input (RD-3.4)",
            )


PROVENANCE_PATTERN = r"(adapter:[a-z0-9_-]+|user|reference:[a-z0-9_-]+)"
"""The three admissible provenance forms (RD-3.7)."""


def _is_provenance_token(value: str) -> bool:
    return re.fullmatch(PROVENANCE_PATTERN, value) is not None


class Junction(BaseModel):
    """One explicit junction coordinate between two adjacent regions (RD-4.3).

    ``position`` is the shared 0-based coordinate: ``sequence[:position]`` ends
    ``left`` exactly where ``sequence[position:]`` begins ``right``.
    """

    model_config = ConfigDict(extra="forbid")

    left: str = Field(description="Region id on the 5' side.")
    right: str = Field(description="Region id on the 3' side.")
    position: int = Field(ge=0, description="Shared 0-based coordinate.")


class MrnaRecord(BaseModel):
    """The exported whole-mRNA view (RD-4.3).

    ``sequence`` is 5'UTR + CDS + 3'UTR concatenated in that order, with the
    junction coordinates recorded as ``region_bounds`` so QC can report
    per-region results and ``dna-construct`` can consume the record without
    re-deriving where the CDS starts. Every present region records its own
    source (RD-3.7): a record built from more than one engine is normal, not a
    special case. Absent regions (RD-2.6) are simply not carried — the record
    never invents a placeholder sequence.
    """

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(description="The full record, DNA, in export order (RD-4.3).")
    region_bounds: dict[str, RegionBounds] = Field(
        description=(
            "Explicit junction coordinates per present region (RD-4.3): "
            "'cds' always; 'utr5'/'utr3' when the record carries them."
        ),
    )
    provenance: dict[str, str] = Field(
        description=(
            "Region -> source token, one of adapter:<id> | user | "
            "reference:<id> (RD-3.7), for exactly the present regions."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_sequence(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("sequence"), str):
            data = {**data, "sequence": normalise_region(data["sequence"], "sequence")}
        return data

    @model_validator(mode="after")
    def _check_structure(self) -> MrnaRecord:
        """The present regions must tile ``sequence`` exactly, in export order,
        with provenance for each (RD-3.7, RD-4.3)."""
        present = [region for region in REGIONS if region in self.region_bounds]
        if CDS not in present:
            raise ValueError(
                "region_bounds: a record without a CDS is not an mRNA record (RD-4.3)",
            )
        if set(self.provenance) != set(self.region_bounds):
            unprovenanced = sorted(set(self.region_bounds) - set(self.provenance))
            unsourced = sorted(set(self.provenance) - set(self.region_bounds))
            detail = []
            if unprovenanced:
                detail.append(
                    f"missing provenance for {', '.join(unprovenanced)}",
                )
            if unsourced:
                detail.append(
                    f"provenance for absent region(s) {', '.join(unsourced)}",
                )
            raise ValueError(
                "provenance: must name exactly the present regions (RD-3.7) — " + "; ".join(detail),
            )
        for region, source in self.provenance.items():
            if not _is_provenance_token(source):
                raise ValueError(
                    f"provenance['{region}']: '{source}' is not one of "
                    "adapter:<id> | user | reference:<id> (RD-3.7)",
                )
        offset = 0
        for region in present:
            bounds = self.region_bounds[region]
            if bounds.start != offset or bounds.end == bounds.start:
                raise ValueError(
                    f"region_bounds: '{region}' declares {bounds.start}..{bounds.end} "
                    "but the present regions must tile the sequence exactly in "
                    "export order (RD-4.3)",
                )
            offset = bounds.end
        if offset != len(self.sequence):
            raise ValueError(
                f"region_bounds: regions tile {offset} nt but the sequence is "
                f"{len(self.sequence)} nt (RD-4.3)",
            )
        return self

    @property
    def junctions(self) -> tuple[Junction, ...]:
        """The explicit junction map (RD-4.3): one entry between each pair of
        adjacent present regions, empty for a single-region record."""
        present = [region for region in REGIONS if region in self.region_bounds]
        lefts, rights = present[:-1], present[1:]
        return tuple(
            Junction(left=left, right=right, position=self.region_bounds[left].end)
            for left, right in zip(lefts, rights, strict=True)
        )

    def region(self, name: str) -> str:
        """One region's sequence, reconstructed from the junction map (RD-SC6)."""
        bounds = self.region_bounds.get(name)
        if bounds is None:
            raise KeyError(
                f"region '{name}' is not carried by this record; present: "
                f"{sorted(self.region_bounds)}",
            )
        return self.sequence[bounds.start : bounds.end]

    @classmethod
    def from_design(
        cls,
        result: DesignResult,
        utr5: str | None = None,
        utr5_source: str | None = None,
        utr3: str | None = None,
        utr3_source: str | None = None,
    ) -> MrnaRecord:
        """Export a ``DesignResult`` as a record (RD-4.3).

        The CDS always comes from ``result`` with provenance
        ``adapter:<result.adapter_id>``. Each UTR is taken explicitly (with a
        provenance token of ``user``, ``reference:<id>`` or another engine's
        ``adapter:<id>`` — a multi-engine record is normal, RD-3.7), falling
        back to the result's own UTR when no explicit one is given. A region
        with no source at all is absent, never a placeholder (RD-2.6).
        """
        sources: dict[str, str] = {}
        pieces: dict[str, str] = {CDS: result.cds}
        sources[CDS] = f"adapter:{result.adapter_id}"
        for name, explicit, explicit_source, fallback in (
            (UTR5, utr5, utr5_source, result.utr5),
            (UTR3, utr3, utr3_source, result.utr3),
        ):
            if explicit is not None and explicit_source is None:
                raise ValueError(
                    f"{name}_source: required when {name} is supplied (RD-3.7)",
                )
            if explicit_source is not None and explicit is None:
                raise ValueError(
                    f"{name}_source: given but {name} was not supplied",
                )
            if explicit is not None:
                pieces[name] = normalise_region(explicit, name)
                sources[name] = explicit_source or ""
            elif fallback is not None:
                pieces[name] = fallback
                sources[name] = f"adapter:{result.adapter_id}"
        bounds: dict[str, RegionBounds] = {}
        offset = 0
        for region in REGIONS:
            if region not in pieces:
                continue
            length = len(pieces[region])
            bounds[region] = RegionBounds(start=offset, end=offset + length)
            offset += length
        return cls(
            sequence="".join(pieces[region] for region in REGIONS if region in pieces),
            region_bounds=bounds,
            provenance={region: sources[region] for region in bounds},
        )
