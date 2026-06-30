"""
Font Manager for Calendar Application
Handles font detection, fallbacks, and cross-platform compatibility
"""

import logging
from PySide6.QtGui import QFontDatabase, QFont
import platform

logger = logging.getLogger(__name__)


class FontManager:
    """Manages fonts and provides robust fallbacks"""

    def __init__(self):
        """Initialize font manager"""
        self.system = platform.system()
        self.available_fonts = set(QFontDatabase.families())
        self._setup_font_fallbacks()
        logger.info("🔤 Font Manager initialized")

    def _setup_font_fallbacks(self):
        """Setup platform-specific font fallbacks"""
        if self.system == "Windows":
            self.ui_font = self._get_best_font(
                ["Segoe UI", "Tahoma", "Arial", "sans-serif"]
            )
            self.mono_font = self._get_best_font(
                ["Cascadia Code", "Consolas", "Courier New", "monospace"]
            )
        elif self.system == "Darwin":  # macOS
            self.ui_font = self._get_best_font(
                [
                    "SF Pro Display",
                    "-apple-system",
                    "Helvetica Neue",
                    "Arial",
                    "sans-serif",
                ]
            )
            self.mono_font = self._get_best_font(
                ["SF Mono", "Monaco", "Menlo", "Courier New", "monospace"]
            )
        else:  # Linux and others
            self.ui_font = self._get_best_font(
                [
                    "Ubuntu",
                    "Roboto",
                    "DejaVu Sans",
                    "Liberation Sans",
                    "Arial",
                    "sans-serif",
                ]
            )
            self.mono_font = self._get_best_font(
                [
                    "Ubuntu Mono",
                    "Roboto Mono",
                    "DejaVu Sans Mono",
                    "Liberation Mono",
                    "Courier New",
                    "monospace",
                ]
            )

    def _get_best_font(self, font_list: list) -> str:
        """Get the best available font from a list"""
        for font_name in font_list:
            if font_name in self.available_fonts or font_name in [
                "sans-serif",
                "monospace",
            ]:
                return font_name
        return font_list[-1]  # Return last fallback

    def get_ui_font(
        self, size: int = 12, weight: QFont.Weight = QFont.Weight.Normal
    ) -> QFont:
        """Get UI font with proper fallbacks"""
        font = QFont(self.ui_font, size, weight)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        return font

    def get_mono_font(
        self, size: int = 12, weight: QFont.Weight = QFont.Weight.Normal
    ) -> QFont:
        """Get monospace font with proper fallbacks"""
        font = QFont(self.mono_font, size, weight)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    def get_emoji_font(self, size: int = 12) -> QFont:
        """Get emoji font with proper fallbacks (avoid problematic fonts)"""
        # Use system UI font for emoji to avoid OpenType script issues
        font = QFont(self.ui_font, size)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        return font

    def log_available_fonts(self):
        """Log available fonts for debugging"""
        logger.info(f"🔤 System: {self.system}")
        logger.info(f"🔤 UI Font: {self.ui_font}")
        logger.info(f"🔤 Mono Font: {self.mono_font}")
        logger.info(f"🔤 Available fonts: {len(self.available_fonts)}")


# Global font manager instance
_font_manager = None


def get_font_manager() -> FontManager:
    """Get global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def get_ui_font(size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Convenience function to get UI font"""
    return get_font_manager().get_ui_font(size, weight)


def get_mono_font(size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Convenience function to get monospace font"""
    return get_font_manager().get_mono_font(size, weight)


def get_emoji_font(size: int = 12) -> QFont:
    """Convenience function to get emoji font"""
    return get_font_manager().get_emoji_font(size)
