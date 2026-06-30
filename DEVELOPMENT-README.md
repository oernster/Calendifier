# Development & Build Guide

How to set up a development environment, run Calendifier and build it for each platform. For end-user installation see [README.md](README.md); for the test gate see [TESTING.md](TESTING.md); for the system design see [docs/architecture.md](docs/architecture.md).

## Prerequisites

- **Python 3.11 or newer** (development is on 3.13).
- **Git**.
- Platform build tooling, only for the platform you are packaging for:
  - **Windows:** nothing beyond Python; the installer is built in pure Python.
  - **macOS:** Xcode command-line tools, Homebrew and `create-dmg` (`brew install create-dmg`).
  - **Linux:** `flatpak` and `flatpak-builder`.

## Environment setup

```bash
git clone https://github.com/oernster/calendifier.git
cd calendifier

python -m venv venv
# Windows (PowerShell):  .\venv\Scripts\Activate.ps1
# macOS / Linux:         source venv/bin/activate

# requirements.txt holds runtime, dev and build dependencies
# (PySide6, holidays, pytest, black, flake8, PyInstaller, ...).
pip install -r requirements.txt
```

The web/Home-Assistant API server has a slimmer, separate dependency set in [api_requirements.txt](api_requirements.txt); install that instead when you only need the server.

## Running during development

```bash
# Desktop application
python main.py

# Web / Home-Assistant API server (FastAPI + Uvicorn)
python api_server.py
# Interactive API docs at http://localhost:8000/docs and /redoc
```

User data lives outside the repo, under `~/.calendar_app/` (`%USERPROFILE%\.calendar_app\` on Windows): `settings.json`, the SQLite database, logs, exports and backups.

## Versioning

The single source of truth for the version is the [VERSION](VERSION) file at the repo root. Nothing else hardcodes a version:

- `version.py` reads `VERSION` at runtime (frozen-build aware).
- `pyproject.toml` declares the version dynamically from `VERSION`.
- The build scripts read it through a `read_version()` helper.
- The docs deliberately carry no version string, so there is nothing to keep in sync: the version lives only in `VERSION`, read by `version.py` at runtime and by `pyproject.toml` as the dynamic project version.

To bump the version, edit `VERSION`. Everything else reads from it.

## Icons

All icon artifacts derive from the master `calendifier.png` (1024x1024):

```bash
python generate_icons.py
```

This regenerates the per-size PNG set, the multi-size Windows `assets/calendar_icon.ico`, the macOS `assets/calendar_icon.icns` and a scalable SVG, all under `assets/`. Run it after changing the master image.

## Building per platform

Every build reads the version from `VERSION` and stamps the docs first. Run from the repo root with the venv active.

### Windows (per-user installer)

Two stages produce a single, self-contained, per-user `CalendifierSetup.exe` that needs no admin rights:

```bash
python buildexe.py        # 1) app bundle    -> dist-pyinstaller/Calendifier/
python buildinstaller.py  # 2) payload+setup -> dist-installer/CalendifierSetup.exe
```

The bespoke PySide6 installer under [installer/](installer/) extracts the bundle to `%LOCALAPPDATA%\Programs\Calendifier`, writes a per-user uninstall entry in the registry, offers Start Menu and Desktop shortcuts and registers itself as its own uninstaller. `buildinstaller.py` stages the app into `payload.zip` (via `installer/build_payload.py`) before wrapping the onefile setup.

### macOS (signed DMG)

```bash
python builddmg.py
```

Builds a code-signed `Calendifier.app` with PyInstaller, packages it as `calendifier.dmg` and, when `APPLE_ID` and `APPLE_APP_PASSWORD` are set in the environment, notarizes and staples it. Helper modules `build_utils.py` and `dmg_icon.py` keep the script small. Requires the macOS prerequisites above.

### Linux (Flatpak)

```bash
chmod +x build_flatpak.sh cleanup_flatpak.sh
./build_flatpak.sh      # builds and optionally installs com.calendifier.Calendar
./cleanup_flatpak.sh    # uninstalls and purges flatpak build artefacts only
```

Output is a `calendifier.flatpak` bundle. `cleanup_flatpak.sh` is scoped to flatpak artefacts and does not touch the Windows or macOS build outputs. Distribution-specific notes are in [FLATPAK_BUILD_README.md](FLATPAK_BUILD_README.md).

## Testing & quality

The full testing and coverage policy, including the 100% gate and how to run it, lives in [TESTING.md](TESTING.md). The short version:

```bash
python -m pytest                                    # core gate (100%)
python -m pytest tests/ui --no-cov -o addopts=""    # Qt/UI suite (not gated)
python -m black --check .                            # format
python -m flake8 .                                   # lint
```

## Other notes

- **Logging.** The console shows only warnings and errors by default; the full INFO-level log is written to `~/.calendar_app/logs/calendar_app.log`. To raise console verbosity while diagnosing, set `CALENDIFIER_LOG_LEVEL=INFO` (or `DEBUG`) before launching.
- **Home Assistant deployment.** `deploy-ha.sh` plus [docs/home-assistant-deployment.md](docs/home-assistant-deployment.md) cover deploying the API server and web components to Home Assistant.
- **Raspberry Pi.** `setup-pi.sh` provisions a Pi for running the app or server.
- **XFCE desktop entry.** On some XFCE setups the desktop entry needs a fix; see `cleanup-xfce.sh` and `xfce-desktop-entry-fix-plan.md`.
- **Broken venv interpreter.** If the venv `python` shim will not start, run tools against the venv's site-packages directly, for example:
  ```bash
  PYTHONUTF8=1 PYTHONPATH="$(pwd)/venv/Lib/site-packages:$(pwd)" py -3 -m pytest
  ```
- **Git.** Build and test steps never commit. Commit and tag releases yourself after reviewing the stamped docs.

## Licensing

Calendifier is distributed under **LGPL-3.0**, aligning with PySide6/Qt. The licence text ships with every installer and is shown in the installer UI.
