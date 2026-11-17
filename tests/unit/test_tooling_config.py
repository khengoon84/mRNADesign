"""T02: the tooling contract is machine-checked, not merely documented.

These tests assert the baseline the rest of the plan relies on: Python 3.11,
the three runtime markers, a default invocation that deselects them, the 80 %
coverage gate with its per-module minimums, and a CI workflow that runs the same
commands the local Verify step runs (SPEC-notebook-shell.md NS-6.2).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _pyproject() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_python_is_pinned_to_311() -> None:
    config = _pyproject()
    assert config["project"]["requires-python"] == ">=3.11,<3.12"
    assert config["tool"]["ruff"]["target-version"] == "py311"
    assert config["tool"]["mypy"]["python_version"] == "3.11"


def test_markers_are_declared_once() -> None:
    options = _pyproject()["tool"]["pytest"]["ini_options"]
    declared = {entry.split(":", 1)[0] for entry in options["markers"]}
    assert declared == {"network", "gpu", "e2e"}


def test_default_invocation_deselects_network_gpu_and_e2e() -> None:
    addopts = _pyproject()["tool"]["pytest"]["ini_options"]["addopts"]
    for marker in ("network", "gpu", "e2e"):
        assert f"not {marker}" in addopts
    assert "--strict-markers" in addopts


def test_coverage_minimums_are_recorded() -> None:
    minimums = _pyproject()["tool"]["mrna_design"]["coverage-minimums"]
    assert minimums == {
        "overall": 80,
        "shell": 80,
        "contracts": 95,
        "adapters": 95,
        "qc": 85,
        "construct": 85,
    }


def test_ci_runs_the_local_command_sequence() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for command in (
        "ruff check .",
        "ruff format --check .",
        "mypy mrna_design",
        'pytest -m "not network and not gpu and not e2e"',
        "--cov-fail-under=80",
    ):
        assert command in workflow, f"CI workflow is missing: {command}"
    assert 'python-version: "3.11"' in workflow


def test_package_is_importable() -> None:
    import mrna_design

    assert mrna_design.__version__ == "0.1.0.dev0"
