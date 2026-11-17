"""The versioned plugin contract for design adapters (T08, RD-6.*).

An adapter is a plugin when it declares an ``id``, a ``capabilities()`` result,
a ``run()`` method, a determinism class, a licence class, a provenance record
and a contract version (RD-6.1). Registration adds it to the registry without
editing the notebook or the core registry (RD-6.2): an entry point or manifest
entry is enough.

This module has no dependency on the QC or construct modules (AD-1).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

CONTRACT_VERSION = "1.0"
"""The current plugin contract version (RD-6.1).

An adapter declaring a different version is refused rather than coerced
(RD-6.1); the refusal names both versions.
"""

CAPABILITY_CLASSES = frozenset({"design", "metrics", "predictor"})
"""The capability classes the contract suite is scoped over (plan AD-3)."""


class ContractVersionError(ValueError):
    """Raised when a plugin's declared contract version is incompatible."""


class ContractVersionMismatchError(ContractVersionError):
    """A plugin declared a contract version different from :data:`CONTRACT_VERSION`."""


class PluginContractError(ValueError):
    """A plugin failed the structural plugin contract (RD-6.1)."""


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


@dataclass
class _CapabilitiesData:
    """Internal canonical storage; the public :class:`Capabilities` wraps it."""


class Capabilities:
    """What an adapter declares about itself (RD-2.1, RD-6.1).

    Fields (all optional with conservative defaults):

    - ``designs``: regions produced (``"cds"``, ``"utr5"``, ``"utr3"``).
      Accepted aliases: ``regions``, ``produces``, ``produced_regions``.
    - ``qc_only``: whether the adapter is QC-only (produces no sequence).
    - ``gpu_required``: whether a GPU is required to run.
    - ``min_aa`` / ``max_aa`` (and ``min_length`` / ``max_length``): supported
      protein length range. ``length_range`` may be given as a ``(min, max)``
      tuple instead.
    - ``determinism``: determinism class (``seeded`` / ``snapshot`` /
      ``deterministic``). Alias: ``deterministic``.
    - ``licence``: licence class (``permissive`` / ``research_only`` /
      ``conditional`` / ``excluded`` / ``unverified``). Aliases: ``license``,
      ``licence_class``.
    - ``maturity``: ``proven`` or ``experimental`` (RD-2.10).
    - ``description``: one-line plain-language description for the notebook.
    """

    def __init__(
        self,
        *,
        designs: Any = None,
        regions: Any = None,
        produces: Any = None,
        produced_regions: Any = None,
        qc_only: bool = False,
        gpu_required: bool = False,
        min_aa: int | None = None,
        max_aa: int | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        length_range: Any = None,
        determinism: str | None = None,
        deterministic: str | None = None,
        licence: str | None = None,
        license: str | None = None,
        licence_class: str | None = None,
        maturity: str = "proven",
        description: str = "",
        summary: str | None = None,
        one_line: str | None = None,
        one_line_description: str | None = None,
        blurb: str | None = None,
        regions_produced: Any = None,
        **extra: Any,
    ) -> None:
        resolved_designs = _first_not_none(
            designs, regions, produces, produced_regions, extra.pop("designs", None)
        )
        # extra may carry unknown aliases; try common ones
        if resolved_designs is None:
            for key in ("produced", "regions_produced", "outputs"):
                if key in extra:
                    resolved_designs = extra.pop(key)
                    break
        self.designs: tuple[str, ...] = _as_tuple(resolved_designs)
        self.regions: tuple[str, ...] = self.designs
        self.produces: tuple[str, ...] = self.designs
        self.produced_regions: tuple[str, ...] = self.designs

        self.qc_only: bool = bool(
            qc_only or extra.get("qc_only", False) or extra.get("qcOnly", False)
        )
        self.gpu_required: bool = bool(
            gpu_required or extra.get("gpu_required", False) or extra.get("gpuRequired", False)
        )

        # length range
        if length_range is not None:
            try:
                lo, hi = length_range
                if min_aa is None:
                    min_aa = lo
                if max_aa is None:
                    max_aa = hi
            except Exception:  # noqa: BLE001
                pass
        if min_length is not None and min_aa is None:
            min_aa = min_length
        if max_length is not None and max_aa is None:
            max_aa = max_length
        # extra aliases
        if min_aa is None:
            min_aa = extra.get("min_aa", extra.get("min_length", extra.get("min")))
        if max_aa is None:
            max_aa = extra.get("max_aa", extra.get("max_length", extra.get("max")))
        # extra aliases for the length range
        if length_range is None:
            for key in ("aa_range", "size_range", "length_bounds", "aa_bounds"):
                if key in extra and extra.get(key) is not None:
                    length_range = extra.pop(key)
                    break
        if length_range is not None:
            try:
                lo, hi = length_range
                if min_aa is None:
                    min_aa = lo
                if max_aa is None:
                    max_aa = hi
            except Exception:  # noqa: BLE001
                pass
        if min_length is not None and min_aa is None:
            min_aa = min_length
        if max_length is not None and max_aa is None:
            max_aa = max_length
        if min_aa is None:
            min_aa = extra.get("min_aa", extra.get("min_length", extra.get("min")))
        if max_aa is None:
            max_aa = extra.get("max_aa", extra.get("max_length", extra.get("max")))
        self.min_aa = min_aa
        self.max_aa = max_aa
        self.length_range = length_range if length_range is not None else (min_aa, max_aa)

        self.determinism: str = (
            _first_not_none(
                determinism, deterministic, extra.get("determinism"), extra.get("deterministic")
            )
            or "deterministic"
        )
        self.deterministic: str = self.determinism

        resolved_licence = _first_not_none(
            licence,
            license,
            licence_class,
            extra.get("licence"),
            extra.get("license"),
            extra.get("licence_class"),
        )
        self.licence: str = resolved_licence or "unverified"
        self.license: str = self.licence
        self.licence_class: str = self.licence

        self.maturity: str = (
            maturity if maturity is not None else (extra.get("maturity") or "proven")
        )
        if self.maturity is None:
            self.maturity = "proven"
        resolved_description = _first_not_none(
            description,
            summary,
            one_line,
            one_line_description,
            blurb,
            extra.get("description"),
            extra.get("summary"),
            extra.get("one_line"),
            extra.get("one_line_description"),
            extra.get("blurb"),
        )
        self.description: str = resolved_description or ""

        # stash any remaining extras (harmless)
        self._extra = {k: v for k, v in extra.items()}

    # convenience
    @property
    def regions_produced(self) -> tuple[str, ...]:
        return self.designs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Capabilities):
            return NotImplemented
        return (
            self.designs == other.designs
            and self.qc_only == other.qc_only
            and self.gpu_required == other.gpu_required
            and self.min_aa == other.min_aa
            and self.max_aa == other.max_aa
            and self.determinism == other.determinism
            and self.licence == other.licence
            and self.maturity == other.maturity
            and self.description == other.description
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.designs,
                self.qc_only,
                self.gpu_required,
                self.min_aa,
                self.max_aa,
                self.determinism,
                self.licence,
                self.maturity,
                self.description,
            )
        )

    def __repr__(self) -> str:
        return (
            f"Capabilities(designs={self.designs!r}, qc_only={self.qc_only!r}, "
            f"gpu_required={self.gpu_required!r}, min_aa={self.min_aa!r}, "
            f"max_aa={self.max_aa!r}, determinism={self.determinism!r}, "
            f"licence={self.licence!r}, maturity={self.maturity!r}, "
            f"description={self.description!r})"
        )


