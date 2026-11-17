"""Pre-flight summary for the notebook and the headless runner (T06).

`SPEC-notebook-shell.md` NS-1.4/NS-1.5 require a summary before any long step:
the resolved config, the adapters that will run, GPU availability, a rough
time/memory class per step, and every skipped branch with the field to set and
the cost of including it. NS-2.6 adds that the engine for each step is visible.

The summary is a model, not a string built on the fly: a skipped branch without
a recovery hint naming a real configuration field, or without a cost, cannot be
constructed (NS-5.4, NS-SC8). `render_preflight` is the only renderer, so the
notebook and the headless runner cannot present different stories.

This module holds no scientific logic and calls no design engine. Adapter
plans arrive from the registry at T08; until then the caller may pass none.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mrna_design.config import BranchResolution, BranchState, ResolvedConfig


class StepEstimate(BaseModel):
    """One step's adapter and its declared runtime/memory class (RD-5.1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step: str = Field(
        min_length=1,
        description="Pipeline step and region, e.g. 'design:cds' or 'qc:structure'.",
    )
    adapter_id: str = Field(min_length=1)
    gpu_required: bool = False
    runtime_class: str = Field(
        min_length=1,
        description="Declared runtime class from the adapter (unmeasured until measured).",
    )
    memory_class: str = Field(
        min_length=1,
        description="Declared peak-memory class from the adapter.",
    )


class PreflightSummary(BaseModel):
    """Everything NS-1.4/NS-1.5 require before compute starts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    resolved: ResolvedConfig
    steps: tuple[StepEstimate, ...] = ()
    gpu_available: bool

    @field_validator("steps")
    @classmethod
    def _steps_are_unique(cls, steps: tuple[StepEstimate, ...]) -> tuple[StepEstimate, ...]:
        seen: set[tuple[str, str]] = set()
        for estimate in steps:
            key = (estimate.step, estimate.adapter_id)
            if key in seen:
                raise ValueError(
                    f"step/adapter pair {key!r} is listed more than once; "
                    "each engine runs once per step"
                )
            seen.add(key)
        return steps

    @property
    def skipped_branches(self) -> tuple[BranchResolution, ...]:
        """Branches the summary must present separately (NS-1.5)."""
        return tuple(
            branch
            for branch in self.resolved.branch_resolution
            if branch.state is BranchState.SKIPPED
        )

    @model_validator(mode="after")
    def _no_bare_skips(self) -> PreflightSummary:
        """A skip without a field-level hint and cost cannot be summarized."""
        for branch in self.skipped_branches:
            if not (branch.recovery_hint or "").strip():
                raise ValueError(f"skipped branch {branch.branch!r} has no recovery_hint (NS-5.4)")
            if not (branch.cost_of_inclusion or "").strip():
                raise ValueError(
                    f"skipped branch {branch.branch!r} has no cost_of_inclusion (NS-1.5)"
                )
        return self


def detect_gpu_available() -> bool:
    """Best-effort GPU presence for the pre-flight line, without importing torch.

    A false negative only tells the user "CPU-only" on a machine whose GPU
    tooling is missing; it never changes the pipeline. T13 may replace this with
    a runtime probe once the pinned Colab runtime is exercised (T68).
    """
    return shutil.which("nvidia-smi") is not None


def build_preflight(
    resolved: ResolvedConfig,
    steps: Sequence[StepEstimate] = (),
    *,
    gpu_available: bool | None = None,
) -> PreflightSummary:
    """Assemble the summary; `gpu_available=None` probes the runtime."""
    available = detect_gpu_available() if gpu_available is None else gpu_available
    return PreflightSummary(
        resolved=resolved,
        steps=tuple(steps),
        gpu_available=available,
    )


def _format_value(value: Any) -> str:
    if value is None:
        return "not supplied"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def render_preflight(summary: PreflightSummary) -> str:
    """Render the summary as plain text; no `print` in library code (NS-1.1)."""
    config = summary.resolved.config
    values = config.model_dump(mode="json")
    lines = ["Pre-flight summary", "=" * 17]
    lines.append(f"Modules: {', '.join(config.run_modules)}")
    lines.append(
        "GPU: available" if summary.gpu_available else "GPU: unavailable (CPU-only runtime)"
    )
    if summary.resolved.sequence_source is not None:
        lines.append(f"Sequence source: {summary.resolved.sequence_source}")

    lines.append("")
    lines.append("Resolved configuration:")
    for name in sorted(values):
        lines.append(f"  {name}: {_format_value(values[name])}")

    lines.append("")
    lines.append("Resolved seeds:")
    if summary.resolved.resolved_seeds:
        for adapter_id, seed in sorted(summary.resolved.resolved_seeds.items()):
            lines.append(f"  {adapter_id}: {seed}")
    else:
        lines.append("  none (no adapter set declared)")

    lines.append("")
    lines.append("Adapters to run:")
    if summary.steps:
        for estimate in summary.steps:
            gpu = "required" if estimate.gpu_required else "not required"
            lines.append(
                f"  - {estimate.step} [{estimate.adapter_id}]; "
                f"runtime class: {estimate.runtime_class}; "
                f"memory class: {estimate.memory_class}; GPU: {gpu}"
            )
    else:
        lines.append("  none declared in this configuration")

    lines.append("")
    lines.append("Skipped branches:")
    if summary.skipped_branches:
        for branch in summary.skipped_branches:
            lines.append(f"  - {branch.branch}: skipped — {branch.reason}")
            lines.append(f"    set: {branch.recovery_hint}")
            lines.append(f"    approximate cost to include: {branch.cost_of_inclusion}")
    else:
        lines.append("  none")

    return "\n".join(lines) + "\n"
