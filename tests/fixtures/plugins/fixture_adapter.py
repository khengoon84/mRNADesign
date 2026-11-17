"""Fixture design adapter for the contract suite (T14, RD-SC10).

Registers through the public plugin path only: importing this module adds it to
``mrna_design.design.REGISTRY``. No core edit is required to add an engine.
"""

from __future__ import annotations

from mrna_design.adapters.base import BaseAdapter, Guard
from mrna_design.design.contracts import DesignRequest, DesignResult, RegionBounds
from mrna_design.design.plugins import CONTRACT_VERSION, Capabilities

# A tiny, hand-verifiable CDS for protein "MKV": M K V stop.
_FIXTURE_CDS = "ATGAAAGTTTAA"


class FixtureAdapter(BaseAdapter):
    id = "fixture"
    contract_version = CONTRACT_VERSION
    deterministic = "deterministic"
    licence = "permissive"
    license = "permissive"
    maturity = "proven"
    provenance = {"source": "fixture"}

    def capabilities(self) -> Capabilities:
        return Capabilities(
            designs=("cds",),
            determinism="deterministic",
            licence="permissive",
            maturity="proven",
            min_aa=1,
            max_aa=1000,
            description="Fixture adapter for the contract suite.",
        )

    def run(self, request: DesignRequest, guard: Guard | None = None) -> DesignResult:
        protein = request.protein or "MKV"
        # Build a trivial CDS: ATG + one codon per amino acid + stop.
        # For the fixture we only support the canonical "MKV".
        cds = _FIXTURE_CDS
        return DesignResult(
            protein=protein,
            cds=cds,
            has_start=True,
            has_stop=True,
            region_bounds={"cds": RegionBounds(start=0, end=len(cds))},
            adapter_id=self.id,
            tool_version="fixture-1.0",
            resolved_params={"seed": request.seed},
            seed=request.seed,
            provenance={"source": "fixture"},
        )


# Register through the public path on import.
from mrna_design.design.registry import REGISTRY  # noqa: E402

REGISTRY.register(FixtureAdapter())
