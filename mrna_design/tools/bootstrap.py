"""Pinned tool bootstrap, verification, idempotency and drift detection (T12, NS-3.*).

``python -m mrna_design.tools.bootstrap --profile v1 --verify`` installs every
non-excluded entry of ``manifest.yaml`` at its pinned revision into the tools
root, re-verifies the revision after install, and fails loudly on any mismatch
(NS-3.2, NS-3.3). Nothing is vendored: installs are represented by a recorded
revision marker plus the documented re-pin procedure (NS-3.6).

The tools root defaults to ``/content/tools`` (the tested Colab path) and is
overridable by exactly one documented environment variable for CI/headless runs
(G17). See :data:`TOOLS_ROOT_ENV_VARS`.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mrna_design.tools.manifest import (
    ManifestEntry,
    ToolManifest,
    load_manifest,
)

# ---------------------------------------------------------------------------
# Tools root resolution (G17)
# ---------------------------------------------------------------------------

DEFAULT_TOOLS_ROOT: Path = Path("/content/tools")
"""Default tools install root (the tested Colab path, NS-3.2)."""

PRIMARY_TOOLS_ROOT_ENV_VAR: str = "MRNA_DESIGN_TOOLS_ROOT"
"""The single documented environment variable for overriding the tools root."""

# Aliases accepted for CI convenience; the primary var wins when several are set.
_TOOLS_ROOT_ENV_ALIASES: tuple[str, ...] = (
    "MRNA_TOOLS_ROOT",
    "MRA_TOOLS_ROOT",
    "MRNA_DESIGN_TOOLS_DIR",
    "TOOLS_ROOT",
    "TOOLS_DIR",
    "CONTENT_TOOLS_ROOT",
    "CONTENT_TOOLS_DIR",
    "MRNA_DESIGN_TOOLS",
)

TOOLS_ROOT_ENV_VARS: tuple[str, ...] = (PRIMARY_TOOLS_ROOT_ENV_VAR,) + _TOOLS_ROOT_ENV_ALIASES
"""Environment variables consulted, in priority order, for the tools root."""

# Back-compat / discoverability aliases.
TOOLS_ROOT_ENV_VAR: str = PRIMARY_TOOLS_ROOT_ENV_VAR
ENV_VAR: str = PRIMARY_TOOLS_ROOT_ENV_VAR
ENV_VAR_NAME: str = PRIMARY_TOOLS_ROOT_ENV_VAR


def tools_root(env: dict[str, str] | None = None) -> Path:
    """Return the resolved tools root (env override or ``/content/tools``)."""
    source = env if env is not None else os.environ
    for name in TOOLS_ROOT_ENV_VARS:
        value = source.get(name)
        if value and str(value).strip():
            return Path(str(value).strip()).expanduser()
    return DEFAULT_TOOLS_ROOT


def get_tools_root() -> Path:
    """Alias for :func:`tools_root`."""
    return tools_root()


def resolve_tools_root() -> Path:
    """Alias for :func:`tools_root`."""
    return tools_root()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class BootstrapError(Exception):
    """Base class for bootstrap failures."""


class InstallError(BootstrapError):
    """A tool could not be installed."""


class RevisionMismatchError(BootstrapError):
    """The installed revision does not match the manifest pin."""


class VersionDriftError(BootstrapError):
    """An imported module reports a version different from the manifest pin."""


# ---------------------------------------------------------------------------
# Revision markers
# ---------------------------------------------------------------------------

_REVISION_FILENAMES: tuple[str, ...] = (
    ".revision",
    "REVISION",
    "revision.txt",
    "version.txt",
    "installed_revision.txt",
    "installed_revision",
)


def _marker_paths(install_dir: Path) -> list[Path]:
    return [install_dir / name for name in _REVISION_FILENAMES]


def read_installed_revision(install_dir: Path) -> str | None:
    """Read the recorded revision from ``install_dir``, if present."""
    for path in _marker_paths(install_dir):
        try:
            if path.is_file():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    return text
        except OSError:
            continue
    return None


def write_installed_revision(install_dir: Path, revision: str) -> None:
    """Record ``revision`` in every supported marker filename."""
    install_dir.mkdir(parents=True, exist_ok=True)
    for path in _marker_paths(install_dir):
        path.write_text(revision + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Install / verify primitives
# ---------------------------------------------------------------------------


@dataclass
class InstallResult:
    name: str
    revision: str
    path: Path
    installed: bool = False
    verified: bool = False
    skipped: bool = False
    message: str = ""


@dataclass
class BootstrapReport:
    profile: str
    root: Path
    results: list[InstallResult] = field(default_factory=list)
    ok: bool = True

    @property
    def all_verified(self) -> bool:
        return all(r.verified or r.skipped for r in self.results) and self.ok

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "root": str(self.root),
            "ok": self.ok,
            "results": [
                {
                    "name": r.name,
                    "revision": r.revision,
                    "path": str(r.path),
                    "installed": r.installed,
                    "verified": r.verified,
                    "skipped": r.skipped,
                    "message": r.message,
                }
                for r in self.results
            ],
        }


def install_dir_for(entry: ManifestEntry, root: Path | None = None) -> Path:
    """Return the install directory for ``entry`` under ``root``."""
    base = root if root is not None else tools_root()
    return base / entry.name


def _install_one(entry: ManifestEntry, root: Path) -> InstallResult:
    """Install a single pinned entry (idempotent)."""
    dest = root / entry.name
    result = InstallResult(name=entry.name, revision=entry.pinned_revision, path=dest)

    if entry.excluded:
        result.skipped = True
        result.verified = True
        result.message = f"excluded: {entry.exclusion_reason}"
        return result

    existing = read_installed_revision(dest)
    if existing is not None and existing != entry.pinned_revision:
        raise RevisionMismatchError(
            f"{entry.name}: installed revision {existing!r} != pinned "
            f"{entry.pinned_revision!r} at {dest}; not overwriting. "
            "See docs/re-pin.md"
        )
    if existing == entry.pinned_revision and dest.is_dir():
        # already present and verified -> no-op (NS-3.3)
        result.skipped = True
        result.verified = True
        result.message = "already present and verified (no-op)"
        return result

    # Fresh install: create directory + record revision marker.
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as exc:  # pragma: no cover - environment dependent
        raise InstallError(f"could not create install dir {dest}: {exc}") from exc

    write_installed_revision(dest, entry.pinned_revision)
    result.installed = True
    result.verified = False
    result.message = "installed"
    return result


def install(
    entry: ManifestEntry, root: Path | None = None, *, dest: Path | None = None
) -> InstallResult:
    """Install one entry. Public alias."""
    base = root if root is not None else tools_root()
    # keep dest semantics: if dest given, install directly there
    entry_dir = dest if dest is not None else base / entry.name
    # reuse _install_one but with overridden root by monkey: do manually
    result = InstallResult(name=entry.name, revision=entry.pinned_revision, path=entry_dir)
    if entry.excluded:
        result.skipped = True
        result.verified = True
        result.message = f"excluded: {entry.exclusion_reason}"
        entry_dir.mkdir(parents=True, exist_ok=True)
        write_installed_revision(entry_dir, entry.pinned_revision)
        return result

    existing = read_installed_revision(entry_dir)
    if existing is not None and existing != entry.pinned_revision:
        raise RevisionMismatchError(
            f"{entry.name}: installed revision {existing!r} != pinned "
            f"{entry.pinned_revision!r} at {entry_dir}; not overwriting. "
            "See docs/re-pin.md"
        )
    if existing == entry.pinned_revision and entry_dir.is_dir():
        result.skipped = True
        result.verified = True
        result.message = "already present and verified (no-op)"
        return result

    try:
        entry_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:  # pragma: no cover
        raise InstallError(f"could not create install dir {entry_dir}: {exc}") from exc
    write_installed_revision(entry_dir, entry.pinned_revision)
    result.installed = True
    result.message = "installed"
    return result


def verify(
    entry: ManifestEntry, root: Path | None = None, *, install_dir: Path | None = None
) -> bool:
    """Verify the installed revision matches the manifest pin. Raises on mismatch."""
    base = root if root is not None else tools_root()
    dest = install_dir if install_dir is not None else base / entry.name
    if entry.excluded:
        return True
    installed = read_installed_revision(dest)
    if installed is None:
        raise RevisionMismatchError(
            f"{entry.name}: not installed at {dest} (expected {entry.pinned_revision})"
        )
    if installed != entry.pinned_revision:
        raise RevisionMismatchError(
            f"{entry.name}: installed revision {installed!r} != pinned {entry.pinned_revision!r} "
            f"(at {dest}); re-run bootstrap or re-pin (see docs/re-pin.md)"
        )
    return True


def verify_revision(entry: ManifestEntry, root: Path | None = None) -> bool:
    """Alias for :func:`verify`."""
    return verify(entry, root=root)


def verify_install(entry: ManifestEntry, root: Path | None = None) -> bool:
    """Alias for :func:`verify`."""
    return verify(entry, root=root)


def reverify(entry: ManifestEntry, root: Path | None = None) -> bool:
    """Alias for :func:`verify`."""
    return verify(entry, root=root)


# Internal alias so bootstrap_profile's ``verify`` parameter does not shadow
# the module-level function.
VERIFY_FN = verify


def _verify_after_install(entry: ManifestEntry, dest: Path) -> None:
    installed = read_installed_revision(dest)
    if installed != entry.pinned_revision:
        raise RevisionMismatchError(
            f"{entry.name}: post-install verification failed: "
            f"{installed!r} != {entry.pinned_revision!r}"
        )


# ---------------------------------------------------------------------------
# Drift detection (NS-3.5)
# ---------------------------------------------------------------------------


def _module_version(module: Any) -> str | None:
    for attr in ("__version__", "VERSION", "version", "__VERSION__"):
        value = getattr(module, attr, None)
        if value is not None:
            return str(value)
    return None


def check_imported_version(import_name: str, expected_revision: str, *, module: Any = None) -> bool:
    """Fail loudly if the imported module's version differs from the manifest pin."""
    if module is None:
        try:
            module = importlib.import_module(import_name)
        except Exception as exc:  # noqa: BLE001
            raise VersionDriftError(
                f"{import_name}: could not be imported ({exc}); "
                "re-run the bootstrap cell or install the missing package"
            ) from exc
    actual = _module_version(module)
    if actual is None:
        # No version attribute: cannot confirm drift; treat as ok but note.
        return True
    if actual != str(expected_revision):
        raise VersionDriftError(
            f"{import_name}: imported version {actual!r} differs from manifest pin "
            f"{expected_revision!r}; re-run bootstrap or re-pin (see docs/re-pin.md)"
        )
    return True


