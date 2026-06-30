"""🔖 Stamp the central version into static docs.

Markdown and the GitHub Pages site cannot read the ``VERSION`` file at render
time, so each carries a delimited token::

    <!--VERSION-->1.7.0<!--/VERSION-->

This script reads ``VERSION`` and overwrites whatever sits between the
delimiters across the repo-root ``*.md`` files plus ``docs/**/*.html`` and
``docs/**/*.md``. It is idempotent (stamping an already-current file changes
nothing) and prints the files it touched.

The build scripts import and call :func:`main` so every packaged release ships
docs whose version matches ``VERSION``.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VERSION_FILE = PROJECT_ROOT / "VERSION"

# Token delimiters; the text between them is replaced with the current version.
_OPEN = "<!--VERSION-->"
_CLOSE = "<!--/VERSION-->"
_TOKEN_RE = re.compile(re.escape(_OPEN) + r".*?" + re.escape(_CLOSE), re.DOTALL)


def read_version() -> str:
    """Return the current version string from the VERSION file."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def _target_files(root: Path = PROJECT_ROOT) -> list[Path]:
    """Collect every doc under ``root`` that may carry a version token."""
    files = sorted(root.glob("*.md"))
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for pattern in ("**/*.html", "**/*.md"):
            files.extend(sorted(docs_dir.glob(pattern)))
    return files


def stamp_file(path: Path, version: str) -> bool:
    """Stamp one file; return True if its contents changed."""
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    replacement = f"{_OPEN}{version}{_CLOSE}"
    updated = _TOKEN_RE.sub(replacement, original)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main(root: Path = PROJECT_ROOT) -> None:
    """Stamp the current version across all doc targets under ``root``."""
    version = read_version()
    touched = [path for path in _target_files(root) if stamp_file(path, version)]
    if touched:
        print(f"🔖 Stamped version {version} into {len(touched)} file(s):")
        for path in touched:
            print(f"  - {path.relative_to(root)}")
    else:
        print(f"🔖 Version {version} already current; no files changed.")


if __name__ == "__main__":
    main()
