"""Tool manifest schema and loader (T11, NS-3.*).

The manifest is the single source of pinned upstream tools. The loader never
falls back to an unpinned entry (NS-3.2): an entry without a pinned revision
or a verification date fails schema validation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LICENCE_CLASSES = ("permissive", "research_only", "conditional", "excluded", "unverified")
"""Machine-readable licence classes (RD-2.7)."""


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    return None


class ManifestEntry(BaseModel):
    """One pinned upstream tool (NS-3.1)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(min_length=1)
    source_url: str = Field(min_length=1, alias="source")
    pinned_revision: str = Field(min_length=1, alias="version")
    licence: str = Field(min_length=1, alias="license")
    licence_class: str = Field(default="unverified", alias="license_class")
    import_name: str = Field(min_length=1, alias="entry_name")
    gpu_required: bool = False
    runtime_estimate: str | None = None
    disk_estimate: str | None = None
    last_verified: date
    stale_after_days: int = 90
    excluded: bool = False
    exclusion_reason: str | None = None
    maturity: str | None = None

    def __init__(self, /, **data: Any) -> None:
        # Normalise alternate keys before pydantic validation.
        normalized = dict(data)
        # source url aliases
        for key in ("source_url", "source", "url", "homepage"):
            if key in normalized and "source_url" not in normalized:
                normalized["source_url"] = normalized.pop(key)
                break
        # pinned revision aliases
        for key in (
            "pinned_revision",
            "version",
            "commit",
            "sha",
            "revision",
            "pinned_sha",
            "pinned_version",
        ):
            if key in normalized and "pinned_revision" not in normalized:
                normalized["pinned_revision"] = normalized.pop(key)
                break
        # licence aliases
        for key in ("licence", "license", "declared_licence", "declared_license"):
            if key in normalized and "licence" not in normalized:
                normalized["licence"] = normalized.pop(key)
                break
        # licence class
        for key in ("licence_class", "license_class", "licenceClass"):
            if key in normalized and "licence_class" not in normalized:
                normalized["licence_class"] = normalized.pop(key)
                break
        # import name
        for key in ("import_name", "entry_name", "entry", "module", "import", "entry_point"):
            if key in normalized and "import_name" not in normalized:
                normalized["import_name"] = normalized.pop(key)
                break
        # gpu
        for key in ("gpu_required", "gpu", "requires_gpu", "gpuRequired"):
            if key in normalized and "gpu_required" not in normalized:
                normalized["gpu_required"] = normalized.pop(key)
                break
        # runtime / disk
        for key in ("runtime_estimate", "runtime", "runtime_class", "runtime_disk_estimate"):
            if key in normalized and "runtime_estimate" not in normalized:
                normalized["runtime_estimate"] = normalized.pop(key)
                break
        for key in ("disk_estimate", "disk", "disk_class"):
            if key in normalized and "disk_estimate" not in normalized:
                normalized["disk_estimate"] = normalized.pop(key)
                break
        # combined runtime/disk estimate string -> split if possible
        combined = normalized.get("runtime_disk_estimate") or normalized.get("runtime_and_disk")
        if combined is not None and "runtime_estimate" not in normalized:
            if isinstance(combined, str) and "/" in combined:
                r, d = [part.strip() for part in combined.split("/", 1)]
                normalized["runtime_estimate"] = r
                normalized["disk_estimate"] = d
            else:
                normalized["runtime_estimate"] = combined
        # last verified
        for key in (
            "last_verified",
            "last_verified_date",
            "verified",
            "verified_at",
            "verification_date",
        ):
            if key in normalized and "last_verified" not in normalized:
                normalized["last_verified"] = normalized.pop(key)
                break
        # stale
        for key in ("stale_after_days", "stale_after", "staleness_days"):
            if key in normalized and "stale_after_days" not in normalized:
                normalized["stale_after_days"] = normalized.pop(key)
                break
        # excluded
        for key in ("excluded", "excluded_tool"):
            if key in normalized and "excluded" not in normalized:
                normalized["excluded"] = normalized.pop(key)
                break
        for key in ("exclusion_reason", "exclusion", "reason_excluded"):
            if key in normalized and "exclusion_reason" not in normalized:
                normalized["exclusion_reason"] = normalized.pop(key)
                break
        super().__init__(**normalized)

    @field_validator("licence_class")
    @classmethod
    def _valid_licence_class(cls, value: str) -> str:
        if value not in LICENCE_CLASSES:
            raise ValueError(
                f"licence_class must be one of {LICENCE_CLASSES}, got {value!r}",
            )
        return value

    @field_validator("last_verified", mode="before")
    @classmethod
    def _coerce_date(cls, value: Any) -> Any:
        if isinstance(value, date):
            return value
        converted = _as_date(value)
        if converted is None and value is not None:
            raise ValueError(f"last_verified: invalid date {value!r}")
        return converted

    @model_validator(mode="after")
    def _excluded_requires_reason(self) -> ManifestEntry:
        if self.excluded and not (self.exclusion_reason or "").strip():
            raise ValueError("excluded entry requires an exclusion_reason (NS-3.4)")
        return self

    @property
    def is_stale(self) -> bool:
        cutoff = self.last_verified + timedelta(days=self.stale_after_days)
        return date.today() > cutoff

    @property
    def requires_acknowledgement(self) -> bool:
        return self.licence_class in {"research_only", "conditional", "excluded", "unverified"}

    @property
    def id(self) -> str:
        return self.name