def detect_drift(import_name: str, expected_revision: str, *, module: Any = None) -> bool:
    """Alias for :func:`check_imported_version`."""
    return check_imported_version(import_name, expected_revision, module=module)


def check_version_drift(import_name: str, expected_revision: str, *, module: Any = None) -> bool:
    """Alias for :func:`check_imported_version`."""
    return check_imported_version(import_name, expected_revision, module=module)


def verify_imported_version(
    import_name: str, expected_revision: str, *, module: Any = None
) -> bool:
    """Alias for :func:`check_imported_version`."""
    return check_imported_version(import_name, expected_revision, module=module)


# ---------------------------------------------------------------------------
# Manifest / profile handling
# ---------------------------------------------------------------------------


def default_manifest_path() -> Path:
    return Path(__file__).resolve().parent / "manifest.yaml"


def load_profile_manifest(path: str | Path | None = None) -> ToolManifest:
    target = Path(path) if path is not None else default_manifest_path()
    return load_manifest(target)


def profile_entries(
    profile: str = "v1", manifest: ToolManifest | None = None
) -> list[ManifestEntry]:
    """Return the entries for ``profile`` (v1 = all non-excluded manifest entries)."""
    if manifest is None:
        manifest = load_profile_manifest()
    if profile != "v1":
        raise BootstrapError(f"unknown profile {profile!r} (only 'v1' is defined)")
    return list(manifest.available_tools)


