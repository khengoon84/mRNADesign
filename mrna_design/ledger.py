"""Run ledger: layout, manifest, log, README, packaging (T09, NS-4.*).

Owns the single output layout (AD-6): ``outputs/<run_id>/`` with the fixed file
set and declared subpaths. Other modules write into those subpaths; none invents
a filename.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

SUBPATHS = ("designs", "construct", "report")
"""Declared subpaths under every run directory (NS-4.1)."""

RUN_FILES = ("config.resolved.yaml", "manifest.json", "run.log", "README.txt")
"""Fixed file set at the top of every run directory (NS-4.1)."""


class StepRecord(BaseModel):
    """One step's status and timing (NS-4.2)."""

    model_config = ConfigDict(extra="allow")

    step: str
    status: str = "not_run"
    started_at: str | None = None
    finished_at: str | None = None
    reason: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Ledger:
    """In-memory + on-disk record of a single run."""

    def __init__(
        self,
        run_dir: str | Path,
        *,
        run_id: str | None = None,
        output_root: str | Path | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id or self.run_dir.name
        self.output_root = Path(output_root) if output_root is not None else self.run_dir.parent
        self.manifest: dict[str, Any] = {
            "run_id": self.run_id,
            "created_at": _now(),
            "input_hash": None,
            "adapter_versions": {},
            "resolved_seeds": {},
            "library_versions": {},
            "runtime_type": None,
            "gpu_model": None,
            "steps": [],
            "skipped": [],
            "status": "in_progress",
        }
        self.steps: list[dict[str, Any]] = self.manifest["steps"]
        self.skipped: list[dict[str, Any]] = self.manifest["skipped"]
        self._tools: dict[str, str] = {}
        self._outputs: list[str] = list(RUN_FILES)
        self.ensure_layout()

    # ------------------------------------------------------------------ layout
    def ensure_layout(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        for sub in SUBPATHS:
            (self.run_dir / sub).mkdir(parents=True, exist_ok=True)
        for name in ("run.log",):
            path = self.run_dir / name
            if not path.exists():
                path.touch()
        # README/config/manifest are written explicitly; touch placeholders so
        # the fixed file set exists even before content is known.
        for name in ("config.resolved.yaml", "manifest.json", "README.txt"):
            path = self.run_dir / name
            if not path.exists():
                path.touch()

    @property
    def path(self) -> Path:
        return self.run_dir

    # --------------------------------------------------------------- resolved config
    def write_resolved_config(self, config: Any) -> Path:
        path = self.run_dir / "config.resolved.yaml"
        text = _render_config(config)
        path.write_text(text, encoding="utf-8")
        import contextlib

        with contextlib.suppress(Exception):
            self.manifest["input_hash"] = input_hash(config)
        return path

    def record_resolved_config(self, config: Any) -> Path:
        return self.write_resolved_config(config)

    # -------------------------------------------------------------------- steps
    def record_step(
        self,
        step: str,
        status: str,
        *,
        started_at: str | None = None,
        finished_at: str | None = None,
        reason: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        record = {
            "step": step,
            "status": status,
            "started_at": started_at or _now(),
            "finished_at": finished_at,
            "reason": reason,
        }
        record.update(extra)
        # drop None reason for cleanliness? keep explicit
        self.steps.append(record)
        if status in {"skipped", "not_run"}:
            self.skipped.append({"step": step, "reason": reason, **extra})
        return record

    def add_step(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.record_step(*args, **kwargs)

    def set_step_status(self, step: str, status: str, **kwargs: Any) -> dict[str, Any]:
        # update existing or append
        for rec in reversed(self.steps):
            if rec.get("step") == step:
                rec["status"] = status
                rec.update(kwargs)
                if "reason" in kwargs:
                    rec["reason"] = kwargs["reason"]
                return rec
        return self.record_step(step, status, **kwargs)

    def step_status(self, step: str, status: str, **kwargs: Any) -> dict[str, Any]:
        return self.set_step_status(step, status, **kwargs)

    # ---------------------------------------------------------------- manifest
    def set_manifest_field(self, key: str, value: Any) -> None:
        self.manifest[key] = value

    def update_manifest(self, data: Mapping[str, Any]) -> None:
        self.manifest.update(dict(data))

    def set_adapters(self, adapter_versions: Mapping[str, Any]) -> None:
        self.manifest["adapter_versions"] = dict(adapter_versions)

    def set_adapter_versions(self, adapter_versions: Mapping[str, Any]) -> None:
        self.set_adapters(adapter_versions)

    def set_seeds(self, seeds: Mapping[str, Any]) -> None:
        self.manifest["resolved_seeds"] = dict(seeds)

    def set_resolved_seeds(self, seeds: Mapping[str, Any]) -> None:
        self.set_seeds(seeds)

    def set_library_versions(self, versions: Mapping[str, Any]) -> None:
        self.manifest["library_versions"] = dict(versions)

    def set_runtime(self, runtime_type: str | None = None, gpu_model: str | None = None) -> None:
        if runtime_type is not None:
            self.manifest["runtime_type"] = runtime_type
        if gpu_model is not None:
            self.manifest["gpu_model"] = gpu_model

    def write_manifest(self, manifest: Any = None) -> Path:
        if manifest is not None:
            if isinstance(manifest, Mapping):
                self.manifest.update(dict(manifest))
            else:
                try:
                    self.manifest.update(dict(manifest))
                except Exception:  # noqa: BLE001
                    self.manifest["manifest"] = manifest
        # sync steps list reference
        self.manifest["steps"] = self.steps
        self.manifest["skipped"] = self.skipped
        path = self.run_dir / "manifest.json"
        path.write_text(
            json.dumps(self.manifest, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        return path

    def dump_manifest(self) -> Path:
        return self.write_manifest()

    # ------------------------------------------------------------------- log
    def append_log(self, message: Any) -> Path:
        path = self.run_dir / "run.log"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(str(message))
            if not str(message).endswith("\n"):
                handle.write("\n")
        return path

    def log(self, message: Any) -> Path:
        return self.append_log(message)

    def append_traceback(self, exc: BaseException) -> Path:
        import traceback

        return self.append_log(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )

    # ----------------------------------------------------------------- readme
    def set_tools(self, tools: Mapping[str, str]) -> None:
        self._tools = dict(tools)

    def set_outputs(self, outputs: Sequence[str]) -> None:
        self._outputs = list(outputs)

    def write_readme(
        self,
        *,
        outputs: Sequence[str] | None = None,
        tools: Mapping[str, str] | None = None,
        skipped: Sequence[Any] | None = None,
        caveat: str | None = None,
        title: str = "mRNADesign run bundle",
    ) -> Path:
        if outputs is not None:
            self._outputs = list(outputs)
        if tools is not None:
            self._tools = dict(tools)
        skipped_items = skipped if skipped is not None else self.skipped
        text = render_readme(
            title=title,
            run_id=self.run_id,
            outputs=self._outputs,
            tools=tools if tools is not None else self._tools,
            skipped=skipped_items,
            caveat=caveat,
        )
        path = self.run_dir / "README.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def render_readme(self, **kwargs: Any) -> str:
        return render_readme(run_id=self.run_id, **kwargs)

    # --------------------------------------------------------------- packaging
    def package(self, *, output_path: str | Path | None = None) -> Path:
        return package_bundle(self.run_dir, output_path=output_path)

    def package_bundle(self, *args: Any, **kwargs: Any) -> Path:
        return self.package(*args, **kwargs)

    def zip(self, *args: Any, **kwargs: Any) -> Path:
        return self.package(*args, **kwargs)

    def bundle_path(self) -> Path:
        return self.run_dir.with_suffix(".zip")

    def finalize(self, status: str = "complete") -> Path:
        self.manifest["status"] = status
        self.write_manifest()
        self.write_readme()
        return self.package()


# ------------------------------------------------------------------ functions
def _now() -> str:
    return datetime.now(UTC).isoformat()


def create_run_dir(
    output_root: str | Path = "outputs",
    run_id: str | None = None,
) -> Path:
    root = Path(output_root)
    if run_id is None:
        run_id = "run-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in SUBPATHS:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    for name in RUN_FILES:
        path = run_dir / name
        if not path.exists():
            path.touch()
    return run_dir


def ensure_layout(run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in SUBPATHS:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    for name in RUN_FILES:
        path = run_dir / name
        if not path.exists():
            path.touch()
    return run_dir


def input_hash(config: Any) -> str:
    canonical = _render_config(config)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _render_config(config: Any) -> str:
    if isinstance(config, str):
        return config
    if isinstance(config, Path):
        return config.read_text(encoding="utf-8")
    if isinstance(config, Mapping):
        return yaml.safe_dump(dict(config), sort_keys=True, default_flow_style=False)
    if isinstance(config, BaseModel):
        data = config.model_dump(mode="json")
        return yaml.safe_dump(data, sort_keys=True, default_flow_style=False)
    # duck-typed resolved config
    if hasattr(config, "model_dump"):
        try:
            data = config.model_dump(mode="json")
            return yaml.safe_dump(data, sort_keys=True, default_flow_style=False)
        except Exception:  # noqa: BLE001
            pass
    if hasattr(config, "config") and hasattr(config, "resolved_seeds"):
        try:
            data = (
                config.config.model_dump(mode="json")
                if hasattr(config.config, "model_dump")
                else dict(config.config)
            )
            data = dict(data)
            data["resolved_seeds"] = dict(getattr(config, "resolved_seeds", {}) or {})
            return yaml.safe_dump(data, sort_keys=True, default_flow_style=False)
        except Exception:  # noqa: BLE001
            pass
    try:
        return yaml.safe_dump(config, sort_keys=True, default_flow_style=False)
    except Exception:  # noqa: BLE001
        return str(config)


def render_readme(
    *,
    title: str = "mRNADesign run bundle",
    run_id: str | None = None,
    outputs: Sequence[str] | None = None,
    tools: Mapping[str, str] | None = None,
    skipped: Sequence[Any] | None = None,
    caveat: str | None = None,
    **_: Any,
) -> str:
    outputs = list(outputs or RUN_FILES)
    tools = dict(tools or {})
    skipped = list(skipped or [])
    caveat = caveat or (
        "Research use only. Outputs are provided for research purposes and are not "
        "validated for clinical or diagnostic use. Commercial use of any "
        "research-only engine's output is not granted by this project; contact the "
        "rights holder before using such output commercially."
    )
    lines: list[str] = [title, "=" * len(title)]
    if run_id:
        lines.append(f"Run id: {run_id}")
    lines.append("")
    lines.append("What was produced")
    lines.append("-" * 17)
    for item in outputs:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("What each file is")
    lines.append("-" * 17)
    descriptions = {
        "config.resolved.yaml": "The fully resolved configuration for this run.",
        "manifest.json": "Machine-readable record of inputs, versions, seeds, and step statuses.",
        "run.log": "Full tracebacks and runtime diagnostics.",
        "README.txt": "This file.",
    }
    for item in outputs:
        name = Path(str(item)).name
        desc = descriptions.get(name, "Pipeline artifact.")
        lines.append(f"- {item}: {desc}")
    lines.append("")
    lines.append("Tools and versions")
    lines.append("-" * 17)
    if tools:
        for name, version in sorted(tools.items()):
            lines.append(f"- {name}: {version}")
    else:
        lines.append("- (none recorded)")
    lines.append("")
    lines.append("Not produced in this run")
    lines.append("-" * 26)
    if skipped:
        for item in skipped:
            if isinstance(item, Mapping):
                step = item.get("step") or item.get("branch") or item.get("name") or "step"
                reason = item.get("reason") or item.get("hint") or ""
                hint = item.get("recovery_hint") or item.get("cost_of_inclusion") or ""
                line = f"- {step}: not produced"
                if reason:
                    line += f" — {reason}"
                lines.append(line)
                if hint:
                    lines.append(f"  recovery: {hint}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Caveat")
    lines.append("-" * 7)
    lines.append(caveat)
    lines.append("")
    return "\n".join(lines)


# module-level manifest helpers
def write_manifest(run_dir: str | Path, manifest: Any = None) -> Path:
    ledger = _ledger_for(run_dir)
    if manifest is not None:
        ledger.write_manifest(manifest)
    else:
        ledger.write_manifest()
    return ledger.run_dir / "manifest.json"


def append_log(run_dir: str | Path, message: Any) -> Path:
    return _ledger_for(run_dir).append_log(message)


def write_readme(run_dir: str | Path, **kwargs: Any) -> Path:
    return _ledger_for(run_dir).write_readme(**kwargs)


def write_resolved_config(run_dir: str | Path, config: Any) -> Path:
    return _ledger_for(run_dir).write_resolved_config(config)


def record_step(run_dir: str | Path, *args: Any, **kwargs: Any) -> dict[str, Any]:
    ledger = _ledger_for(run_dir)
    result = ledger.record_step(*args, **kwargs)
    ledger.write_manifest()
    return result


def package_bundle(
    run_dir: str | Path,
    *,
    output_path: str | Path | None = None,
) -> Path:
    run_dir = Path(run_dir)
    ensure_layout(run_dir)
    if output_path is None:
        output_path = run_dir.with_suffix(".zip")
    output_path = Path(output_path)
    # remove existing
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(run_dir.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(run_dir).as_posix()
            zf.write(path, rel)
            zf.write(path, f"{run_dir.name}/{rel}")
    return output_path


def package(run_dir: str | Path, **kwargs: Any) -> Path:
    return package_bundle(run_dir, **kwargs)


def zip_bundle(run_dir: str | Path, **kwargs: Any) -> Path:
    return package_bundle(run_dir, **kwargs)


def _ledger_for(run_dir: str | Path) -> Ledger:
    run_dir = Path(run_dir)
    # Rehydrate a lightweight ledger without overwriting; if manifest exists, load
    ledger = Ledger(run_dir)
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                ledger.manifest.update(data)
                ledger.steps = ledger.manifest.setdefault("steps", [])
                ledger.skipped = ledger.manifest.setdefault("skipped", [])
        except Exception:  # noqa: BLE001
            pass
    return ledger


# aliases
RunLedger = Ledger
RunManifest = None


class Manifest(dict):
    """Dict subclass convenient for tests; behaves as a plain mapping."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


# backward/alias names
LedgerManager = Ledger
RunManager = Ledger

__all__ = [
    "Ledger",
    "RunLedger",
    "StepRecord",
    "Manifest",
    "create_run_dir",
    "ensure_layout",
    "input_hash",
    "render_readme",
    "package_bundle",
    "package",
    "zip_bundle",
    "write_manifest",
    "append_log",
    "write_readme",
    "write_resolved_config",
    "record_step",
    "SUBPATHS",
    "RUN_FILES",
]
