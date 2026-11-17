"""T06: resolution makes every value explicit and every skip recoverable.

The tests cover NS-2.1/2.3 (a resolved config with no hidden values),
NS-2.4 (`branch_resolution` states), NS-1.5/NS-5.4 (a skip without a field-level
recovery hint and cost is unconstructible) and NS-2.5 (Module-2-only sequence
sources). `docs/config-fields.md` remains the field authority from T05.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from mrna_design.config import (
    DEFAULT_REPORT_TITLE,
    DEFAULT_SEED,
    PLASMID_POLY_A_DEFAULT,
    BranchResolution,
    BranchState,
    ConfigValidationError,
    ResolvedConfig,
    RunConfig,
    parse_config,
    resolve_config,
)

BACKBONE = "tests/fixtures/backbones/puc19.gb"
RESOLUTION_KEYS = {"branch_resolution", "resolved_seeds", "sequence_source"}


def _design(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"protein_sequence": "MKV", "run_modules": ["design", "construct"]}
    payload.update(overrides)
    return payload


def _branches(resolved: ResolvedConfig) -> dict[str, BranchResolution]:
    return {branch.branch: branch for branch in resolved.branch_resolution}


def test_resolution_writes_every_field_explicitly() -> None:
    """NS-2.1/NS-2.3: no field is left implicit, including resolved seeds."""
    resolved = resolve_config(parse_config(_design()), adapter_ids=["codonbert"])
    data = yaml.safe_load(resolved.to_yaml())

    assert set(data) == set(RunConfig.model_fields) | RESOLUTION_KEYS

    assert data["protein_sequence"] == "MKV"
    assert data["sequence_input"] is None
    assert data["backbone_path"] is None
    assert data["run_modules"] == ["design", "construct"]
    assert data["template_type"] == "pcr"
    assert data["poly_a_length"] is None
    assert data["construct_source"] == "codonbert"
    assert data["default_adapters"] is None
    assert data["seed"] == DEFAULT_SEED
    assert data["adapter_seeds"] == {}
    assert data["report_title"] == DEFAULT_REPORT_TITLE
    assert data["run_label"] is None
    assert data["resolved_seeds"] == {"codonbert": DEFAULT_SEED}
    assert data["sequence_source"] is None


def test_resolution_writes_a_deterministic_yaml_file(tmp_path: Path) -> None:
    resolved = resolve_config(parse_config(_design()), adapter_ids=["codonbert"])
    target = tmp_path / "run" / "config.resolved.yaml"

    written = resolved.write_yaml(target)

    assert written == target
    assert target.read_text(encoding="utf-8") == resolved.to_yaml()
    assert resolved.to_yaml() == resolved.to_yaml()
    assert yaml.safe_load(target.read_text(encoding="utf-8")) == yaml.safe_load(resolved.to_yaml())


def test_default_path_branch_states_are_recorded() -> None:
    """NS-2.4: one entry per optional branch, with its reason."""
    resolved = resolve_config(parse_config(_design()), adapter_ids=["codonbert"])
    branches = _branches(resolved)

    assert [branch.branch for branch in resolved.branch_resolution] == [
        "design_module",
        "construct_module",
        "plasmid",
        "encoded_poly_a",
    ]
    assert branches["design_module"].state is BranchState.SUPPLIED
    assert branches["construct_module"].state is BranchState.SUPPLIED
    assert branches["plasmid"].state is BranchState.SKIPPED
    assert branches["encoded_poly_a"].state is BranchState.SKIPPED
    for branch in resolved.branch_resolution:
        assert branch.reason


def test_every_skipped_branch_names_a_real_field_and_its_cost() -> None:
    """NS-1.5/NS-5.4/NS-SC8: no bare skip reaches the summary."""
    resolved = resolve_config(parse_config(_design()), adapter_ids=["codonbert"])
    skipped = [b for b in resolved.branch_resolution if b.state is BranchState.SKIPPED]

    assert skipped
    for branch in skipped:
        assert branch.cost_of_inclusion
        assert any(
            field_name in (branch.recovery_hint or "") for field_name in RunConfig.model_fields
        ), f"{branch.branch} hint does not name a config field"

    plasmid = _branches(resolved)["plasmid"]
    assert "backbone_path" in (plasmid.recovery_hint or "")
    assert "~5 s, no recompute" in (plasmid.cost_of_inclusion or "")


def test_design_only_run_records_the_construct_module_skipped() -> None:
    resolved = resolve_config(parse_config(_design(run_modules=["design"])))
    branches = _branches(resolved)

    assert branches["design_module"].state is BranchState.SUPPLIED
    assert branches["construct_module"].state is BranchState.SKIPPED
    assert "run_modules" in (branches["construct_module"].recovery_hint or "")
    assert branches["construct_module"].cost_of_inclusion


def test_plasmid_resolves_the_default_poly_a_length() -> None:
    """DC-2.2: the 100 nt plasmid default is resolved explicitly, not hidden."""
    resolved = resolve_config(
        parse_config(_design(template_type="plasmid", backbone_path=BACKBONE)),
        adapter_ids=["codonbert"],
    )
    branches = _branches(resolved)

    assert resolved.config.poly_a_length == PLASMID_POLY_A_DEFAULT
    assert yaml.safe_load(resolved.to_yaml())["poly_a_length"] == PLASMID_POLY_A_DEFAULT
    assert branches["plasmid"].state is BranchState.SUPPLIED
    assert branches["encoded_poly_a"].state is BranchState.DEFAULTED
    assert branches["encoded_poly_a"].recovery_hint is None
    assert branches["encoded_poly_a"].cost_of_inclusion is None


def test_supplied_poly_a_is_not_redefaulted() -> None:
    resolved = resolve_config(
        parse_config(_design(template_type="plasmid", backbone_path=BACKBONE, poly_a_length=150))
    )

    assert resolved.config.poly_a_length == 150
    assert _branches(resolved)["encoded_poly_a"].state is BranchState.SUPPLIED


def test_module_two_only_records_a_user_sequence_source() -> None:
    """NS-2.5: the source is explicit, and design is a recorded skip, not a failure."""
    resolved = resolve_config(
        parse_config({"run_modules": ["construct"], "sequence_input": "AUGGUU"})
    )
    branches = _branches(resolved)

    assert resolved.sequence_source == "user"
    assert yaml.safe_load(resolved.to_yaml())["sequence_source"] == "user"
    assert resolved.resolved_seeds == {}
    assert branches["design_module"].state is BranchState.SKIPPED
    assert "run_modules" in (branches["design_module"].recovery_hint or "")
    assert branches["design_module"].cost_of_inclusion
    assert branches["construct_module"].state is BranchState.SUPPLIED


@pytest.mark.parametrize("source", ["design:lineardesign", "run:20261117T045947Z-abc"])
def test_module_two_accepts_the_other_ns_2_5_sources(source: str) -> None:
    resolved = resolve_config(
        parse_config({"run_modules": ["construct"], "sequence_input": "AUGGUU"}),
        sequence_source=source,
    )

    assert resolved.sequence_source == source
    assert yaml.safe_load(resolved.to_yaml())["sequence_source"] == source


def test_an_invalid_sequence_source_is_a_field_level_error() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        resolve_config(
            parse_config({"run_modules": ["construct"], "sequence_input": "AUGGUU"}),
            sequence_source="codonbert",
        )

    assert excinfo.value.messages[0].startswith("sequence_source:")
    assert "design:<adapter_id>" in excinfo.value.messages[0]


def test_sequence_source_for_a_design_run_is_refused_not_ignored() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        resolve_config(parse_config(_design()), sequence_source="user")

    assert list(excinfo.value.messages) == [
        "sequence_source: only applies when run_modules excludes 'design' (NS-2.5)"
    ]


def test_resolved_seeds_respect_per_adapter_overrides() -> None:
    """RD-3.6: one global seed, overridable per adapter, every value recorded."""
    resolved = resolve_config(
        parse_config(_design(seed=7, adapter_seeds={"codonbert": 9})),
        adapter_ids=["codonbert", "lineardesign"],
    )

    assert resolved.resolved_seeds == {"codonbert": 9, "lineardesign": 7}
    assert yaml.safe_load(resolved.to_yaml())["resolved_seeds"] == {
        "codonbert": 9,
        "lineardesign": 7,
    }


def test_resolved_seeds_fall_back_to_the_declared_default_adapters() -> None:
    resolved = resolve_config(parse_config(_design(default_adapters=["codonbert"])))

    assert resolved.resolved_seeds == {"codonbert": DEFAULT_SEED}


def test_duplicate_adapter_ids_resolve_once_and_blank_ids_are_refused() -> None:
    resolved = resolve_config(parse_config(_design()), adapter_ids=["codonbert", "codonbert"])
    assert resolved.resolved_seeds == {"codonbert": DEFAULT_SEED}

    with pytest.raises(ConfigValidationError) as excinfo:
        resolve_config(parse_config(_design()), adapter_ids=[" "])
    assert list(excinfo.value.messages) == ["adapter_ids: adapter ids must not be empty"]


def test_a_skip_without_a_real_hint_and_cost_is_unconstructible() -> None:
    """NS-5.4/NS-SC8: the model, not review, makes a bare skip impossible."""
    with pytest.raises(ValidationError, match="recovery_hint"):
        BranchResolution(branch="plasmid", state="skipped", reason="no backbone")

    with pytest.raises(ValidationError, match="cost_of_inclusion"):
        BranchResolution(
            branch="plasmid",
            state="skipped",
            reason="no backbone",
            recovery_hint="set `backbone_path`",
        )

    with pytest.raises(ValidationError, match="real RunConfig field"):
        BranchResolution(
            branch="plasmid",
            state="skipped",
            reason="no backbone",
            recovery_hint="supply the vector file",
            cost_of_inclusion="~5 s",
        )


def test_a_resolved_branch_cannot_carry_a_stale_recovery_hint() -> None:
    with pytest.raises(ValidationError, match="only a skipped branch"):
        BranchResolution(
            branch="plasmid",
            state="supplied",
            reason="backbone supplied",
            recovery_hint="set `backbone_path`",
        )
