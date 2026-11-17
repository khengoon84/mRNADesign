"""Licence responsibility notices (T15, RD-2.7, NS-3.8).

The engine-selective printed notice (G26) wording lives here and is reused
verbatim by T16/T64/T67 so the restriction is stated identically everywhere.
"""

from __future__ import annotations

RESPONSIBILITY_NOTICE = (
    "Commercial use of this engine's output is not granted by this project. "
    "Contact the rights holder before using the output commercially."
)
"""The single wording for any research-only / restricted dependency (G26)."""

RESEARCH_ONLY_NOTICE = RESPONSIBILITY_NOTICE


def responsibility_notice(engine: str | None = None) -> str:
    """Return the responsibility notice, optionally naming the engine."""
    if engine:
        return f"{engine}: {RESPONSIBILITY_NOTICE}"
    return RESPONSIBILITY_NOTICE


def research_only_notice(engine: str | None = None) -> str:
    """Alias for :func:`responsibility_notice`."""
    return responsibility_notice(engine)


def print_restricted_notice(engine: str | None = None) -> str:
    """Return (not print) the notice text for a restricted dependency."""
    return responsibility_notice(engine)


# aliases
NOTICE_TEXT = RESPONSIBILITY_NOTICE
RESTRICTED_NOTICE = RESPONSIBILITY_NOTICE


__all__ = [
    "RESPONSIBILITY_NOTICE",
    "RESEARCH_ONLY_NOTICE",
    "NOTICE_TEXT",
    "RESTRICTED_NOTICE",
    "responsibility_notice",
    "research_only_notice",
    "print_restricted_notice",
]
