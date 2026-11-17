"""T13 integration paths for run_modules (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mrna_design.run import run_pipeline


@pytest.mark.parametrize("modules", [["design"], ["construct"], ["design", "construct"]])
def test_run_modules_end_to_end(tmp_path: Path, modules: list[str]) -> None:
    cfg = tmp_path / "cfg.yaml"
    if "design" in modules:
        cfg.write_text(f"run_modules: {modules}\nprotein_sequence: MKV\n", encoding="utf-8")
    else:
        cfg.write_text(f"run_modules: {modules}\nsequence_input: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    result = run_pipeline(cfg, out)
    assert result.ok is True
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "complete"
