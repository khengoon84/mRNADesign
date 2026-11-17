"""T05: `RunConfig` implements the approved field taxonomy (NS-1.2a).

The tests pin the three classes, the conditional requiredness (G20), the
no-material-default rule (G19/DC-3.0), the declarative defaults that make a
run reproducible (NS-2.3), and the field-level error surface (NS-2.2). The
taxonomy is also recorded in `docs/config-fields.md`; a drift test at the end
keeps the prose and the code from disagreeing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from mrna_design.config import (
    DEFAULT_REPORT_TITLE,
    DEFAULT_SEED,
    ConfigValidationError,
    FieldClass,
    RunConfig,
    parse_config,
)

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "fixtures" / "golden_rbd.yaml"
CONFIG_FIELDS = ROOT / "docs" / "config-fields.md"


def _design(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"protein_sequence": "MKV", "run_modules": ["design", "construct"]}
    payload.update(overrides)
    return payload


def _messages(payload: dict[str, Any]) -> list[str]:
    with pytest.raises(ConfigValidationError) as excinfo:
        parse_config(payload)
    return list(excinfo.value.messages)


def test_default_path_needs_only_a_protein() -> None:
    """NS-1.2/NS-SC7: Run all with only the sequence entered is valid."""
    config = RunConfig(protein_sequence="MKV")

    assert config.run_modules == ["design", "construct"]
    assert config.template_type == "pcr"
    assert config.construct_source == "codonbert"  # G25-B, RD-4.1b delta
    assert config.seed == DEFAULT_SEED
    assert config.report_title == DEFAULT_REPORT_TITLE
    assert config.backbone_path is None
    assert config.poly_a_length is None
    assert config.default_adapters is None


def test_module_two_only_run_requires_sequence_input() -> None:
    """NS-1.7/DC-1.1: no design step, so a sequence is the required input."""
    config = parse_config({"run_modules": ["construct"], "sequence_input": "AUGGUU"})
    assert config.protein_sequence is None

    messages = _messages({"run_modules": ["construct"]})
    assert messages == [
        "sequence_input: required when run_modules does not include 'design' (NS-1.7, DC-1.1)"
    ]


def test_design_run_requires_protein_sequence() -> None:
    """G20: the protein is required exactly when the design module runs."""
    messages = _messages({"run_modules": ["design"]})
    assert any(
        message.startswith("protein_sequence: required when run_modules includes 'design'")
        for message in messages
    )


def test_blank_sequences_are_rejected_with_a_field_message() -> None:
    messages = _messages(_design(protein_sequence="   \n"))
    assert any(message.startswith("protein_sequence: must not be empty") for message in messages)


def test_run_modules_are_validated() -> None:
    assert any(
        message.startswith("run_modules: List should have at least 1 item")
        for message in _messages(_design(run_modules=[]))
    )
    assert any(
        "must not repeat a module" in message
        for message in _messages(_design(run_modules=["design", "design"]))
    )
    assert any(
        message.startswith("run_modules.1:")
        for message in _messages(_design(run_modules=["design", "qc"]))
    )


def test_unknown_fields_are_rejected_rather_than_dropped() -> None:
    """NS-2.3: a misspelled field must not vanish from the manifest."""
    messages = _messages(_design(protein_sequnce="MKV"))
    assert messages == ["protein_sequnce: Extra inputs are not permitted"]


def test_backbone_is_the_only_material_field_and_has_no_value_default() -> None:
    material = [spec for spec in RunConfig.field_specs() if spec.field_class is FieldClass.MATERIAL]

    assert [spec.name for spec in material] == ["backbone_path"]
    assert material[0].default is None
    assert material[0].has_default is True  # optional at the pipeline level
    assert RunConfig(protein_sequence="MKV").backbone_path is None


def test_plasmid_is_unreachable_without_a_supplied_backbone() -> None:
    """DC-3.0: no backbone is invented and plasmid is never guessed."""
    messages = _messages(_design(template_type="plasmid"))
    assert any(
        message.startswith("backbone_path: required for template_type='plasmid'")
        for message in messages
    )


def test_supplied_backbone_with_pcr_template_is_not_silently_ignored() -> None:
    messages = _messages(_design(backbone_path="tests/fixtures/backbones/puc19.gb"))
    assert any(
        message.startswith("template_type: a backbone_path was supplied") for message in messages
    )


def test_blank_backbone_path_is_a_field_error() -> None:
    messages = _messages(_design(template_type="plasmid", backbone_path="   "))
    assert any(message.startswith("backbone_path: must not be empty") for message in messages)


def test_plasmid_with_a_backbone_is_valid() -> None:
    config = parse_config(
        _design(
            template_type="plasmid",
            backbone_path="tests/fixtures/backbones/puc19.gb",
            poly_a_length=120,
        )
    )
    assert config.template_type == "plasmid"
    assert config.poly_a_length == 120


def test_poly_a_is_derived_from_template_type_not_a_toggle() -> None:
    """DC-2.2: a pcr template carries no tract and the control does not exist."""
    messages = _messages(_design(poly_a_length=100))
    assert messages == [
        "poly_a_length: not used for template_type='pcr'; the tail is added "
        "enzymatically and the control does not exist (DC-2.2)"
    ]
    assert "poly_a_length: Input should be greater than 0" in _messages(
        _design(
            template_type="plasmid",
            backbone_path="tests/fixtures/backbones/puc19.gb",
            poly_a_length=0,
        )
    )


def test_seeding_policy_is_explicit_and_overridable_per_adapter() -> None:
    """RD-3.6: one global seed, overridable per adapter, all enumerable."""
    config = parse_config(_design(seed=7, adapter_seeds={"codonbert": 9, "lineardesign": 11}))
    assert config.seed == 7
    assert config.adapter_seeds == {"codonbert": 9, "lineardesign": 11}

    messages = _messages(_design(adapter_seeds={"": 1}))
    assert messages == ["adapter_seeds: adapter ids must not be empty"]


def test_output_naming_is_filename_safe() -> None:
    assert RunConfig(protein_sequence="MKV", run_label="rbd-run_01").run_label == "rbd-run_01"
    messages = _messages(_design(run_label="../escape"))
    assert any(message.startswith("run_label:") for message in messages)


def test_every_field_carries_exactly_one_taxonomy_class() -> None:
    specs = RunConfig.field_specs()

    assert {spec.name for spec in specs} == set(RunConfig.model_fields)
    assert {spec.name for spec in specs if spec.field_class is FieldClass.REQUIRED} == {
        "protein_sequence",
        "sequence_input",
    }
    assert {spec.name for spec in specs if spec.field_class is FieldClass.MATERIAL} == {
        "backbone_path"
    }
    assert {spec.name for spec in specs if spec.field_class is FieldClass.REPRESENTATION} == {
        "run_modules",
        "template_type",
        "poly_a_length",
        "construct_source",
        "default_adapters",
        "seed",
        "adapter_seeds",
        "report_title",
        "run_label",
    }


def test_enumeration_fails_closed_when_a_field_has_no_class() -> None:
    class Unclassified(RunConfig):
        mystery: str = "x"

    with pytest.raises(RuntimeError, match="no field_class classification"):
        Unclassified.field_specs()


def test_resolved_values_are_serialisable_for_the_manifest() -> None:
    """NS-2.3: every field is enumerable, with no hidden key outside the dump."""
    config = RunConfig(protein_sequence="MKV")
    dumped = config.model_dump(mode="json")

    assert set(dumped) == set(RunConfig.model_fields)
    assert yaml.safe_load(yaml.safe_dump(dumped)) == dumped


def test_validation_messages_are_field_level_and_never_pydantic_machinery() -> None:
    """NS-2.2: multiple failures arrive as readable messages, not a traceback."""
    messages = _messages(
        {"run_modules": ["design"], "protein_sequence": "  ", "seed": "not-an-int"}
    )

    assert len(messages) == 2
    rendered = "\n".join(messages)
    assert any(message.startswith("seed:") for message in messages)
    assert any(message.startswith("protein_sequence:") for message in messages)
    assert "Traceback" not in rendered
    assert "ValidationError" not in rendered
    assert "pydantic" not in rendered.lower()

    with pytest.raises(ConfigValidationError) as excinfo:
        parse_config({"run_modules": ["design"]})
    assert str(excinfo.value) == "\n".join(excinfo.value.messages)


def test_golden_config_fixture_conforms_to_the_schema() -> None:
    payload = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    config = parse_config(payload)

    assert config.run_modules == ["design", "construct"]
    assert config.protein_sequence is not None
    assert config.backbone_path is None
    # Placeholders, not decisions: T40 encodes the default adapter set.
    assert config.construct_source is None
    assert config.default_adapters is None


DOC_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")


def test_documentation_names_every_field_and_its_class() -> None:
    """The prose and the schema cannot disagree (T05 delta note)."""
    documented: dict[str, str] = {}
    for line in CONFIG_FIELDS.read_text(encoding="utf-8").splitlines():
        match = DOC_ROW.match(line)
        if match:
            documented[match.group(1)] = match.group(2)

    assert documented == {spec.name: spec.field_class.value for spec in RunConfig.field_specs()}
