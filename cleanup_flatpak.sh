#!/usr/bin/env bash
# cleanup_flatpak.sh - Uninstall and purge the Calendifier Flatpak.
#
# Scoped to flatpak artefacts only. It deliberately does NOT touch the
# PyInstaller/DMG outputs (dist-pyinstaller/, dist-installer/, dist/) produced by
# buildexe.py / buildinstaller.py / builddmg.py, nor the committed flatpak
# manifest, so the build paths stay independent.
set -euo pipefail

# Must match the app-id used by build_flatpak.sh.
APP_ID="com.calendifier.Calendar"
BUNDLE="calendifier.flatpak"

bold=$(tput bold 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)
section() { echo; echo "${bold}=== $* ===${reset}"; }

section "Uninstalling ${APP_ID}"
if flatpak list --user 2>/dev/null | grep -q "${APP_ID}"; then
    flatpak uninstall --user -y "${APP_ID}"
    echo "  Uninstalled."
else
    echo "  Not installed, skipping."
fi

section "Removing flatpak build artefacts"
rm -f "${BUNDLE}"
rm -rf .flatpak-build .flatpak-repo .flatpak-builder
rm -f "${APP_ID}.yml"
rm -rf packaging
echo "  Done."

echo
echo "${bold}Purge complete.${reset}"
