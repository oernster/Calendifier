"""Light and dark themes (QSS) for the installer UI.

The palette mirrors the Calendifier application's own theme tokens
(see ``calendar_app/config/themes.py``) so the installer matches the app it
installs: the Calendifier blue accent (#0078d4), neutral grey surfaces and the
app's error red, rather than the purple/pink palette inherited from the
o7Debrief installer lineage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    """Semantic colour tokens for one theme, taken from the Calendifier app."""

    background: str
    surface: str
    surface_variant: str
    border: str
    text: str
    text_secondary: str
    text_disabled: str
    primary: str
    primary_hover: str
    danger: str
    danger_hover: str


@dataclass(frozen=True, slots=True)
class Theme:
    name: str
    toggle_label: str
    qss: str


# Calendifier dark theme tokens (calendar_app/config/themes.py).
_DARK_PALETTE = Palette(
    background="#1e1e1e",
    surface="#2d2d2d",
    surface_variant="#3d3d3d",
    border="#4a4a4a",
    text="#ffffff",
    text_secondary="#cccccc",
    text_disabled="#6b6b6b",
    primary="#0078d4",
    primary_hover="#106ebe",
    danger="#d13438",
    # A darker shade of the app's error red for the destructive-button hover.
    danger_hover="#a82a2e",
)

# Calendifier light theme tokens (calendar_app/config/themes.py).
_LIGHT_PALETTE = Palette(
    background="#ffffff",
    surface="#f5f5f5",
    surface_variant="#e5e5e5",
    border="#cccccc",
    text="#000000",
    text_secondary="#333333",
    text_disabled="#8a8a8a",
    primary="#0078d4",
    primary_hover="#106ebe",
    danger="#d13438",
    danger_hover="#a82a2e",
)


def _build_qss(p: Palette) -> str:
    """Build the installer stylesheet from a Calendifier palette."""
    return f"""
        QWidget {{
            background: {p.background};
            color: {p.text};
            font-family: 'Segoe UI';
        }}
        QLabel#HeaderTitle {{
            font-size: 38px; font-weight: 700; color: {p.primary};
        }}
        QLabel#HeaderVersion {{ font-size: 14px; color: {p.text_secondary}; }}
        QLabel#SubTitle {{
            font-size: 22px; font-weight: 700; color: {p.primary};
        }}
        QLabel#StatusLine {{ font-size: 13px; color: {p.text_secondary}; }}

        QCheckBox {{ spacing: 10px; font-size: 13px; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px;
            border: 1px solid {p.border}; border-radius: 2px;
            background: {p.surface};
        }}
        QCheckBox::indicator:checked {{
            background: {p.primary}; border-color: {p.primary};
        }}

        QPushButton#ThemeToggle {{
            background: {p.primary}; color: white; border: none;
            padding: 10px 18px; border-radius: 18px; font-weight: 600;
        }}
        QPushButton#ThemeToggle:hover {{ background: {p.primary_hover}; }}

        QPushButton#LicenceButton {{
            background: {p.primary}; color: white; border: none;
            padding: 10px 18px; border-radius: 18px; font-weight: 600;
        }}
        QPushButton#LicenceButton:hover {{ background: {p.primary_hover}; }}

        QPushButton#PrimaryAction {{
            background: {p.primary}; color: white; border: none;
            padding: 14px 26px; border-radius: 26px; font-size: 14px;
            font-weight: 700; min-width: 150px;
        }}
        QPushButton#PrimaryAction:hover {{ background: {p.primary_hover}; }}

        QPushButton#DangerAction {{
            background: {p.danger}; color: white; border: none;
            padding: 12px 26px; border-radius: 22px; font-size: 13px;
            font-weight: 700; min-width: 190px;
        }}
        QPushButton#DangerAction:hover {{ background: {p.danger_hover}; }}

        QLineEdit {{
            background: {p.surface};
            border: 1px solid {p.border};
            border-radius: 10px;
            padding: 8px;
        }}
        QPushButton#BrowseButton {{
            background: {p.surface_variant};
            color: {p.text};
            border: none;
            border-radius: 10px;
            padding: 8px 12px;
        }}
        QPushButton#BrowseButton:hover {{ background: {p.border}; }}

        QProgressBar#ProgressBar {{
            background: {p.surface};
            border: 1px solid {p.border};
            border-radius: 10px;
            height: 16px;
            text-align: center;
        }}
        QProgressBar#ProgressBar::chunk {{
            background: {p.primary};
            border-radius: 8px;
            width: 10px;
            margin: 1px;
        }}
    """


LIGHT = Theme(
    name="light",
    toggle_label="Dark Theme",
    qss=_build_qss(_LIGHT_PALETTE),
)


DARK = Theme(
    name="dark",
    toggle_label="Light Theme",
    qss=_build_qss(_DARK_PALETTE),
)