def declared_contract_version(plugin: Any) -> str:
    """Return the contract version an adapter declares (RD-6.1)."""
    for attr in ("contract_version", "CONTRACT_VERSION", "contractVersion"):
        value = getattr(plugin, attr, None)
        if value is not None:
            return str(value)
    caps = None
    try:
        caps = plugin.capabilities() if callable(getattr(plugin, "capabilities", None)) else None
    except Exception:  # noqa: BLE001
        caps = None
    if caps is not None:
        for attr in ("contract_version", "CONTRACT_VERSION", "contractVersion"):
            value = getattr(caps, attr, None)
            if value is not None:
                return str(value)
    return CONTRACT_VERSION


def check_contract_version(plugin: Any) -> None:
    """Raise :class:`ContractVersionMismatchError` if versions differ (RD-6.1)."""
    declared = declared_contract_version(plugin)
    if declared != CONTRACT_VERSION:
        raise ContractVersionMismatchError(
            f"contract version mismatch: plugin declares {declared!r}, "
            f"registry requires {CONTRACT_VERSION!r}",
        )


def is_experimental(plugin: Any) -> bool:
    """Whether an adapter is experimental (RD-2.10)."""
    maturity = None
    try:
        caps = plugin.capabilities() if callable(getattr(plugin, "capabilities", None)) else None
        if caps is not None:
            maturity = getattr(caps, "maturity", None)
    except Exception:  # noqa: BLE001
        pass
    if maturity is None:
        maturity = getattr(plugin, "maturity", None)
    return str(maturity).lower() == "experimental"


def adapter_id(plugin: Any) -> str:
    """Return an adapter's id (RD-6.1)."""
    value = getattr(plugin, "id", None)
    if value is None and callable(getattr(plugin, "capabilities", None)):
        try:
            value = getattr(plugin.capabilities(), "id", None)
        except Exception:  # noqa: BLE001
            value = None
    if value is None:
        raise PluginContractError("plugin is missing required 'id'")
    return str(value)


def adapter_determinism(plugin: Any) -> str:
    """Return an adapter's determinism class."""
    # Prefer an explicitly overridden attribute. ``deterministic`` is the
    # historical name; ``determinism`` is the alternate spelling. A subclass that
    # sets either one (in its own __dict__ or class __dict__) wins over the
    # base default.
    for attr in ("determinism", "deterministic"):
        if attr in getattr(plugin, "__dict__", {}):
            value = plugin.__dict__.get(attr)
            if value is not None:
                return str(value)
    for attr in ("determinism", "deterministic"):
        for cls in type(plugin).__mro__:
            if cls is object:
                continue
            if (
                attr in cls.__dict__
                and cls.__dict__.get(attr) is not None
                and cls.__name__ != "BaseAdapter"
            ):
                return str(cls.__dict__[attr])
    for attr in ("deterministic", "determinism"):
        value = getattr(plugin, attr, None)
        if value is not None:
            return str(value)
    try:
        caps = plugin.capabilities() if callable(getattr(plugin, "capabilities", None)) else None
        if caps is not None:
            value = getattr(caps, "determinism", None) or getattr(caps, "deterministic", None)
            if value is not None:
                return str(value)
    except Exception:  # noqa: BLE001
        pass
    return "deterministic"


def adapter_licence(plugin: Any) -> str:
    """Return an adapter's licence class."""
    for attr in ("licence", "license", "licence_class"):
        value = getattr(plugin, attr, None)
        if value is not None:
            return str(value)
    try:
        caps = plugin.capabilities() if callable(getattr(plugin, "capabilities", None)) else None
        if caps is not None:
            value = (
                getattr(caps, "licence", None)
                or getattr(caps, "license", None)
                or getattr(caps, "licence_class", None)
            )
            if value is not None:
                return str(value)
    except Exception:  # noqa: BLE001
        pass
    return "unverified"