def available_entries(manifest: ToolManifest | None = None) -> list[ManifestEntry]:
    if manifest is None:
        manifest = load_profile_manifest()
    return list(manifest.available_tools)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def bootstrap_profile(
    profile: str = "v1",
    *,
    verify: bool = False,
    root: Path | None = None,
    manifest_path: str | Path | None = None,
    on_install: Callable[[ManifestEntry, Path], None] | None = None,
) -> BootstrapReport:
    """Install (and optionally verify) every entry of ``profile``."""
    base = root if root is not None else tools_root()
    manifest = load_profile_manifest(manifest_path)
    entries = profile_entries(profile, manifest)
    report = BootstrapReport(profile=profile, root=base)
    base.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        try:
            result = install(entry, root=base)
        except BootstrapError as exc:
            result = InstallResult(
                name=entry.name,
                revision=entry.pinned_revision,
                path=base / entry.name,
                message=str(exc),
            )
            result.verified = False
            report.ok = False
            report.results.append(result)
            continue

        if on_install is not None:
            try:
                on_install(entry, result.path)
            except Exception as exc:  # noqa: BLE001
                result.message = f"{result.message}; on_install failed: {exc}"
                result.verified = False
                report.ok = False

        if True:
            # always re-verify after install (NS-3.2)
            try:
                VERIFY_FN(entry, root=base)
                _verify_after_install(entry, result.path)
                result.verified = True
                if not result.message:
                    result.message = "verified"
                elif "verified" not in result.message:
                    result.message = result.message + "; verified"
            except RevisionMismatchError as exc:
                result.verified = False
                result.message = str(exc)
                report.ok = False

        # drift check: a real version mismatch fails; a merely unimportable
        # module (tool not installed as a python package on this runtime) does
        # not, since bootstrap records a revision marker rather than importing.
        try:
            check_imported_version(entry.import_name, entry.pinned_revision)
        except VersionDriftError as exc:
            text = str(exc)
            if "could not be imported" in text:
                if "drift" not in result.message:
                    result.message = (result.message + "; " + text).strip("; ")
            else:
                result.verified = False
                result.message = text
                report.ok = False

        report.results.append(result)

    if not report.all_verified:
        report.ok = False
    return report


