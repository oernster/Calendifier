"""🎨 Icon generator for Calendifier.

Derives every packaged icon artifact from a single master PNG
(``calendifier.png`` at the repo root): the per-size hicolor PNG set, a
multi-size Windows ``.ico``, a macOS ``.icns`` and an SVG wrapper that embeds
the largest raster so the scalable variant stays visually identical.

Run from the repo root:  python generate_icons.py
"""

from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image

# Single source of truth for the artwork.
MASTER_PNG = Path("calendifier.png")
ASSETS_DIR = Path("assets")

# Base name every artifact shares; keeps the existing build-script wiring intact.
ICON_STEM = "calendar_icon"

# Hicolor PNG sizes shipped to Linux/macOS/Windows and the About dialog.
PNG_SIZES = (16, 24, 32, 48, 64, 96, 128, 256, 512, 1024)

# Sizes embedded in the multi-resolution Windows .ico.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

# Size used for the plain ``calendar_icon.png`` and the SVG raster payload.
BASE_PNG_SIZE = 256
SVG_EMBED_SIZE = 512


def _load_master() -> Image.Image:
    """Load the master PNG as RGBA, failing loudly if it is missing."""
    if not MASTER_PNG.exists():
        raise SystemExit(f"❌ Master icon not found: {MASTER_PNG.resolve()}")
    return Image.open(MASTER_PNG).convert("RGBA")


def _resized(master: Image.Image, size: int) -> Image.Image:
    """Return a high-quality square copy of the master at ``size`` px."""
    return master.resize((size, size), Image.LANCZOS)


def _write_png_set(master: Image.Image) -> None:
    """Write the per-size PNG set plus the plain base PNG."""
    for size in PNG_SIZES:
        out = ASSETS_DIR / f"{ICON_STEM}_{size}x{size}.png"
        _resized(master, size).save(out, format="PNG")
        print(f"🖼️  {out}")

    base = ASSETS_DIR / f"{ICON_STEM}.png"
    _resized(master, BASE_PNG_SIZE).save(base, format="PNG")
    print(f"🖼️  {base}")


def _write_ico(master: Image.Image) -> None:
    """Write a multi-resolution Windows .ico."""
    out = ASSETS_DIR / f"{ICON_STEM}.ico"
    _resized(master, max(ICO_SIZES)).save(
        out, format="ICO", sizes=[(s, s) for s in ICO_SIZES]
    )
    print(f"🪟 {out}")


def _write_icns(master: Image.Image) -> None:
    """Write a macOS .icns (Pillow requires a square RGBA source)."""
    out = ASSETS_DIR / f"{ICON_STEM}.icns"
    # Pillow derives the standard icns members from the largest provided image.
    _resized(master, max(PNG_SIZES)).save(out, format="ICNS")
    print(f"🍎 {out}")


def _write_svg_wrapper(master: Image.Image) -> None:
    """Write an SVG that embeds the raster so scalable art matches the bitmap."""
    raster = ASSETS_DIR / f"{ICON_STEM}_{SVG_EMBED_SIZE}x{SVG_EMBED_SIZE}.png"
    encoded = base64.b64encode(raster.read_bytes()).decode("ascii")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SVG_EMBED_SIZE}" height="{SVG_EMBED_SIZE}" '
        f'viewBox="0 0 {SVG_EMBED_SIZE} {SVG_EMBED_SIZE}">'
        f'<image width="{SVG_EMBED_SIZE}" height="{SVG_EMBED_SIZE}" '
        f'href="data:image/png;base64,{encoded}"/>'
        f"</svg>\n"
    )
    out = ASSETS_DIR / f"{ICON_STEM}.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"🐧 {out}")


def main() -> None:
    """Regenerate every icon artifact from the master PNG."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    master = _load_master()

    _write_png_set(master)
    _write_ico(master)
    _write_icns(master)
    _write_svg_wrapper(master)

    print("✅ Icon generation complete.")


if __name__ == "__main__":
    main()
