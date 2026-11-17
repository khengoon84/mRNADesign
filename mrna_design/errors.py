"""Step-boundary error handling and run.log (T10, NS-5.*).

Exceptions are caught at step boundaries and rendered for a non-programmer:
what failed, which step, the likely cause, and the concrete next action. The
full traceback goes to ``run.log`` and is referenced, never shown (NS-5.1/5.2).
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mrna_design.ledger import append_log


class SkipBranch(Exception):
    """An optional branch was skipped (NS-5.4): not a failure."""


class StopBranch(Exception):
    """A user-requested branch with no fallback stopped the run (NS-5.4)."""


@dataclass
class RenderedError:
    """The user-facing rendering of a step failure (NS-5.1)."""

    step: str
    what_failed: str
    likely_cause: str
    next_action: str
    log_path: str | None = None
    messages: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"Step '{self.step}' failed: {self.what_failed}",
            f"Likely cause: {self.likely_cause}",
            f"Next action: {self.next_action}",
        ]
        if self.log_path:
            lines.append(f"Full traceback written to {self.log_path}; reference it for support.")
        return "\n".join(lines)


def _log_path(run_dir: Any) -> Path | None:
    if run_dir is None:
        return None
    path = Path(run_dir) / "run.log"
    return path


def classify_exception(exc: BaseException) -> tuple[str, str, str]:
    """Return (what_failed, likely_cause, next_action) for an exception."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if "modulenotfound" in text or "importerror" in text or "no module named" in text:
        return (
            "a required tool or library could not be imported",
            "a dependency is missing or not installed on this runtime",
            "re-run the bootstrap cell or install the missing package, then retry",
        )
    if "cuda" in text or "gpu" in text or "nvidia" in text:
        return (
            "a step requiring a GPU could not run",
            "no compatible GPU is available on this runtime",
            "set skip_gpu_tools=True or re-run on a GPU runtime; the default path is CPU-only",
        )
    if "length" in text or "max_aa" in text or "too long" in text or "exceeds" in text:
        return (
            "the protein is too long for this adapter",
            "the input exceeds the adapter's declared length cap",
            "split the protein or choose an adapter with a higher length limit",
        )
    if "valueerror" in text or "invalid" in text or "bad input" in text:
        return (
            "the input could not be processed",
            "the supplied value is invalid for this step",
            "check the field named in the message and re-run with a corrected value",
        )
    return (
        "the step raised an unexpected error",
        "an unclassified failure occurred during this step",
        "inspect run.log for the full traceback and retry the step",
    )


def log_traceback(run_dir: Any, exc: BaseException) -> Path | None:
    """Append the full traceback to run.log; return its path."""
    path = _log_path(run_dir)
    if path is None:
        return None
    try:
        append_log(
            path.parent, "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )
    except Exception:  # noqa: BLE001
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    return path


def render_exception(
    exc: BaseException,
    *,
    step: str = "unknown",
    run_dir: Any = None,
    what_failed: str | None = None,
    likely_cause: str | None = None,
    next_action: str | None = None,
) -> RenderedError:
    """Render an exception without exposing its traceback (NS-5.1)."""
    default_what, default_cause, default_action = classify_exception(exc)
    log_path = log_traceback(run_dir, exc)
    rendered = RenderedError(
        step=step,
        what_failed=what_failed or default_what,
        likely_cause=likely_cause or default_cause,
        next_action=next_action or default_action,
        log_path=str(log_path) if log_path is not None else None,
    )
    return rendered


def render_error(*args: Any, **kwargs: Any) -> RenderedError:
    """Alias for :func:`render_exception`."""
    return render_exception(*args, **kwargs)


def render_step_error(*args: Any, **kwargs: Any) -> RenderedError:
    return render_exception(*args, **kwargs)


def handle_step_exception(
    step: str,
    exc: BaseException,
    *,
    run_dir: Any = None,
    **overrides: Any,
) -> RenderedError:
    """Catch at a step boundary: log traceback, return rendered error."""
    return render_exception(exc, step=step, run_dir=run_dir, **overrides)


def step_boundary(step: str, run_dir: Any = None) -> Any:
    """Context manager that catches and renders step failures."""

    class _Boundary:
        def __enter__(self) -> _Boundary:
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
            if exc is None:
                return False
            rendered = render_exception(exc, step=step, run_dir=run_dir)
            # store on the exception for callers
            import contextlib

            with contextlib.suppress(Exception):
                exc.rendered = rendered
            return True  # suppress

    return _Boundary()


def run_step(
    step: str, func: Callable[..., Any], *args: Any, run_dir: Any = None, **kwargs: Any
) -> tuple[Any, RenderedError | None]:
    """Run ``func`` at a step boundary; return (result, error_or_None)."""
    try:
        return func(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001
        return None, render_exception(exc, step=step, run_dir=run_dir)


# skip / stop helpers (NS-5.4)
def render_skip(branch: str, reason: str, recovery_hint: str) -> str:
    return f"Skipped '{branch}': {reason}\nRecovery: {recovery_hint}"


def render_stop(branch: str, message: str) -> str:
    return f"Stopped at '{branch}': {message}"


__all__ = [
    "RenderedError",
    "SkipBranch",
    "StopBranch",
    "classify_exception",
    "handle_step_exception",
    "log_traceback",
    "render_error",
    "render_exception",
    "render_skip",
    "render_stop",
    "render_step_error",
    "run_step",
    "step_boundary",
]
