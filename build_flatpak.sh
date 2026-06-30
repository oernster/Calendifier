#!/usr/bin/env bash
# build_flatpak.sh — Build calendifier.flatpak for Linux
# Usage: ./build_flatpak.sh
#
# Modelled on the Meridian build script. Calendifier's entry point is the
# repo-root main.py (not an installed package), so the application source is
# staged under /app/share/calendifier and launched from there, while the Python
# dependencies are pip-installed into the Flatpak prefix.

set -euo pipefail

APP_ID="com.calendifier.Calendar"
APP_VERSION=$(cat VERSION)
RELEASE_DATE=$(date +%F)
BUNDLE="calendifier.flatpak"
BUILD_DIR=".flatpak-build"
REPO_DIR=".flatpak-repo"
MANIFEST="${APP_ID}.yml"

# The KDE runtime bundles Qt6 plus Python 3.12 (PySide6 also ships its own Qt).
RUNTIME="org.kde.Platform"
SDK="org.kde.Sdk"
RUNTIME_VERSION="6.8"
PYTHON_DIR="python3.12"

# ── Colour helpers ────────────────────────────────────────────────────────────
bold=$(tput bold 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)
section() { echo; echo "${bold}=== $* ===${reset}"; }

# ── Tool checks / install ─────────────────────────────────────────────────────
section "Checking dependencies"

install_if_missing() {
    local pkg="$1"
    if ! command -v "$pkg" &>/dev/null; then
        echo "  $pkg not found — installing..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y "$pkg"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y "$pkg"
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm "$pkg"
        elif command -v zypper &>/dev/null; then
            sudo zypper install -y "$pkg"
        else
            echo "ERROR: Cannot install $pkg — unsupported package manager." >&2
            exit 1
        fi
    else
        echo "  $pkg: OK"
    fi
}

install_if_missing flatpak
install_if_missing flatpak-builder

# ── Flatpak remotes ───────────────────────────────────────────────────────────
section "Configuring Flathub remote"
flatpak remote-add --if-not-exists --user flathub \
    https://dl.flathub.org/repo/flathub.flatpakrepo

# ── Runtime / SDK ─────────────────────────────────────────────────────────────
section "Installing runtime and SDK"
flatpak install --user --noninteractive flathub \
    "${RUNTIME}//${RUNTIME_VERSION}" \
    "${SDK}//${RUNTIME_VERSION}" \
    || true

# ── packaging/ helpers ────────────────────────────────────────────────────────
section "Writing packaging helpers"
mkdir -p packaging

cat > packaging/calendifier-launcher.sh <<'LAUNCHER'
#!/bin/sh
export PYTHONPATH="/app/lib/python3.12/site-packages:/app/share/calendifier${PYTHONPATH:+:$PYTHONPATH}"
export QT_PLUGIN_PATH="/app/lib/python3.12/site-packages/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="/app/lib/python3.12/site-packages/PySide6/Qt/plugins/platforms"
export QML2_IMPORT_PATH="/app/lib/python3.12/site-packages/PySide6/Qt/qml"
if [ -n "$WAYLAND_DISPLAY" ] && [ -z "$FORCE_X11" ]; then
    export QT_QPA_PLATFORM=wayland
elif [ -n "$DISPLAY" ]; then
    export QT_QPA_PLATFORM=xcb
else
    export QT_QPA_PLATFORM=xcb
fi
exec python3 /app/share/calendifier/main.py "$@"
LAUNCHER
chmod +x packaging/calendifier-launcher.sh

cat > "packaging/${APP_ID}.desktop" <<DESKTOP
[Desktop Entry]
Name=Calendifier
Comment=Cross-platform desktop calendar with international holidays
Exec=calendifier
Icon=${APP_ID}
Terminal=false
Type=Application
Categories=Office;Calendar;
DESKTOP

cat > "packaging/${APP_ID}.metainfo.xml" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>${APP_ID}</id>
  <name>Calendifier</name>
  <summary>Cross-platform desktop calendar with international holidays</summary>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>LGPL-3.0-only</project_license>
  <launchable type="desktop-id">${APP_ID}.desktop</launchable>
  <description>
    <p>Calendifier is a cross-platform desktop calendar with an analogue clock,
    event handling, note taking and international public holidays and cultural
    observances.</p>
  </description>
  <releases>
    <release version="${APP_VERSION}" date="${RELEASE_DATE}"/>
  </releases>
  <url type="homepage">https://github.com/oernster/calendifier</url>
