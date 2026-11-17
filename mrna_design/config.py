"""The validated pipeline configuration (T05, `SPEC-notebook-shell.md` NS-2.1).

`RunConfig` is the single input to the pipeline. It carries the approved
three-class field taxonomy (NS-1.2a, G19/G20 resolved 2026-11-16):

- ``required`` — a sequence the user must supply: ``protein_sequence`` when the
  design module runs, ``sequence_input`` when it does not.
- ``material`` — a choice that changes what a user would order. Only
  ``backbone_path`` is material, and it has **no default**: absent means the
  plasmid branch is skipped, never a guessed vector (DC-3.0).
- ``representation`` — conventions with declared defaults: construct source,
  template type, poly(A) length, seeds, report wording, output naming.

Every field is tagged in its JSON schema with ``field_class`` so the manifest
can enumerate what affected the output without a second hand-written list
(NS-2.3, "no hidden defaults"). Validation failures are raised as
:class:`ConfigValidationError` carrying field-level, human-readable messages —
never a bare pydantic traceback in the user's path (NS-2.2).

The taxonomy and each field's rule are recorded in ``docs/config-fields.md``;
changing one there or here is a specification change, not a cleanup.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import ErrorDetails

FIELD_CLASS_KEY = "field_class"
"""JSON-schema key that carries a field's taxonomy class."""

DEFAULT_SEED = 42
"""One global default seed, overridable per adapter (RD-3.6)."""

DEFAULT_REPORT_TITLE = "mRNADesign run report"

PLASMID_POLY_A_DEFAULT = 100
"""Default encoded poly(A) length for plasmid templates (DC-2.2, applied at T06)."""


class FieldClass(StrEnum):
    """The approved NS-1.2a classification of a configuration field."""

    REQUIRED = "required"
    MATERIAL = "material"
    REPRESENTATION = "representation"


@dataclass(frozen=True)
class FieldSpec:
    """One enumerable configuration field, for manifest recording (NS-2.3)."""

    name: str
    field_class: FieldClass
    has_default: bool
    default: object


def _classified(field_class: FieldClass, **kwargs: Any) -> Any:
    """Declare a field with its taxonomy class in the JSON schema."""
    extra = dict(kwargs.pop("json_schema_extra", None) or {})
    extra[FIELD_CLASS_KEY] = field_class.value
    return Field(**kwargs, json_schema_extra=extra)


class ConfigValidationError(ValueError):
    """Configuration is invalid; ``messages`` are field-level and renderable.

    Callers (the notebook, the headless runner) catch this and display
    ``messages``. Nothing here is a traceback: that is the NS-2.2 contract.
    """

    def __init__(self, messages: list[str]) -> None:
        self.messages = tuple(messages)
        super().__init__("\n".join(self.messages))

    def __str__(self) -> str:
        return "\n".join(self.messages)


def _format_validation_error(error: ErrorDetails) -> str:
    """Render one pydantic error as ``field.path: reason`` without machinery."""
    location = ".".join(str(part) for part in error["loc"])
    message = error["msg"]
    prefix = "Value error, "
    if message.startswith(prefix):
        message = message[len(prefix) :]
    return f"{location}: {message}" if location else message


def format_validation_errors(error: ValidationError) -> list[str]:
    """Field-level messages for a pydantic validation failure (NS-2.2)."""
    return [_format_validation_error(detail) for detail in error.errors()]


