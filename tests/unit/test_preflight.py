"""T06: the pre-flight summary is complete, honest and unskippable.

NS-1.4/NS-1.5 require the resolved config, adapters, GPU state, per-step
time/memory class and every skipped branch with a field-level hint and cost.
NS-5.4/NS-SC8 are enforced by construction: the summary model refuses a skip
that lacks either. NS-2.5 requires the Module-2-only sequence source to show.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mrna_design import notebook_ui
from mrna_design.config import (
    BranchResolution,
    BranchState,
    RunConfig,
    parse_config,
    resolve_config,
)
from mrna_design.notebook_ui import (
    PreflightSummary,
    StepEstimate,
    build_preflight,
    detect_gpu_available,
    render_preflight,
)


def _resolved(**overrides: Any) -> Any:
    payload: dict[str, Any] = {"protein_sequence": "MKV", "run_modules": ["design", "construct"]}
    payload.update(overrides)
    return resolve_config(parse_config(payload), adapter_ids=["codonbert"])


def _step(
    *,
    step: str = "design:cds",
    adapter_id: str = "codonbert",
    gpu_required: bool = False,
) -> StepEstimate:
    return StepEstimate(
        step=step,
        adapter_id=adapter_id,
        gpu_required=gpu_required,
        runtime_class="minutes",
        memory_class="high",
    )


def test_render_lists_every_ns_1_4_item() -> None:
    summary = build_preflight(_resolved(), [_step()], gpu_available=False)
    text = render_preflight(summary)

    assert "Pre-flight summary" in text
    assert "Modules: design, construct" in text
    assert "GPU: unavailable (CPU-only runtime)" in text
    assert "Resolved configuration:" in text
    for field_name in RunConfig.model_fields:
        assert f"  {field_name}:" in text, f"resolved config omits {field_name}"
    assert "  protein_sequence: MKV" in text
    assert "  construct_source: codonbert" in text
    assert "  template_type: pcr" in text
    assert "  seed: 42" in text
    assert "  backbone_path: not supplied" in text

    assert "Resolved seeds:" in text
    assert "  codonbert: 42" in text

    assert "Adapters to run:" in text
    assert "design:cds [codonbert]" in text
    assert "runtime class: minutes" in text
    assert "memory class: high" in text
    assert "GPU: not required" in text

    assert "Skipped branches:" in text


def test_gpu_required_and_available_states_are_rendered() -> None:
    text = render_preflight(
        build_preflight(_resolved(), [_step(gpu_required=True)], gpu_available=True)
    )

    assert "GPU: available" in text
    assert "GPU: required" in text


def test_every_skip_is_rendered_with_its_field_hint_and_cost() -> None:
    summary = build_preflight(_resolved(), [_step()], gpu_available=False)

    assert {branch.branch for branch in summary.skipped_branches} == {
        "plasmid",
        "encoded_poly_a",
    }
    text = render_preflight(summary)
    for branch in summary.skipped_branches:
        assert f"  - {branch.branch}: skipped — {branch.reason}" in text
        assert branch.recovery_hint is not None
        assert branch.cost_of_inclusion is not None
        assert branch.recovery_hint in text
        assert branch.cost_of_inclusion in text

    assert "set: set `backbone_path`" in text
    assert "approximate cost to include: ~5 s, no recompute" in text


def test_summary_rejects_a_skip_without_a_hint_or_cost() -> None:
    payload = _resolved().model_dump(mode="python")
    for branch in payload["branch_resolution"]:
        if branch["branch"] == "plasmid":
            branch["recovery_hint"] = None

    with pytest.raises(ValidationError, match="recovery_hint"):
        PreflightSummary.model_validate({"resolved": payload, "steps": [], "gpu_available": False})

    # Bypass nest validation to prove the summary's own guard is not decorative.
    bare = BranchResolution.model_construct(
        branch="plasmid",
        state=BranchState.SKIPPED,
        reason="no backbone",
        recovery_hint=None,
        cost_of_inclusion=None,
    )
    resolved = _resolved().model_copy(update={"branch_resolution": (bare,)})
    with pytest.raises(ValidationError, match="no recovery_hint"):
        PreflightSummary(resolved=resolved, steps=(), gpu_available=False)

    no_cost = BranchResolution.model_construct(
        branch="plasmid",
        state=BranchState.SKIPPED,
        reason="no backbone",
        recovery_hint="set `backbone_path`",
        cost_of_inclusion=None,
    )
    resolved = _resolved().model_copy(update={"branch_resolution": (no_cost,)})
    with pytest.raises(ValidationError, match="no cost_of_inclusion"):
        PreflightSummary(resolved=resolved, steps=(), gpu_available=False)


def test_module_two_summary_shows_the_sequence_source_and_design_skip() -> None:
    resolved = resolve_config(
        parse_config({"run_modules": ["construct"], "sequence_input": "AUGGUU"}),
        sequence_source="run:20261117T045947Z-abc",
    )
    text = render_preflight(build_preflight(resolved, [], gpu_available=True))

    assert "Sequence source: run:20261117T045947Z-abc" in text
    assert "design_module: skipped" in text
    assert "set `run_modules` to include 'design'" in text
    assert "Adapters to run:\n  none declared in this configuration" in text


def test_a_summary_with_no_skips_says_none() -> None:
    resolved = _resolved(
        template_type="plasmid",
        backbone_path="tests/fixtures/backbones/puc19.gb",
    )
    text = render_preflight(build_preflight(resolved, [], gpu_available=True))

    assert "Skipped branches:\n  none" in text


def test_none_values_render_as_not_supplied() -> None:
    text = render_preflight(build_preflight(_resolved(), [], gpu_available=True))

    assert "  backbone_path: not supplied" in text
    assert "  poly_a_length: not supplied" in text
    assert "  run_label: not supplied" in text
    assert "  default_adapters: not supplied" in text


def test_gpu_detection_is_best_effort_and_injectable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notebook_ui.shutil,
        "which",
        lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None,
    )
    assert detect_gpu_available() is True

    monkeypatch.setattr(notebook_ui.shutil, "which", lambda name: None)
    assert detect_gpu_available() is False

    monkeypatch.setattr(notebook_ui, "detect_gpu_available", lambda: True)
    assert build_preflight(_resolved(), []).gpu_available is True
    assert build_preflight(_resolved(), [], gpu_available=False).gpu_available is False


def test_duplicate_step_adapter_pairs_are_rejected() -> None:
    with pytest.raises(ValidationError, match="more than once"):
        PreflightSummary(
            resolved=_resolved(),
            steps=(_step(), _step()),
            gpu_available=False,
        )


def test_one_adapter_may_serve_two_distinct_steps() -> None:
    summary = build_preflight(
        _resolved(),
        [_step(step="design:cds"), _step(step="qc:structure")],
        gpu_available=True,
    )

    assert len(summary.steps) == 2


def test_render_is_deterministic() -> None:
    summary = build_preflight(_resolved(), [_step()], gpu_available=False)
    assert render_preflight(summary) == render_preflight(summary)
