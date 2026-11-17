"""T14 integration adapter contract (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))

import fixtures.plugins.fixture_adapter  # noqa: F401,E402

from mrna_design.design.contracts import DesignRequest  # noqa: E402
from mrna_design.design.registry import REGISTRY  # noqa: E402


def test_adapter_contract() -> None:
    plugin = REGISTRY.get("fixture")
    request = DesignRequest(protein="MKV")
    result = plugin.run(request)
    result.validated()
    assert result.cds == "ATGAAAGTTTAA"