class RunConfig(BaseModel):
    """The single validated pipeline input (NS-2.1).

    Unknown keys are rejected rather than silently dropped: a misspelled field
    must not vanish from the manifest.
    """

    model_config = ConfigDict(extra="forbid")

    # -- required: the sequence class (conditionally required, NS-1.2/NS-1.7) --
    protein_sequence: str | None = _classified(
        FieldClass.REQUIRED,
        default=None,
        description=(
            "Protein to design from. Required when run_modules includes 'design' "
            "(NS-1.2, RD-1.1); normalisation is owned by rna-design (RD-1.4)."
        ),
    )
    sequence_input: str | None = _classified(
        FieldClass.REQUIRED,
        default=None,
        description=(
            "mRNA or DNA sequence for a Module-2-only run. Required when "
            "run_modules excludes 'design' (NS-1.7, DC-1.1)."
        ),
    )

    # -- material: never defaulted (NS-1.2a, DC-3.0) --------------------------
    backbone_path: str | None = _classified(
        FieldClass.MATERIAL,
        default=None,
        description=(
            "User-supplied GenBank or FASTA backbone. No default: absent resolves "
            "the plasmid branch to skipped with a recovery hint (DC-3.0/DC-3.1)."
        ),
    )

    # -- representation: declared conventions (defaults are written out) -----
    run_modules: list[Literal["design", "construct"]] = _classified(
        FieldClass.REPRESENTATION,
        default_factory=lambda: ["design", "construct"],
        min_length=1,
        description="Modules to execute; each may appear once (NS-1.7).",
    )
    template_type: Literal["pcr", "plasmid"] = _classified(
        FieldClass.REPRESENTATION,
        default="pcr",
        description=(
            "Construct template type (DC-2.0). 'plasmid' is reachable only when a "
            "backbone is supplied."
        ),
    )
    poly_a_length: int | None = _classified(
        FieldClass.REPRESENTATION,
        default=None,
        gt=0,
        description=(
            "Encoded poly(A) length for plasmid templates; defaulted to 100 nt at "
            "resolution. 'pcr' carries no tract and must leave this unset (DC-2.2)."
        ),
    )
    construct_source: str | None = _classified(
        FieldClass.REPRESENTATION,
        default="codonbert",
        min_length=1,
        description=(
            "Named adapter whose result is built into the construct (RD-4.1b delta, "
            "G25-B). Not 'the first result' and never a ranking."
        ),
    )
    default_adapters: list[str] | None = _classified(
        FieldClass.REPRESENTATION,
        default=None,
        description=(
            "Per-step default adapter set, encoded at T40. Null means 'not encoded "
            "yet', never 'run nothing' (NS-1.2, RD-4.1a)."
        ),
    )
    seed: int = _classified(
        FieldClass.REPRESENTATION,
        default=DEFAULT_SEED,
        description="Global seed, overridable per adapter via adapter_seeds (RD-3.6).",
    )
    adapter_seeds: dict[str, int] = _classified(
        FieldClass.REPRESENTATION,
        default_factory=dict,
        description="Per-adapter seed overrides; every resolved seed is recorded (RD-3.6).",
    )
    report_title: str = _classified(
        FieldClass.REPRESENTATION,
        default=DEFAULT_REPORT_TITLE,
        min_length=1,
        description="Report wording; the research-use caveat itself is mandated elsewhere.",
    )
    run_label: str | None = _classified(
        FieldClass.REPRESENTATION,
        default=None,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        description=(
            "Optional filename-safe label used when naming the output directory; "
            "absent uses the ledger-generated run id (T09, NS-4.1)."
        ),
    )

    @field_validator("run_modules")
    @classmethod
    def _modules_are_unique(
        cls, modules: list[Literal["design", "construct"]]
    ) -> list[Literal["design", "construct"]]:
        if len(set(modules)) != len(modules):
            raise ValueError("must not repeat a module; list each module at most once")
        return modules

    @field_validator("protein_sequence", "sequence_input")
    @classmethod
    def _sequence_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be empty; omit the field if it is not supplied")
        return value

    @field_validator("backbone_path")
    @classmethod
    def _backbone_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError(
                "must not be empty; omit the field to resolve the plasmid branch to skipped"
            )
        return value

    @field_validator("adapter_seeds")
    @classmethod
    def _adapter_seed_ids_are_not_blank(cls, seeds: dict[str, int]) -> dict[str, int]:
        if any(not adapter_id.strip() for adapter_id in seeds):
            raise ValueError("adapter ids must not be empty")
        return seeds

    @model_validator(mode="after")
    def _required_input_and_branch_rules(self) -> RunConfig:
        needs_design = "design" in self.run_modules
        if needs_design and self.protein_sequence is None:
            raise ValueError(
                "protein_sequence: required when run_modules includes 'design' "
                "(NS-1.2); use a Module-2-only run with sequence_input instead"
            )
        if not needs_design and self.sequence_input is None:
            raise ValueError(
                "sequence_input: required when run_modules does not include 'design' "
                "(NS-1.7, DC-1.1)"
            )

        if self.template_type == "plasmid" and self.backbone_path is None:
            raise ValueError(
                "backbone_path: required for template_type='plasmid'; no backbone is "
                "bundled or invented (DC-3.0) — supply one or use template_type='pcr'"
            )
        if self.template_type == "pcr" and self.backbone_path is not None:
            raise ValueError(
                "template_type: a backbone_path was supplied but template_type is 'pcr'; "
                "set template_type='plasmid' to use it, or remove backbone_path — a "
                "supplied backbone is never ignored silently"
            )
        if self.template_type == "pcr" and self.poly_a_length is not None:
            raise ValueError(
                "poly_a_length: not used for template_type='pcr'; the tail is added "
                "enzymatically and the control does not exist (DC-2.2)"
            )
        return self

    @classmethod
    def field_specs(cls) -> tuple[FieldSpec, ...]:
        """Enumerate every field with its class and declared default (NS-2.3).

        Fails closed: a field without a taxonomy class is a programming error,
        not a field to record as "unknown".
        """
        specs: list[FieldSpec] = []
        for name, info in cls.model_fields.items():
            extra = info.json_schema_extra
            raw = extra.get(FIELD_CLASS_KEY) if isinstance(extra, dict) else None
            if not isinstance(raw, str):
                raise RuntimeError(f"config field {name!r} has no {FIELD_CLASS_KEY} classification")
            try:
                field_class = FieldClass(raw)
            except ValueError as exc:  # pragma: no cover - only reachable by a bad edit
                raise RuntimeError(f"config field {name!r} has unknown class {raw!r}") from exc
            has_default = not info.is_required()
            specs.append(
                FieldSpec(
                    name=name,
                    field_class=field_class,
                    has_default=has_default,
                    default=info.get_default(call_default_factory=True) if has_default else None,
                )
            )
        return tuple(specs)


