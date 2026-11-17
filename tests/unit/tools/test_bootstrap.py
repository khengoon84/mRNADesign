"""T12 unit paths for bootstrap (no network)."""

from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from mrna_design.tools import bootstrap as bs
from mrna_design.tools.manifest import load_manifest


def test_tools_root_default() -> None:
    env = {k: v for k, v in os.environ.items() if k not in bs.TOOLS_ROOT_ENV_VARS}
    assert bs.tools_root(env) == Path("/content/tools")


def test_tools_root_env_override() -> None:
    env = {"MRNA_DESIGN_TOOLS_ROOT": "/tmp/scratchpad/tools"}
    assert bs.tools_root(env) == Path("/tmp/scratchpad/tools")


def test_tools_root_alias() -> None:
    env = {"TOOLS_ROOT": "/tmp/alias/tools"}
    assert bs.tools_root(env) == Path("/tmp/alias/tools")


def test_primary_wins_over_alias() -> None:
    env = {"MRNA_DESIGN_TOOLS_ROOT": "/tmp/primary", "TOOLS_ROOT": "/tmp/alias"}
    assert bs.tools_root(env) == Path("/tmp/primary")


def test_install_idempotent(tmp_path: Path) -> None:
    manifest = load_manifest(Path("mrna_design/tools/manifest.yaml"))
    entry = [e for e in manifest.available_tools][0]
    root = tmp_path / "tools"
    first = bs.install(entry, root=root)
    assert first.installed is True
    second = bs.install(entry, root=root)
    assert second.skipped is True
    assert second.message.startswith("already present")


def test_verify_mismatch_raises(tmp_path: Path) -> None:
    manifest = load_manifest(Path("mrna_design/tools/manifest.yaml"))
    entry = [e for e in manifest.available_tools][0]
    root = tmp_path / "tools"
    bs.install(entry, root=root)
    # tamper
    for p in (root / entry.name / ".revision",):
        p.write_text("v9.9\n", encoding="utf-8")
    # also tamper REVISION if present
    (root / entry.name / "REVISION").write_text("v9.9\n", encoding="utf-8")
    with pytest.raises(bs.RevisionMismatchError):
        bs.verify(entry, root=root)


def test_drift_detection_raises() -> None:
    mod = types.ModuleType("drift_mod")
    mod.__version__ = "2.0"
    with pytest.raises(bs.VersionDriftError):
        bs.check_imported_version("drift_mod", "v1.0", module=mod)


def test_drift_detection_ok() -> None:
    mod = types.ModuleType("drift_mod2")
    mod.__version__ = "v1.0"
    assert bs.check_imported_version("drift_mod2", "v1.0", module=mod) is True


def test_cli_verify_end_to_end(tmp_path: Path) -> None:
    root = tmp_path / "tools"
    env = dict(os.environ)
    env["MRNA_DESIGN_TOOLS_ROOT"] = str(root)
    proc = subprocess.run(
        [sys.executable, "-m", "mrna_design.tools.bootstrap", "--profile", "v1", "--verify"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert root.exists()


def test_cli_mismatch_fails(tmp_path: Path) -> None:
    root = tmp_path / "tools"
    env = dict(os.environ)
    env["MRNA_DESIGN_TOOLS_ROOT"] = str(root)
    subprocess.run(
        [sys.executable, "-m", "mrna_design.tools.bootstrap", "--profile", "v1", "--verify"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    # tamper all markers
    for tool_dir in root.iterdir():
        for marker in tool_dir.iterdir():
            marker.write_text("v9.9\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "mrna_design.tools.bootstrap", "--profile", "v1", "--verify"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_import_bootstrap() -> None:
    import mrna_design.tools.bootstrap  # noqa: F401
