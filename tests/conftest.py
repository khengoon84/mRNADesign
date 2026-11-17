"""Shared pytest configuration.

Marker policy (SPEC-notebook-shell.md NS-6.2): `network`, `gpu` and `e2e` tests
are declared in `pyproject.toml` and deselected by the default invocation. They
are opt-in per runtime because their outcome depends on the machine, not only on
the code — `pytest -m network`, `pytest -m gpu`, `pytest -m e2e`.

Fixtures shared by more than one test module belong here; fixture data lives in
`tests/fixtures/` and is immutable (T04).
"""
