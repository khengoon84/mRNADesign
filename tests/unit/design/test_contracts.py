"""Contract tests for ``mrna_design.design.contracts`` (T07).

Slice 1 covered ``DesignRequest`` (RD-3.1); slice 2 covers ``DesignResult`` and
``validated()``'s RD-3.3 structural checks. The translation-fidelity slice
(RD-3.4) lives in ``test_translation_fidelity.py``, and the ``MrnaRecord``
round-trip (RD-SC6) extends this module.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from mrna_design.design.contracts import (
    CDS,
    UTR3,
    UTR5,
    AdapterDefectError,
    DesignRequest,
    DesignResult,
    GcBounds,
    MrnaRecord,
    normalise_protein,
)

MV_CDS = "ATGGTTTAA"  # ATG GTT TAA -> MV*

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def golden_protein() -> str:
    """The golden RBD protein, header line dropped (T04 fixture)."""
    lines = (FIXTURES / "golden_rbd" / "protein.fasta").read_text().splitlines()
    return "".join(line for line in lines if not line.startswith(">"))


def make_request(**overrides: object) -> DesignRequest:
    """A valid minimal request, overridden per test."""
    fields: dict[str, object] = {"protein": golden_protein()}
    fields.update(overrides)
    return DesignRequest.model_validate(fields)


class TestProteinNormalisation:
    def test_fixture_protein_is_accepted(self) -> None:
        request = make_request()
        assert request.protein == golden_protein()
        assert len(request.protein) == 223  # RBD residues 319-541 inclusive

    def test_whitespace_and_case_are_normalised(self) -> None:
        wrapped = "  rvqpte\nsIVRFPNIT\tNLCPFGEVFNATRFASVYAWNRKRISNCVADYS  \n"
        assert normalise_protein(wrapped) == "RVQPTESIVRFPNITNLCPFGEVFNATRFASVYAWNRKRISNCVADYS"

    def test_trailing_stop_star_is_removed(self) -> None:
        assert normalise_protein("MVF*") == "MVF"

    def test_interior_stop_star_is_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"letter 2 is '\*'"):
            normalise_protein("M*F")

    def test_unknown_letter_is_rejected_with_position(self) -> None:
        with pytest.raises(ValueError, match=r"letter 3 is '1'") as excinfo:
            normalise_protein("MV1F")
        assert "20 unambiguous amino-acid codes" in str(excinfo.value)

    @pytest.mark.parametrize(
        ("letter", "expected"),
        [
            ("B", "ambiguity code"),
            ("J", "ambiguity code"),
            ("X", "ambiguity code"),
            ("Z", "ambiguity code"),
            ("U", "ambiguity code"),
            ("O", "ambiguity code"),
        ],
    )
    def test_ambiguity_codes_are_rejected_with_reason(self, letter: str, expected: str) -> None:
        with pytest.raises(ValueError, match=expected):
            normalise_protein(f"MV{letter}F")

    def test_empty_protein_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            normalise_protein("   \n*")

    def test_normalisation_runs_inside_the_model(self) -> None:
        request = make_request(protein=golden_protein().lower())
        assert request.protein == golden_protein()


class TestDesignRequestFields:
    def test_unknown_fields_are_rejected(self) -> None:
        with pytest.raises(ValidationError, match="unused_peptide"):
            make_request(unused_peptide="MKT")

    def test_signal_peptide_span_is_accepted(self) -> None:
        request = make_request(signal_peptide_span={"start": 1, "end": 10})
        assert request.signal_peptide_span is not None
        assert request.signal_peptide_span.start == 1
        assert request.signal_peptide_span.end == 10

    def test_span_beyond_the_protein_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="beyond the protein length"):
            make_request(signal_peptide_span={"start": 1, "end": 10_000})

    @pytest.mark.parametrize("span", [{"start": 0, "end": 3}, {"start": 5, "end": 3}])
    def test_malformed_spans_are_rejected(self, span: dict[str, int]) -> None:
        with pytest.raises(ValidationError):
            make_request(signal_peptide_span=span)

    def test_optional_fields_default_to_none_or_empty(self) -> None:
        request = make_request()
        assert request.signal_peptide_span is None
        assert request.seed is None
        assert request.host_codon_usage_profile is None
        assert request.gc_bounds is None
        assert request.constraint_hints == {}
        assert request.adapter_params == {}

    def test_adapter_payloads_pass_through_verbatim(self) -> None:
        request = make_request(
            constraint_hints={"dnachisel": {"avoid_patterns": ["BsaI"]}},
            adapter_params={"lineardesign": {"n_candidates": 3}},
        )
        assert request.constraint_hints == {"dnachisel": {"avoid_patterns": ["BsaI"]}}
        assert request.adapter_params == {"lineardesign": {"n_candidates": 3}}

    def test_seed_and_profile_are_carried(self) -> None:
        request = make_request(seed=7, host_codon_usage_profile="human_heavy")
        assert request.seed == 7
        assert request.host_codon_usage_profile == "human_heavy"


class TestGcBounds:
    def test_valid_bounds_are_accepted(self) -> None:
        bounds = GcBounds.model_validate({"minimum": 0.4, "maximum": 0.6})
        assert bounds.minimum == 0.4
        assert bounds.maximum == 0.6

    def test_inverted_bounds_are_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must not be below"):
            GcBounds.model_validate({"minimum": 0.6, "maximum": 0.4})

    @pytest.mark.parametrize("field", ["minimum", "maximum"])
    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_out_of_range_bounds_are_rejected(self, field: str, value: float) -> None:
        payload = {"minimum": 0.4, "maximum": 0.6}
        payload[field] = value
        with pytest.raises(ValidationError):
            GcBounds.model_validate(payload)


def make_result(**overrides: object) -> DesignResult:
    """A valid CDS-only result for the two-residue protein 'MV'."""
    fields: dict[str, object] = {
        "protein": "MV",
        "cds": "ATGGTTTAA",
        "has_start": True,
        "has_stop": True,
        "region_bounds": {"cds": {"start": 0, "end": 9}},
        "adapter_id": "fixture",
        "tool_version": "1.0",
        "resolved_params": {},
    }
    fields.update(overrides)
    return DesignResult.model_validate(fields)


class TestDesignResultConstruction:
    def test_nucleotide_regions_are_normalised(self) -> None:
        result = make_result(cds=" atg gtt taa ", protein=" mv ")
        assert result.cds == "ATGGTTTAA"
        assert result.protein == "MV"

    def test_rna_u_is_rejected_with_transcription_message(self) -> None:
        with pytest.raises(ValidationError, match="the contracts carry DNA"):
            make_result(cds="AUGGUUUAA")

    def test_non_dna_letter_is_rejected_with_position(self) -> None:
        with pytest.raises(ValidationError, match=r"letter 2 is 'N'"):
            make_result(cds="ANTGGTTTAA")

    def test_empty_region_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            make_result(cds="   ")

    def test_unknown_fields_are_rejected(self) -> None:
        with pytest.raises(ValidationError, match="rank"):
            make_result(rank=1)

    def test_minimal_fields_and_defaults(self) -> None:
        result = make_result()
        assert result.utr5 is None
        assert result.utr3 is None
        assert result.seed is None
        assert result.metrics == {}
        assert result.warnings == ()
        assert result.provenance == {}

    def test_warnings_are_verbatim_and_attributed(self) -> None:
        result = make_result(
            warnings=[{"tool": "lineardesign", "message": "GC low at codon 7"}],
        )
        assert result.warnings[0].model_dump() == {
            "tool": "lineardesign",
            "message": "GC low at codon 7",
        }


class TestValidatedRd33:
    def test_a_valid_result_passes_and_returns_itself(self) -> None:
        result = make_result()
        assert result.validated() is result

    def test_a_result_with_utrs_passes(self) -> None:
        result = make_result(
            utr5="GGG",
            utr3="CCCAAA",
            region_bounds={
                "utr5": {"start": 0, "end": 3},
                "cds": {"start": 3, "end": 12},
                "utr3": {"start": 12, "end": 18},
            },
        )
        assert result.validated() is result

    def test_length_not_a_multiple_of_three(self) -> None:
        with pytest.raises(AdapterDefectError, match="not a multiple of 3"):
            make_result(cds="ATGGTTTAAG").validated()

    def test_missing_start_codon(self) -> None:
        with pytest.raises(AdapterDefectError, match="no start codon"):
            make_result(cds="GTGGTTTAA").validated()

    def test_missing_terminating_stop(self) -> None:
        with pytest.raises(AdapterDefectError, match="no terminating stop codon"):
            make_result(cds="ATGGTT").validated()

    def test_internal_stop_is_named_by_position(self) -> None:
        with pytest.raises(AdapterDefectError, match="internal stop codon\\(s\\) at 2:TAG"):
            make_result(cds="ATGTAGTTTTAA").validated()

    def test_false_has_start_declaration(self) -> None:
        with pytest.raises(AdapterDefectError, match="has_start: declared False"):
            make_result(has_start=False).validated()

    def test_false_has_stop_declaration(self) -> None:
        with pytest.raises(AdapterDefectError, match="has_stop: declared False"):
            make_result(has_stop=False).validated()

    def test_all_structural_defects_are_listed_at_once(self) -> None:
        result = make_result(cds="GTGGTT", has_start=False, has_stop=False)
        with pytest.raises(AdapterDefectError) as excinfo:
            result.validated()
        text = str(excinfo.value)
        assert "no start codon" in text
        assert "no terminating stop codon" in text


class TestRegionBounds:
    def test_present_region_without_declaration_is_a_defect(self) -> None:
        result = make_result(
            utr5="GGG",
            region_bounds={"cds": {"start": 0, "end": 9}},
        )
        with pytest.raises(AdapterDefectError, match="'utr5' is present but not declared"):
            result.validated()

    def test_absent_region_with_declaration_is_a_defect(self) -> None:
        result = make_result(
            region_bounds={"cds": {"start": 0, "end": 9}, "utr3": {"start": 9, "end": 12}},
        )
        with pytest.raises(AdapterDefectError, match="'utr3' is declared but absent"):
            result.validated()

    def test_wrong_offsets_are_a_defect(self) -> None:
        result = make_result(region_bounds={"cds": {"start": 1, "end": 10}})
        with pytest.raises(AdapterDefectError, match="place in export order is 0..9"):
            result.validated()

    def test_inverted_bounds_are_rejected_at_construction(self) -> None:
        with pytest.raises(ValidationError, match="must not be before start"):
            make_result(region_bounds={"cds": {"start": 9, "end": 0}})


class TestAdapterDefectError:
    def test_messages_are_individually_recoverable(self) -> None:
        error = AdapterDefectError(["one", "two"])
        assert error.messages == ("one", "two")
        assert str(error) == "one; two"


class TestMrnaRecord:
    """RD-3.7 per-region provenance, RD-4.3 junction map, RD-SC6 round-trip."""

    def test_cds_only_record_round_trips(self) -> None:
        result = make_result()
        record = MrnaRecord.from_design(result)
        assert record.sequence == "ATGGTTTAA"
        assert record.region_bounds["cds"].model_dump() == {"start": 0, "end": 9}
        assert record.provenance == {"cds": "adapter:fixture"}
        assert record.junctions == ()  # nothing to join in a single-region record

    def test_multi_engine_record_is_normal(self) -> None:
        result = make_result()
        record = MrnaRecord.from_design(
            result,
            utr5="GGCAT",  # a UTR library entry travels in its DNA form (see docs/contracts.md)
            utr5_source="user",
            utr3="CAT",
            utr3_source="reference:bnt162b2_utr",
        )
        assert record.provenance == {
            "utr5": "user",
            "cds": "adapter:fixture",
            "utr3": "reference:bnt162b2_utr",
        }
        assert record.region_bounds["utr5"].model_dump() == {"start": 0, "end": 5}
        assert record.region_bounds["cds"].model_dump() == {"start": 5, "end": 14}
        assert record.region_bounds["utr3"].model_dump() == {"start": 14, "end": 17}

    def test_explicit_junction_map_coordinates(self) -> None:
        result = make_result(utr5="GGG")
        record = MrnaRecord.from_design(
            result,
            utr3="CCC",
            utr3_source="user",
        )
        junctions = [(j.left, j.right, j.position) for j in record.junctions]
        assert junctions == [("utr5", "cds", 3), ("cds", "utr3", 12)]

    def test_rd_sc6_round_trip_reconstructs_each_region_exactly(self) -> None:
        utr5, utr3 = "GGCACGT", "CCC"
        result = make_result(utr5=utr5)
        record = MrnaRecord.from_design(
            result,
            utr5=utr5,  # re-supplied explicitly to exercise the normalisation path
            utr5_source="adapter:optimus5",
            utr3=utr3,
            utr3_source="reference:human_beta_globin",
        )
        assert record.region(UTR5) == utr5
        assert record.region(CDS) == MV_CDS
        assert record.region(UTR3) == utr3
        # And the junction coordinates alone rebuild the pieces:
        cuts = [0] + [j.position for j in record.junctions] + [len(record.sequence)]
        slices = [
            record.sequence[start:end] for start, end in zip(cuts[:-1], cuts[1:], strict=True)
        ]
        assert slices == [utr5, MV_CDS, utr3]

    def test_junction_is_a_shared_coordinate_between_adjacent_regions(self) -> None:
        record = MrnaRecord.from_design(
            make_result(utr5="GGG"),
            utr3="CCC",
            utr3_source="user",
        )
        junction = record.junctions[1]
        assert junction.model_dump() == {"left": "cds", "right": "utr3", "position": 12}
        assert record.sequence[: junction.position].endswith(MV_CDS)
        assert record.sequence[junction.position :] == "CCC"

    def test_absent_utrs_are_absent_not_invented(self) -> None:
        record = MrnaRecord.from_design(make_result())
        assert "utr5" not in record.region_bounds
        assert "utr3" not in record.region_bounds
        with pytest.raises(KeyError, match="utr5"):
            record.region("utr5")

    def test_source_required_with_supplied_utr(self) -> None:
        with pytest.raises(ValueError, match="utr5_source: required"):
            MrnaRecord.from_design(make_result(), utr5="GGG")

    def test_source_without_sequence_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="utr3_source: given but"):
            MrnaRecord.from_design(make_result(), utr3_source="user")

    def test_falls_back_to_the_result_own_utr(self) -> None:
        result = make_result(utr5="GGG")
        record = MrnaRecord.from_design(result)
        assert record.region(UTR5) == "GGG"
        assert record.provenance["utr5"] == "adapter:fixture"

    def test_record_without_a_cds_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="without a CDS"):
            MrnaRecord.model_validate(
                {
                    "sequence": "GGG",
                    "region_bounds": {"utr5": {"start": 0, "end": 3}},
                    "provenance": {"utr5": "user"},
                },
            )

    def test_provenance_must_match_present_regions(self) -> None:
        with pytest.raises(ValidationError, match="missing provenance for cds"):
            MrnaRecord.model_validate(
                {
                    "sequence": "ATGGTTTAA",
                    "region_bounds": {"cds": {"start": 0, "end": 9}},
                    "provenance": {},
                },
            )
        with pytest.raises(ValidationError, match="provenance for absent region"):
            MrnaRecord.model_validate(
                {
                    "sequence": "ATGGTTTAA",
                    "region_bounds": {"cds": {"start": 0, "end": 9}},
                    "provenance": {"cds": "adapter:fixture", "utr5": "user"},
                },
            )

    @pytest.mark.parametrize("token", ["optimus5", "adapter:", "reference:", "USER"])
    def test_malformed_provenance_tokens_are_rejected(self, token: str) -> None:
        with pytest.raises(ValidationError, match="not one of"):
            MrnaRecord.model_validate(
                {
                    "sequence": "ATGGTTTAA",
                    "region_bounds": {"cds": {"start": 0, "end": 9}},
                    "provenance": {"cds": token},
                },
            )

    def test_regions_must_tile_the_sequence_exactly(self) -> None:
        with pytest.raises(ValidationError, match="RD-4.3"):
            MrnaRecord.model_validate(
                {
                    "sequence": "ATGGTTTAAGGG",  # 12 nt but bounds claim 9
                    "region_bounds": {"cds": {"start": 0, "end": 9}},
                    "provenance": {"cds": "adapter:fixture"},
                },
            )
        with pytest.raises(ValidationError, match="RD-4.3"):
            MrnaRecord.model_validate(
                {
                    "sequence": "ATGGTTTAA",
                    "region_bounds": {
                        "cds": {"start": 3, "end": 12},  # gap at the 5' end
                    },
                    "provenance": {"cds": "adapter:fixture"},
                },
            )