def parse_config(data: Mapping[str, Any]) -> RunConfig:
    """Validate raw configuration, raising field-level messages (NS-2.2).

    Raises:
        ConfigValidationError: when any field is invalid; ``messages`` names each
            field and the rule it broke, with no pydantic internals.
    """
    try:
        return RunConfig.model_validate(data)
    except ValidationError as error:
        raise ConfigValidationError(format_validation_errors(error)) from error


SEQUENCE_SOURCE_PATTERN = re.compile(r"^(?:user|design:\S+|run:\S+)$")
"""The NS-2.5 vocabulary: ``user``, ``design:<adapter>``, ``run:<previous_run_id>``."""


class BranchState(StrEnum):
    """Resolution state of one optional branch (NS-2.4)."""

    DEFAULTED = "defaulted"
    SUPPLIED = "supplied"
    SKIPPED = "skipped"


class BranchResolution(BaseModel):
    """One optional branch's resolved state, reason and — if skipped — recovery.

    A skipped branch without a recovery hint naming a real configuration field,
    and without an approximate cost of inclusion, cannot be constructed
    (NS-1.5, NS-5.4, NS-SC8). The pre-flight summary embeds this model, so the
    summary cannot render a bare skip either.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    branch: str = Field(min_length=1, description="Stable branch name, e.g. 'plasmid'.")
    state: BranchState
    reason: str = Field(min_length=1)
    recovery_hint: str | None = None
    cost_of_inclusion: str | None = None

    @model_validator(mode="after")
    def _skips_are_recoverable_and_others_are_not(self) -> BranchResolution:
        if self.state is not BranchState.SKIPPED:
            if self.recovery_hint is not None or self.cost_of_inclusion is not None:
                raise ValueError("only a skipped branch carries recovery_hint or cost_of_inclusion")
            return self

        hint = (self.recovery_hint or "").strip()
        cost = (self.cost_of_inclusion or "").strip()
        if not hint:
            raise ValueError(
                "a skipped branch requires recovery_hint naming the field to set (NS-5.4)"
            )
        if not cost:
            raise ValueError("a skipped branch requires cost_of_inclusion (NS-1.5)")
        if not any(
            re.search(rf"\b{re.escape(field_name)}\b", hint)
            for field_name in RunConfig.model_fields
        ):
            raise ValueError(
                "recovery_hint must name a real RunConfig field so the user can act (NS-1.5)"
            )
        return self


class ResolvedConfig(BaseModel):
    """A `RunConfig` with every value explicit, plus resolution metadata (NS-2.1/2.3/2.4).

    ``as_dict()`` is the flat `config.resolved.yaml` payload: every `RunConfig`
    field plus ``branch_resolution``, ``resolved_seeds`` and (for Module-2-only
    runs) ``sequence_source``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    config: RunConfig
    branch_resolution: tuple[BranchResolution, ...] = ()
    resolved_seeds: dict[str, int] = Field(default_factory=dict)
    sequence_source: str | None = None

    @field_validator("sequence_source")
    @classmethod
    def _sequence_source_is_ns_2_5(cls, value: str | None) -> str | None:
        if value is not None and not SEQUENCE_SOURCE_PATTERN.fullmatch(value):
            raise ValueError(
                "must be 'user', 'design:<adapter_id>' or 'run:<previous_run_id>' (NS-2.5)"
            )
        return value

    def as_dict(self) -> dict[str, Any]:
        """Flat, JSON-compatible mapping written to `config.resolved.yaml` (NS-2.1)."""
        payload: dict[str, Any] = self.config.model_dump(mode="json")
        payload["branch_resolution"] = [
            branch.model_dump(mode="json") for branch in self.branch_resolution
        ]
        payload["resolved_seeds"] = dict(sorted(self.resolved_seeds.items()))
        payload["sequence_source"] = self.sequence_source
        return payload

    def to_yaml(self) -> str:
        """Deterministic YAML: sorted keys make re-runs comparable (NS-SC5)."""
        return yaml.safe_dump(self.as_dict(), sort_keys=True, allow_unicode=True)

    def write_yaml(self, path: str | Path) -> Path:
        """Write the resolved config to `path`, creating parent directories."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_yaml(), encoding="utf-8")
        return target


def _resolve_branches(config: RunConfig) -> list[BranchResolution]:
    """Record every optional branch's state, reason and recovery (NS-2.4)."""
    branches: list[BranchResolution] = []

    design_runs = "design" in config.run_modules
    branches.append(
        BranchResolution(
            branch="design_module",
            state=BranchState.SUPPLIED if design_runs else BranchState.SKIPPED,
            reason=(
                "listed in run_modules and a protein_sequence is supplied"
                if design_runs
                else "run_modules does not include 'design' (NS-1.7); no design step is attempted"
            ),
            recovery_hint=(
                None
                if design_runs
                else "set `run_modules` to include 'design' — runs the CDS design step"
            ),
            cost_of_inclusion=(
                None
                if design_runs
                else "the selected design engine's declared runtime and memory class (RD-5.1)"
            ),
        )
    )

    construct_runs = "construct" in config.run_modules
    branches.append(
        BranchResolution(
            branch="construct_module",
            state=BranchState.SUPPLIED if construct_runs else BranchState.SKIPPED,
            reason=(
                "listed in run_modules"
                if construct_runs
                else "run_modules does not include 'construct' (NS-1.7)"
            ),
            recovery_hint=(
                None
                if construct_runs
                else (
                    "set `run_modules` to include 'construct' — adds template assembly "
                    "and the order block"
                )
            ),
            cost_of_inclusion=(None if construct_runs else "~seconds after design; no recompute"),
        )
    )

    backbone_supplied = config.backbone_path is not None
    branches.append(
        BranchResolution(
            branch="plasmid",
            state=BranchState.SUPPLIED if backbone_supplied else BranchState.SKIPPED,
            reason=(
                "backbone_path supplied for the plasmid template"
                if backbone_supplied
                else (
                    "no backbone supplied; the plasmid branch is skipped and the "
                    "template stays 'pcr' (DC-3.0)"
                )
            ),
            recovery_hint=(
                None
                if backbone_supplied
                else "set `backbone_path` and `template_type='plasmid'` — adds plasmid assembly"
            ),
            cost_of_inclusion=(
                None if backbone_supplied else "~5 s, no recompute (NS-1.5 example)"
            ),
        )
    )

    if config.template_type == "plasmid":
        if config.poly_a_length is None:
            branches.append(
                BranchResolution(
                    branch="encoded_poly_a",
                    state=BranchState.DEFAULTED,
                    reason=(
                        f"defaulted to {PLASMID_POLY_A_DEFAULT} nt for a plasmid template (DC-2.2)"
                    ),
                )
            )
        else:
            branches.append(
                BranchResolution(
                    branch="encoded_poly_a",
                    state=BranchState.SUPPLIED,
                    reason="poly_a_length supplied for the plasmid template",
                )
            )
    else:
        branches.append(
            BranchResolution(
                branch="encoded_poly_a",
                state=BranchState.SKIPPED,
                reason=(
                    "pcr templates carry no encoded poly(A); the tail is added "
                    "enzymatically (DC-2.2)"
                ),
                recovery_hint=(
                    "set `template_type='plasmid'` and supply `backbone_path` — "
                    "encodes a poly(A) tract"
                ),
                cost_of_inclusion="requires a plasmid backbone; no recompute",
            )
        )

    return branches


