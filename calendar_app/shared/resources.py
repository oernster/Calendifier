"""Runtime resource discovery.

Locates the bundled Calendifier icon files without hard-coding absolute paths,
so the same lookup works from a source checkout and from a PyInstaller bundle
(onefile via ``sys._MEIPASS`` or onedir via ``_internal``). Icons live under
``assets/`` in the repo and may be bundled either flat or under ``assets/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Native Windows icon first, then PNGs in descending size as fallbacks.
_ICO_NAME = "calendar_icon.ico"
_PNG_NAMES = (
    "calendar_icon.png",
    "calendar_icon_256x256.png",
    "calendar_icon_128x128.png",
    "calendar_icon_64x64.png",
    "calendar_icon_48x48.png",
    "calendar_icon_32x32.png",
    "calendar_icon_16x16.png",
)


def _candidate_roots(project_root: Path | None) -> list[Path]:
    """Directories that may contain the icon (source + frozen layouts)."""
    roots: list[Path] = []

    if project_root is not None:
        roots.append(project_root)

    # PyInstaller onefile unpack dir.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))

    # Next to the executable, and the onedir _internal sibling.
    exe_dir = Path(sys.executable).resolve().parent
    roots.append(exe_dir)
    roots.append(exe_dir / "_internal")

    # Repo layout: calendar_app/shared/resources.py -> repo root is parents[2].
    roots.append(Path(__file__).resolve().parents[2])

    # Current working directory as a last resort.
    roots.append(Path.cwd())

    # De-duplicate while preserving order; expand each root with its assets/ dir.
    expanded: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for candidate in (root, root / "assets"):
            key = str(candidate)
            if key not in seen:
                seen.add(key)
                expanded.append(candidate)
    return expanded


def _first_existing(names: tuple[str, ...], project_root: Path | None) -> Path | None:
    for root in _candidate_roots(project_root):
        for name in names:
            path = root / name
            if path.is_file():
                return path
    return None


def find_app_icon_path(*, project_root: Path | None = None) -> Path | None:
    """Locate the Calendifier ``.ico`` for window/taskbar/shortcut icons."""
    return _first_existing((_ICO_NAME,), project_root)


def find_qt_window_icon_path(*, project_root: Path | None = None) -> Path | None:
    """Locate an icon for Qt windows, preferring ``.ico`` then a PNG fallback."""
    return _first_existing((_ICO_NAME, *_PNG_NAMES), project_root)
