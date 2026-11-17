"""T14 plugin contract tests (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests"))

import fixtures.plugins.fixture_adapter  # noqa: F401,E402

from mrna_design.design.contracts import DesignRequest  # noqa: E402
from mrna_design.design.registry import REGISTRY  # noqa: E402


def test_fixture_registers() -> None:
    assert "fixture" in REGISTRY.ids()


def test_fixture_returns_validated_result() -> None:
    plugin = REGISTRY.get("fixture")
    request = DesignRequest(protein="MKV")
    result = plugin.run(request)
    validated = result.validated()
    assert validated.adapter_id == "fixture"


def test_contract_suite_parametrised_from_registry() -> None:
    ids = REGISTRY.ids()
    assert ids == ["fixture"]


def test_broken_plugin_rejected() -> None:
    from mrna_design.design.plugins import ContractVersionMismatchError, check_contract_version

    class Broken:
        id = "broken"
        contract_version = "9.9"

        def capabilities(self):  # type: ignore[no-untyped-def]
            from mrna_design.design.plugins import Capabilities

            return Capabilities(designs=("cds",))

        def run(self, request, guard=None):  # type: ignore[no-untyped-def]
            return None

    try:
        check_contract_version(Broken())
        raised = False
    except ContractVersionMismatchError:
        raised = True
    assert raised
