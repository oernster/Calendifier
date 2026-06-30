"""Build the standalone Calendifier app bundle with PyInstaller.

Produces a onedir bundle at ``dist-pyinstaller/Calendifier/`` which the
installer (``buildinstaller.py``) then packages into a single setup exe.

Run from the repo root inside the venv:  python buildexe.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "Calendifier"
ENTRYPOINT = "main.py"
ICON = Path("assets") / "calendar_icon.ico"

# App data folders that must be shipped beside the code (src, dest-in-bundle).
DATA_DIRS = (
    (
        "calendar_app/localization/translations",
        "calendar_app/localization/translations",
    ),
    (
        "calendar_app/localization/locale_holiday_translations",
        "calendar_app/localization/locale_holiday_translations",
    ),
    ("assets", "assets"),
)

# Loose data files (src, dest-in-bundle).
DATA_FILES = (("VERSION", "."),)

# Packages whose data/binaries/hidden imports PyInstaller must collect whole.
COLLECT_ALL = ("PySide6", "shiboken6", "holidays")

# Imports PyInstaller cannot discover statically.
HIDDEN_IMPORTS = ("holidays", "holidays.countries", "calendar_app")


def _add_data(src: str, dest: str) -> str:
    """Format an --add-data spec using the platform path separator."""
    return f"{src}{os.pathsep}{dest}"


def _pyinstaller_available() -> bool:
    """Return True if PyInstaller can be run from this interpreter."""
    if shutil.which("pyinstaller"):
        return True
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return False
    return True


def build_exe() -> int:
    """Create the standalone app bundle using PyInstaller."""
    print(f"Building {APP_NAME} app bundle...")

    root = Path(__file__).resolve().parent
    dist_dir = root / "dist-pyinstaller"
    build_dir = root / "build"
    spec_file = root / f"{APP_NAME}.spec"

    if not _pyinstaller_available():
        print("Error: PyInstaller not found. Activate the venv and pip install it.")
        return 1

    # Regenerate the spec from the CLI each run (the spec is a build artifact).
    for path in (spec_file, dist_dir, build_dir):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name={APP_NAME}",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--distpath=dist-pyinstaller",
        f"--icon={ICON}",
    ]
    for src, dest in (*DATA_DIRS, *DATA_FILES):
        cmd.append("--add-data=" + _add_data(src, dest))
    for package in COLLECT_ALL:
        cmd.append(f"--collect-all={package}")
    for name in HIDDEN_IMPORTS:
        cmd.append(f"--hidden-import={name}")
    cmd.append(ENTRYPOINT)

    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        print("PyInstaller build failed")
        return 1

    exe_path = dist_dir / APP_NAME / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[OK] App bundle created: {exe_path} ({size_mb:.1f} MB exe)")
        return 0

    print("App bundle not found after build")
    return 1


if __name__ == "__main__":
    sys.exit(build_exe())
