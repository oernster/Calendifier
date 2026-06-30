"""
📅 Calendar Widget for Calendar Application

This module contains the calendar grid display with navigation and event indicators.
"""

import logging
from datetime import date, datetime
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from calendar_app.core.calendar_manager import CalendarManager
from calendar_app.data.models import CalendarMonth, CalendarDay
from calendar_app.localization.i18n_manager import get_i18n_manager, convert_numbers


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that always uses current locale."""
    return get_i18n_manager().get_text(key, **kwargs)


from version import UI_EMOJIS  # noqa: E402

logger = logging.getLogger(__name__)


class CalendarDayWidget(QLabel):
    """📅 Individual calendar day widget."""

    clicked = Signal(date)

    def __init__(self, calendar_day: CalendarDay, parent=None):
        """Initialize calendar day widget."""
        super().__init__(parent)

        self.calendar_day = calendar_day
        self.is_selected = False

        self._setup_widget()
        self._update_display()

    def _setup_widget(self):
        """🏗️ Setup day widget properties."""
        # Set EXACT same size for ALL calendar day widgets (scaled for 13" MacBook)
        self.setFixedSize(80, 64)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)

        # Ensure consistent sizing policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set font size smaller for better text fitting
        font = self.font()
        font.setPointSize(8)
        self.setFont(font)

    def _update_display(self):
        """🔄 Update day display."""
        day = self.calendar_day

        # Build display text using HTML for better formatting
        html_parts = []

        # Day number (normal size) - convert to locale-appropriate numerals
        day_num = day.date.day
        converted_day_num = convert_numbers(str(day_num))
        html_parts.append(
            f'<div style="font-weight: bold; margin-bottom: 2px;">'
            f"{converted_day_num}</div>"
        )

        # Add event indicators as larger icons
        if day.has_events():
            indicators = day.get_event_indicators()
            if indicators:
                # Create a grid layout for icons (2 columns, up to 3 rows)
                icon_html = (
                    '<div style="display: grid; '
                    'grid-template-columns: 1fr 1fr; gap: 1px; font-size: 20px;">'
                )

                for i, indicator in enumerate(indicators):
                    if i < 6:  # Maximum 6 slots (5 icons + 1 overflow)
                        icon_html += (
                            f'<span style="text-align: center;">{indicator}</span>'
                        )

                # Fill remaining slots with empty spans to maintain grid
                remaining_slots = 6 - len(indicators)
                for _ in range(remaining_slots):
                    icon_html += "<span></span>"

                icon_html += "</div>"
                html_parts.append(icon_html)

        # Add holiday indicator
        if day.is_holiday and day.holiday:
            holiday_name = (
                day.holiday.name if hasattr(day.holiday, "name") else str(day.holiday)
            )

            # Ensure ENTIRE holiday name is always visible - no truncation
            lines = []
            remaining_text = holiday_name

            while remaining_text:
                if len(remaining_text) <= 12:
                    # Fits on one line
                    lines.append(remaining_text)
                    break
                else:
                    # Need to break the line
                    break_point = -1
                    # Look for space between characters 8-12
                    for i in range(8, min(12, len(remaining_text))):
                        if remaining_text[i] == " ":
                            break_point = i
                            break

                    if break_point > 0:
                        # Break at space
                        lines.append(remaining_text[:break_point])
                        remaining_text = remaining_text[break_point + 1 :]
                    else:
                        # Break with hyphen at character 10
                        lines.append(remaining_text[:10] + "-")
                        remaining_text = remaining_text[10:]

            # Join lines with <br> tags
            holiday_display = "<br>".join(lines)

            # Use smaller font for longer text to ensure it fits
            font_size = "8px" if len(lines) > 2 else "9px" if len(lines) > 1 else "10px"

            # Use theme-aware colors: inherit from parent
            # (white in dark mode, black in light mode)
            html_parts.append(
                f'<div style="font-size: {font_size}; margin-top: 1px; '
                f"text-align: left; line-height: 0.9; font-weight: bold; "
                f'overflow: hidden;">{holiday_display}</div>'
            )

        # Set HTML content
        self.setText("".join(html_parts))

        # Set widget class for styling
        self._update_style_class()

    def _update_style_class(self):
        """🎨 Update widget style class."""
        day = self.calendar_day

        classes = ["calendar-day"]

        if day.is_today:
            classes.append("calendar-day-today")
        elif day.is_weekend:
            classes.append("calendar-day-weekend")
        elif day.is_holiday:
            classes.append("calendar-day-holiday")

        if day.is_other_month:
            classes.append("calendar-day-other-month")

        if self.is_selected:
            classes.append("calendar-day-selected")

        self.setProperty("class", " ".join(classes))

        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)

    def set_selected(self, selected: bool):
        """🎯 Set selection state."""
        self.is_selected = selected
        self._update_style_class()

    def update_calendar_day(self, calendar_day: CalendarDay):
        """🔄 Update calendar day data."""
        self.calendar_day = calendar_day
        self._update_display()

    def mousePressEvent(self, event):
        """🖱️ Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug(
                f"🖱️ DEBUG: Day widget clicked for date: {self.calendar_day.date}"
            )
            self.clicked.emit(self.calendar_day.date)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """🖱️ Handle mouse enter."""
        # Add hover effect
        self.setStyleSheet("background-color: rgba(0, 120, 212, 0.1);")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """🖱️ Handle mouse leave."""
        # Remove hover effect
        self.setStyleSheet("")
        super().leaveEvent(event)