def _resolve_adapter_ids(config: RunConfig, adapter_ids: Sequence[str]) -> list[str]:
    """The adapters whose seeds are resolved: explicit, else the declared default set."""
    ordered = list(adapter_ids) if adapter_ids else list(config.default_adapters or [])
    resolved: list[str] = []
    for adapter_id in ordered:
        if not adapter_id.strip():
            raise ConfigValidationError(["adapter_ids: adapter ids must not be empty"])
        if adapter_id not in resolved:
            resolved.append(adapter_id)
    return resolved


def resolve_config(
    config: RunConfig,
    *,
    adapter_ids: Sequence[str] = (),
    sequence_source: str | None = None,
) -> ResolvedConfig:
    """Resolve a validated config into explicit values and branch states.

    Args:
        config: the validated user input (T05).
        adapter_ids: adapters selected for this run, used to resolve per-adapter
            seeds (RD-3.6). When empty, ``config.default_adapters`` is used; with
            no declared set yet (T40), the resolved seed map is empty.
        sequence_source: for a Module-2-only run, one of ``user``,
            ``design:<adapter>`` or ``run:<previous_run_id>`` (NS-2.5). Supplying
            it for a run that includes design is an error, not an ignored value.

    Raises:
        ConfigValidationError: for a resolution-level inconsistency, with the
            same field-level message shape as input validation (NS-2.2).
    """
    design_runs = "design" in config.run_modules
    if design_runs and sequence_source is not None:
        raise ConfigValidationError(
            ["sequence_source: only applies when run_modules excludes 'design' (NS-2.5)"]
        )

    resolved_poly_a = config.poly_a_length
    if config.template_type == "plasmid" and resolved_poly_a is None:
        resolved_poly_a = PLASMID_POLY_A_DEFAULT

    resolved_input = config.model_copy(update={"poly_a_length": resolved_poly_a})
    seed_ids = _resolve_adapter_ids(config, adapter_ids)
    resolved_seeds = {
        adapter_id: config.adapter_seeds.get(adapter_id, config.seed) for adapter_id in seed_ids
    }

    try:
        return ResolvedConfig(
            config=resolved_input,
            branch_resolution=tuple(_resolve_branches(config)),
            resolved_seeds=resolved_seeds,
            sequence_source=None if design_runs else sequence_source or "user",
        )
    except ValidationError as error:
        raise ConfigValidationError(format_validation_errors(error)) from error
