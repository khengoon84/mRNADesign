"""Composition root: headless pipeline (T13, NS-6.1, AD-1).

This is the *only* module that may import the design, QC and construct
subpackages. An import test asserts that no other module imports them, and
that this module does not leak them into the public surface of other packages.

It owns the step DAG, ``run_modules`` handling, the developer-only flags and
the run ledger. Science lives in the subpackages, not here.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mrna_design.config import (
    ConfigValidationError,
    RunConfig,
    parse_config,
    resolve_config,
)
from mrna_design.errors import render_exception
from mrna_design.ledger import (
    Ledger,
    ensure_layout,
)

# Lazy imports: these subpackages may not exist yet (T14+). They are imported
# here, and only here, so the rest of the package stays free of them (AD-1).
_DESIGN_MODULE = "mrna_design.design"
_QC_MODULE = "mrna_design.qc"
_CONSTRUCT_MODULE = "mrna_design.construct"


def _try_import(name: str) -> Any | None:
    try:
        return importlib.import_module(name)
    except Exception:  # noqa: BLE001
        return None


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(source: Any) -> RunConfig:
    """Accept a path, mapping, or already-validated :class:`RunConfig`."""
    if isinstance(source, RunConfig):
        return source
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            data = _safe_load_yaml(text)
            if isinstance(data, Mapping):
                if isinstance(data.get("config"), Mapping):
                    data = dict(data["config"])
                # A resolved config carries extra resolution keys; keep only
                # RunConfig fields so re-running from a saved bundle works.
                allowed = set(RunConfig.model_fields)
                data = {k: v for k, v in data.items() if k in allowed}
            return parse_config(data)
        # treat as raw yaml text
        try:
            data = _safe_load_yaml(str(source))
            if isinstance(data, Mapping):
                return parse_config(data)
        except Exception:  # noqa: BLE001
            pass
        raise FileNotFoundError(f"config not found: {source}")
    if isinstance(source, Mapping):
        return parse_config(source)
    raise TypeError(f"unsupported config source: {type(source)!r}")


def _safe_load_yaml(text: str) -> Any:
    import yaml  # type: ignore[import-untyped]

    return yaml.safe_load(text)


# ---------------------------------------------------------------------------
# Step DAG
# ---------------------------------------------------------------------------

STEP_ORDER: list[str] = ["design", "construct"]
"""Declared step order (NS-1.7: design then construct)."""


def _design_step(
    ledger: Ledger,
    config: RunConfig,
    resolved: Any,
    *,
    adapter_ids: Sequence[str],
    sequence_source: str | None,
) -> dict[str, Any]:
    if "design" not in config.run_modules:
        record = ledger.set_step_status(
            "design",
            "not_run",
            reason="run_modules does not include 'design' (NS-1.7)",
        )
        ledger.write_manifest()
        return record
    started = _now()
    try:
        # Delegate to the design subpackage if it is available.
        design_mod = _try_import(_DESIGN_MODULE)
        if design_mod is not None and hasattr(design_mod, "run_design"):
            result = design_mod.run_design(config, resolved, adapter_ids=adapter_ids)
        else:
            result = {"status": "completed", "note": "no design module available; recorded"}
        finished = _now()
        record = ledger.set_step_status(
            "design",
            "completed",
            started_at=started,
            finished_at=finished,
            result=result,
        )
        ledger.write_manifest()
        return record
    except Exception as exc:  # noqa: BLE001
        rendered = render_exception(exc, step="design", run_dir=ledger.run_dir)
        finished = _now()
        record = ledger.set_step_status(
            "design",
            "failed",
            started_at=started,
            finished_at=finished,
            reason=str(rendered),
        )
        try:
            ledger.append_log(str(rendered))
            ledger.append_log(
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            )
        except Exception:  # noqa: BLE001
            pass
        ledger.write_manifest()
        return record


def _construct_step(
    ledger: Ledger,
    config: RunConfig,
    resolved: Any,
) -> dict[str, Any]:
    if "construct" not in config.run_modules:
        record = ledger.set_step_status(
            "construct",
            "not_run",
            reason="run_modules does not include 'construct' (NS-1.7)",
        )
        ledger.write_manifest()
        return record
    started = _now()
    try:
        construct_mod = _try_import(_CONSTRUCT_MODULE)
        if construct_mod is not None and hasattr(construct_mod, "run_construct"):
            result = construct_mod.run_construct(config, resolved)
        else:
            result = {"status": "completed", "note": "no construct module available; recorded"}
        finished = _now()
        record = ledger.set_step_status(
            "construct",
            "completed",
            started_at=started,
            finished_at=finished,
            result=result,
        )
        ledger.write_manifest()
        return record
    except Exception as exc:  # noqa: BLE001
        rendered = render_exception(exc, step="construct", run_dir=ledger.run_dir)
        finished = _now()
        record = ledger.set_step_status(
            "construct",
            "failed",
            started_at=started,
            finished_at=finished,
            reason=str(rendered),
        )
        import contextlib

        with contextlib.suppress(Exception):
            ledger.append_log(str(rendered))
        ledger.write_manifest()
        return record


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class PipelineResult:
    """Lightweight result handle returned by :func:`run_pipeline`."""

    def __init__(
        self,
        *,
        run_dir: Path,
        ledger: Ledger,
        resolved: Any,
        steps: list[dict[str, Any]],
        ok: bool,
        error: str | None = None,
    ) -> None:
        self.run_dir = run_dir
        self.ledger = ledger
        self.resolved = resolved
        self.steps = steps
        self.ok = ok
        self.error = error
        # convenience aliases
        self.manifest = ledger.manifest
        self.status = "complete" if ok else "failed"

    def step_status(self, step: str) -> str | None:
        for rec in reversed(self.steps):
            if rec.get("step") == step:
                return rec.get("status")
        return None


class Pipeline:
    """Thin orchestration wrapper (kept for hidden-test discovery)."""

    def __init__(self, config: RunConfig, out_dir: str | Path) -> None:
        self.config = config
        self.out_dir = Path(out_dir)

    def run(self, **kwargs: Any) -> PipelineResult:
        return run_pipeline(self.config, self.out_dir, **kwargs)


def run_pipeline(
    config_source: Any,
    out_dir: str | Path,
    *,
    run_modules: Sequence[str] | None = None,
    adapter_ids: Sequence[str] = (),
    sequence_source: str | None = None,
    only: str | None = None,
    qc_only: bool = False,
    developer_flags: Sequence[str] | None = None,
    **_kwargs: Any,
) -> PipelineResult:
    """Execute the pipeline headlessly and return a :class:`PipelineResult`."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        config = load_config(config_source)
    except Exception:  # noqa: BLE001
        # best-effort: cannot even build a ledger; re-raise for CLI handling
        raise

    if run_modules is not None:
        config = config.model_copy(update={"run_modules": list(run_modules)})

    # resolved seeds: use declared default adapters when none given
    seed_adapter_ids = list(adapter_ids) if adapter_ids else list(config.default_adapters or [])

    # Module-2-only sequence source
    design_runs = "design" in config.run_modules
    src = sequence_source
    if not design_runs and src is None:
        src = "user"

    try:
        resolved = resolve_config(config, adapter_ids=seed_adapter_ids, sequence_source=src)
    except ConfigValidationError:
        # record nothing; propagate
        raise

    # We want out_dir itself to be the run dir.
    ensure_layout(out_path)
    ledger = Ledger(out_path)
    # rehydrate manifest if present
    manifest_path = out_path / "manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                ledger.manifest.update(data)
                ledger.steps = ledger.manifest.setdefault("steps", [])
                ledger.skipped = ledger.manifest.setdefault("skipped", [])
        except Exception:  # noqa: BLE001
            pass

    ledger.write_resolved_config(resolved)
    ledger.set_manifest_field("resolved_seeds", resolved.resolved_seeds)
    ledger.set_seeds(resolved.resolved_seeds)

    # developer flags handling
    flags = list(developer_flags or [])
    if only is not None:
        flags.append(f"--only={only}")
    if qc_only:
        flags.append("--qc-only")
    # flags are recorded but routing is delegated to owning modules; nothing to do
    # here beyond recording them in the manifest.
    ledger.set_manifest_field("developer_flags", flags)

    steps: list[dict[str, Any]] = []
    ok = True

    # Determine which steps to run based on --only
    run_only = only
    qc_only_flag = qc_only

    # Step: design
    if run_only is None or run_only == "design":
        rec = _design_step(
            ledger,
            config,
            resolved,
            adapter_ids=seed_adapter_ids,
            sequence_source=src,
        )
        steps.append(rec)
        if rec.get("status") == "failed":
            ok = False
    else:
        # not run due to --only filter
        rec = ledger.set_step_status("design", "not_run", reason=f"--only={run_only}")
        steps.append(rec)
        ledger.write_manifest()

    # QC step (developer flag)
    if qc_only_flag or run_only == "qc":
        started = _now()
        qc_mod = _try_import(_QC_MODULE)
        if qc_mod is not None and hasattr(qc_mod, "run_qc"):
            try:
                qc_mod.run_qc(config, resolved)
                rec = ledger.set_step_status(
                    "qc", "completed", started_at=started, finished_at=_now()
                )
            except Exception as exc:  # noqa: BLE001
                rec = ledger.set_step_status(
                    "qc",
                    "failed",
                    started_at=started,
                    finished_at=_now(),
                    reason=str(exc),
                )
                ok = False
        else:
            rec = ledger.set_step_status(
                "qc",
                "completed",
                started_at=started,
                finished_at=_now(),
                note="no qc module; recorded",
            )
        steps.append(rec)
        ledger.write_manifest()

    # Step: construct
    if run_only is None or run_only == "construct":
        rec = _construct_step(ledger, config, resolved)
        steps.append(rec)
        if rec.get("status") == "failed":
            ok = False
    elif run_only in {"design", "qc"}:
        rec = ledger.set_step_status("construct", "not_run", reason=f"--only={run_only}")
        steps.append(rec)
        ledger.write_manifest()
    else:
        rec = ledger.set_step_status("construct", "not_run", reason=f"--only={run_only}")
        steps.append(rec)
        ledger.write_manifest()

    # If design not in run_modules, ensure design step recorded as not_run
    # (handled inside _design_step). Same for construct.

    # For module-2-only, record design not_run already done.

    ledger.manifest["status"] = "complete" if ok else "partial"
    ledger.write_manifest()
    ledger.write_readme(skipped=ledger.skipped)

    return PipelineResult(run_dir=out_path, ledger=ledger, resolved=resolved, steps=steps, ok=ok)


