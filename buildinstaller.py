"""Build CalendifierSetup.exe (single-file per-user installer).

Workflow:

1) Build app bundle:     python buildexe.py
2) Build payload+setup:  python buildinstaller.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

APP_NAME = "Calendifier"
SETUP_NAME = "CalendifierSetup"
ICON = PROJECT_ROOT / "assets" / "calendar_icon.ico"


def _require_windows() -> None:
    if os.name != "nt":
        raise SystemExit("buildinstaller.py is Windows-only")


def _run(cmd: list[str]) -> None:
    print("\n> " + " ".join(cmd))
    subprocess.check_call(cmd)


def _retry_unlink(path: Path, *, attempts: int = 20, delay_s: float = 0.15) -> None:
    """Try to delete a file that may be briefly locked by AV/Explorer."""
    if not path.exists():
        return

    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return
        except OSError as exc:
            last_exc = exc
            time.sleep(delay_s)
    if last_exc:
        raise last_exc


def _replace_file(src: Path, dst: Path) -> None:
    """Replace dst with src (dst may be locked if the setup exe is running)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        _retry_unlink(dst)
    shutil.move(str(src), str(dst))


def main() -> int:
    _require_windows()

    # 1) Build payload zip + manifest.
    _run([sys.executable, "-m", "installer.build_payload"])

    final_dist_root = PROJECT_ROOT / "dist-installer"
    work_root = PROJECT_ROOT / "build" / "installer"

    # Build into a temp dist folder, then move into place. Avoids PyInstaller
    # failing mid-build if an old setup exe is still locked.
    temp_dist_root = PROJECT_ROOT / "dist-installer.build"
    for p in (temp_dist_root, work_root):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)

    entrypoint = PROJECT_ROOT / "installer" / "app.py"
    payload_zip = PROJECT_ROOT / "installer" / "payload" / "payload.zip"
    manifest_json = PROJECT_ROOT / "installer" / "payload" / "manifest.json"
    if not payload_zip.exists() or not manifest_json.exists():
        raise SystemExit("Payload build did not produce payload.zip/manifest.json")

    sep = os.pathsep
    add_data = [
        f"{payload_zip}{sep}installer/payload",
        f"{manifest_json}{sep}installer/payload",
        # Version file (read by the version module) and the licence text.
        f"{PROJECT_ROOT / 'VERSION'}{sep}.",
        f"{PROJECT_ROOT / 'LICENSE'}{sep}.",
        # Ship the icon assets so the installer can set its own window icon and
        # deploy them next to the app exe for taskbar/shortcut consistency.
        f"{PROJECT_ROOT / 'assets'}{sep}assets",
    ]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        SETUP_NAME,
        "--icon",
        str(ICON),
        "--paths",
        str(PROJECT_ROOT),
        "--distpath",
        str(temp_dist_root),
        "--workpath",
        str(work_root),
    ]
    for spec in add_data:
        cmd.extend(["--add-data", spec])

    # The UI worker is loaded dynamically by the installer window.
    cmd.extend(["--hidden-import", "installer.ui.worker"])

    cmd.append(str(entrypoint))
    _run(cmd)

    built_exe = temp_dist_root / f"{SETUP_NAME}.exe"
    final_exe = final_dist_root / f"{SETUP_NAME}.exe"
    if built_exe.exists():
        try:
            _replace_file(built_exe, final_exe)
        except PermissionError as exc:
            raise SystemExit(
                "Unable to overwrite the installer EXE because it is in use.\n"
                "Close any running installer instances, then try again."
            ) from exc

        shutil.rmtree(temp_dist_root, ignore_errors=True)
        print(f"\nBuilt: {final_exe}")
        return 0

    print("\nBuild finished; expected installer exe not found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
