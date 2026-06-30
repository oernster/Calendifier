"""
📝 Event Panel for Calendar Application

This module contains the event display and management panel.
"""

import logging
from datetime import date, time
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QMessageBox,
    QFileDialog,
    QDialog,
)
from PySide6.QtCore import Qt, Signal

from calendar_app.core.event_manager import EventManager
from calendar_app.data.models import Event
from calendar_app.ui.event_dialog import EventDialog
from calendar_app.localization.i18n_manager import (
    get_i18n_manager,
    format_date_for_locale,
)


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that always uses current locale."""
    try:
        # Extract default before passing to get_text
        default = kwargs.pop("default", key)
        result = get_i18n_manager().get_text(key, **kwargs)
        # If result is the same as key, it means translation wasn't found
        if result == key and default != key:
            return default
        return result
    except Exception:
        # Fallback to default or key if translation fails
        return kwargs.get("default", key)


from version import UI_EMOJIS  # noqa: E402

logger = logging.getLogger(__name__)


class CustomDeleteDialog(QDialog):
    """Custom dialog for delete recurring event with proper width control."""

    def __init__(self, title: str, message: str, event_title: str, parent=None):
        super().__init__(parent)
        self.result_action = None

        self.setWindowTitle(title)
        self.setMinimumWidth(800)
        self.setFixedWidth(800)  # Force exact width

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Icon and message
        message_layout = QHBoxLayout()

        # Question icon (using emoji since we don't have icon resources)
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 32px;")
        message_layout.addWidget(icon_label)

        # Message text
        message_label = QLabel(f"{message}\n\n{event_title}")
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 12px; padding-left: 10px;")
        message_layout.addWidget(message_label, 1)

        layout.addLayout(message_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.delete_this_btn = QPushButton(
            _("events.delete_this_occurrence", default="Delete this occurrence only")
        )
        self.delete_this_btn.clicked.connect(lambda: self._set_result("delete_this"))
        self.delete_this_btn.setMinimumWidth(200)
        button_layout.addWidget(self.delete_this_btn)

        self.delete_all_btn = QPushButton(
            _("events.delete_all_occurrences", default="Delete all occurrences")
        )
        self.delete_all_btn.clicked.connect(lambda: self._set_result("delete_all"))
        self.delete_all_btn.setMinimumWidth(200)
        button_layout.addWidget(self.delete_all_btn)

        self.cancel_btn = QPushButton(_("Cancel", default="Cancel"))
        self.cancel_btn.clicked.connect(lambda: self._set_result("cancel"))
        self.cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Set default button
        self.cancel_btn.setDefault(True)

    def _set_result(self, action: str):
        self.result_action = action
        self.accept()

    def get_result(self) -> str:
        return self.result_action or "cancel"


class EventItemWidget(QFrame):
    """📝 Individual event item widget."""

    edit_requested = Signal(Event)
    delete_requested = Signal(Event)

    def __init__(self, event: Event, parent=None):
        """Initialize event item widget."""
        super().__init__(parent)

        self.event_data = event
        self._setup_ui()

    def _setup_ui(self):
        """🏗️ Setup event item UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(4, 4, 4, 4)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header row with title and actions
        header_layout = QHBoxLayout()

        # Event title with emoji
        title_text = self.event_data.get_display_title()
        self.title_label = QLabel(title_text)
        self.title_label.setProperty("class", "title")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label, 1)

        # Action buttons
        self.edit_btn = QPushButton(UI_EMOJIS["edit_event"])
        self.edit_btn.setProperty("class", "icon")
        self.edit_btn.setToolTip(_("events.edit_event", default="Edit event"))
        self.edit_btn.setFixedSize(24, 24)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.event_data))
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(UI_EMOJIS["delete_event"])
        self.delete_btn.setProperty("class", "icon")
        self.delete_btn.setToolTip(_("events.delete_event", default="Delete event"))
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.event_data)
        )
        header_layout.addWidget(self.delete_btn)

        layout.addLayout(header_layout)

        # Time and details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)

        # Time information
        if self.event_data.is_all_day:
            time_text = f"🕐 {_('events.all_day', default='All day')}"
        elif self.event_data.start_time:
            if self.event_data.end_time:
                time_text = f"🕐 {self.event_data.start_time.strftime('%H:%M')} - {self.event_data.end_time.strftime('%H:%M')}"  # noqa: E501
            else:
                time_text = f"🕐 {self.event_data.start_time.strftime('%H:%M')}"
        else:
            time_text = f"🕐 {_('events.no_time_set', default='No time set')}"

        self.time_label = QLabel(time_text)
        self.time_label.setProperty("class", "secondary")
        details_layout.addWidget(self.time_label)

        # Description (if any)
        if self.event_data.description:
            self.desc_label = QLabel(self.event_data.description)
            self.desc_label.setProperty("class", "secondary")
            self.desc_label.setWordWrap(True)
            self.desc_label.setMaximumHeight(60)  # Limit height
            details_layout.addWidget(self.desc_label)

        layout.addLayout(details_layout)

        # Set background color based on category
        self._update_style()

    def _update_style(self):
        """🎨 Update widget styling based on event category."""
        # Set a subtle background color based on event category
        category_colors = {
            "work": "#0078d4",
            "personal": "#16c60c",
            "meeting": "#ffb900",
            "meal": "#8a8a8a",
            "holiday": "#d13438",
            "default": "#6b6b6b",
        }

        color = category_colors.get(
            self.event_data.category, category_colors["default"]
        )

        # Set a very subtle background
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        self.setStyleSheet(f"""
            EventItemWidget {{
                border-left: 3px solid {color};
                background-color: rgba({red}, {green}, {blue}, 0.1);
            }}
        """)

    def update_event(self, event: Event):
        """🔄 Update event data."""
        self.event_data = event

        # Update title
        self.title_label.setText(event.get_display_title())

        # Update time
        if event.is_all_day:
            time_text = f"🕐 {_('events.all_day', default='All day')}"
        elif event.start_time:
            if event.end_time:
                time_text = f"🕐 {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}"  # noqa: E501
            else:
                time_text = f"🕐 {event.start_time.strftime('%H:%M')}"
        else:
            time_text = f"🕐 {_('events.no_time_set', default='No time set')}"

        self.time_label.setText(time_text)

        # Update description
        if hasattr(self, "desc_label"):
            if event.description:
                self.desc_label.setText(event.description)
                self.desc_label.show()
            else:
                self.desc_label.hide()

        self._update_style()