class CalendarHeaderWidget(QWidget):
    """📅 Calendar header with navigation and month/year display."""

    previous_month = Signal()
    next_month = Signal()
    previous_year = Signal()
    next_year = Signal()
    today_clicked = Signal()
    month_year_clicked = Signal(int, int)  # year, month

    def __init__(self, parent=None):
        """Initialize calendar header."""
        super().__init__(parent)

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self._setup_ui()

    def _setup_ui(self):
        """🏗️ Setup header UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Previous month button
        self.prev_month_btn = QPushButton(UI_EMOJIS["navigation_prev"])
        self.prev_month_btn.setProperty("class", "icon")
        self.prev_month_btn.setToolTip(_("toolbar.previous", default="Previous"))
        self.prev_month_btn.clicked.connect(self.previous_month.emit)
        layout.addWidget(self.prev_month_btn)

        # Month label only (clickable)
        self.month_label = QLabel()
        self.month_label.setProperty("class", "title")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.month_label.mousePressEvent = self._month_year_clicked
        layout.addWidget(self.month_label, 1)

        # Next month button
        self.next_month_btn = QPushButton(UI_EMOJIS["navigation_next"])
        self.next_month_btn.setProperty("class", "icon")
        self.next_month_btn.setToolTip(_("toolbar.next", default="Next"))
        self.next_month_btn.clicked.connect(self.next_month.emit)
        layout.addWidget(self.next_month_btn)

        # Spacer
        layout.addStretch()

        # Today button
        self.today_btn = QPushButton(
            f"{UI_EMOJIS['today']} {_('toolbar.today', default='Today')}"
        )
        self.today_btn.setToolTip(_("calendar.today", default="Today"))
        self.today_btn.clicked.connect(self.today_clicked.emit)
        layout.addWidget(self.today_btn)

        # Year navigation buttons with year label in between
        self.prev_year_btn = QPushButton("◀◀")
        self.prev_year_btn.setProperty("class", "icon")
        self.prev_year_btn.setToolTip(_("toolbar.previous", default="Previous"))
        self.prev_year_btn.clicked.connect(self.previous_year.emit)
        layout.addWidget(self.prev_year_btn)

        # Year label (clickable)
        self.year_label = QLabel()
        self.year_label.setProperty("class", "title")
        self.year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.year_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.year_label.mousePressEvent = self._month_year_clicked
        self.year_label.setMinimumWidth(60)  # Ensure enough width for 4-digit year
        layout.addWidget(self.year_label)

        self.next_year_btn = QPushButton("▶▶")
        self.next_year_btn.setProperty("class", "icon")
        self.next_year_btn.setToolTip(_("toolbar.next", default="Next"))
        self.next_year_btn.clicked.connect(self.next_year.emit)
        layout.addWidget(self.next_year_btn)

        self._update_display()

    def _update_display(self):
        """🔄 Update header display."""
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

        month_name = month_names[self.current_month - 1]
        converted_year = convert_numbers(str(self.current_year))

        # Set month label (left side)
        self.month_label.setText(f"📅 {month_name}")

        # Set year label (right side between year arrows)
        self.year_label.setText(converted_year)

    def set_month_year(self, year: int, month: int):
        """📅 Set current month and year."""
        self.current_year = year
        self.current_month = month
        self._update_display()

    def _month_year_clicked(self, event):
        """📅 Handle month/year label click."""
        # For now, just emit signal - could open date picker dialog
        self.month_year_clicked.emit(self.current_year, self.current_month)

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update button texts and tooltips
            self.today_btn.setText(
                f"{UI_EMOJIS['today']} {_('toolbar.today', default='Today')}"
            )
            self.today_btn.setToolTip(_("calendar.today", default="Today"))

            self.prev_month_btn.setToolTip(_("toolbar.previous", default="Previous"))
            self.next_month_btn.setToolTip(_("toolbar.next", default="Next"))
            self.prev_year_btn.setToolTip(_("toolbar.previous", default="Previous"))
            self.next_year_btn.setToolTip(_("toolbar.next", default="Next"))

            # Update month/year display
            self._update_display()

            # Force button updates
            self.today_btn.update()
            self.prev_month_btn.update()
            self.next_month_btn.update()
            self.prev_year_btn.update()
            self.next_year_btn.update()
            self.month_label.update()
            self.year_label.update()

            logger.debug("🔄 Calendar header UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh calendar header UI text: {e}")


class CalendarGridWidget(QWidget):
    """📆 Calendar grid with day widgets."""

    date_selected = Signal(date)

    def __init__(self, parent=None):
        """Initialize calendar grid."""
        super().__init__(parent)

        self.calendar_month: Optional[CalendarMonth] = None
        self.day_widgets: List[List[CalendarDayWidget]] = []
        self.selected_date: Optional[date] = None
        self.show_week_numbers: bool = True  # Always show week numbers
        self.week_number_widgets: List[QLabel] = []

        self._setup_ui()

    def _setup_ui(self):
        """🏗️ Setup grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Day headers
        self._create_day_headers(layout)

        # Calendar grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(1)

        # Set fixed size for the grid widget to ensure consistent layout
        # Width: 7 widgets * 100px + 6 spacings * 1px + week numbers column
        # (30px) + 1px margin = 737px (when week numbers shown)
        # Height: 6 widgets * 80px + 5 spacings * 1px + extra margin = 490px
        self._update_grid_size()

        layout.addWidget(self.grid_widget)

        # Initialize empty grid
        self._create_empty_grid()

    def _update_grid_size(self):
        """📏 Update grid size - always includes week numbers."""
        # Width: week numbers column (24px) + 7 widgets * 80px
        # + 7 spacings * 1px = 591px
        # Height: 6 widgets * 64px + 5 spacings * 1px = 389px (scaled for 13" MacBook)
        self.grid_widget.setFixedSize(591, 389)

    def _create_day_headers(self, layout: QVBoxLayout):
        """📅 Create day name headers."""
        # Create header widget with width matching grid widget
        header_widget = QWidget()
        self._update_header_size(header_widget)

        # Use QGridLayout to match the grid layout below exactly
        header_layout = QGridLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(1)  # Same spacing as grid layout

        # Store header widget for later updates
        self.header_widget = header_widget
        self.header_layout = header_layout

        # Initially create with localized day names
        day_names = [
            _("calendar.days_short.mon", default="Mon"),
            _("calendar.days_short.tue", default="Tue"),
            _("calendar.days_short.wed", default="Wed"),
            _("calendar.days_short.thu", default="Thu"),
            _("calendar.days_short.fri", default="Fri"),
            _("calendar.days_short.sat", default="Sat"),
            _("calendar.days_short.sun", default="Sun"),
        ]
        self._update_day_headers(day_names)

        layout.addWidget(header_widget)

    def _update_header_size(self, header_widget):
        """📏 Update header size - always includes week numbers."""
        header_widget.setFixedSize(
            591, 24
        )  # Same width as scaled grid widget with week numbers

    def _update_day_headers(self, day_names: List[str] = None):
        """📅 Update day name headers."""
        # Clear existing labels
        while self.header_layout.count():
            child = self.header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get localized day names if not provided
        if day_names is None:
            day_names = [
                _("calendar.days_short.mon", default="Mon"),
                _("calendar.days_short.tue", default="Tue"),
                _("calendar.days_short.wed", default="Wed"),
                _("calendar.days_short.thu", default="Thu"),
                _("calendar.days_short.fri", default="Fri"),
                _("calendar.days_short.sat", default="Sat"),
                _("calendar.days_short.sun", default="Sun"),
            ]

        # Always add week number header
        week_header = QLabel(_("calendar.week_short", default="Wk"))
        week_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_header.setProperty("class", "secondary")
        week_header.setFixedSize(24, 24)
        week_header.setToolTip(_("calendar.week_number", default="Week Number"))
        self.header_layout.addWidget(week_header, 0, 0)
        col_offset = 1

        # Add day name labels using grid layout to match calendar grid exactly
        for col, day_name in enumerate(day_names):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("class", "secondary")
            label.setFixedSize(80, 24)
            self.header_layout.addWidget(
                label, 0, col + col_offset
            )  # Row 0, column col + offset

    def _create_empty_grid(self):
        """📅 Create empty calendar grid - always with week numbers."""
        # Initialize lists if they don't exist
        if not hasattr(self, "day_widgets"):
            self.day_widgets = []
        if not hasattr(self, "week_number_widgets"):
            self.week_number_widgets = []

        # Always use column offset of 1 for week numbers
        col_offset = 1
        logger.debug(
            f"📅 Creating grid with week numbers: always enabled, "
            f"col_offset: {col_offset}"
        )

        for week in range(6):  # 6 weeks maximum
            # Create week number widget
            week_number_widget = QLabel()
            week_number_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            week_number_widget.setProperty("class", "week-number")
            week_number_widget.setFixedSize(24, 64)

            # Always add week number widget to grid
            self.grid_layout.addWidget(week_number_widget, week, 0)
            week_number_widget.hide()  # Hide until we have real data

            self.week_number_widgets.append(week_number_widget)

            week_widgets = []
            for day in range(7):  # 7 days per week
                # Create placeholder day
                placeholder_day = CalendarDay(date=date.today())
                day_widget = CalendarDayWidget(placeholder_day)
                day_widget.clicked.connect(self._day_clicked)
                day_widget.hide()  # Hide until we have real data

                # Add widget to grid with week number column offset
                self.grid_layout.addWidget(day_widget, week, day + col_offset)

                week_widgets.append(day_widget)

            self.day_widgets.append(week_widgets)

        # Set row and column stretch factors to maintain proper sizing
        for row in range(6):
            self.grid_layout.setRowStretch(row, 1)

        # Set column stretch factors - always with week numbers
        self.grid_layout.setColumnStretch(0, 0)  # Week number column - no stretch
        for col in range(1, 8):  # Day columns
            self.grid_layout.setColumnStretch(col, 1)

    def update_calendar(self, calendar_month: CalendarMonth):
        """📆 Update calendar with new month data."""
        self.calendar_month = calendar_month

        # Update day widgets
        for week_idx, week in enumerate(calendar_month.weeks):
            # Always update week numbers
            if week_idx < len(self.week_number_widgets):
                week_number_widget = self.week_number_widgets[week_idx]
                if week:  # If week has days
                    # Get week number from first day of the week -
                    # convert to locale-appropriate numerals
                    first_day = week[0].date
                    week_number = first_day.isocalendar()[1]  # ISO week number
                    converted_week_number = convert_numbers(str(week_number))
                    week_number_widget.setText(converted_week_number)
                    week_number_widget.show()
                else:
                    week_number_widget.hide()

            for day_idx, calendar_day in enumerate(week):
                if week_idx < len(self.day_widgets) and day_idx < len(
                    self.day_widgets[week_idx]
                ):
                    day_widget = self.day_widgets[week_idx][day_idx]
                    day_widget.update_calendar_day(calendar_day)
                    day_widget.show()

        # Hide unused widgets
        for week_idx in range(len(calendar_month.weeks), 6):
            # Hide unused week number widgets
            if week_idx < len(self.week_number_widgets):
                self.week_number_widgets[week_idx].hide()

            for day_idx in range(7):
                if week_idx < len(self.day_widgets) and day_idx < len(
                    self.day_widgets[week_idx]
                ):
                    self.day_widgets[week_idx][day_idx].hide()

        # Update selection
        self._update_selection()

    def _day_clicked(self, clicked_date: date):
        """📅 Handle day click."""
        logger.debug(f"📅 DEBUG: Grid received day click for date: {clicked_date}")
        self.selected_date = clicked_date
        self._update_selection()
        logger.debug(
            f"📅 DEBUG: Grid emitting date_selected signal for: {clicked_date}"
        )
        self.date_selected.emit(clicked_date)

    def _update_selection(self):
        """🎯 Update day selection display."""
        for week_widgets in self.day_widgets:
            for day_widget in week_widgets:
                is_selected = (
                    self.selected_date is not None
                    and day_widget.calendar_day.date == self.selected_date
                )
                day_widget.set_selected(is_selected)

    def set_selected_date(self, selected_date: date):
        """🎯 Set selected date."""
        self.selected_date = selected_date
        self._update_selection()

    def get_selected_date(self) -> Optional[date]:
        """📅 Get currently selected date."""
        return self.selected_date

    # Week numbers are always enabled - no toggle method needed