</component>
XML

# ── Generate manifest ─────────────────────────────────────────────────────────
section "Writing manifest ${MANIFEST}"

cat > "${MANIFEST}" <<YAML
app-id: ${APP_ID}
runtime: ${RUNTIME}
runtime-version: "${RUNTIME_VERSION}"
sdk: ${SDK}

command: calendifier

build-options:
  build-args:
    - --share=network

finish-args:
  - --share=ipc
  - --share=network
  - --socket=fallback-x11
  - --socket=wayland
  - --device=dri
  - --filesystem=home

modules:

  # ── MIT Kerberos 5 (provides libgssapi_krb5.so.2 needed by PySide6/Qt) ──────
  - name: krb5
    subdir: src
    config-opts:
      - --prefix=/app
      - --localstatedir=/var/lib
      - --sbindir=/app/bin
      - --disable-rpath
      - --disable-static
      - --without-ldap
      - --without-keyutils
    sources:
      - type: archive
        url: https://kerberos.org/dist/krb5/1.21/krb5-1.21.3.tar.gz
        sha256: b7a4cd5ead67fb08b980b21abd150ff7217e85ea320c9ed0c6dadd304840ad35

  # ── Ensure pip is available ────────────────────────────────────────────────
  - name: python3-pip
    buildsystem: simple
    build-commands:
      - python3 -m ensurepip --upgrade

  # ── PySide6 (Qt for Python; the wheel bundles its own Qt) ──────────────────
  - name: pyside6
    buildsystem: simple
    build-commands:
      - pip3 install --no-cache-dir --prefix=/app "PySide6>=6.9.1"

  # ── Remaining Python dependencies ──────────────────────────────────────────
  - name: python-deps
    buildsystem: simple
    build-commands:
      - pip3 install --no-cache-dir --prefix=/app "holidays>=0.75" "ntplib>=0.4.0" "icalendar>=6.3.1" "python-dateutil>=2.9" "tzdata"

  # ── Calendifier application (staged source + launcher + assets) ─────────────
  - name: calendifier
    buildsystem: simple
    build-commands:
      - install -d /app/share/calendifier
      - cp -r main.py version.py calendar_app assets VERSION /app/share/calendifier/
      - install -Dm644 LGPL3_LICENSE.txt /app/share/calendifier/LGPL3_LICENSE.txt
      - install -Dm755 packaging/calendifier-launcher.sh /app/bin/calendifier
      - install -Dm644 packaging/${APP_ID}.desktop /app/share/applications/${APP_ID}.desktop
      - install -Dm644 packaging/${APP_ID}.metainfo.xml /app/share/metainfo/${APP_ID}.metainfo.xml
      - install -Dm644 assets/calendar_icon_16x16.png /app/share/icons/hicolor/16x16/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_24x24.png /app/share/icons/hicolor/24x24/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_32x32.png /app/share/icons/hicolor/32x32/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_48x48.png /app/share/icons/hicolor/48x48/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_64x64.png /app/share/icons/hicolor/64x64/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_96x96.png /app/share/icons/hicolor/96x96/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_128x128.png /app/share/icons/hicolor/128x128/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon_256x256.png /app/share/icons/hicolor/256x256/apps/${APP_ID}.png
      - install -Dm644 assets/calendar_icon.svg /app/share/icons/hicolor/scalable/apps/${APP_ID}.svg
    sources:
      - type: dir
        path: .
YAML

echo "  Manifest written."

# ── Build ─────────────────────────────────────────────────────────────────────
section "Building Flatpak"
rm -rf "${BUILD_DIR}" "${REPO_DIR}"

flatpak-builder \
    --user \
    --install-deps-from=flathub \
    --force-clean \
    --repo="${REPO_DIR}" \
    "${BUILD_DIR}" \
    "${MANIFEST}"

# ── Bundle ────────────────────────────────────────────────────────────────────
section "Bundling to ${BUNDLE}"
flatpak build-bundle \
    --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo \
    "${REPO_DIR}" \
    "${BUNDLE}" \
    "${APP_ID}"

echo
echo "${bold}Build complete: ${BUNDLE}${reset}"
echo
echo "Install with:"
echo "  flatpak install --user ${BUNDLE}"
echo
echo "Run with:"
echo "  flatpak run ${APP_ID}"
