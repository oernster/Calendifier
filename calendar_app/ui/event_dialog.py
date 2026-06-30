"""
📝 Event Dialog for Calendar Application

This module contains the event creation and editing dialog.
"""

import logging
from datetime import date, time
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QCheckBox,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import Qt, QDate, QTime, Signal, QTimer

from calendar_app.data.models import Event
from calendar_app.localization import get_i18n_manager
from calendar_app.localization.i18n_manager import convert_numbers
from version import UI_EMOJIS, EVENT_CATEGORY_EMOJIS

logger = logging.getLogger(__name__)


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that gets current locale text."""
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


class EventDialog(QDialog):
    """📝 Event creation and editing dialog."""

    event_saved = Signal(Event)

    def __init__(
        self,
        event_data: Optional[Event] = None,
        selected_date: Optional[date] = None,
        parent=None,
    ):
        """Initialize event dialog."""
        super().__init__(parent)

        self.event_data = event_data
        self.selected_date = selected_date or date.today()
        self.is_editing = event_data is not None

        self._setup_ui()
        self._load_event_data()
        self._refresh_qt_widgets_locale()  # Apply locale immediately

        # Setup timer for continuous calendar conversion
        self._calendar_conversion_timer = QTimer()
        self._calendar_conversion_timer.timeout.connect(self._update_calendar_numbers)
        self._calendar_conversion_timer.start(500)  # Update every 500ms

        logger.debug(
            f"📝 Event dialog initialized "
            f"({'editing' if self.is_editing else 'creating'})"
        )

    def _setup_ui(self):
        """🏗️ Setup event dialog UI."""
        title = (
            f"{UI_EMOJIS['edit_event']} {_('event_dialog_edit_title')}"
            if self.is_editing
            else f"{UI_EMOJIS['add_event']} {_('event_dialog_add_title')}"
        )
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(650, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Use VBoxLayout with HBoxLayout rows instead of QFormLayout
        # to avoid label borders
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title_label = QLabel(f"📝 {_('label_title')}")
        title_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        title_label.setMinimumWidth(100)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(_("placeholder_enter_event_title"))
        title_row.addWidget(title_label)
        title_row.addWidget(self.title_edit)
        form_layout.addLayout(title_row)

        # Category
        category_row = QHBoxLayout()
        category_label = QLabel(f"📂 {_('label_category')}")
        category_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        category_label.setMinimumWidth(100)
        self.category_combo = QComboBox()
        for category, emoji in EVENT_CATEGORY_EMOJIS.items():
            localized_name = _(f"category_{category}")
            self.category_combo.addItem(f"{emoji} {localized_name}", category)
        category_row.addWidget(category_label)
        category_row.addWidget(self.category_combo)
        form_layout.addLayout(category_row)

        # Date
        date_row = QHBoxLayout()
        date_label = QLabel(f"📅 {_('label_date')}")
        date_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        date_label.setMinimumWidth(100)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(
            QDate(
                self.selected_date.year,
                self.selected_date.month,
                self.selected_date.day,
            )
        )
        self.date_edit.setCalendarPopup(True)

        # Connect signals for continuous numeral conversion
        self.date_edit.dateChanged.connect(self._on_date_changed)
        date_row.addWidget(date_label)
        date_row.addWidget(self.date_edit)
        form_layout.addLayout(date_row)

        # All day checkbox
        allday_row = QHBoxLayout()
        allday_spacer = QLabel("")
        allday_spacer.setStyleSheet("border: none; padding: 0; margin: 0;")
        allday_spacer.setMinimumWidth(100)
        self.all_day_check = QCheckBox(_("label_all_day_event"))
        self.all_day_check.toggled.connect(self._on_all_day_toggled)
        allday_row.addWidget(allday_spacer)
        allday_row.addWidget(self.all_day_check)
        form_layout.addLayout(allday_row)

        # Start time
        start_time_row = QHBoxLayout()
        start_time_label = QLabel(f"🕐 {_('label_start_time')}")
        start_time_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        start_time_label.setMinimumWidth(100)
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(9, 0))  # Default 9:00 AM

        # Connect signals for continuous numeral conversion
        self.start_time_edit.timeChanged.connect(
            lambda: self._apply_numeral_conversion_to_time_widget(self.start_time_edit)
        )
        start_time_row.addWidget(start_time_label)
        start_time_row.addWidget(self.start_time_edit)
        form_layout.addLayout(start_time_row)

        # End time
        end_time_row = QHBoxLayout()
        end_time_label = QLabel(f"🕐 {_('label_end_time')}")
        end_time_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        end_time_label.setMinimumWidth(100)
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(10, 0))  # Default 10:00 AM

        # Connect signals for continuous numeral conversion
        self.end_time_edit.timeChanged.connect(
            lambda: self._apply_numeral_conversion_to_time_widget(self.end_time_edit)
        )
        end_time_row.addWidget(end_time_label)
        end_time_row.addWidget(self.end_time_edit)
        form_layout.addLayout(end_time_row)

        # Description
        desc_row = QHBoxLayout()
        desc_label = QLabel(f"📄 {_('label_description')}")
        desc_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        desc_label.setMinimumWidth(100)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            _("placeholder_enter_event_description")
        )
        self.description_edit.setMaximumHeight(100)
        desc_row.addWidget(desc_label)
        desc_row.addWidget(self.description_edit)
        form_layout.addLayout(desc_row)

        # Recurring event section
        recurring_row = QHBoxLayout()
        recurring_label = QLabel(
            f"🔄 {_('recurring.title', default='Recurring Event')}"
        )
        recurring_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        recurring_label.setMinimumWidth(100)

        # Recurring checkbox and button container
        recurring_container = QHBoxLayout()

        # Add stretch to push checkbox and button to the right
        recurring_container.addStretch()

        self.recurring_check = QCheckBox(
            _("recurring.enable", default="Make Recurring")
        )
        self.recurring_check.toggled.connect(self._on_recurring_toggled)
        recurring_container.addWidget(self.recurring_check)

        # RRULE pattern button (directly after checkbox)
        self.rrule_button = QPushButton(
            _("recurring.pattern", default="Repeat Pattern")
        )
        self.rrule_button.setEnabled(False)
        self.rrule_button.setFixedWidth(150)  # Set fixed width to ensure text fits

        # Apply custom styling for enabled/disabled states
        self._apply_repeat_button_styling()

        self.rrule_button.clicked.connect(self._open_rrule_dialog)
        recurring_container.addWidget(self.rrule_button)

        # Pattern description label
        self.pattern_description = QLabel(
            _("recurring.description.custom", default="Custom repeat pattern")
        )
        self.pattern_description.setStyleSheet("color: #666; font-style: italic;")
        self.pattern_description.setVisible(False)
        recurring_container.addWidget(self.pattern_description)

        recurring_widget = QWidget()
        recurring_widget.setLayout(recurring_container)

        recurring_row.addWidget(recurring_label)
        recurring_row.addWidget(
            recurring_widget, 1
        )  # Give stretch factor of 1 to expand
        form_layout.addLayout(recurring_row)

        # Store RRULE data
        self.current_rrule = None

        layout.addWidget(form_widget)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_event)
        button_box.rejected.connect(self.reject)

        # Change button texts
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText(f"{UI_EMOJIS['success']} {_('button_save_event')}")

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText(_("button_cancel"))

        layout.addWidget(button_box)

        # Set focus to title
        self.title_edit.setFocus()

    def _apply_repeat_button_styling(self):
        """Apply custom styling to the repeat pattern button"""
        try:
            # Custom stylesheet for the repeat pattern button
            button_style = """
            QPushButton {
                background-color: #0078d4;  /* Blue background when enabled */
                color: white;
                border: 1px solid #005a9e;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;  /* Lighter blue on hover when enabled */
                border-color: #004578;
            }
            QPushButton:pressed {
                background-color: #005a9e;  /* Darker blue when pressed */
                border-color: #004578;
            }
            QPushButton:disabled {
                background-color: #004578;  /* Darker blue when disabled */
                color: #b3d9ff;             /* Light blue text when disabled */
                border-color: #003d66;
            }
            """

            self.rrule_button.setStyleSheet(button_style)
            logger.debug("🎨 Applied custom styling to repeat pattern button")

        except Exception as e:
            logger.warning(f"⚠️ Failed to apply repeat button styling: {e}")

    def _load_event_data(self):
        """📥 Load event data if editing."""
        if not self.event_data:
            return

        try:
            # Load basic info
            self.title_edit.setText(self.event_data.title or "")
            self.description_edit.setPlainText(self.event_data.description or "")

            # Load category
            category_index = self.category_combo.findData(self.event_data.category)
            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)

            # Load date
            if self.event_data.start_date:
                event_date = self.event_data.start_date
                self.date_edit.setDate(
                    QDate(event_date.year, event_date.month, event_date.day)
                )

            # Load time info
            self.all_day_check.setChecked(self.event_data.is_all_day)

            if not self.event_data.is_all_day:
                if self.event_data.start_time:
                    start_time = self.event_data.start_time
                    self.start_time_edit.setTime(
                        QTime(start_time.hour, start_time.minute)
                    )
                if self.event_data.end_time:
                    end_time = self.event_data.end_time
                    self.end_time_edit.setTime(QTime(end_time.hour, end_time.minute))

            self._on_all_day_toggled(self.event_data.is_all_day)

            # Load recurring info
            self.recurring_check.setChecked(self.event_data.is_recurring)
            if self.event_data.rrule:
                self.current_rrule = self.event_data.rrule
                self._update_pattern_description()
            self._on_recurring_toggled(self.event_data.is_recurring)

        except Exception as e:
            logger.error(f"❌ Failed to load event data: {e}")

    def _on_all_day_toggled(self, checked: bool):
        """🔄 Handle all day checkbox toggle."""
        self.start_time_edit.setEnabled(not checked)
        self.end_time_edit.setEnabled(not checked)

    def _on_recurring_toggled(self, checked: bool):
        """🔄 Handle recurring checkbox toggle."""
        self.rrule_button.setEnabled(checked)
        self.pattern_description.setVisible(checked and self.current_rrule is not None)

        # Refresh button styling after enable/disable
        self._apply_repeat_button_styling()

        if not checked:
            self.current_rrule = None
            self.pattern_description.setText("")

    def _open_rrule_dialog(self):
        """🔄 Open RRULE pattern builder dialog."""
        try:
            # Get current date for RRULE dialog
            qdate = self.date_edit.date()
            start_date = date(qdate.year(), qdate.month(), qdate.day())

            # Show RRULE dialog
            try:
                from calendar_app.ui.rrule_dialog_pyside import show_rrule_dialog

                i18n_manager = get_i18n_manager()

                result_rrule = show_rrule_dialog(
                    parent=self,
                    i18n=i18n_manager,
                    initial_rrule=self.current_rrule,
                    start_date=start_date,
                )
            except ImportError:
                # Fallback: Simple text input for RRULE
                from PySide6.QtWidgets import QInputDialog

                result_rrule, ok = QInputDialog.getText(
                    self,
                    _("recurring.pattern", default="Repeat Pattern"),
                    "Enter RRULE pattern:",
                    text=self.current_rrule or "FREQ=WEEKLY",
                )
                if not ok:
                    result_rrule = None

            if result_rrule:
                self.current_rrule = result_rrule
                self._update_pattern_description()
                self.pattern_description.setVisible(True)

        except Exception as e:
            logger.error(f"❌ Failed to open RRULE dialog: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_title', default='Error')}",
                f"{_('recurring.error.invalid_rrule', default='Invalid recurrence pattern')}"  # noqa: E501
                f"\n{str(e)}",
            )

    def _update_pattern_description(self):
        """🔄 Update pattern description from RRULE."""
        if not self.current_rrule:
            self.pattern_description.setText("")
            return

        try:
            from calendar_app.core.rrule_parser import RRuleParser

            parser = RRuleParser()
            i18n_manager = get_i18n_manager()

            # Parse RRULE and get description
            components = parser.parse_rrule(self.current_rrule)
            description = parser.get_human_readable_description(
                components, i18n_manager
            )

            self.pattern_description.setText(description)

        except Exception as e:
            logger.warning(f"⚠️ Failed to update pattern description: {e}")
            self.pattern_description.setText(
                _("recurring.description.custom", default="Custom repeat pattern")
            )

    def _save_event(self):
        """💾 Save event data."""
        try:
            # Validate title
            title = self.title_edit.text().strip()
            if not title:
                QMessageBox.warning(
                    self,
                    f"⚠️ {_('error_validation_error')}",
                    _("validation_title_required"),
                )
                self.title_edit.setFocus()
                return

            # Get form data
            category = self.category_combo.currentData() or "default"
            description = self.description_edit.toPlainText().strip()

            # Convert QDate to Python date
            qdate = self.date_edit.date()
            event_date = date(qdate.year(), qdate.month(), qdate.day())

            is_all_day = self.all_day_check.isChecked()

            start_time = None
            end_time = None

            if not is_all_day:
                # Convert QTime to Python time
                qstart_time = self.start_time_edit.time()
                start_time = time(qstart_time.hour(), qstart_time.minute())

                qend_time = self.end_time_edit.time()
                end_time = time(qend_time.hour(), qend_time.minute())

                # Validate times
                if end_time <= start_time:
                    QMessageBox.warning(
                        self,
                        f"⚠️ {_('error_validation_error')}",
                        _("validation_end_time_after_start"),
                    )
                    self.end_time_edit.setFocus()
                    return

            # Get recurring data
            is_recurring = self.recurring_check.isChecked()
            rrule = self.current_rrule if is_recurring else None

            # Create or update event
            if self.is_editing and self.event_data:
                # Update existing event
                self.event_data.title = title
                self.event_data.description = description
                self.event_data.category = category
                self.event_data.start_date = event_date
                self.event_data.is_all_day = is_all_day
                self.event_data.start_time = start_time
                self.event_data.end_time = end_time
                self.event_data.is_recurring = is_recurring
                self.event_data.rrule = rrule

                saved_event = self.event_data
            else:
                # Create new event
                saved_event = Event(
                    title=title,
                    description=description,
                    category=category,
                    start_date=event_date,
                    is_all_day=is_all_day,
                    start_time=start_time,
                    end_time=end_time,
                    is_recurring=is_recurring,
                    rrule=rrule,
                )

            # Emit signal and close
            self.event_saved.emit(saved_event)
            self.accept()

        except Exception as e:
            logger.error(f"❌ Failed to save event: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_save_error')}",
                f"{_('error_failed_to_save_event')}\n{str(e)}",
            )

    def get_event(self) -> Optional[Event]:
        """📝 Get the event (for external access)."""
        return self.event_data

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update window title
            title = (
                f"{UI_EMOJIS['edit_event']} {_('event_dialog_edit_title')}"
                if self.is_editing
                else f"{UI_EMOJIS['add_event']} {_('event_dialog_add_title')}"
            )
            self.setWindowTitle(title)

            # Update all labels
            # Find all labels and update their text
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if text.startswith("📝"):
                    widget.setText(f"📝 {_('label_title')}")
                elif text.startswith("📂"):
                    widget.setText(f"📂 {_('label_category')}")
                elif text.startswith("📅"):
                    widget.setText(f"📅 {_('label_date')}")
                elif text.startswith("🕐") and "start" in text.lower():
                    widget.setText(f"🕐 {_('label_start_time')}")
                elif text.startswith("🕐") and "end" in text.lower():
                    widget.setText(f"🕐 {_('label_end_time')}")
                elif text.startswith("📄"):
                    widget.setText(f"📄 {_('label_description')}")
                elif text.startswith("🔄"):
                    widget.setText(
                        f"🔄 {_('recurring.title', default='Recurring Event')}"
                    )

            # Update placeholders
            if hasattr(self, "title_edit"):
                self.title_edit.setPlaceholderText(_("placeholder_enter_event_title"))
            if hasattr(self, "description_edit"):
                self.description_edit.setPlaceholderText(
                    _("placeholder_enter_event_description")
                )

            # Update checkbox text
            if hasattr(self, "all_day_check"):
                self.all_day_check.setText(_("label_all_day_event"))
            if hasattr(self, "recurring_check"):
                self.recurring_check.setText(
                    _("recurring.enable", default="Make Recurring")
                )

            # Update recurring button text
            if hasattr(self, "rrule_button"):
                self.rrule_button.setText(
                    _("recurring.pattern", default="Repeat Pattern")
                )
                # Reapply custom styling after text update
                self._apply_repeat_button_styling()

            # Update category combo box items
            if hasattr(self, "category_combo"):
                current_data = self.category_combo.currentData()
                self.category_combo.clear()
                for category, emoji in EVENT_CATEGORY_EMOJIS.items():
                    localized_name = _(f"category_{category}")
                    self.category_combo.addItem(f"{emoji} {localized_name}", category)

                # Restore selection
                if current_data:
                    index = self.category_combo.findData(current_data)
                    if index >= 0:
                        self.category_combo.setCurrentIndex(index)

            # Update Qt widgets locale (QDateEdit, QTimeEdit)
            self._refresh_qt_widgets_locale()

            # Trigger delayed numeral conversion to ensure Qt widgets
            # are fully initialized
            QTimer.singleShot(100, self._delayed_numeral_conversion)

            # Update button texts
            button_box = self.findChild(QDialogButtonBox)
            if button_box:
                ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
                if ok_button:
                    ok_button.setText(
                        f"{UI_EMOJIS['success']} {_('button_save_event')}"
                    )

                cancel_button = button_box.button(
                    QDialogButtonBox.StandardButton.Cancel
                )
                if cancel_button:
                    cancel_button.setText(_("button_cancel"))

            logger.debug("🔄 Event dialog UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh event dialog UI text: {e}")

    def _refresh_qt_widgets_locale(self):
        """🌍 Refresh Qt widgets to use current locale."""
        try:
            from PySide6.QtCore import QLocale

            # Get current locale from I18n manager
            i18n_manager = get_i18n_manager()
            current_locale = i18n_manager.current_locale

            # Map ALL supported locale codes to Qt locale codes
            qt_locale_mapping = {
                # Core English locales
                "en_US": QLocale(
                    QLocale.Language.English, QLocale.Country.UnitedStates
                ),
                "en_GB": QLocale(
                    QLocale.Language.English, QLocale.Country.UnitedKingdom
                ),
                # French locales
                "fr_CA": QLocale(QLocale.Language.French, QLocale.Country.Canada),
                "fr_FR": QLocale(QLocale.Language.French, QLocale.Country.France),
                # Catalan locales
                "ca_ES": QLocale(QLocale.Language.Catalan, QLocale.Country.Spain),
                # Major European languages
                "es_ES": QLocale(QLocale.Language.Spanish, QLocale.Country.Spain),
                "de_DE": QLocale(QLocale.Language.German, QLocale.Country.Germany),
                "it_IT": QLocale(QLocale.Language.Italian, QLocale.Country.Italy),
                "pt_BR": QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil),
                "pt_PT": QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal),
                "ru_RU": QLocale(QLocale.Language.Russian, QLocale.Country.Russia),
                "nl_NL": QLocale(QLocale.Language.Dutch, QLocale.Country.Netherlands),
                "pl_PL": QLocale(QLocale.Language.Polish, QLocale.Country.Poland),
                # Nordic languages
                "sv_SE": QLocale(QLocale.Language.Swedish, QLocale.Country.Sweden),
                "nb_NO": QLocale(
                    QLocale.Language.NorwegianBokmal, QLocale.Country.Norway
                ),
                "da_DK": QLocale(QLocale.Language.Danish, QLocale.Country.Denmark),
                "fi_FI": QLocale(QLocale.Language.Finnish, QLocale.Country.Finland),
                # Central/Eastern European languages
                "cs_CZ": QLocale(QLocale.Language.Czech, QLocale.Country.CzechRepublic),
                "tr_TR": QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey),
                "uk_UA": QLocale(QLocale.Language.Ukrainian, QLocale.Country.Ukraine),
                "el_GR": QLocale(QLocale.Language.Greek, QLocale.Country.Greece),
                # Asian languages
                "zh_CN": QLocale(QLocale.Language.Chinese, QLocale.Country.China),
                "zh_TW": QLocale(QLocale.Language.Chinese, QLocale.Country.Taiwan),
                "ja_JP": QLocale(QLocale.Language.Japanese, QLocale.Country.Japan),
                "ko_KR": QLocale(QLocale.Language.Korean, QLocale.Country.SouthKorea),
                "hi_IN": QLocale(QLocale.Language.Hindi, QLocale.Country.India),
                "ar_SA": QLocale(QLocale.Language.Arabic, QLocale.Country.SaudiArabia),
                # Southeast Asian languages
                "id_ID": QLocale(
                    QLocale.Language.Indonesian, QLocale.Country.Indonesia
                ),
                "vi_VN": QLocale(QLocale.Language.Vietnamese, QLocale.Country.Vietnam),
                "th_TH": QLocale(QLocale.Language.Thai, QLocale.Country.Thailand),
                # Middle Eastern languages
                "he_IL": QLocale(QLocale.Language.Hebrew, QLocale.Country.Israel),
                # Additional European languages
                "ro_RO": QLocale(QLocale.Language.Romanian, QLocale.Country.Romania),
                "hu_HU": QLocale(QLocale.Language.Hungarian, QLocale.Country.Hungary),
                "hr_HR": QLocale(QLocale.Language.Croatian, QLocale.Country.Croatia),
                "bg_BG": QLocale(QLocale.Language.Bulgarian, QLocale.Country.Bulgaria),
                "sk_SK": QLocale(QLocale.Language.Slovak, QLocale.Country.Slovakia),
                "sl_SI": QLocale(QLocale.Language.Slovenian, QLocale.Country.Slovenia),
                "et_EE": QLocale(QLocale.Language.Estonian, QLocale.Country.Estonia),
                "lv_LV": QLocale(QLocale.Language.Latvian, QLocale.Country.Latvia),
                "lt_LT": QLocale(
                    QLocale.Language.Lithuanian, QLocale.Country.Lithuania
                ),
            }

            # Special handling for Hindi and Thai - use Arabic locale to
            # get numeral conversion
            if current_locale in ["hi_IN", "th_TH"]:
                # Use Arabic locale for Qt to enable numeral conversion,
                # then convert to target numerals
                qt_locale = QLocale(
                    QLocale.Language.Arabic, QLocale.Country.SaudiArabia
                )
            else:
                qt_locale = qt_locale_mapping.get(
                    current_locale,
                    QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom),
                )

            # Update QDateEdit and QTimeEdit widgets
            if hasattr(self, "date_edit"):
                self.date_edit.setLocale(qt_locale)

                # Set explicit date format based on locale
                if (
                    current_locale.startswith("en_US")
                    or current_locale.startswith("en_CA")
                    or current_locale.startswith("en_PH")
                ):
                    # US format: MM/dd/yyyy
                    self.date_edit.setDisplayFormat("MM/dd/yyyy")
                elif current_locale.startswith(("ja_", "ko_", "zh_")):
                    # East Asian format: yyyy/MM/dd
                    self.date_edit.setDisplayFormat("yyyy/MM/dd")
                else:
                    # Most other locales: dd/MM/yyyy
                    self.date_edit.setDisplayFormat("dd/MM/yyyy")

                # Force refresh the calendar popup
                if self.date_edit.calendarWidget():
                    self.date_edit.calendarWidget().setLocale(qt_locale)
                # Apply numeral conversion for Hindi and Thai (Arabic works natively)
                self._apply_numeral_conversion_to_date_widget()

            if hasattr(self, "start_time_edit"):
                self.start_time_edit.setLocale(qt_locale)
                self._apply_numeral_conversion_to_time_widget(self.start_time_edit)

            if hasattr(self, "end_time_edit"):
                self.end_time_edit.setLocale(qt_locale)
                self._apply_numeral_conversion_to_time_widget(self.end_time_edit)

            logger.debug(
                f"🌍 Updated Qt widgets locale to: {current_locale} "
                f"({qt_locale.name()})"
            )

        except Exception as e:
            logger.warning(f"⚠️ Failed to refresh Qt widgets locale: {e}")

    def _apply_numeral_conversion_to_date_widget(self):
        """Apply numeral conversion to date widget for Hindi and Thai locales."""
        try:
            current_locale = get_i18n_manager().current_locale

            # Only apply conversion for Hindi and Thai (Arabic works natively)
            if current_locale not in ["hi_IN", "th_TH"]:
                return

            # Convert the date display
            if hasattr(self, "date_edit"):
                current_date = self.date_edit.date()
                date_str = current_date.toString(self.date_edit.displayFormat())

                # First convert from Arabic-Indic to Western, then to target numerals
                if current_locale == "hi_IN":
                    # Convert Arabic-Indic to Western first
                    western_date = self._arabic_to_western(date_str)
                    # Then convert Western to Devanagari
                    converted_date = convert_numbers(western_date, "hi_IN")
                elif current_locale == "th_TH":
                    # Convert Arabic-Indic to Western first
                    western_date = self._arabic_to_western(date_str)
                    # Then convert Western to Thai
                    converted_date = convert_numbers(western_date, "th_TH")
                else:
                    converted_date = convert_numbers(date_str)

                if converted_date != date_str:
                    line_edit = self.date_edit.lineEdit()
                    if line_edit:
                        line_edit.blockSignals(True)
                        line_edit.setText(converted_date)
                        line_edit.blockSignals(False)

                # Also convert calendar popup numbers
                calendar_widget = self.date_edit.calendarWidget()
                if calendar_widget:
                    self._convert_calendar_widget_numbers(calendar_widget)

        except Exception as e:
            logger.warning(f"⚠️ Failed to apply numeral conversion to date widget: {e}")

    def _apply_numeral_conversion_to_time_widget(self, time_widget):
        """Apply numeral conversion to time widget for Hindi and Thai locales."""
        try:
            current_locale = get_i18n_manager().current_locale

            # Only apply conversion for Hindi and Thai (Arabic works natively)
            if current_locale not in ["hi_IN", "th_TH"]:
                return

            # Convert the time display
            current_time = time_widget.time()
            time_str = current_time.toString(time_widget.displayFormat())

            # First convert from Arabic-Indic to Western, then to target numerals
            if current_locale == "hi_IN":
                # Convert Arabic-Indic to Western first
                western_time = self._arabic_to_western(time_str)
                # Then convert Western to Devanagari
                converted_time = convert_numbers(western_time, "hi_IN")
            elif current_locale == "th_TH":
                # Convert Arabic-Indic to Western first
                western_time = self._arabic_to_western(time_str)
                # Then convert Western to Thai
                converted_time = convert_numbers(western_time, "th_TH")
            else:
                converted_time = convert_numbers(time_str)

            logger.debug(f"🔢 Converting time: '{time_str}' -> '{converted_time}'")

            if converted_time != time_str:
                line_edit = time_widget.lineEdit()
                if line_edit:
                    line_edit.blockSignals(True)
                    line_edit.setText(converted_time)
                    line_edit.blockSignals(False)
                    logger.debug(f"🔢 Time display updated to: {converted_time}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to apply numeral conversion to time widget: {e}")

    def _convert_calendar_widget_numbers(self, calendar_widget):
        """Convert numbers in calendar widget for Hindi and Thai locales."""
        try:
            current_locale = get_i18n_manager().current_locale

            # Only apply conversion for Hindi and Thai (Arabic works natively)
            if current_locale not in ["hi_IN", "th_TH"]:
                return

            conversion_count = 0
            # Find all QLabel widgets in the calendar and convert their text
            for label in calendar_widget.findChildren(QLabel):
                if label.text() and any(c.isdigit() for c in label.text()):
                    original_text = label.text()

                    # First convert from Arabic-Indic to Western,
                    # then to target numerals
                    if current_locale == "hi_IN":
                        # Convert Arabic-Indic to Western first
                        western_text = self._arabic_to_western(original_text)
                        # Then convert Western to Devanagari
                        converted_text = convert_numbers(western_text, "hi_IN")
                    elif current_locale == "th_TH":
                        # Convert Arabic-Indic to Western first
                        western_text = self._arabic_to_western(original_text)
                        # Then convert Western to Thai
                        converted_text = convert_numbers(western_text, "th_TH")
                    else:
                        converted_text = convert_numbers(original_text)

                    if converted_text != original_text:
                        label.setText(converted_text)
                        conversion_count += 1

            if conversion_count > 0:
                logger.debug(f"🔢 Converted {conversion_count} calendar labels")

        except Exception as e:
            logger.warning(f"⚠️ Failed to convert calendar widget numbers: {e}")

    def _on_date_changed(self):
        """Handle date change to update numeral conversion."""
        self._apply_numeral_conversion_to_date_widget()

    def _update_calendar_numbers(self):
        """Continuously update calendar numbers for Hindi and Thai locales."""
        try:
            current_locale = get_i18n_manager().current_locale

            # Only apply conversion for Hindi and Thai (Arabic works natively)
            if current_locale not in ["hi_IN", "th_TH"]:
                return

            # Update calendar widget if it exists and is visible
            if hasattr(self, "date_edit"):
                calendar_widget = self.date_edit.calendarWidget()
                if calendar_widget and calendar_widget.isVisible():
                    self._convert_calendar_widget_numbers(calendar_widget)

        except Exception as e:
            logger.warning(f"⚠️ Failed to update calendar numbers: {e}")

    def _delayed_numeral_conversion(self):
        """Apply numeral conversion after a delay to ensure widgets are ready."""
        try:
            logger.debug("🔢 Applying delayed numeral conversion")
            self._apply_numeral_conversion_to_date_widget()
            if hasattr(self, "start_time_edit"):
                self._apply_numeral_conversion_to_time_widget(self.start_time_edit)
            if hasattr(self, "end_time_edit"):
                self._apply_numeral_conversion_to_time_widget(self.end_time_edit)
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply delayed numeral conversion: {e}")

    def _arabic_to_western(self, text):
        """Convert Arabic-Indic numerals to Western numerals."""
        arabic_to_western_map = {
            "٠": "0",
            "١": "1",
            "٢": "2",
            "٣": "3",
            "٤": "4",
            "٥": "5",
            "٦": "6",
            "٧": "7",
            "٨": "8",
            "٩": "9",
        }

        result = text
        for arabic, western in arabic_to_western_map.items():
            result = result.replace(arabic, western)

        return result
