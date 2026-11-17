"""T16 reproduction from saved config (NS-SC5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mrna_design.run import run_pipeline

pytestmark = pytest.mark.e2e


def test_reproduction(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("run_modules: [design, construct]\nprotein_sequence: MKV\n", encoding="utf-8")
    out1 = tmp_path / "out1"
    run_pipeline(cfg, out1)
    saved = out1 / "config.resolved.yaml"
    assert saved.exists()
    out2 = tmp_path / "out2"
    run_pipeline(saved, out2)
    m1 = json.loads((out1 / "manifest.json").read_text())
    m2 = json.loads((out2 / "manifest.json").read_text())
    assert [s["status"] for s in m1["steps"]] == [s["status"] for s in m2["steps"]]
    for name in ("config.resolved.yaml", "manifest.json", "run.log", "README.txt"):
        assert (out2 / name).exists()
