"""Structural test: source modules stay within the line limit.

Per the project's engineering standards a module over ~400 lines should be
decomposed. New modules MUST comply.

Two escape hatches, both deliberately narrow:

* ``_DATA_MODULES`` are pure lookup tables (data, not logic) and are exempt.
* ``_LEGACY_OVER_LIMIT`` predate this rule and are tracked technical debt. The
  set is a ratchet: a file may leave it once decomposed, but it must never grow,
  and ``test_legacy_allowlist_has_no_stale_entries`` fails if an entry is no
  longer actually over the limit (or has been deleted).
"""

from __future__ import annotations

from pathlib import Path

_MAX_LINES = 400
_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_DIRS = ("calendar_app",)
_ROOT_MODULES = ("version.py", "stamp_version.py")

# Pure data tables (data, not logic): permanently exempt from the line limit.
_DATA_MODULES = frozenset(
    {
        "calendar_app/core/observance_data.py",
    }
)

# Modules already over the limit when this rule was introduced. Tracked debt:
# this set may only shrink. Do not add to it; decompose new code instead.
_LEGACY_OVER_LIMIT = frozenset(
    {
        "calendar_app/ui/main_window.py",
        "calendar_app/ui/event_panel.py",
        "calendar_app/ui/settings_dialog.py",
        "calendar_app/ui/rrule_dialog_pyside.py",
        "calendar_app/ui/event_dialog.py",
        "calendar_app/ui/calendar_widget.py",
        "calendar_app/data/database.py",
        "calendar_app/core/multi_country_holiday_provider.py",
        "calendar_app/localization/i18n_manager.py",
        "calendar_app/core/recurring_event_generator.py",
        "calendar_app/config/themes.py",
        "calendar_app/ui/rrule_dialog.py",
        "calendar_app/ui/clock_widget.py",
        "calendar_app/core/event_manager.py",
        "calendar_app/utils/ntp_client.py",
        "calendar_app/core/calendar_manager.py",
        "calendar_app/config/settings.py",
        "calendar_app/data/models.py",
        "calendar_app/localization/__init__.py",
        "calendar_app/localization/locale_detector.py",
        "calendar_app/ui/notes_widget.py",
    }
)


def _iter_source_files():
    for source_dir in _SOURCE_DIRS:
        yield from sorted((_ROOT / source_dir).rglob("*.py"))
    for module in _ROOT_MODULES:
        yield _ROOT / module


def _rel(path: Path) -> str:
    return path.relative_to(_ROOT).as_posix()


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_modules_within_line_limit():
    offenders = []
    for path in _iter_source_files():
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path)
        if rel in _DATA_MODULES or rel in _LEGACY_OVER_LIMIT:
            continue
        lines = _line_count(path)
        if lines > _MAX_LINES:
            offenders.append(f"{rel}: {lines} lines (limit {_MAX_LINES})")
    assert not offenders, "Modules over the line limit (decompose them):\n" + "\n".join(
        offenders
    )


def test_legacy_allowlist_has_no_stale_entries():
    stale = []
    for rel in sorted(_LEGACY_OVER_LIMIT):
        path = _ROOT / rel
        if not path.exists():
            stale.append(f"{rel}: missing (remove from allowlist)")
        elif _line_count(path) <= _MAX_LINES:
            stale.append(f"{rel}: now within limit (remove from allowlist)")
    assert not stale, "Stale legacy allowlist entries:\n" + "\n".join(stale)