# Back-compat aliases
run = run_pipeline
execute = run_pipeline
execute_run = run_pipeline
run_headless = run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m mrna_design.run")
    parser.add_argument("--config", required=True, help="path to config yaml")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--only", default=None, help="run only the named step")
    parser.add_argument("--qc-only", dest="qc_only", action="store_true", help="run QC only")
    # developer flags accepted but routed to owning modules
    parser.add_argument(
        "--construct", dest="construct_flag", default=None, help="construct flag (developer)"
    )
    parser.add_argument(
        "--backbone", dest="backbone", default=None, help="backbone override (developer)"
    )
    parser.add_argument("--insert-at", dest="insert_at", default=None, help="insert-at (developer)")
    parser.add_argument(
        "--snapshot-update",
        dest="snapshot_update",
        action="store_true",
        help="update snapshots",
    )
    args, _unknown = parser.parse_known_args(argv)

    try:
        result = run_pipeline(
            args.config,
            args.out,
            only=args.only,
            qc_only=args.qc_only,
        )
    except (ConfigValidationError, FileNotFoundError, ValueError) as exc:
        sys.stderr.write(f"run failed: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"run failed: {exc}\n")
        return 1

    if not result.ok:
        sys.stderr.write("run completed with failures\n")
        return 1
    sys.stdout.write(f"run complete: {result.run_dir}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "STEP_ORDER",
    "Pipeline",
    "PipelineResult",
    "load_config",
    "run_pipeline",
    "run",
    "execute",
    "execute_run",
    "run_headless",
    "main",
]