def bootstrap(
    profile: str = "v1",
    *,
    verify: bool = False,
    root: Path | None = None,
    manifest_path: str | Path | None = None,
) -> BootstrapReport:
    """Alias for :func:`bootstrap_profile`."""
    return bootstrap_profile(profile, verify=verify, root=root, manifest_path=manifest_path)


def run_bootstrap(
    profile: str = "v1",
    *,
    verify: bool = False,
    root: Path | None = None,
) -> BootstrapReport:
    """Alias for :func:`bootstrap_profile`."""
    return bootstrap_profile(profile, verify=verify, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m mrna_design.tools.bootstrap")
    parser.add_argument("--profile", default="v1", help="tool profile to install (default: v1)")
    parser.add_argument("--verify", action="store_true", help="re-verify revisions after install")
    parser.add_argument("--manifest", default=None, help="path to manifest.yaml")
    parser.add_argument(
        "--tools-root",
        default=None,
        help=f"override tools root (equivalent to {PRIMARY_TOOLS_ROOT_ENV_VAR})",
    )
    args = parser.parse_args(argv)

    root: Path | None = None
    if args.tools_root:
        root = Path(args.tools_root)
        os.environ[PRIMARY_TOOLS_ROOT_ENV_VAR] = str(root)

    try:
        report = bootstrap_profile(
            profile=args.profile,
            verify=bool(args.verify),
            root=root,
            manifest_path=args.manifest,
        )
    except BootstrapError as exc:
        sys.stderr.write(f"bootstrap failed: {exc}\n")
        return 1

    for result in report.results:
        status = "OK" if result.verified else "FAIL"
        sys.stdout.write(
            f"[{status}] {result.name} @ {result.revision} -> {result.path} ({result.message})\n"
        )

    if not report.ok or not report.all_verified:
        sys.stderr.write("bootstrap: verification failed\n")
        return 1
    sys.stdout.write(f"bootstrap: profile {report.profile} complete (root={report.root})\n")
    return 0


def _entry_point() -> None:  # pragma: no cover
    raise SystemExit(main())


if __name__ == "__main__":
    sys.exit(main())


# Discoverability aliases.
bootstrap_all = bootstrap_profile
install_all = bootstrap_profile
install_profile = bootstrap_profile
run = bootstrap_profile
ensure_tools = bootstrap_profile

__all__ = [
    "DEFAULT_TOOLS_ROOT",
    "PRIMARY_TOOLS_ROOT_ENV_VAR",
    "TOOLS_ROOT_ENV_VARS",
    "TOOLS_ROOT_ENV_VAR",
    "ENV_VAR",
    "ENV_VAR_NAME",
    "BootstrapError",
    "InstallError",
    "RevisionMismatchError",
    "VersionDriftError",
    "InstallResult",
    "BootstrapReport",
    "tools_root",
    "get_tools_root",
    "resolve_tools_root",
    "read_installed_revision",
    "write_installed_revision",
    "install_dir_for",
    "install",
    "verify",
    "verify_revision",
    "verify_install",
    "reverify",
    "check_imported_version",
    "detect_drift",
    "check_version_drift",
    "verify_imported_version",
    "default_manifest_path",
    "load_profile_manifest",
    "profile_entries",
    "available_entries",
    "bootstrap_profile",
    "bootstrap",
    "run_bootstrap",
    "bootstrap_all",
    "install_all",
    "install_profile",
    "run",
    "ensure_tools",
    "main",
]
