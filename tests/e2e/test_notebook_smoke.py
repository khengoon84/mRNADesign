"""T15 notebook smoke (NS-6.3)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

NOTEBOOK = Path("notebooks/mRNADesign.ipynb")


@pytest.mark.e2e
def test_notebook_smoke(tmp_path: Path) -> None:
    if shutil.which("jupyter") is None and not _has_nbconvert():
        pytest.skip("nbconvert not installed")
    out_dir = tmp_path / "nb"
    cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        str(NOTEBOOK),
        "--output-dir",
        str(out_dir),
        "--ExecutePreprocessor.timeout=3600",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def _has_nbconvert() -> bool:
    try:
        import nbconvert  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False
