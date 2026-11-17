"""T16 bundle contract (NS-SC4, NS-SC8)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mrna_design.ledger import RUN_FILES, SUBPATHS
from mrna_design.run import run_pipeline

pytestmark = pytest.mark.e2e


def test_bundle_file_set(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [design, construct]\nprotein_sequence: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    run_pipeline(cfg, out)
    for name in RUN_FILES:
        assert (out / name).exists(), name
    for sub in SUBPATHS:
        assert (out / sub).is_dir(), sub
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert "steps" in manifest
    assert "skipped" in manifest


def test_skip_rendering(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [design, construct]\nprotein_sequence: MKV\n", encoding="utf-8")
    out = tmp_path / "out"
    run_pipeline(cfg, out)
    readme = (out / "README.txt").read_text()
    manifest = json.loads((out / "manifest.json").read_text())
    # skipped list present
    assert "skipped" in manifest
    # README has "Not produced" section
    assert "Not produced in this run" in readme