class EventListWidget(QScrollArea):
    """📝 Scrollable list of events."""

    edit_requested = Signal(Event)
    delete_requested = Signal(Event)

    def __init__(self, parent=None):
        """Initialize event list widget."""
        super().__init__(parent)

        self.events: List[Event] = []
        self.event_widgets: List[EventItemWidget] = []

        self._setup_ui()

    def _setup_ui(self):
        """🏗️ Setup event list UI."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create scroll content widget
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)

        # Add stretch to push items to top
        self.scroll_layout.addStretch()

        self.setWidget(self.scroll_content)

    def set_events(self, events: List[Event]):
        """📝 Set events to display."""
        self.events = events
        self._update_display()

    def _update_display(self):
        """🔄 Update event display."""
        # Clear existing widgets
        self._clear_widgets()

        # Create new widgets
        self.event_widgets = []

        if not self.events:
            # Show "no events" message
            no_events_label = QLabel(
                f"📅 {_('events.no_events_for_date', default='No events for this date')}"
            )
            no_events_label.setProperty("class", "secondary")
            no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.insertWidget(0, no_events_label)
        else:
            # Sort events by time
            sorted_events = sorted(
                self.events,
                key=lambda e: (
                    e.start_time or time.min if not e.is_all_day else time.min,
                    e.title,
                ),
            )

            for event in sorted_events:
                event_widget = EventItemWidget(event)
                event_widget.edit_requested.connect(self.edit_requested.emit)
                event_widget.delete_requested.connect(self.delete_requested.emit)

                self.scroll_layout.insertWidget(len(self.event_widgets), event_widget)
                self.event_widgets.append(event_widget)

    def _clear_widgets(self):
        """🗑️ Clear all event widgets."""
        # Remove all widgets except the stretch
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.event_widgets.clear()

    def add_event(self, event: Event):
        """➕ Add new event to list."""
        self.events.append(event)
        self._update_display()

    def remove_event(self, event: Event):
        """➖ Remove event from list."""
        if event in self.events:
            self.events.remove(event)
            self._update_display()

    def update_event(self, updated_event: Event):
        """🔄 Update existing event in list."""
        for i, event in enumerate(self.events):
            if event.id == updated_event.id:
                self.events[i] = updated_event
                break

        self._update_display()


class EventPanel(QWidget):
    """📝 Complete event panel with list and controls."""

    event_created = Signal(Event)
    event_updated = Signal(Event)
    event_deleted = Signal(Event)

    def __init__(self, event_manager: Optional[EventManager] = None, parent=None):
        """Initialize event panel."""
        super().__init__(parent)

        self.event_manager = event_manager
        self.current_date: Optional[date] = None

        self._setup_ui()
        self._setup_connections()

        logger.debug("📝 Event panel initialized")

    def _setup_ui(self):
        """🏗️ Setup event panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header with date and add button
        header_layout = QHBoxLayout()

        self.date_label = QLabel(f"📅 {_('calendar.today', default='Select a date')}")
        self.date_label.setProperty("class", "title")
        header_layout.addWidget(self.date_label, 1)

        self.add_event_btn = QPushButton(
            f"{UI_EMOJIS['add_event']} {_('toolbar.add_event', default='Add Event')}"
        )
        self.add_event_btn.clicked.connect(self._add_event)
        self.add_event_btn.setEnabled(
            True
        )  # Enable by default - will use today's date if no date selected
        header_layout.addWidget(self.add_event_btn)

        layout.addLayout(header_layout)

        # Event list
        self.event_list = EventListWidget()
        layout.addWidget(self.event_list, 1)

        # Action buttons
        action_layout = QHBoxLayout()

        self.import_btn = QPushButton(
            f"{UI_EMOJIS['import']} {_('import_export.import', default='Import')}"
        )
        self.import_btn.setToolTip(
            _("import_export.import_events", default="Import events from file")
        )
        self.import_btn.clicked.connect(self._import_events)
        action_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton(
            f"{UI_EMOJIS['export']} {_('import_export.export', default='Export')}"
        )
        self.export_btn.setToolTip(
            _("import_export.export_events", default="Export events to file")
        )
        self.export_btn.clicked.connect(self._export_events)
        action_layout.addWidget(self.export_btn)

        action_layout.addStretch()

        layout.addLayout(action_layout)

    def _setup_connections(self):
        """🔗 Setup signal connections."""
        self.event_list.edit_requested.connect(self._edit_event)
        self.event_list.delete_requested.connect(self._delete_event)

    def set_event_manager(self, event_manager: EventManager):
        """📝 Set event manager."""
        self.event_manager = event_manager

    def show_events_for_date(self, selected_date: date):
        """📅 Show events for selected date."""
        self.current_date = selected_date

        # Update date label with localized formatting
        try:
            # Use manual localization for consistent translation
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

            weekday = weekday_names[selected_date.weekday()]
            month = month_names[selected_date.month - 1]

            # Use centralized date formatting for the numeric part
            formatted_date = format_date_for_locale(selected_date)
            date_str = f"{weekday}, {formatted_date} ({month})"
        except Exception as e:
            # Ultimate fallback
            logger.warning(f"⚠️ Failed to format date: {e}")
            date_str = format_date_for_locale(selected_date)

        self.date_label.setText(f"📅 {date_str}")

        # Enable add button
        self.add_event_btn.setEnabled(True)

        # Load events
        if self.event_manager:
            try:
                events = self.event_manager.get_events_for_date(selected_date)
                self.event_list.set_events(events)

                logger.debug(f"📅 Loaded {len(events)} events for {selected_date}")

            except Exception as e:
                logger.error(f"❌ Failed to load events for {selected_date}: {e}")
                self.event_list.set_events([])
        else:
            self.event_list.set_events([])

    def _add_event(self):
        """➕ Add new event."""
        # Use current date or today if no date selected
        selected_date = self.current_date or date.today()

        if not self.event_manager:
            # Show a proper error dialog for testing purposes
            QMessageBox.warning(
                self,
                f"❌ {_('error_no_event_manager', default='No Event Manager')}",
                _(
                    "error_event_manager_unavailable",
                    default="Event manager is not available. Please check the application setup.",  # noqa: E501
                ),
            )
            return

        try:
            # Open event dialog
            dialog = EventDialog(selected_date=selected_date, parent=self)
            dialog.event_saved.connect(self._on_event_saved)

            # Refresh UI text to ensure correct language
            if hasattr(dialog, "refresh_ui_text"):
                dialog.refresh_ui_text()

            dialog.exec()

        except Exception as e:
            logger.error(f"❌ Failed to open add event dialog: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_title', default='Error')}",
                f"Failed to open event dialog:\n{str(e)}",
            )

    def _edit_event(self, event: Event):
        """✏️ Edit existing event."""
        try:
            # Check if this is a generated recurring event occurrence
            if event.id is None and event.recurrence_master_id:
                # This is a generated occurrence - edit the master event instead
                if self.event_manager:
                    master_event = self.event_manager.get_event(
                        event.recurrence_master_id
                    )
                    if master_event:
                        event_to_edit = master_event
                        QMessageBox.information(
                            self,
                            f"🔄 {_('events.edit_recurring_event', default='Edit Recurring Event')}",  # noqa: E501
                            _(
                                "events.editing_master_event",
                                default="You are editing the master recurring event. Changes will affect all occurrences.",  # noqa: E501
                            ),
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            f"❌ {_('error_title', default='Error')}",
                            _(
                                "events.master_event_not_found",
                                default="Master event not found.",
                            ),
                        )
                        return
                else:
                    return
            else:
                # Regular event
                event_to_edit = event

            # Open event dialog for editing
            dialog = EventDialog(event_data=event_to_edit, parent=self)
            dialog.event_saved.connect(self._on_event_updated)

            # Refresh UI text to ensure correct language
            if hasattr(dialog, "refresh_ui_text"):
                dialog.refresh_ui_text()

            dialog.exec()

        except Exception as e:
            logger.error(f"❌ Failed to open edit event dialog: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_title', default='Error')}",
                f"Failed to open event dialog:\n{str(e)}",
            )

    def _delete_event(self, event: Event):
        """🗑️ Delete event."""
        if not self.event_manager:
            return

        # Check if this is a generated recurring event occurrence
        if event.id is None and event.recurrence_master_id:
            # This is a generated occurrence - offer options using custom dialog
            dialog = CustomDeleteDialog(
                title=f"{UI_EMOJIS['delete_event']} {_('events.delete_recurring_occurrence', default='Delete Recurring Event')}",  # noqa: E501
                message=f"🔄 {_('confirm_delete_recurring_message', default='This is a recurring event occurrence. What would you like to do?')}",  # noqa: E501
                event_title=event.get_display_title(),
                parent=self,
            )

            dialog.exec()
            result = dialog.get_result()

            if result == "delete_this":
                # Add this date as an exception to the master event
                try:
                    if self.event_manager.add_exception_date(
                        event.recurrence_master_id, event.start_date
                    ):
                        self.refresh_events()  # Refresh to hide this occurrence
                        self.event_deleted.emit(event)
                        QMessageBox.information(
                            self,
                            f"✅ {_('info_title', default='Information')}",
                            _(
                                "events.exception_added_successfully",
                                default="This occurrence has been successfully excluded from the recurring event series.",  # noqa: E501
                            ),
                        )
                        logger.debug(
                            f"✅ Added exception date {event.start_date} to recurring event: {event.get_display_title()}"  # noqa: E501
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            f"❌ {_('error_title', default='Error')}",
                            _(
                                "events.exception_add_failed",
                                default="Failed to exclude this occurrence. Please try again.",  # noqa: E501
                            ),
                        )
                except Exception as e:
                    logger.error(f"❌ Failed to add exception date: {e}")
                    QMessageBox.critical(
                        self,
                        f"❌ {_('error_title', default='Error')}",
                        f"An error occurred while excluding this occurrence:\n{str(e)}",
                    )
            elif result == "delete_all":
                # Delete the master event
                try:
                    if self.event_manager.delete_event(event.recurrence_master_id):
                        self.refresh_events()  # Refresh to remove all occurrences
                        self.event_deleted.emit(event)
                        logger.debug(
                            f"🗑️ Deleted recurring event series: {event.get_display_title()}"  # noqa: E501
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            f"❌ {_('error_delete_failed', default='Delete Failed')}",
                            _(
                                "error_failed_to_delete_event",
                                default="Failed to delete the event. Please try again.",
                            ),
                        )
                except Exception as e:
                    logger.error(f"❌ Failed to delete recurring event: {e}")
                    QMessageBox.critical(
                        self,
                        f"❌ {_('error_title', default='Error')}",
                        f"An error occurred while deleting the event:\n{str(e)}",
                    )
            # If cancel was clicked, do nothing
            return

        # Regular event deletion
        # Confirm deletion
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(
            f"{UI_EMOJIS['delete_event']} {_('events.delete_event', default='Delete Event')}"  # noqa: E501
        )
        msg_box.setText(
            f"🗑️ {_('confirm_delete_event_message', default='Are you sure you want to delete this event?')}\n\n{event.get_display_title()}"  # noqa: E501
        )
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Create custom buttons
        yes_button = msg_box.addButton(
            _("Yes", default="Yes"), QMessageBox.ButtonRole.YesRole
        )
        no_button = msg_box.addButton(
            _("No", default="No"), QMessageBox.ButtonRole.NoRole
        )
        msg_box.setDefaultButton(no_button)

        msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == yes_button:
            try:
                if event.id and self.event_manager.delete_event(event.id):
                    self.event_list.remove_event(event)
                    self.event_deleted.emit(event)

                    logger.debug(f"🗑️ Deleted event: {event.get_display_title()}")
                else:
                    QMessageBox.warning(
                        self,
                        f"❌ {_('error_delete_failed', default='Delete Failed')}",
                        _(
                            "error_failed_to_delete_event",
                            default="Failed to delete the event. Please try again.",
                        ),
                    )

            except Exception as e:
                logger.error(f"❌ Failed to delete event: {e}")
                QMessageBox.critical(
                    self,
                    f"❌ {_('error_title', default='Error')}",
                    f"An error occurred while deleting the event:\n{str(e)}",
                )

    def _import_events(self):
        """📥 Import events from file."""
        if not self.event_manager:
            QMessageBox.information(
                self,
                f"{UI_EMOJIS['import']} {_('info_import_events', default='Import Events')}",  # noqa: E501
                _(
                    "info_import_placeholder",
                    default="Import functionality will be implemented in the event panel.",  # noqa: E501
                ),
            )
            return

        try:
            # Open file dialog
            file_path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                f"{UI_EMOJIS['import']} Import Events",
                "",
                "CSV Files (*.csv);;ICS Files (*.ics);;All Files (*)",
            )

            if file_path:
                if file_path.lower().endswith(".csv"):
                    self._import_csv_events(file_path)
                elif file_path.lower().endswith(".ics"):
                    QMessageBox.information(
                        self,
                        f"{UI_EMOJIS['import']} ICS Import",
                        "📅 ICS import will be implemented in a future update.",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "⚠️ Unsupported Format",
                        "Please select a CSV or ICS file.",
                    )

        except Exception as e:
            logger.error(f"❌ Import error: {e}")
            QMessageBox.critical(
                self, "❌ Import Error", f"Failed to import events:\n{str(e)}"
            )

    def _import_csv_events(self, file_path: str):
        """📥 Import events from CSV file."""
        try:
            import csv
            from datetime import datetime

            imported_count = 0
            errors = []

            with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
                # Try to detect if file has headers
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                has_header = sniffer.has_header(sample)

                reader = csv.reader(csvfile)

                # Skip header if present
                if has_header:
                    next(reader)

                for row_num, row in enumerate(reader, start=1):
                    try:
                        if len(row) < 4:
                            errors.append(
                                f"Row {row_num}: Not enough columns (need at least 4)"
                            )
                            continue

                        # Expected format: Title, Description, Category, Date, Start Time, End Time, All Day  # noqa: E501
                        title = row[0].strip()
                        description = row[1].strip() if len(row) > 1 else ""
                        category = row[2].strip() if len(row) > 2 else "default"
                        date_str = row[3].strip()
                        start_time_str = row[4].strip() if len(row) > 4 else ""
                        end_time_str = row[5].strip() if len(row) > 5 else ""
                        is_all_day = (
                            row[6].strip().lower() in ["true", "1", "yes"]
                            if len(row) > 6
                            else False
                        )

                        if not title:
                            errors.append(f"Row {row_num}: Title is required")
                            continue

                        # Parse date - try multiple formats
                        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]

                        event_date = None
                        for fmt in date_formats:
                            try:
                                event_date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue

                        if not event_date:
                            errors.append(
                                f"Row {row_num}: Invalid date format: {date_str}"
                            )
                            continue

                        # Parse times if provided
                        start_time = None
                        end_time = None

                        if start_time_str and not is_all_day:
                            time_formats = [
                                "%H:%M",
                                "%H:%M:%S",
                                "%I:%M %p",
                                "%I:%M:%S %p",
                            ]
                            for fmt in time_formats:
                                try:
                                    start_time = datetime.strptime(
                                        start_time_str, fmt
                                    ).time()
                                    break
                                except ValueError:
                                    continue

                        if end_time_str and not is_all_day:
                            time_formats = [
                                "%H:%M",
                                "%H:%M:%S",
                                "%I:%M %p",
                                "%I:%M:%S %p",
                            ]
                            for fmt in time_formats:
                                try:
                                    end_time = datetime.strptime(
                                        end_time_str, fmt
                                    ).time()
                                    break
                                except ValueError:
                                    continue

                        # Check for duplicate events before creating
                        if self.event_manager:
                            # Get existing events for this date
                            existing_events = self.event_manager.get_events_for_date(
                                event_date
                            )

                            # Check if an event with the same title, date, and time already exists  # noqa: E501
                            is_duplicate = False
                            for existing_event in existing_events:
                                if (
                                    existing_event.title == title
                                    and existing_event.start_date == event_date
                                    and existing_event.start_time == start_time
                                    and existing_event.end_time == end_time
                                    and existing_event.is_all_day == is_all_day
                                ):
                                    is_duplicate = True
                                    break

                            if is_duplicate:
                                errors.append(
                                    f"Row {row_num}: Duplicate event skipped - '{title}' on {event_date}"  # noqa: E501
                                )
                                continue

                            # Create event
                            event = Event(
                                title=title,
                                description=description,
                                category=category,
                                start_date=event_date,
                                end_date=event_date,  # Single day event
                                start_time=start_time,
                                end_time=end_time,
                                is_all_day=is_all_day,
                            )

                            # Save event using event manager
                            saved_event = self.event_manager.create_event(event)
                            if saved_event:
                                imported_count += 1
                            else:
                                errors.append(f"Row {row_num}: Failed to save event")
                        else:
                            errors.append(f"Row {row_num}: Event manager not available")

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

            # Show results
            message = "📥 Import completed!\n\n"
            message += f"✅ Successfully imported: {imported_count} events\n"

            if errors:
                message += f"⚠️ Errors encountered: {len(errors)}\n\n"
                if len(errors) <= 5:
                    message += "Errors:\n" + "\n".join(errors)
                else:
                    message += "First 5 errors:\n" + "\n".join(errors[:5])
                    message += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.information(
                self, f"{UI_EMOJIS['import']} Import Results", message
            )

            # Refresh the event list
            if imported_count > 0:
                self.refresh_events()
                # Emit signal to refresh calendar
                if hasattr(self, "event_created"):
                    self.event_created.emit(Event())  # Dummy event to trigger refresh

        except Exception as e:
            logger.error(f"❌ CSV import error: {e}")
            QMessageBox.critical(
                self, "❌ CSV Import Error", f"Failed to import CSV events:\n{str(e)}"
            )

    def _export_events(self):
        """📤 Export events to file."""
        if not self.event_manager:
            QMessageBox.information(
                self,
                f"{UI_EMOJIS['export']} {_('info_export_events', default='Export Events')}",  # noqa: E501
                _(
                    "info_export_placeholder",
                    default="Export functionality will be implemented in the event panel.",  # noqa: E501
                ),
            )
            return

        try:
            # Open file dialog
            file_path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                f"{UI_EMOJIS['export']} Export Events",
                "calendar_events.csv",
                "CSV Files (*.csv);;All Files (*)",
            )

            if file_path:
                # Get all events
                from datetime import date, timedelta

                start_date = date.today() - timedelta(days=365)  # Past year
                end_date = date.today() + timedelta(days=365)  # Next year

                all_events = []
                current_date = start_date
                while current_date <= end_date:
                    events = self.event_manager.get_events_for_date(current_date)
                    all_events.extend(events)
                    current_date += timedelta(days=1)

                # Remove duplicates
                unique_events = []
                seen_ids = set()
                for event in all_events:
                    if event.id not in seen_ids:
                        unique_events.append(event)
                        if event.id:
                            seen_ids.add(event.id)

                # Export to CSV
                import csv

                with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)

                    # Write header
                    writer.writerow(
                        [
                            "Title",
                            "Description",
                            "Category",
                            "Date",
                            "Start Time",
                            "End Time",
                            "All Day",
                        ]
                    )

                    # Write events
                    for event in unique_events:
                        writer.writerow(
                            [
                                event.title or "",
                                event.description or "",
                                event.category or "",
                                (
                                    event.start_date.strftime("%Y-%m-%d")
                                    if event.start_date
                                    else ""
                                ),
                                (
                                    event.start_time.strftime("%H:%M")
                                    if event.start_time
                                    else ""
                                ),
                                (
                                    event.end_time.strftime("%H:%M")
                                    if event.end_time
                                    else ""
                                ),
                                "Yes" if event.is_all_day else "No",
                            ]
                        )

                QMessageBox.information(
                    self,
                    f"{UI_EMOJIS['export']} Export Complete",
                    f"📤 Successfully exported {len(unique_events)} events to:\n{file_path}",  # noqa: E501
                )

        except Exception as e:
            logger.error(f"❌ Export error: {e}")
            QMessageBox.critical(
                self, "❌ Export Error", f"Failed to export events:\n{str(e)}"
            )

    def refresh_events(self):
        """🔄 Refresh events for current date."""
        if self.current_date:
            self.show_events_for_date(self.current_date)

    def get_current_date(self) -> Optional[date]:
        """📅 Get currently selected date."""
        return self.current_date

    def _on_event_saved(self, event: Event):
        """📝 Handle new event saved."""
        if not self.event_manager:
            return

        try:
            # Save the event
            saved_event = self.event_manager.create_event(event)
            if saved_event:
                # Refresh the event list
                self.refresh_events()
                self.event_created.emit(saved_event)
                logger.debug(f"✅ Created event: {event.get_display_title()}")
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Save Failed",
                    "Failed to save the event. Please try again.",
                )

        except Exception as e:
            logger.error(f"❌ Failed to save new event: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_title', default='Error')}",
                f"An error occurred while saving the event:\n{str(e)}",
            )

    def _on_event_updated(self, event: Event):
        """📝 Handle event updated."""
        if not self.event_manager:
            return

        try:
            # Update the event
            if event.id and self.event_manager.update_event(event):
                # Refresh the event list
                self.refresh_events()
                self.event_updated.emit(event)
                logger.debug(f"✅ Updated event: {event.get_display_title()}")
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Update Failed",
                    "Failed to update the event. Please try again.",
                )

        except Exception as e:
            logger.error(f"❌ Failed to update event: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_title', default='Error')}",
                f"An error occurred while updating the event:\n{str(e)}",
            )

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update button texts
            self.add_event_btn.setText(
                f"{UI_EMOJIS['add_event']} {_('toolbar.add_event', default='Add Event')}"  # noqa: E501
            )
            self.import_btn.setText(
                f"{UI_EMOJIS['import']} {_('import_export.import', default='Import')}"
            )
            self.export_btn.setText(
                f"{UI_EMOJIS['export']} {_('import_export.export', default='Export')}"
            )

            # Update tooltips
            self.import_btn.setToolTip(
                _("import_export.import_events", default="Import events from file")
            )
            self.export_btn.setToolTip(
                _("import_export.export_events", default="Export events to file")
            )

            # Update date label if no date is selected
            if not self.current_date:
                self.date_label.setText(
                    f"📅 {_('calendar.today', default='Select a date')}"
                )
            else:
                # Refresh the date label with localized date format
                self.show_events_for_date(self.current_date)

            # Update event item tooltips
            for event_widget in self.event_list.event_widgets:
                if hasattr(event_widget, "edit_btn"):
                    event_widget.edit_btn.setToolTip(
                        _("events.edit_event", default="Edit event")
                    )
                if hasattr(event_widget, "delete_btn"):
                    event_widget.delete_btn.setToolTip(
                        _("events.delete_event", default="Delete event")
                    )

            # Force refresh event list display to update all text
            self.event_list._update_display()

            # Force button updates
            self.add_event_btn.update()
            self.import_btn.update()
            self.export_btn.update()
            self.date_label.update()

            logger.debug("🔄 Event panel UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh event panel UI text: {e}")
