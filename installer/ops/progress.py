"""Shared progress-reporting helper for installer operations.

Operations receive an optional ``progress`` callback. The UI advances the
progress bar only for dict payloads carrying an integer ``pct`` (see
``installer.ui._main_window_actions.on_progress``); a bare string updates the
status text only. Both install and uninstall emit through this single helper so
the bar behaves identically for every operation.
"""

from __future__ import annotations


def emit_progress(progress, *, pct: int | None, message: str) -> None:  # noqa: ANN001
    """Send a progress update; ``pct`` None sends text only, else a {pct,message}."""
    if not progress:
        return
    if pct is None:
        progress(message)
    else:
        progress({"pct": int(pct), "message": message})
