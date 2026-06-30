"""
🕐 Clock Widget for Calendar Application

This module contains the analog clock with digital display.
"""

import logging
import math
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor

from calendar_app.utils.ntp_client import TimeManager, NTPResult
from calendar_app.config.themes import ThemeManager
from calendar_app.localization.i18n_manager import get_i18n_manager, convert_numbers
from calendar_app.utils.font_manager import get_emoji_font


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that always uses current locale."""
    default = kwargs.pop("default", None)
    try:
        return get_i18n_manager().get_text(key, **kwargs)
    except Exception:
        return default if default is not None else key


from version import UI_EMOJIS, STATUS_EMOJIS  # noqa: E402

logger = logging.getLogger(__name__)

# Vertical gaps inside the clock column (px). Kept modest so the column fits on
# short screens; the surrounding scroll area handles any residual overflow.
SECTION_GAP = 16
CONTROL_GAP = 12

# Point size of the clock emoji shown beside the digital time. The emoji lives
# in its own label with a proportional emoji font: rendering it inside the
# monospace time label clipped it (the emoji glyph is wider/taller than a
# monospace cell). Roughly matches the 24px monospace digits.
DIGITAL_TIME_ICON_PT = 18
# Gap (px) between the clock emoji and the digits.
DIGITAL_TIME_ICON_GAP = 8


class AnalogClockWidget(QWidget):
    """🕐 Analog clock face widget."""

    # Preferred size on roomy screens, and the smallest the face may shrink to
    # before the surrounding column starts to scroll (keeps it legible on 13"
    # Linux/macOS displays where fonts render larger).
    PREFERRED_SIZE = 240
    MINIMUM_SIZE = 150

    def __init__(self, parent=None):
        """Initialize analog clock widget."""
        super().__init__(parent)

        self.current_time = datetime.now()

        # Responsive sizing: shrink to fit tight vertical space rather than a
        # fixed 240px that overlaps the text below on small screens. paintEvent
        # already scales to min(width, height), so the face stays circular.
        self.setMinimumSize(self.MINIMUM_SIZE, self.MINIMUM_SIZE)
        self.setMaximumHeight(self.PREFERRED_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Clock appearance
        self.face_color = QColor("#2d2d2d")
        self.border_color = QColor("#4a4a4a")
        self.number_color = QColor("#ffffff")
        self.hand_color = QColor("#0078d4")
        self.center_color = QColor("#ffffff")

        logger.debug("🕐 Analog clock widget initialized")

    def sizeHint(self) -> QSize:
        """📐 Preferred (roomy) clock size."""
        return QSize(self.PREFERRED_SIZE, self.PREFERRED_SIZE)

    def set_time(self, time: datetime):
        """⏰ Set current time and update display."""
        self.current_time = time
        self.update()

    def set_colors(self, face: str, border: str, numbers: str, hands: str, center: str):
        """🎨 Set clock colors."""
        self.face_color = QColor(face)
        self.border_color = QColor(border)
        self.number_color = QColor(numbers)
        self.hand_color = QColor(hands)
        self.center_color = QColor(center)
        self.update()

    def paintEvent(self, event):
        """🎨 Paint the analog clock."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)

        # Center the clock
        center_x = width // 2
        center_y = height // 2
        radius = (size - 20) // 2

        # Draw clock face
        painter.setBrush(QBrush(self.face_color))
        painter.setPen(QPen(self.border_color, 2))
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

        # Draw hour markers
        painter.setPen(QPen(self.number_color, 2))
        for hour in range(12):
            angle = hour * 30 - 90  # Start from 12 o'clock
            angle_rad = math.radians(angle)

            # Major tick marks
            outer_x = center_x + (radius - 15) * math.cos(angle_rad)
            outer_y = center_y + (radius - 15) * math.sin(angle_rad)
            inner_x = center_x + (radius - 25) * math.cos(angle_rad)
            inner_y = center_y + (radius - 25) * math.sin(angle_rad)

            painter.drawLine(int(outer_x), int(outer_y), int(inner_x), int(inner_y))

            # Draw numbers for 12, 3, 6, 9
            if hour % 3 == 0:
                number = 12 if hour == 0 else hour
                text_x = center_x + (radius - 35) * math.cos(angle_rad)
                text_y = center_y + (radius - 35) * math.sin(angle_rad)

                painter.setFont(QFont("system-ui", 14, QFont.Weight.Bold))
                text_rect = QRect(int(text_x - 10), int(text_y - 10), 20, 20)

                # Convert number to locale-appropriate numerals
                number_str = convert_numbers(str(number))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, number_str)

        # Draw minute markers
        painter.setPen(QPen(self.number_color, 1))
        for minute in range(60):
            if minute % 5 != 0:  # Skip hour markers
                angle = minute * 6 - 90
                angle_rad = math.radians(angle)

                outer_x = center_x + (radius - 10) * math.cos(angle_rad)
                outer_y = center_y + (radius - 10) * math.sin(angle_rad)
                inner_x = center_x + (radius - 15) * math.cos(angle_rad)
                inner_y = center_y + (radius - 15) * math.sin(angle_rad)

                painter.drawLine(int(outer_x), int(outer_y), int(inner_x), int(inner_y))

        # Calculate hand angles
        hour = self.current_time.hour % 12
        minute = self.current_time.minute
        second = self.current_time.second

        hour_angle = (hour * 30) + (minute * 0.5) - 90
        minute_angle = minute * 6 - 90
        second_angle = second * 6 - 90

        # Draw hour hand
        hour_angle_rad = math.radians(hour_angle)
        hour_length = radius * 0.5
        hour_x = center_x + hour_length * math.cos(hour_angle_rad)
        hour_y = center_y + hour_length * math.sin(hour_angle_rad)

        painter.setPen(
            QPen(self.hand_color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(center_x, center_y, int(hour_x), int(hour_y))

        # Draw minute hand
        minute_angle_rad = math.radians(minute_angle)
        minute_length = radius * 0.7
        minute_x = center_x + minute_length * math.cos(minute_angle_rad)
        minute_y = center_y + minute_length * math.sin(minute_angle_rad)

        painter.setPen(
            QPen(self.hand_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(center_x, center_y, int(minute_x), int(minute_y))

        # Draw second hand
        second_angle_rad = math.radians(second_angle)
        second_length = radius * 0.8
        second_x = center_x + second_length * math.cos(second_angle_rad)
        second_y = center_y + second_length * math.sin(second_angle_rad)

        painter.setPen(
            QPen(QColor("#d13438"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(center_x, center_y, int(second_x), int(second_y))

        # Draw center circle
        painter.setBrush(QBrush(self.center_color))
        painter.setPen(QPen(self.center_color, 1))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)


class DigitalDisplayWidget(QWidget):
    """📱 Digital time and date display widget."""

    def __init__(self, parent=None):
        """Initialize digital display widget."""
        super().__init__(parent)

        self.current_time = datetime.now()
        self.ntp_status: Optional[NTPResult] = None

        self._setup_ui()
        logger.debug("📱 Digital display widget initialized")

    def _setup_ui(self):
        """🏗️ Setup digital display UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Time row: a clock emoji in its own proportional-font label next to the
        # monospace digits. Keeping the emoji out of the monospace time label
        # avoids it being clipped by the narrow monospace cell.
        time_row = QHBoxLayout()
        time_row.setSpacing(DIGITAL_TIME_ICON_GAP)
        time_row.addStretch()

        self.time_icon = QLabel("🕐")
        self.time_icon.setFont(get_emoji_font(DIGITAL_TIME_ICON_PT))
        self.time_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_row.addWidget(self.time_icon)

        self.time_label = QLabel()
        self.time_label.setProperty("class", "clock-time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_row.addWidget(self.time_label)

        time_row.addStretch()
        layout.addLayout(time_row)

        # Date label
        self.date_label = QLabel()
        self.date_label.setProperty("class", "clock-date")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        # Status label
        self.status_label = QLabel()
        self.status_label.setProperty("class", "secondary")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set smaller font size for status label on all platforms to prevent truncation
        font = self.status_label.font()
        font.setPointSize(8)  # Reduced from default for better fit
        self.status_label.setFont(font)

        layout.addWidget(self.status_label)

        self._update_display()

    def set_time(self, time: datetime):
        """⏰ Set current time and update display."""
        self.current_time = time
        self._update_display()

    def set_ntp_status(self, status: Optional[NTPResult]):
        """🌐 Set NTP status and update display."""
        self.ntp_status = status
        self._update_display()

    def _update_display(self):
        """🔄 Update digital display."""
        # Format time and convert to locale-appropriate numerals
        time_str = self.current_time.strftime("%H:%M:%S")
        converted_time_str = convert_numbers(time_str)
        self.time_label.setText(converted_time_str)

        # Format date with localized day and month names
        try:
            # Use manual localization for consistent translation
            from calendar_app.localization.i18n_manager import get_i18n_manager

            def _(key: str, **kwargs) -> str:
                """Dynamic translation function."""
                default = kwargs.pop("default", None)
                try:
                    return get_i18n_manager().get_text(key, **kwargs)
                except Exception:
                    return default if default is not None else key

            weekday_names = [
                _("calendar.days.monday", default="Monday"),
                _("calendar.days.tuesday", default="Tuesday"),
                _("calendar.days.wednesday", default="Wednesday"),
                _("calendar.days.thursday", default="Thursday"),
                _("calendar.days.friday", default="Friday"),
                _("calendar.days.saturday", default="Saturday"),
                _("calendar.days.sunday", default="Sunday"),
            ]
            month_names = [
                _("calendar.months.january", default="January"),
                _("calendar.months.february", default="February"),
                _("calendar.months.march", default="March"),
                _("calendar.months.april", default="April"),
                _("calendar.months.may", default="May"),
                _("calendar.months.june", default="June"),
                _("calendar.months.july", default="July"),
                _("calendar.months.august", default="August"),
                _("calendar.months.september", default="September"),
                _("calendar.months.october", default="October"),
                _("calendar.months.november", default="November"),
                _("calendar.months.december", default="December"),
            ]

            weekday = weekday_names[self.current_time.weekday()]
            month = month_names[self.current_time.month - 1]
            date_str = (
                f"{weekday}, {self.current_time.day} {month} {self.current_time.year}"
            )
        except Exception:
            # Fallback to manual localization
            weekday_names = [
                _("weekday_monday", default="Monday"),
                _("weekday_tuesday", default="Tuesday"),
                _("weekday_wednesday", default="Wednesday"),
                _("weekday_thursday", default="Thursday"),
                _("weekday_friday", default="Friday"),
                _("weekday_saturday", default="Saturday"),
                _("weekday_sunday", default="Sunday"),
            ]
            month_names = [
                _("month_january", default="January"),
                _("month_february", default="February"),
                _("month_march", default="March"),
                _("month_april", default="April"),
                _("month_may", default="May"),
                _("month_june", default="June"),
                _("month_july", default="July"),
                _("month_august", default="August"),
                _("month_september", default="September"),
                _("month_october", default="October"),
                _("month_november", default="November"),
                _("month_december", default="December"),
            ]

            weekday = weekday_names[self.current_time.weekday()]
            month = month_names[self.current_time.month - 1]
            date_str = (
                f"{weekday}, {self.current_time.day} {month} {self.current_time.year}"
            )

        self.date_label.setText(f"📅 {date_str}")

        # Format status
        if self.ntp_status:
            if self.ntp_status.success:
                status_text = (
                    f"🌐 NTP: {STATUS_EMOJIS['ntp_connected']} "
                    f"{_('status.status_ntp_connected', default='Connected')}"
                )
                if self.ntp_status.server:
                    status_text += f" ({self.ntp_status.server})"
            else:
                status_text = (
                    f"🌐 NTP: {STATUS_EMOJIS['ntp_disconnected']} "
                    f"{_('status.status_ntp_disconnected', default='Disconnected')}"
                )
        else:
            status_text = (
                f"🌐 NTP: {STATUS_EMOJIS['ntp_syncing']} "
                f"{_('status.status_ntp_connecting', default='Connecting...')}"
            )

        self.status_label.setText(status_text)

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Force update display to refresh status text
            self._update_display()

            logger.debug("🔄 Digital display widget UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh digital display widget UI text: {e}")


class ThemeControlWidget(QWidget):
    """🎨 Theme control widget with toggle buttons."""

    theme_changed = Signal(str)
    settings_requested = Signal()
    about_requested = Signal()

    def __init__(self, theme_manager: ThemeManager, parent=None):
        """Initialize theme control widget."""
        super().__init__(parent)

        self.theme_manager = theme_manager
        self._setup_ui()

        logger.debug("🎨 Theme control widget initialized")

    def _setup_ui(self):
        """🏗️ Setup theme control UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Theme toggle row
        theme_layout = QHBoxLayout()

        # Dark theme button
        self.dark_button = QPushButton(
            f"{UI_EMOJIS['theme_dark']} "
            f"{_('settings.theme_options.dark', default='Dark')}"
        )
        self.dark_button.setCheckable(True)
        self.dark_button.setProperty("class", "theme-dark")
        self.dark_button.clicked.connect(lambda: self._change_theme("dark"))
        theme_layout.addWidget(self.dark_button)

        # Light theme button
        self.light_button = QPushButton(
            f"{UI_EMOJIS['theme_light']} "
            f"{_('settings.theme_options.light', default='Light')}"
        )
        self.light_button.setCheckable(True)
        self.light_button.setProperty("class", "theme-light")
        self.light_button.clicked.connect(lambda: self._change_theme("light"))
        theme_layout.addWidget(self.light_button)

        layout.addLayout(theme_layout)

        # Control buttons row
        control_layout = QHBoxLayout()

        # Settings button
        self.settings_button = QPushButton(
            f"{UI_EMOJIS['settings']} {_('settings.settings', default='Settings')}"
        )
        self.settings_button.clicked.connect(self.settings_requested.emit)
        control_layout.addWidget(self.settings_button)

        # About button
        self.about_button = QPushButton(
            f"{UI_EMOJIS['about']} {_('settings.about', default='About')}"
        )
        self.about_button.clicked.connect(self.about_requested.emit)
        control_layout.addWidget(self.about_button)

        layout.addLayout(control_layout)

        # Update button states
        self._update_theme_buttons()

    def _change_theme(self, theme_name: str):
        """🎨 Change theme."""
        if self.theme_manager.set_theme(theme_name):
            self._update_theme_buttons()
            self.theme_changed.emit(theme_name)

    def _update_theme_buttons(self):
        """🔄 Update theme button states."""
        current_theme = self.theme_manager.current_theme

        self.dark_button.setChecked(current_theme == "dark")
        self.light_button.setChecked(current_theme == "light")

        # Update button classes for styling
        if current_theme == "dark":
            self.dark_button.setProperty("class", "theme-active")
            self.light_button.setProperty("class", "theme-light")
        else:
            self.dark_button.setProperty("class", "theme-dark")
            self.light_button.setProperty("class", "theme-active")

        # Force style update
        self.dark_button.style().unpolish(self.dark_button)
        self.dark_button.style().polish(self.dark_button)
        self.light_button.style().unpolish(self.light_button)
        self.light_button.style().polish(self.light_button)

    def update_theme(self, theme_name: str):
        """🔄 Update theme from external change."""
        # Only update the UI, don't trigger another theme change
        self.theme_manager.current_theme = theme_name
        self._update_theme_buttons()

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update button texts
            self.dark_button.setText(
                f"{UI_EMOJIS['theme_dark']} "
                f"{_('settings.theme_options.dark', default='Dark')}"
            )
            self.light_button.setText(
                f"{UI_EMOJIS['theme_light']} "
                f"{_('settings.theme_options.light', default='Light')}"
            )
            self.settings_button.setText(
                f"{UI_EMOJIS['settings']} {_('settings.settings', default='Settings')}"
            )
            self.about_button.setText(
                f"{UI_EMOJIS['about']} {_('settings.about', default='About')}"
            )

            # Force button updates
            self.dark_button.update()
            self.light_button.update()
            self.settings_button.update()
            self.about_button.update()

            logger.debug("🔄 Theme control widget UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh theme control widget UI text: {e}")


class ClockWidget(QWidget):
    """🕐 Complete clock widget with analog clock, digital display, and controls."""

    time_updated = Signal(datetime)
    theme_changed = Signal(str)
    settings_requested = Signal()
    about_requested = Signal()

    def __init__(
        self,
        theme_manager: Optional[ThemeManager] = None,
        time_manager: Optional[TimeManager] = None,
        parent=None,
    ):
        """Initialize complete clock widget."""
        super().__init__(parent)

        self.theme_manager = theme_manager or ThemeManager()
        self.time_manager = time_manager
        self.current_time = datetime.now()

        self._setup_ui()
        self._setup_timer()
        self._setup_connections()

        logger.debug("🕐 Clock widget initialized")

    def _setup_ui(self):
        """🏗️ Setup clock widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Analog clock - flexes between its minimum and preferred size so it
        # never overlaps the digital display below on short screens.
        self.analog_clock = AnalogClockWidget()
        layout.addWidget(self.analog_clock, 1, Qt.AlignmentFlag.AlignHCenter)

        # Proportional gap that collapses first when vertical space is scarce.
        layout.addSpacing(SECTION_GAP)

        # Digital display - ensure it's below the analog clock
        self.digital_display = DigitalDisplayWidget()
        layout.addWidget(self.digital_display, 0, Qt.AlignmentFlag.AlignHCenter)

        # Add spacing between digital display and theme controls
        layout.addSpacing(CONTROL_GAP)

        # Theme controls - ensure they're at the bottom
        self.theme_controls = ThemeControlWidget(self.theme_manager)
        layout.addWidget(self.theme_controls, 0, Qt.AlignmentFlag.AlignHCenter)

        # Add stretch to fill remaining space
        layout.addStretch(0)

    def _setup_timer(self):
        """⏰ Setup update timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_time)
        self.update_timer.start(1000)  # Update every second

    def _setup_connections(self):
        """🔗 Setup signal connections."""
        # Connect theme control signals
        self.theme_controls.theme_changed.connect(self.theme_changed.emit)
        self.theme_controls.settings_requested.connect(self.settings_requested.emit)
        self.theme_controls.about_requested.connect(self.about_requested.emit)

    def _update_time(self):
        """🔄 Update time display."""
        if self.time_manager:
            self.current_time = self.time_manager.get_current_time()
        else:
            self.current_time = datetime.now()

        # Update displays
        self.analog_clock.set_time(self.current_time)
        self.digital_display.set_time(self.current_time)

        # Emit signal
        self.time_updated.emit(self.current_time)

    def set_time_manager(self, time_manager: TimeManager):
        """⏰ Set time manager."""
        self.time_manager = time_manager

    def set_ntp_client(self, ntp_client):
        """🌐 Set NTP client for time synchronization."""
        # For now, we'll just store it - could be used for manual sync
        self.ntp_client = ntp_client
        logger.debug("🌐 NTP client set for clock widget")

    def update_ntp_status(self, status: Optional[NTPResult]):
        """🌐 Update NTP status display."""
        self.digital_display.set_ntp_status(status)

    def apply_theme(self):
        """🎨 Apply current theme to clock."""
        theme = self.theme_manager.get_current_theme()
        colors = theme["colors"]

        # Update analog clock colors
        self.analog_clock.set_colors(
            colors["clock_face"],
            colors["clock_border"],
            colors["clock_numbers"],
            colors["clock_hands"],
            colors["clock_center"],
        )

        # Update theme controls
        self.theme_controls._update_theme_buttons()

    def get_current_time(self) -> datetime:
        """🕐 Get current time."""
        return self.current_time

    def force_update(self):
        """🔄 Force immediate time update."""
        self._update_time()

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Refresh theme control buttons
            if hasattr(self, "theme_controls"):
                self.theme_controls.refresh_ui_text()

            # Refresh digital display
            if hasattr(self, "digital_display"):
                self.digital_display.refresh_ui_text()

            logger.debug("🔄 Clock widget UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh clock widget UI text: {e}")