class CalendarWidget(QWidget):
    """📅 Complete calendar widget with header and grid."""

    date_selected = Signal(date)
    month_changed = Signal(int, int)  # year, month

    def __init__(self, calendar_manager: Optional[CalendarManager] = None, parent=None):
        """Initialize calendar widget."""
        super().__init__(parent)

        self.calendar_manager = calendar_manager
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self._setup_ui()
        self._setup_connections()

        # Initially show placeholder until calendar manager is injected
        self._show_placeholder_calendar()

        logger.debug("📅 Calendar widget initialized")

    def _setup_ui(self):
        """🏗️ Setup calendar widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Calendar header
        self.header = CalendarHeaderWidget()
        layout.addWidget(self.header)

        # Calendar grid
        self.grid = CalendarGridWidget()
        layout.addWidget(self.grid, 1)

        # Set size policy and fixed size for consistent layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Set minimum size to accommodate scaled week numbers
        # With week numbers: 7*80 + 24 (week numbers) + 14 margins = 598px width
        # Height: 389px (grid) + 24px (header) + 16px (margins) = 429px
        self.setMinimumSize(598, 429)

    def _setup_connections(self):
        """🔗 Setup signal connections."""
        # Header navigation
        self.header.previous_month.connect(self.navigate_previous_month)
        self.header.next_month.connect(self.navigate_next_month)
        self.header.previous_year.connect(self.navigate_previous_year)
        self.header.next_year.connect(self.navigate_next_year)
        self.header.today_clicked.connect(self.jump_to_today)

        # Grid selection
        self.grid.date_selected.connect(self.date_selected.emit)

    def set_calendar_manager(self, calendar_manager: CalendarManager):
        """📅 Set calendar manager."""
        self.calendar_manager = calendar_manager
        # Update current position from manager
        self.current_year, self.current_month = calendar_manager.get_current_position()

        # Update day headers to match calendar manager's first day of week setting
        day_names = calendar_manager.get_day_names()
        self.grid._update_day_headers(day_names)

        self._load_current_month()
        logger.debug(
            f"📅 Calendar manager set and loaded "
            f"{self.current_year}-{self.current_month:02d}"
        )

    def _load_current_month(self):
        """📆 Load current month data."""
        if not self.calendar_manager:
            return

        try:
            calendar_month = self.calendar_manager.get_month_data(
                self.current_year, self.current_month
            )

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)

            logger.debug(
                f"📆 Loaded calendar for {self.current_year}-{self.current_month:02d}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to load calendar month: {e}")

    def navigate_previous_month(self):
        """◀️ Navigate to previous month."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.navigate_previous_month()
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)
        else:
            # Navigate without manager
            if self.current_month == 1:
                self.current_year -= 1
                self.current_month = 12
            else:
                self.current_month -= 1
            self._show_placeholder_calendar()
            self.month_changed.emit(self.current_year, self.current_month)

    def navigate_next_month(self):
        """▶️ Navigate to next month."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.navigate_next_month()
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)
        else:
            # Navigate without manager
            if self.current_month == 12:
                self.current_year += 1
                self.current_month = 1
            else:
                self.current_month += 1
            self._show_placeholder_calendar()
            self.month_changed.emit(self.current_year, self.current_month)

    def navigate_previous_year(self):
        """⏮️ Navigate to previous year."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.navigate_previous_year()
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)
        else:
            # Navigate without manager
            self.current_year -= 1
            self._show_placeholder_calendar()
            self.month_changed.emit(self.current_year, self.current_month)

    def navigate_next_year(self):
        """⏭️ Navigate to next year."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.navigate_next_year()
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)
        else:
            # Navigate without manager
            self.current_year += 1
            self._show_placeholder_calendar()
            self.month_changed.emit(self.current_year, self.current_month)

    def jump_to_today(self):
        """📅 Jump to today's date."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.jump_to_today()
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)

            # Select today's date
            today = date.today()
            self.grid.set_selected_date(today)
            self.date_selected.emit(today)
        else:
            # Jump to today without manager
            today = date.today()
            self.current_year = today.year
            self.current_month = today.month
            self._show_placeholder_calendar()
            self.grid.set_selected_date(today)
            self.date_selected.emit(today)
            self.month_changed.emit(self.current_year, self.current_month)

    def navigate_to_date(self, target_date: date):
        """📅 Navigate to specific date."""
        if self.calendar_manager:
            calendar_month = self.calendar_manager.navigate_to_month(
                target_date.year, target_date.month
            )
            self.current_year = calendar_month.year
            self.current_month = calendar_month.month

            self.grid.update_calendar(calendar_month)
            self.header.set_month_year(self.current_year, self.current_month)
            self.month_changed.emit(self.current_year, self.current_month)

            # Select the target date
            self.grid.set_selected_date(target_date)
            self.date_selected.emit(target_date)

    def refresh_calendar(self):
        """🔄 Refresh current calendar display."""
        self._load_current_month()

    def set_first_day_of_week(self, day: int):
        """⚙️ Set first day of week and refresh calendar."""
        if self.calendar_manager:
            self.calendar_manager.set_first_day_of_week(day)
            # Update day headers to match new first day of week
            day_names = self.calendar_manager.get_day_names()
            self.grid._update_day_headers(day_names)
            # Refresh calendar to show new layout
            self.refresh_calendar()

    def set_holiday_country(self, country_code: str):
        """🌍 Set holiday country and refresh calendar."""
        if self.calendar_manager:
            self.calendar_manager.set_holiday_country(country_code)
            # Refresh calendar to show new holidays
            self.refresh_calendar()

    # Week numbers are always enabled - no toggle method needed

    def get_selected_date(self) -> Optional[date]:
        """📅 Get currently selected date."""
        return self.grid.get_selected_date()

    def set_selected_date(self, selected_date: date):
        """🎯 Set selected date."""
        # Navigate to the month if necessary
        if (
            selected_date.year != self.current_year
            or selected_date.month != self.current_month
        ):
            self.navigate_to_date(selected_date)
        else:
            self.grid.set_selected_date(selected_date)
            self.date_selected.emit(selected_date)

    def get_current_month_year(self) -> tuple[int, int]:
        """📅 Get current month and year."""
        return (self.current_year, self.current_month)

    def _show_placeholder_calendar(self):
        """📅 Show placeholder calendar with basic day numbers."""
        import calendar
        from calendar_app.data.models import CalendarDay, CalendarMonth

        weeks = []
        today = date.today()

        # Use Python's calendar module to get the correct calendar structure
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_calendar = cal.monthdatescalendar(self.current_year, self.current_month)

        for week_dates in month_calendar:
            week = []
            for day_date in week_dates:
                is_other_month = day_date.month != self.current_month

                calendar_day = CalendarDay(
                    date=day_date,
                    is_today=(day_date == today),
                    is_weekend=(day_date.weekday() >= 5),
                    is_other_month=is_other_month,
                    is_holiday=False,
                    holiday=None,
                    events=[],
                )
                week.append(calendar_day)

            weeks.append(week)

        # Create calendar month
        calendar_month = CalendarMonth(
            year=self.current_year,
            month=self.current_month,
            weeks=weeks,
            holidays=[],
            events=[],
        )

        # Update display
        self.grid.update_calendar(calendar_month)
        self.header.set_month_year(self.current_year, self.current_month)

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Refresh header
            if hasattr(self.header, "refresh_ui_text"):
                self.header.refresh_ui_text()

            # Update day headers with localized day names AND week header
            if self.calendar_manager:
                day_names = self.calendar_manager.get_day_names()
                self.grid._update_day_headers(day_names)

                # Refresh holiday translations for new locale
                self.calendar_manager.refresh_holiday_translations()
            else:
                # Even without calendar manager, update day headers to
                # refresh week header text
                self.grid._update_day_headers()

            # Force complete calendar refresh to update month names and holiday content
            self.refresh_calendar()

            logger.debug("🔄 Calendar widget UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh calendar widget UI text: {e}")
