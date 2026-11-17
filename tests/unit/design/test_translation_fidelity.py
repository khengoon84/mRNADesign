"""RD-3.4 translation-fidelity tests for the design contracts (T07).

The hard contract: retranslating ``cds`` with Biopython must reproduce the
input protein exactly, for every adapter, every run. A violation is a defect
in the adapter, never in the input — so ``validated()`` raises the typed
adapter-defect error and names the clause.
"""

import pytest
from Bio.Seq import Seq
from pydantic import ValidationError

from mrna_design.design.contracts import AdapterDefectError, DesignResult

MV_CDS = "ATGGTTTAA"  # ATG GTT TAA -> MV*
MVHLP_CDS = "ATGGTTCATCTGCCATAA"  # ATG GTT CAT CTG CCA TAA -> MVHLP*


def make_result(**overrides: object) -> DesignResult:
    """A valid CDS-only result for the protein 'MV'."""
    fields: dict[str, object] = {
        "protein": "MV",
        "cds": MV_CDS,
        "has_start": True,
        "has_stop": True,
        "region_bounds": {"cds": {"start": 0, "end": 9}},
        "adapter_id": "fixture",
        "tool_version": "1.0",
        "resolved_params": {},
    }
    fields.update(overrides)
    return DesignResult.model_validate(fields)


class TestTranslationFidelity:
    def test_biopython_agrees_with_the_recorded_codon_table(self) -> None:
        # Guard against the test itself drifting from the standard code.
        assert str(Seq(MV_CDS).translate()) == "MV*"
        assert str(Seq(MVHLP_CDS).translate()) == "MVHLP*"

    def test_a_faithful_result_passes(self) -> None:
        result = make_result()
        assert result.validated() is result

    def test_a_longer_faithful_result_passes(self) -> None:
        result = make_result(
            protein="MVHLP",
            cds=MVHLP_CDS,
            region_bounds={"cds": {"start": 0, "end": 18}},
        )
        assert result.validated() is result

    def test_a_single_wrong_codon_is_named(self) -> None:
        # GTT -> GGT encodes G instead of V: the adapter's defect, RD-3.4.
        result = make_result(cds="ATGGGTTAA")
        with pytest.raises(AdapterDefectError) as excinfo:
            result.validated()
        message = str(excinfo.value)
        assert "translation fidelity" in message
        assert "'MG'" in message  # the retranslation that failed
        assert "'MV'" in message  # the protein it failed to reproduce
        assert "never in the input" in message

    def test_result_protein_disagreeing_with_construction_protein(self) -> None:
        result = make_result(protein="MF")
        with pytest.raises(AdapterDefectError, match="translation fidelity"):
            result.validated()

    def test_broken_frame_skips_retranslation_but_still_fails(self) -> None:
        # A partial codon proves nothing; RD-3.3 records the frame defect and
        # no fidelity message is appended.
        result = make_result(cds="ATGGTTTAAG")
        with pytest.raises(AdapterDefectError) as excinfo:
            result.validated()
        assert "not a multiple of 3" in str(excinfo.value)
        assert "translation fidelity" not in str(excinfo.value)

    def test_validated_is_typed_as_the_adapter_defect_error(self) -> None:
        with pytest.raises(AdapterDefectError):
            make_result(cds="ATGTTTTAA").validated()


class TestNormalisationGuardsFidelity:
    def test_lowercased_cds_is_normalised_before_translation(self) -> None:
        result = make_result(cds=MV_CDS.lower())
        assert result.validated() is result

    def test_whitespace_inside_cds_is_normalised(self) -> None:
        result = make_result(cds="ATG GTT\nTAA")
        assert result.validated() is result

    def test_ambiguity_in_protein_cannot_reach_a_result(self) -> None:
        # X would make RD-3.4 unverifiable; normalisation rejects it upstream.
        with pytest.raises(ValidationError, match="ambiguity"):
            make_result(protein="XV")
