"""🪟 Startup splash screen for Calendifier.

Shows the app icon, the author line and the version (read from the central
``VERSION`` source of truth via ``version.__version__``) while the application
initialises in the background.

Implemented as a lightweight frameless ``QWidget`` rather than ``QSplashScreen``:
``QSplashScreen.show()`` carries a ~1 second cost on first display, which made
the splash appear only just before the main window. A plain widget shows
immediately.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from version import __version__, __author__
from calendar_app.shared.resources import find_qt_window_icon_path

_TITLE = "Calendifier"
_AUTHOR_LINE = f"by {__author__}"

# Canvas geometry and palette (named so there are no bare layout magic numbers).
_CANVAS_W = 460
_CANVAS_H = 300
_BG = QColor("#1e1e1e")
_ACCENT = QColor("#0078d4")
_TEXT = QColor("#ffffff")
_SUBTLE = QColor("#cccccc")

# Vertical layout (pixels from the top of the canvas).
_ICON_PX = 112
_ICON_TOP = 30
_TITLE_TOP = 154
_TITLE_H = 44
_AUTHOR_TOP = 200
_VERSION_TOP = 228
_LINE_H = 24

# Progress-message band at the bottom of the canvas.
_MESSAGE_H = 22
_MESSAGE_BOTTOM_MARGIN = 12


def _load_icon_pixmap() -> Optional[QPixmap]:
    """Load the app icon scaled for the splash, or None if unavailable."""
    path = find_qt_window_icon_path()
    if not path:
        return None
    pixmap = QIcon(str(path)).pixmap(_ICON_PX, _ICON_PX)
    return pixmap if not pixmap.isNull() else None


def _build_canvas() -> QPixmap:
    """Paint the static splash content (icon, title, author, version)."""
    canvas = QPixmap(_CANVAS_W, _CANVAS_H)
    canvas.fill(_BG)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    icon = _load_icon_pixmap()
    if icon is not None:
        # Centre on the icon's logical (device-independent) width. On HiDPI
        # displays pixmap.width() is the larger physical size while the icon is
        # drawn at its logical size, so using the physical width here would push
        # the icon left of centre.
        logical_w = icon.width() / icon.devicePixelRatio()
        painter.drawPixmap(int((_CANVAS_W - logical_w) / 2), _ICON_TOP, icon)

    painter.setPen(_TEXT)
    painter.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
    painter.drawText(
        0, _TITLE_TOP, _CANVAS_W, _TITLE_H, Qt.AlignmentFlag.AlignHCenter, _TITLE
    )

    painter.setPen(_SUBTLE)
    painter.setFont(QFont("Segoe UI", 12))
    painter.drawText(
        0, _AUTHOR_TOP, _CANVAS_W, _LINE_H, Qt.AlignmentFlag.AlignHCenter, _AUTHOR_LINE
    )

    painter.setPen(_ACCENT)
    painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
    painter.drawText(
        0,
        _VERSION_TOP,
        _CANVAS_W,
        _LINE_H,
        Qt.AlignmentFlag.AlignHCenter,
        f"Version {__version__}",
    )
    painter.end()
    return canvas


class SplashScreen(QWidget):
    """Frameless, always-on-top splash painted from a pre-rendered canvas."""

    def __init__(self, canvas: QPixmap) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._canvas = canvas
        self._message = ""
        self.setFixedSize(canvas.size())
        self._centre_on_screen()

    def _centre_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.move(available.center() - self.rect().center())

    def paintEvent(self, event) -> None:  # noqa: ANN001 (Qt override)
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._canvas)
        if self._message:
            painter.setPen(_SUBTLE)
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                0,
                _CANVAS_H - _MESSAGE_BOTTOM_MARGIN - _MESSAGE_H,
                _CANVAS_W,
                _MESSAGE_H,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self._message,
            )
        painter.end()

    def show_message(self, message: str) -> None:
        """Set the progress message and repaint immediately."""
        self._message = message
        self.repaint()

    def finish(self, widget) -> None:  # noqa: ANN001 (Qt parity with QSplashScreen)
        """Close the splash once the given window is up."""
        del widget
        self.close()


def make_splash() -> SplashScreen:
    """Build and return a ready-to-show splash screen."""
    return SplashScreen(_build_canvas())


def splash_message(splash: SplashScreen, message: str) -> None:
    """Show a progress message along the bottom of the splash."""
    splash.show_message(message)
