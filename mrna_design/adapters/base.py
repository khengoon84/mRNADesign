"""Shared adapter base (T08, RD-6.*, AD-7).

One module per upstream tool lives alongside this one; each subclass declares
``id``, ``capabilities()``, ``run()`` and the determinism/licence/provenance
attributes. This module imports only ``mrna_design.design`` (AD-1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mrna_design.design.contracts import DesignRequest, DesignResult
from mrna_design.design.plugins import (
    CONTRACT_VERSION,
    Capabilities,
    adapter_determinism,
    adapter_id,
    adapter_licence,
    declared_contract_version,
    is_experimental,
)


class Guard:
    """Lightweight budget handle passed to ``run()`` (placeholder, T13+).

    Adapters may ignore it; it exists so the signature is stable.
    """

    def budget(self, *, tool: str) -> Guard:
        return self

    def __enter__(self) -> Guard:
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


class BaseAdapter(ABC):
    """Abstract base for every design adapter (RD-6.1)."""

    id: str = ""
    contract_version: str = CONTRACT_VERSION
    deterministic: str = "deterministic"
    licence: str = "unverified"
    license: str = "unverified"
    maturity: str = "proven"
    provenance: Any = None
    # normalise in __init__? keep None default

    @abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abstractmethod
    def run(self, request: DesignRequest, guard: Guard | None = None) -> DesignResult: ...

    # aliases / helpers -------------------------------------------------------
    @property
    def determinism(self) -> str:
        return adapter_determinism(self)

    @property
    def licence_class(self) -> str:
        return adapter_licence(self)

    def is_experimental(self) -> bool:
        return is_experimental(self)

    def declared_contract_version(self) -> str:
        return declared_contract_version(self)

    def adapter_id(self) -> str:
        return adapter_id(self)

    def is_available(self) -> tuple[bool, str]:
        """Override to report runtime availability (RD-2.2). Default: available."""
        return True, ""

    def availability(self) -> tuple[bool, str]:
        return self.is_available()

    def available(self) -> tuple[bool, str]:
        return self.is_available()


# alias
Adapter = BaseAdapter


__all__ = ["Adapter", "BaseAdapter", "Guard", "Plugin", "BasePlugin"]
Plugin = BaseAdapter
BasePlugin = BaseAdapter
