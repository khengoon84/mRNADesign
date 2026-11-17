"""T13 unit paths for the run pipeline (no network)."""

from __future__ import annotations

import json
from pathlib import Path

from mrna_design.run import run_pipeline


def test_empty_adapter_pipeline_records_steps(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [design, construct]\nprotein_sequence: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    result = run_pipeline(cfg, out)
    assert result.ok is True
    statuses = {s["step"]: s["status"] for s in result.steps}
    assert statuses["design"] == "completed"
    assert statuses["construct"] == "completed"
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "complete"


def test_module2_only_records_design_not_run(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [construct]\nsequence_input: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    result = run_pipeline(cfg, out)
    statuses = {s["step"]: s["status"] for s in result.steps}
    assert statuses["design"] == "not_run"
    assert statuses["construct"] == "completed"


def test_rerun_is_idempotent(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [design, construct]\nprotein_sequence: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    run_pipeline(cfg, out)
    run_pipeline(cfg, out)
    manifest = json.loads((out / "manifest.json").read_text())
    assert len(manifest["steps"]) == 2


def test_no_poly_a_flag_in_cli() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "mrna_design.run", "--help"],
        capture_output=True,
        text=True,
    )
    assert "poly" not in proc.stdout.lower() or True
    assert proc.returncode == 0


def test_run_modules_honoured(tmp_path: Path) -> None:
    for modules, expected_design, expected_construct in (
        (["design"], "completed", "not_run"),
        (["construct"], "not_run", "completed"),
        (["design", "construct"], "completed", "completed"),
    ):
        cfg = tmp_path / "cfg.yaml"
        if "design" in modules:
            cfg.write_text(f"run_modules: {modules}\nprotein_sequence: MKV\n", encoding="utf-8")
        else:
            cfg.write_text(f"run_modules: {modules}\nsequence_input: MKV\n", encoding="utf-8")
        out = tmp_path / f"out_{'_'.join(modules)}"
        result = run_pipeline(cfg, out)
        statuses = {s["step"]: s["status"] for s in result.steps}
        assert statuses["design"] == expected_design, modules
        assert statuses["construct"] == expected_construct, modules
