"""
🎨 Theme Manager for Calendar Application

This module handles dark/light theme definitions and switching.
"""

import logging
from typing import Dict, Any, Optional
from version import __version__, THEME_DARK_ICON, THEME_LIGHT_ICON

logger = logging.getLogger(__name__)


class ThemeManager:
    """🎨 Manages application themes and styling."""

    def __init__(self):
        """Initialize theme manager with default themes."""
        self.current_theme = "dark"
        self.themes = {
            "dark": self._create_dark_theme(),
            "light": self._create_light_theme(),
        }

        logger.info("🎨 Theme Manager initialized")

    def _create_dark_theme(self) -> Dict[str, Any]:
        """🌙 Create dark theme configuration."""
        return {
            "name": "dark",
            "display_name": f"{THEME_DARK_ICON} Dark Theme",
            "colors": {
                # Main colors
                "background": "#1e1e1e",
                "surface": "#2d2d2d",
                "surface_variant": "#3d3d3d",
                "primary": "#0078d4",
                "primary_variant": "#106ebe",
                "secondary": "#6b6b6b",
                "secondary_variant": "#5a5a5a",
                # Text colors
                "text_primary": "#ffffff",
                "text_secondary": "#cccccc",
                "text_disabled": "#6b6b6b",
                "text_on_primary": "#ffffff",
                # Status colors
                "success": "#16c60c",
                "warning": "#ffb900",
                "error": "#d13438",
                "info": "#0078d4",
                # Calendar specific
                "today": "#0078d4",
                "today_bg": "#1a4a6b",
                "weekend": "#2d2d2d",
                "weekend_text": "#cccccc",
                "holiday": "#d13438",
                "holiday_bg": "#4a1a1a",
                "other_month": "#4a4a4a",
                "selected": "#0078d4",
                "selected_bg": "#1a4a6b",
                # Event colors
                "event_work": "#0078d4",
                "event_personal": "#16c60c",
                "event_meeting": "#ffb900",
                "event_meal": "#8a8a8a",
                "event_holiday": "#d13438",
                # UI elements
                "border": "#4a4a4a",
                "border_light": "#5a5a5a",
                "hover": "#3d3d3d",
                "pressed": "#4d4d4d",
                "focus": "#0078d4",
                # Clock colors
                "clock_face": "#2d2d2d",
                "clock_border": "#4a4a4a",
                "clock_numbers": "#ffffff",
                "clock_hands": "#0078d4",
                "clock_center": "#ffffff",
            },
            "fonts": {
                "family": 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',  # noqa: E501
                "family_mono": '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',  # noqa: E501
                "size_small": 10,
                "size_normal": 12,
                "size_large": 14,
                "size_xlarge": 16,
                "size_clock": 24,
                "weight_normal": "normal",
                "weight_bold": "bold",
            },
            "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
            "borders": {"radius": 4, "width": 1, "width_thick": 2},
        }

    def _create_light_theme(self) -> Dict[str, Any]:
        """☀️ Create light theme configuration."""
        return {
            "name": "light",
            "display_name": f"{THEME_LIGHT_ICON} Light Theme",
            "colors": {
                # Main colors
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "surface_variant": "#e5e5e5",
                "primary": "#0078d4",
                "primary_variant": "#106ebe",
                "secondary": "#8a8a8a",
                "secondary_variant": "#7a7a7a",
                # Text colors
                "text_primary": "#000000",
                "text_secondary": "#333333",
                "text_disabled": "#8a8a8a",
                "text_on_primary": "#ffffff",
                # Status colors
                "success": "#107c10",
                "warning": "#ff8c00",
                "error": "#d13438",
                "info": "#0078d4",
                # Calendar specific
                "today": "#0078d4",
                "today_bg": "#e6f3ff",
                "weekend": "#f5f5f5",
                "weekend_text": "#666666",
                "holiday": "#d13438",
                "holiday_bg": "#ffe6e6",
                "other_month": "#cccccc",
                "selected": "#0078d4",
                "selected_bg": "#e6f3ff",
                # Event colors
                "event_work": "#0078d4",
                "event_personal": "#107c10",
                "event_meeting": "#ff8c00",
                "event_meal": "#666666",
                "event_holiday": "#d13438",
                # UI elements
                "border": "#cccccc",
                "border_light": "#e0e0e0",
                "hover": "#f0f0f0",
                "pressed": "#e0e0e0",
                "focus": "#0078d4",
                # Clock colors
                "clock_face": "#ffffff",
                "clock_border": "#cccccc",
                "clock_numbers": "#000000",
                "clock_hands": "#0078d4",
                "clock_center": "#000000",
            },
            "fonts": {
                "family": 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',  # noqa: E501
                "family_mono": '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',  # noqa: E501
                "size_small": 10,
                "size_normal": 12,
                "size_large": 14,
                "size_xlarge": 16,
                "size_clock": 24,
                "weight_normal": "normal",
                "weight_bold": "bold",
            },
            "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
            "borders": {"radius": 4, "width": 1, "width_thick": 2},
        }

    def get_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """📋 Get theme configuration by name."""
        return self.themes.get(theme_name)

    def get_current_theme(self) -> Dict[str, Any]:
        """📋 Get current theme configuration."""
        return self.themes[self.current_theme]

    def set_theme(self, theme_name: str) -> bool:
        """🎨 Set current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            logger.info(
                f"🎨 Theme changed to: {self.themes[theme_name]['display_name']}"
            )
            return True
        else:
            logger.warning(f"⚠️ Unknown theme: {theme_name}")
            return False

    def get_available_themes(self) -> Dict[str, str]:
        """📋 Get list of available themes."""
        return {name: theme["display_name"] for name, theme in self.themes.items()}

    def toggle_theme(self) -> str:
        """🔄 Toggle between dark and light themes."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def get_color(self, color_name: str, fallback: str = "#000000") -> str:
        """🎨 Get color value from current theme."""
        theme = self.get_current_theme()
        return theme["colors"].get(color_name, fallback)

    def get_font(self, font_property: str, fallback: Any = None) -> Any:
        """🔤 Get font property from current theme."""
        theme = self.get_current_theme()
        return theme["fonts"].get(font_property, fallback)

    def get_spacing(self, size: str, fallback: int = 8) -> int:
        """📏 Get spacing value from current theme."""
        theme = self.get_current_theme()
        return theme["spacing"].get(size, fallback)

    def generate_qss_stylesheet(self) -> str:
        """🎨 Generate Qt stylesheet (QSS) for current theme."""
        theme = self.get_current_theme()
        colors = theme["colors"]
        fonts = theme["fonts"]
        spacing = theme["spacing"]
        borders = theme["borders"]

        qss = f"""
/* 📅 Calendar Application - {theme['display_name']} */

/* Main Window */
QMainWindow {{
    background-color: {colors['background']};
    color: {colors['text_primary']};
    font-family: {fonts['family']};
    font-size: {fonts['size_normal']}px;
}}

/* Panels and Containers */
QWidget {{
    background-color: {colors['background']};
    color: {colors['text_primary']};
    border: none;
}}

QFrame {{
    background-color: {colors['surface']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
}}

/* Buttons */
QPushButton {{
    background-color: {colors['primary']};
    color: {colors['text_on_primary']};
    border: none;
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px {spacing['md']}px;
    font-weight: {fonts['weight_bold']};
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {colors['primary_variant']};
}}

QPushButton:pressed {{
    background-color: {colors['pressed']};
}}

QPushButton:disabled {{
    background-color: {colors['secondary']};
    color: {colors['text_disabled']};
}}

/* Secondary Buttons */
QPushButton[class="secondary"] {{
    background-color: transparent;
    color: {colors['primary']};
    border: {borders['width']}px solid {colors['primary']};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {colors['primary']};
    color: {colors['text_on_primary']};
}}

/* Icon Buttons */
QPushButton[class="icon"] {{
    background-color: transparent;
    border: none;
    padding: {spacing['sm']}px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    color: {colors['primary']};
}}

QPushButton[class="icon"]:hover {{
    background-color: {colors['hover']};
    border-radius: {borders['radius']}px;
}}

/* Theme Toggle Buttons */
QPushButton[class="theme-dark"] {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
}}

QPushButton[class="theme-light"] {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
}}

QPushButton[class="theme-active"] {{
    background-color: {colors['primary']};
    color: {colors['text_on_primary']};
    border: {borders['width']}px solid {colors['primary']};
}}

/* Labels */
QLabel {{
    color: {colors['text_primary']};
    background-color: transparent;
}}

QLabel[class="secondary"] {{
    color: {colors['text_secondary']};
}}

QLabel[class="title"] {{
    font-size: {fonts['size_large']}px;
    font-weight: {fonts['weight_bold']};
}}

QLabel[class="clock-time"] {{
    font-family: {fonts['family_mono']};
    font-size: {fonts['size_clock']}px;
    font-weight: {fonts['weight_bold']};
    color: {colors['primary']};
}}

QLabel[class="clock-date"] {{
    font-size: {fonts['size_normal']}px;
    color: {colors['text_secondary']};
}}

/* Input Fields */
QLineEdit {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px;
    font-size: {fonts['size_normal']}px;
}}

QLineEdit:focus {{
    border-color: {colors['focus']};
    border-width: {borders['width_thick']}px;
}}

QTextEdit {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px;
    font-size: {fonts['size_normal']}px;
}}

QTextEdit:focus {{
    border-color: {colors['focus']};
    border-width: {borders['width_thick']}px;
}}

/* Combo Boxes */
QComboBox {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px;
    min-width: 100px;
}}

QComboBox:hover {{
    border-color: {colors['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {colors['text_primary']};
}}

QComboBox QAbstractItemView {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    selection-background-color: {colors['primary']};
}}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox, QTimeEdit, QDateEdit {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px;
}}

/* Check Boxes */
QCheckBox {{
    color: {colors['text_primary']};
    spacing: {spacing['sm']}px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: {borders['width']}px solid {colors['border']};
    border-radius: 2px;
    background-color: {colors['surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['primary']};
    border-color: {colors['primary']};
}}

/* Radio Buttons */
QRadioButton {{
    color: {colors['text_primary']};
    spacing: {spacing['sm']}px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: {borders['width']}px solid {colors['border']};
    border-radius: 8px;
    background-color: {colors['surface']};
}}

QRadioButton::indicator:checked {{
    background-color: {colors['primary']};
    border-color: {colors['primary']};
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background-color: {colors['surface']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['secondary']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['primary']};
}}

QScrollBar:horizontal {{
    background-color: {colors['surface']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['secondary']};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors['primary']};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border-bottom: {borders['width']}px solid {colors['border']};
}}

QMenuBar::item {{
    padding: {spacing['sm']}px {spacing['md']}px;
}}

QMenuBar::item:selected {{
    background-color: {colors['hover']};
}}

/* Menus */
QMenu {{
    background-color: {colors['surface']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
}}

QMenu::item {{
    padding: {spacing['sm']}px {spacing['md']}px;
}}

QMenu::item:selected {{
    background-color: {colors['primary']};
    color: {colors['text_on_primary']};
}}

/* Status Bar */
QStatusBar {{
    background-color: {colors['surface']};
    color: {colors['text_secondary']};
    border-top: {borders['width']}px solid {colors['border']};
}}

/* Status Bar Size Grip (bottom right corner) */
QSizeGrip {{
    background-color: {colors['text_primary']};
    width: 12px;
    height: 12px;
    border-radius: 2px;
    margin: 2px;
}}

/* Tool Tips */
QToolTip {{
    background-color: {colors['surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
    padding: {spacing['sm']}px;
}}

/* Calendar Widget Specific Styles */
QWidget[class="calendar-grid"] {{
    background-color: {colors['surface']};
    border: {borders['width']}px solid {colors['border']};
    border-radius: {borders['radius']}px;
}}

QWidget[class="calendar-day"] {{
    border: {borders['width']}px solid {colors['border_light']};
    min-width: 40px;
    min-height: 40px;
}}

QWidget[class="calendar-day-today"] {{
    background-color: {colors['today_bg']};
    border: {borders['width_thick']}px solid {colors['today']};
    color: {colors['today']};
    font-weight: {fonts['weight_bold']};
}}

QWidget[class="calendar-day-weekend"] {{
    background-color: {colors['weekend']};
    color: {colors['weekend_text']};
}}

QWidget[class="calendar-day-holiday"] {{
    background-color: {colors['holiday_bg']};
    color: {colors['holiday']};
    font-weight: {fonts['weight_bold']};
}}

QWidget[class="calendar-day-other-month"] {{
    color: {colors['other_month']};
}}

QWidget[class="calendar-day-selected"] {{
    background-color: {colors['selected_bg']};
    border: {borders['width_thick']}px solid {colors['selected']};
}}

/* Week Number Styles */
QLabel[class="week-number"] {{
    background-color: {colors['surface_variant']};
    color: {colors['text_secondary']};
    border: {borders['width']}px solid {colors['border_light']};
    font-size: {fonts['size_small']}px;
    font-weight: {fonts['weight_bold']};
    text-align: center;
}}

/* Clock Widget Specific Styles */
QWidget[class="clock-widget"] {{
    background-color: {colors['clock_face']};
    border: {borders['width_thick']}px solid {colors['clock_border']};
    border-radius: 150px;
}}

/* Event Indicators */
QWidget[class="event-indicator"] {{
    border-radius: 4px;
    min-width: 8px;
    min-height: 8px;
    max-width: 8px;
    max-height: 8px;
}}

QWidget[class="event-work"] {{
    background-color: {colors['event_work']};
}}

QWidget[class="event-personal"] {{
    background-color: {colors['event_personal']};
}}

QWidget[class="event-meeting"] {{
    background-color: {colors['event_meeting']};
}}

QWidget[class="event-meal"] {{
    background-color: {colors['event_meal']};
}}

QWidget[class="event-holiday"] {{
    background-color: {colors['event_holiday']};
}}
"""

        return qss

    def get_theme_icon(self, theme_name: str) -> str:
        """🎨 Get emoji icon for theme."""
        if theme_name == "dark":
            return THEME_DARK_ICON
        elif theme_name == "light":
            return THEME_LIGHT_ICON
        else:
            return "🎨"

    def create_custom_theme(
        self, name: str, base_theme: str, color_overrides: Dict[str, str]
    ) -> bool:
        """🎨 Create custom theme based on existing theme."""
        try:
            if base_theme not in self.themes:
                logger.error(f"❌ Base theme not found: {base_theme}")
                return False

            # Copy base theme
            custom_theme = self.themes[base_theme].copy()
            custom_theme["name"] = name
            custom_theme["display_name"] = f"🎨 {name.title()}"

            # Apply color overrides
            custom_theme["colors"].update(color_overrides)

            # Add to themes
            self.themes[name] = custom_theme

            logger.info(f"🎨 Created custom theme: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create custom theme: {e}")
            return False

    def export_theme(self, theme_name: str, export_path: str) -> bool:
        """📤 Export theme to file."""
        try:
            if theme_name not in self.themes:
                logger.error(f"❌ Theme not found: {theme_name}")
                return False

            import json
            from pathlib import Path

            theme_data = {
                "calendar_app_theme": True,
                "version": __version__,
                "theme": self.themes[theme_name],
            }

            with open(Path(export_path), "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)

            logger.info(f"📤 Exported theme {theme_name} to {export_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to export theme: {e}")
            return False

    def import_theme(self, import_path: str) -> Optional[str]:
        """📥 Import theme from file."""
        try:
            import json
            from pathlib import Path

            path_obj = Path(import_path)
            if not path_obj.exists():
                logger.error(f"❌ Theme file not found: {import_path}")
                return None

            with open(path_obj, "r", encoding="utf-8") as f:
                theme_data = json.load(f)

            if not theme_data.get("calendar_app_theme"):
                logger.error("❌ Invalid theme file format")
                return None

            theme = theme_data["theme"]
            theme_name = theme["name"]

            self.themes[theme_name] = theme

            logger.info(f"📥 Imported theme: {theme_name}")
            return theme_name

        except Exception as e:
            logger.error(f"❌ Failed to import theme: {e}")
            return None