# aliases
ToolManifestEntry = ManifestEntry
Entry = ManifestEntry
ManifestItem = ManifestEntry


class ToolManifest(BaseModel):
    """Container for a manifest file (NS-3.1)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tools: list[ManifestEntry] = Field(default_factory=list, alias="entries")
    stale_after_days: int = 90

    def __init__(self, /, **data: Any) -> None:
        # accept a top-level list
        if isinstance(data.get("tools") if False else None, list):
            pass
        # If data itself is a list handled in loader; here normalize
        normalized = dict(data)
        if "tools" not in normalized and "entries" not in normalized:
            # maybe a list passed positionally
            pass
        super().__init__(**normalized)

    def __iter__(self) -> Any:
        return iter(self.tools)

    def __len__(self) -> int:
        return len(self.tools)

    def __getitem__(self, index: Any) -> Any:
        return self.tools[index]

    @property
    def entries(self) -> list[ManifestEntry]:
        return self.tools

    @property
    def excluded_tools(self) -> list[ManifestEntry]:
        return [e for e in self.tools if e.excluded]

    @property
    def available_tools(self) -> list[ManifestEntry]:
        return [e for e in self.tools if not e.excluded]


# aliases
Manifest = ToolManifest
ToolManifestDocument = ToolManifest


class ManifestLoader:
    """Loader helper."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None

    def load(self, path: str | Path | None = None) -> ToolManifest:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("manifest path is required")
        return load_manifest(target)

    def __call__(self, path: str | Path | None = None) -> ToolManifest:
        return self.load(path)


def load_manifest(path: str | Path) -> ToolManifest:
    """Load and validate a manifest file (NS-3.1, NS-3.2)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    if raw is None:
        raw = {}
    if isinstance(raw, list):
        raw = {"tools": raw}
    if not isinstance(raw, dict):
        raise ValueError("manifest must be a mapping or a list of entries")
    if "entries" in raw and "tools" not in raw:
        raw = {"tools": raw["entries"], **{k: v for k, v in raw.items() if k != "entries"}}
    manifest = ToolManifest.model_validate(raw)
    # ensure no unpinned entries slipped through
    for entry in manifest.tools:
        if not entry.pinned_revision.strip():
            raise ValueError(f"unpinned entry: {entry.name}")
        if entry.last_verified is None:
            raise ValueError(f"missing last_verified: {entry.name}")
    return manifest


def load_manifest_entries(path: str | Path) -> list[ManifestEntry]:
    return list(load_manifest(path).tools)


def read_manifest(path: str | Path) -> ToolManifest:
    return load_manifest(path)


__all__ = [
    "LICENCE_CLASSES",
    "Manifest",
    "ManifestEntry",
    "ManifestItem",
    "ToolManifest",
    "ToolManifestEntry",
    "ToolManifestDocument",
    "Entry",
    "ManifestLoader",
    "load_manifest",
    "load_manifest_entries",
    "read_manifest",
]
