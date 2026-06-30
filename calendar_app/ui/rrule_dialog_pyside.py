"""
🔄 RRULE Dialog for PySide6 Desktop Application
Advanced recurring event pattern builder with RFC 5545 RRULE support
"""

import logging
from datetime import date, timedelta
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QListWidget,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QScrollArea,
)

logger = logging.getLogger(__name__)

# Import native numeral widgets
try:
    from .native_widgets import NativeSpinBox, NativeLineEdit

    NATIVE_WIDGETS_AVAILABLE = True
except ImportError:
    logger.warning("Native widgets not available, using standard widgets")
    NATIVE_WIDGETS_AVAILABLE = False
    NativeSpinBox = QSpinBox
    NativeLineEdit = QLineEdit
from PySide6.QtCore import Qt, QDate  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402

from ..core.rrule_parser import RRuleParser  # noqa: E402
from ..core.recurring_event_generator import RecurringEventGenerator  # noqa: E402
from ..localization import get_i18n_manager  # noqa: E402

logger = logging.getLogger(__name__)


class RRuleDialog(QDialog):
    """🔄 Advanced RRULE pattern builder dialog for PySide6"""

    def __init__(
        self,
        parent=None,
        initial_rrule: Optional[str] = None,
        start_date: Optional[date] = None,
    ):
        """Initialize RRULE dialog"""
        super().__init__(parent)

        self.start_date = start_date or date.today()
        self.result_rrule: Optional[str] = None
        self.cancelled = True

        # Initialize RRULE parser and generator
        self.parser = RRuleParser()
        self.generator = RecurringEventGenerator()
        self.i18n = get_i18n_manager()

        # Setup dialog
        self.setWindowTitle(
            self.i18n.get_text("recurring.title", default="Recurring Event")
        )
        self.setModal(True)
        self.resize(800, 750)
        self.setMinimumSize(700, 650)

        # Create UI
        self._create_ui()

        # Load initial RRULE if provided
        if initial_rrule:
            self._load_rrule(initial_rrule)
        else:
            self._set_defaults()

        # Update preview
        self._update_preview()

        # Update native displays after everything is set up
        from PySide6.QtCore import QTimer

        QTimer.singleShot(200, self._update_native_displays)

    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create scroll area for main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create sections
        self._create_frequency_section(main_layout)
        self._create_interval_section(main_layout)
        self._create_weekdays_section(main_layout)
        self._create_monthly_section(main_layout)
        self._create_end_condition_section(main_layout)
        self._create_preview_section(main_layout)

        scroll.setWidget(main_widget)
        layout.addWidget(scroll)

        # Create buttons
        self._create_buttons(layout)

    def _create_frequency_section(self, layout: QVBoxLayout):
        """Create frequency selection section"""
        group = QGroupBox(
            self.i18n.get_text("recurring.form.frequency", default="Frequency")
        )
        group_layout = QHBoxLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(15, 25, 15, 15)

        # Remove stretch for vertical alignment
        # group_layout.addStretch()

        self.frequency_group = QButtonGroup()

        frequencies = [
            ("DAILY", self.i18n.get_text("rrule.frequency.daily", default="Daily")),
            ("WEEKLY", self.i18n.get_text("rrule.frequency.weekly", default="Weekly")),
            (
                "MONTHLY",
                self.i18n.get_text("rrule.frequency.monthly", default="Monthly"),
            ),
            ("YEARLY", self.i18n.get_text("rrule.frequency.yearly", default="Yearly")),
        ]

        for i, (value, text) in enumerate(frequencies):
            radio = QRadioButton(text)
            radio.setProperty("frequency", value)
            self.frequency_group.addButton(radio, i)
            group_layout.addWidget(radio)

            if value == "WEEKLY":
                radio.setChecked(True)

        self.frequency_group.buttonClicked.connect(self._on_frequency_change)
        layout.addWidget(group)

    def _create_interval_section(self, layout: QVBoxLayout):
        """Create interval selection section"""
        group = QGroupBox(
            self.i18n.get_text("recurring.form.interval", default="Interval")
        )
        group_layout = QHBoxLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(15, 25, 15, 15)

        # Remove stretch for vertical alignment
        # group_layout.addStretch()

        group_layout.addWidget(
            QLabel(self.i18n.get_text("rrule.interval.every", default="Every"))
        )

        self.interval_spin = (
            NativeSpinBox(i18n_manager=self.i18n)
            if NATIVE_WIDGETS_AVAILABLE
            else QSpinBox()
        )
        self.interval_spin.setRange(1, 999)
        self.interval_spin.setValue(1)
        if NATIVE_WIDGETS_AVAILABLE and hasattr(self.interval_spin, "setI18nManager"):
            self.interval_spin.setI18nManager(self.i18n)
        self.interval_spin.valueChanged.connect(self._update_preview)
        group_layout.addWidget(self.interval_spin)

        self.interval_label = QLabel(
            self.i18n.get_text("rrule.interval.weeks", default="weeks")
        )
        group_layout.addWidget(self.interval_label)

        # Remove stretch for vertical alignment
        # group_layout.addStretch()
        layout.addWidget(group)

    def _create_weekdays_section(self, layout: QVBoxLayout):
        """Create weekdays selection section"""
        self.weekdays_group = QGroupBox(
            self.i18n.get_text("recurring.form.weekdays", default="Days of Week")
        )
        group_layout = QHBoxLayout(self.weekdays_group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(15, 25, 15, 15)

        # Remove stretch for vertical alignment
        # group_layout.addStretch()

        self.weekday_checks = {}
        weekdays = [
            ("MO", self.i18n.get_text("rrule.weekday.short.mon", default="Mon")),
            ("TU", self.i18n.get_text("rrule.weekday.short.tue", default="Tue")),
            ("WE", self.i18n.get_text("rrule.weekday.short.wed", default="Wed")),
            ("TH", self.i18n.get_text("rrule.weekday.short.thu", default="Thu")),
            ("FR", self.i18n.get_text("rrule.weekday.short.fri", default="Fri")),
            ("SA", self.i18n.get_text("rrule.weekday.short.sat", default="Sat")),
            ("SU", self.i18n.get_text("rrule.weekday.short.sun", default="Sun")),
        ]

        for day, text in weekdays:
            check = QCheckBox(text)
            check.toggled.connect(self._update_preview)
            self.weekday_checks[day] = check
            group_layout.addWidget(check)

        layout.addWidget(self.weekdays_group)

    def _create_monthly_section(self, layout: QVBoxLayout):
        """Create monthly options section"""
        self.monthly_group = QGroupBox(
            self.i18n.get_text(
                "recurring.advanced.by_monthday", default="Monthly Options"
            )
        )
        group_layout = QVBoxLayout(self.monthly_group)
        group_layout.setContentsMargins(15, 25, 15, 15)

        # By month day option
        self.monthday_radio = QRadioButton(
            self.i18n.get_text(
                "recurring.advanced.by_monthday", default="By day of month"
            )
        )
        self.monthday_radio.setChecked(True)
        self.monthday_radio.toggled.connect(self._update_preview)
        group_layout.addWidget(self.monthday_radio)

        monthday_layout = QHBoxLayout()
        # Remove stretch for vertical alignment
        # monthday_layout.addStretch()
        monthday_layout.addWidget(
            QLabel(self.i18n.get_text("recurring.form.monthday", default="Day"))
        )
        self.monthday_spin = (
            NativeSpinBox(i18n_manager=self.i18n)
            if NATIVE_WIDGETS_AVAILABLE
            else QSpinBox()
        )
        self.monthday_spin.setRange(1, 31)
        self.monthday_spin.setValue(self.start_date.day)
        if NATIVE_WIDGETS_AVAILABLE and hasattr(self.monthday_spin, "setI18nManager"):
            self.monthday_spin.setI18nManager(self.i18n)
        self.monthday_spin.valueChanged.connect(self._update_preview)
        monthday_layout.addWidget(self.monthday_spin)
        # monthday_layout.addStretch()
        group_layout.addLayout(monthday_layout)

        # By position option
        self.setpos_radio = QRadioButton(
            self.i18n.get_text("recurring.advanced.by_setpos", default="By position")
        )
        self.setpos_radio.toggled.connect(self._update_preview)
        group_layout.addWidget(self.setpos_radio)

        setpos_layout = QHBoxLayout()
        self.setpos_combo = QComboBox()
        positions = [
            ("1", self.i18n.get_text("rrule.position.first", default="First")),
            ("2", self.i18n.get_text("rrule.position.second", default="Second")),
            ("3", self.i18n.get_text("rrule.position.third", default="Third")),
            ("4", self.i18n.get_text("rrule.position.fourth", default="Fourth")),
            ("-1", self.i18n.get_text("rrule.position.last", default="Last")),
        ]
        for value, text in positions:
            self.setpos_combo.addItem(text, value)
        self.setpos_combo.currentTextChanged.connect(self._update_preview)
        setpos_layout.addWidget(self.setpos_combo)

        self.setpos_weekday_combo = QComboBox()
        weekdays = [
            ("MO", self.i18n.get_text("rrule.weekday.monday", default="Monday")),
            ("TU", self.i18n.get_text("rrule.weekday.tuesday", default="Tuesday")),
            ("WE", self.i18n.get_text("rrule.weekday.wednesday", default="Wednesday")),
            ("TH", self.i18n.get_text("rrule.weekday.thursday", default="Thursday")),
            ("FR", self.i18n.get_text("rrule.weekday.friday", default="Friday")),
            ("SA", self.i18n.get_text("rrule.weekday.saturday", default="Saturday")),
            ("SU", self.i18n.get_text("rrule.weekday.sunday", default="Sunday")),
        ]
        for value, text in weekdays:
            self.setpos_weekday_combo.addItem(text, value)
        self.setpos_weekday_combo.currentTextChanged.connect(self._update_preview)
        setpos_layout.addWidget(self.setpos_weekday_combo)
        # Remove stretch for vertical alignment
        # setpos_layout.addStretch()
        group_layout.addLayout(setpos_layout)

        self.monthly_group.setVisible(False)
        layout.addWidget(self.monthly_group)

    def _create_end_condition_section(self, layout: QVBoxLayout):
        """Create end condition section"""
        group = QGroupBox(
            self.i18n.get_text("recurring.form.end_condition", default="End Condition")
        )
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(15, 25, 15, 15)

        self.end_group = QButtonGroup()

        # Never end
        self.never_radio = QRadioButton(
            self.i18n.get_text("rrule.end.never", default="Never")
        )
        self.never_radio.setChecked(True)
        self.never_radio.toggled.connect(self._update_preview)
        self.end_group.addButton(self.never_radio)
        group_layout.addWidget(self.never_radio)

        # End after count
        count_layout = QHBoxLayout()
        # Remove stretch for vertical alignment
        # count_layout.addStretch()  # Push controls to the right
        self.count_radio = QRadioButton(
            self.i18n.get_text("rrule.end.after", default="After")
        )
        self.count_radio.toggled.connect(self._update_preview)
        self.end_group.addButton(self.count_radio)
        count_layout.addWidget(self.count_radio)

        self.count_spin = (
            NativeSpinBox(i18n_manager=self.i18n)
            if NATIVE_WIDGETS_AVAILABLE
            else QSpinBox()
        )
        self.count_spin.setRange(1, 9999)
        self.count_spin.setValue(10)
        if NATIVE_WIDGETS_AVAILABLE and hasattr(self.count_spin, "setI18nManager"):
            self.count_spin.setI18nManager(self.i18n)
        self.count_spin.valueChanged.connect(self._update_preview)
        count_layout.addWidget(self.count_spin)

        count_layout.addWidget(
            QLabel(self.i18n.get_text("rrule.end.occurrences", default="occurrences"))
        )
        # Remove stretch for vertical alignment
        # count_layout.addStretch()
        group_layout.addLayout(count_layout)

        # End until date
        until_layout = QHBoxLayout()
        # Remove stretch for vertical alignment
        # until_layout.addStretch()  # Push controls to the right
        self.until_radio = QRadioButton(
            self.i18n.get_text("rrule.end.until", default="Until")
        )
        self.until_radio.toggled.connect(self._update_preview)
        self.end_group.addButton(self.until_radio)
        until_layout.addWidget(self.until_radio)

        # Create pure datepicker button (no edit field)
        from PySide6.QtWidgets import QPushButton
        from PySide6.QtCore import QLocale
        from PySide6.QtGui import QIcon

        # Store the selected date
        self.until_date = self.start_date + timedelta(days=365)

        # Create button that shows selected date with dropdown arrow
        self.until_edit = QPushButton()
        self.until_edit.setMaximumWidth(150)
        self.until_edit.setMinimumWidth(120)
        self.until_edit.clicked.connect(self._show_until_calendar)

        # Don't use system icon - we'll use emoji in text instead
        # Remove any default icon
        self.until_edit.setIcon(QIcon())

        # Set stylesheet to center text
        self.until_edit.setStyleSheet("""
            QPushButton {
                text-align: center;
            }
        """)

        # Update button text with formatted date
        self._update_until_button_text()

        # Store locale info for calendar
        self.current_locale = getattr(self.i18n, "current_locale", "en_US")

        # Set Qt locale for proper calendar behavior
        self.qt_locale_mapping = {
            "en_US": QLocale(QLocale.Language.English, QLocale.Country.UnitedStates),
            "en_GB": QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom),
            "en_CA": QLocale(QLocale.Language.English, QLocale.Country.Canada),
            "fr_FR": QLocale(QLocale.Language.French, QLocale.Country.France),
            "de_DE": QLocale(QLocale.Language.German, QLocale.Country.Germany),
            "es_ES": QLocale(QLocale.Language.Spanish, QLocale.Country.Spain),
            "it_IT": QLocale(QLocale.Language.Italian, QLocale.Country.Italy),
            "ja_JP": QLocale(QLocale.Language.Japanese, QLocale.Country.Japan),
            "ko_KR": QLocale(QLocale.Language.Korean, QLocale.Country.SouthKorea),
            "zh_CN": QLocale(QLocale.Language.Chinese, QLocale.Country.China),
            "zh_TW": QLocale(QLocale.Language.Chinese, QLocale.Country.Taiwan),
        }
        self.qt_locale = self.qt_locale_mapping.get(
            self.current_locale,
            QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom),
        )
        until_layout.addWidget(self.until_edit)
        # Remove stretch for vertical alignment
        # until_layout.addStretch()
        group_layout.addLayout(until_layout)

        layout.addWidget(group)

    def _create_preview_section(self, layout: QVBoxLayout):
        """Create preview section"""
        group = QGroupBox(self.i18n.get_text("recurring.preview", default="Preview"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(
            15, 30, 15, 15
        )  # Extra top margin to prevent overlap

        # Preview description
        self.preview_description = QLabel()
        self.preview_description.setWordWrap(True)
        group_layout.addWidget(self.preview_description)

        # Preview list
        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(150)
        group_layout.addWidget(self.preview_list)

        # RRULE display
        self.rrule_display = QLineEdit()
        self.rrule_display.setReadOnly(True)
        self.rrule_display.setFont(QFont("monospace"))
        group_layout.addWidget(self.rrule_display)

        layout.addWidget(group)

    def _create_buttons(self, layout: QVBoxLayout):
        """Create buttons section"""
        # Preset buttons
        preset_layout = QHBoxLayout()
        presets = [
            ("daily", self.i18n.get_text("recurring.preset.daily", default="Daily")),
            (
                "weekdays",
                self.i18n.get_text("recurring.preset.weekdays", default="Weekdays"),
            ),
            ("weekly", self.i18n.get_text("recurring.preset.weekly", default="Weekly")),
            (
                "monthly",
                self.i18n.get_text("recurring.preset.monthly", default="Monthly"),
            ),
        ]

        for preset, text in presets:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, p=preset: self._apply_preset(p))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Dialog buttons
        button_box = QDialogButtonBox()

        # Create custom OK button with translation
        ok_button = QPushButton(self.i18n.get_text("button_ok", default="OK"))
        ok_button.clicked.connect(self._on_ok)
        button_box.addButton(ok_button, QDialogButtonBox.ButtonRole.AcceptRole)

        # Create custom Cancel button with translation
        cancel_button = QPushButton(
            self.i18n.get_text("button_cancel", default="Cancel")
        )
        cancel_button.clicked.connect(self._on_cancel)
        button_box.addButton(cancel_button, QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

    def _on_frequency_change(self):
        """Handle frequency change"""
        frequency = self._get_selected_frequency()

        # Update interval label
        if frequency == "DAILY":
            self.interval_label.setText(
                self.i18n.get_text("rrule.interval.days", default="days")
            )
            self.weekdays_group.setVisible(False)
            self.monthly_group.setVisible(False)
        elif frequency == "WEEKLY":
            self.interval_label.setText(
                self.i18n.get_text("rrule.interval.weeks", default="weeks")
            )
            self.weekdays_group.setVisible(True)
            self.monthly_group.setVisible(False)
        elif frequency == "MONTHLY":
            self.interval_label.setText(
                self.i18n.get_text("rrule.interval.months", default="months")
            )
            self.weekdays_group.setVisible(False)
            self.monthly_group.setVisible(True)
        elif frequency == "YEARLY":
            self.interval_label.setText(
                self.i18n.get_text("rrule.interval.years", default="years")
            )
            self.weekdays_group.setVisible(False)
            self.monthly_group.setVisible(False)

        # Update native displays after frequency change
        from PySide6.QtCore import QTimer

        QTimer.singleShot(50, self._update_native_displays)

        self._update_preview()

    def _apply_preset(self, preset: str):
        """Apply preset configuration"""
        if preset == "daily":
            self._set_frequency("DAILY")
            self.interval_spin.setValue(1)
        elif preset == "weekdays":
            self._set_frequency("WEEKLY")
            self.interval_spin.setValue(1)
            # Set Monday to Friday
            for day in ["MO", "TU", "WE", "TH", "FR"]:
                self.weekday_checks[day].setChecked(True)
            for day in ["SA", "SU"]:
                self.weekday_checks[day].setChecked(False)
        elif preset == "weekly":
            self._set_frequency("WEEKLY")
            self.interval_spin.setValue(1)
            # Set start date weekday
            start_weekday = self.start_date.weekday()  # 0=Monday
            weekday_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            for day in weekday_map:
                self.weekday_checks[day].setChecked(False)
            self.weekday_checks[weekday_map[start_weekday]].setChecked(True)
        elif preset == "monthly":
            self._set_frequency("MONTHLY")
            self.interval_spin.setValue(1)
            self.monthday_radio.setChecked(True)
            self.monthday_spin.setValue(self.start_date.day)

        self._on_frequency_change()

        # Update native displays after applying preset
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, self._update_native_displays)

    def _set_defaults(self):
        """Set default values"""
        self._apply_preset("weekly")

    def _get_selected_frequency(self) -> str:
        """Get selected frequency"""
        checked_button = self.frequency_group.checkedButton()
        if checked_button:
            return checked_button.property("frequency")
        return "WEEKLY"

    def _set_frequency(self, frequency: str):
        """Set frequency selection"""
        for button in self.frequency_group.buttons():
            if button.property("frequency") == frequency:
                button.setChecked(True)
                break

    def _build_rrule(self) -> str:
        """Build RRULE from current settings"""
        try:
            parts = []

            # Frequency
            frequency = self._get_selected_frequency()
            parts.append(f"FREQ={frequency}")

            # Interval
            interval = self.interval_spin.value()
            if interval > 1:
                parts.append(f"INTERVAL={interval}")

            # Weekdays for weekly frequency
            if frequency == "WEEKLY":
                selected_days = [
                    day
                    for day, check in self.weekday_checks.items()
                    if check.isChecked()
                ]
                if selected_days:
                    parts.append(f"BYDAY={','.join(selected_days)}")

            # Monthly options
            elif frequency == "MONTHLY":
                if self.monthday_radio.isChecked():
                    monthday = self.monthday_spin.value()
                    parts.append(f"BYMONTHDAY={monthday}")
                elif self.setpos_radio.isChecked():
                    setpos = self.setpos_combo.currentData()
                    weekday = self.setpos_weekday_combo.currentData()
                    parts.append(f"BYDAY={weekday}")
                    parts.append(f"BYSETPOS={setpos}")

            # End condition
            if self.count_radio.isChecked():
                count = self.count_spin.value()
                parts.append(f"COUNT={count}")
            elif self.until_radio.isChecked():
                # Get date from stored until_date
                if hasattr(self, "until_date") and self.until_date:
                    parts.append(f"UNTIL={self.until_date.strftime('%Y%m%d')}")

            return ";".join(parts)

        except Exception as e:
            logger.error(f"❌ Failed to build RRULE: {e}")
            return ""

    def _load_rrule(self, rrule: str):
        """Load RRULE into dialog"""
        try:
            components = self.parser.parse_rrule(rrule)

            # Set frequency
            self._set_frequency(components.freq.value)

            # Set interval
            if components.interval:
                self.interval_spin.setValue(components.interval)

            # Set weekdays
            if components.byday:
                for day in self.weekday_checks:
                    self.weekday_checks[day].setChecked(False)
                for weekday_str in components.byday:
                    if weekday_str in self.weekday_checks:
                        self.weekday_checks[weekday_str].setChecked(True)

            # Set monthly options
            if components.bymonthday:
                self.monthday_radio.setChecked(True)
                self.monthday_spin.setValue(components.bymonthday[0])
            elif components.bysetpos and components.byday:
                self.setpos_radio.setChecked(True)
                # Find setpos value in combo
                for i in range(self.setpos_combo.count()):
                    if self.setpos_combo.itemData(i) == str(components.bysetpos[0]):
                        self.setpos_combo.setCurrentIndex(i)
                        break
                # Find weekday value in combo
                for i in range(self.setpos_weekday_combo.count()):
                    if self.setpos_weekday_combo.itemData(i) == components.byday[0]:
                        self.setpos_weekday_combo.setCurrentIndex(i)
                        break

            # Set end condition
            if components.count:
                self.count_radio.setChecked(True)
                self.count_spin.setValue(components.count)
            elif components.until:
                self.until_radio.setChecked(True)
                # Store the until date and update button
                self.until_date = components.until
                self._update_until_button_text()
            else:
                self.never_radio.setChecked(True)

            self._on_frequency_change()

            # Update native displays after loading
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, self._update_native_displays)

        except Exception as e:
            logger.error(f"❌ Failed to load RRULE: {e}")
            QMessageBox.warning(
                self,
                self.i18n.get_text("error.title", default="Error"),
                f"{self.i18n.get_text('recurring.error.invalid_rrule', default='Invalid recurrence pattern')}: {e}",  # noqa: E501
            )

    def _update_native_displays(self):
        """Update all native numeral displays"""
        try:
            # Force update native spinboxes multiple times to ensure they stick
            spinboxes = [self.interval_spin, self.monthday_spin, self.count_spin]

            for spinbox in spinboxes:
                if hasattr(spinbox, "forceNativeDisplay"):
                    spinbox.forceNativeDisplay()

            # Also trigger additional updates with delays
            from PySide6.QtCore import QTimer

            QTimer.singleShot(25, lambda: self._force_update_spinboxes(spinboxes))
            QTimer.singleShot(100, lambda: self._force_update_spinboxes(spinboxes))

        except Exception as e:
            logger.warning(f"Error updating native displays: {e}")

    def _force_update_spinboxes(self, spinboxes):
        """Force update specific spinboxes"""
        try:
            for spinbox in spinboxes:
                if hasattr(spinbox, "forceNativeDisplay"):
                    spinbox.forceNativeDisplay()
        except Exception as e:
            logger.warning(f"Error in force update: {e}")

    def _update_preview(self):
        """Update preview display"""
        try:
            rrule = self._build_rrule()

            if not rrule:
                self.preview_description.setText(
                    self.i18n.get_text(
                        "recurring.error.invalid_rrule",
                        default="Invalid recurrence pattern",
                    )
                )
                self.preview_list.clear()
                self.rrule_display.setText("")
                return

            # Show human-readable description instead of raw RRULE
            try:
                human_description = self.parser.get_human_readable_description(
                    rrule, self.i18n.current_locale
                )
                self.rrule_display.setText(human_description)
            except Exception as e:
                logger.warning(
                    f"Failed to get human description, showing raw RRULE: {e}"
                )
                self.rrule_display.setText(rrule)

            # Generate preview occurrences
            from ..data.models import Event

            # Create temporary event for preview
            temp_event = Event(
                title="Preview Event",
                start_date=self.start_date,
                rrule=rrule,
                is_recurring=True,
            )

            # Generate occurrences for next 3 months
            end_date = self.start_date + timedelta(days=90)
            occurrences = self.generator.generate_occurrences(
                temp_event, self.start_date, end_date
            )

            # Update preview text - use simple, safe description
            frequency = self._get_selected_frequency()
            interval = self.interval_spin.value()

            # Build safe description without complex parsing
            if frequency == "DAILY":
                if interval == 1:
                    description = self.i18n.get_text(
                        "recurring.preset.daily", default="Daily"
                    )
                else:
                    every_text = self.i18n.get_text(
                        "rrule.interval.every", default="Every"
                    )
                    days_text = self.i18n.get_text(
                        "rrule.interval.days", default="days"
                    )
                    description = f"{every_text} {interval} {days_text}"
            elif frequency == "WEEKLY":
                selected_days = [
                    day
                    for day, check in self.weekday_checks.items()
                    if check.isChecked()
                ]
                if interval == 1 and len(selected_days) == 1:
                    # Simple weekly on one day
                    weekday_name = self._get_weekday_name_from_code(
                        list(selected_days)[0]
                    )
                    day_key = f"rrule.weekday.{weekday_name}"
                    day_name = self.i18n.get_text(
                        day_key, default=list(selected_days)[0]
                    )
                    every_text = self.i18n.get_text(
                        "rrule.interval.every", default="Every"
                    )
                    description = f"{every_text} {day_name}"
                else:
                    # Complex weekly pattern
                    weekly_text = self.i18n.get_text(
                        "recurring.preset.weekly", default="Weekly"
                    )
                    if interval > 1:
                        every_text = self.i18n.get_text(
                            "rrule.interval.every", default="Every"
                        )
                        weeks_text = self.i18n.get_text(
                            "rrule.interval.weeks", default="weeks"
                        )
                        description = f"{every_text} {interval} {weeks_text}"
                    else:
                        description = weekly_text
            elif frequency == "MONTHLY":
                if interval == 1:
                    description = self.i18n.get_text(
                        "recurring.preset.monthly", default="Monthly"
                    )
                else:
                    every_text = self.i18n.get_text(
                        "rrule.interval.every", default="Every"
                    )
                    months_text = self.i18n.get_text(
                        "rrule.interval.months", default="months"
                    )
                    description = f"{every_text} {interval} {months_text}"
            elif frequency == "YEARLY":
                if interval == 1:
                    description = self.i18n.get_text(
                        "rrule.frequency.yearly", default="Yearly"
                    )
                else:
                    every_text = self.i18n.get_text(
                        "rrule.interval.every", default="Every"
                    )
                    years_text = self.i18n.get_text(
                        "rrule.interval.years", default="years"
                    )
                    description = f"{every_text} {interval} {years_text}"
            else:
                description = self.i18n.get_text(
                    "recurring.error.invalid_rrule",
                    default="Invalid recurrence pattern",
                )

            self.preview_description.setText(description)

            # Update preview list
            self.preview_list.clear()
            for occurrence in occurrences[:20]:  # Show first 20 occurrences
                # Format date with native numerals
                date_str = self._format_date_with_native_numerals(occurrence.start_date)

                # Get translated weekday name
                weekday_index = occurrence.start_date.weekday()  # 0=Monday, 6=Sunday
                weekday_keys = [
                    "rrule.weekday.monday",
                    "rrule.weekday.tuesday",
                    "rrule.weekday.wednesday",
                    "rrule.weekday.thursday",
                    "rrule.weekday.friday",
                    "rrule.weekday.saturday",
                    "rrule.weekday.sunday",
                ]
                weekday_defaults = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
                weekday = self.i18n.get_text(
                    weekday_keys[weekday_index], default=weekday_defaults[weekday_index]
                )

                self.preview_list.addItem(f"{date_str} ({weekday})")

            if len(occurrences) > 20:
                self.preview_list.addItem(f"... and {len(occurrences) - 20} more")

        except Exception as e:
            logger.error(f"❌ Preview update failed: {e}")
            self.preview_description.setText(
                f"{self.i18n.get_text('recurring.error.invalid_rrule', default='Invalid recurrence pattern')}: {e}"  # noqa: E501
            )
            self.preview_list.clear()

    def _on_ok(self):
        """Handle OK button"""
        try:
            rrule = self._build_rrule()
            if not rrule:
                QMessageBox.warning(
                    self,
                    self.i18n.get_text("error.title", default="Error"),
                    self.i18n.get_text(
                        "recurring.error.invalid_rrule",
                        default="Invalid recurrence pattern",
                    ),
                )
                return

            # Validate RRULE
            if not self.parser.validate_rrule(rrule):
                QMessageBox.warning(
                    self,
                    self.i18n.get_text("error.title", default="Error"),
                    self.i18n.get_text(
                        "recurring.error.invalid_rrule",
                        default="Invalid recurrence pattern",
                    ),
                )
                return

            self.result_rrule = rrule
            self.cancelled = False
            self.accept()

        except Exception as e:
            logger.error(f"❌ RRULE validation failed: {e}")
            QMessageBox.warning(
                self,
                self.i18n.get_text("error.title", default="Error"),
                f"{self.i18n.get_text('recurring.error.invalid_rrule', default='Invalid recurrence pattern')}: {e}",  # noqa: E501
            )

    def _on_cancel(self):
        """Handle Cancel button"""
        self.cancelled = True
        self.reject()

    def _format_date_with_native_numerals(self, date_obj):
        """Format date with native numerals for current locale"""
        try:
            # Use centralized date formatting from i18n manager
            from calendar_app.localization.i18n_manager import format_date_for_locale

            return format_date_for_locale(date_obj)
        except Exception as e:
            logger.warning(f"Failed to format date with native numerals: {e}")
            return date_obj.strftime("%Y-%m-%d")

    def _get_weekday_name_from_code(self, code: str) -> str:
        """Convert weekday code to name for translation"""
        weekday_map = {
            "MO": "monday",
            "TU": "tuesday",
            "WE": "wednesday",
            "TH": "thursday",
            "FR": "friday",
            "SA": "saturday",
            "SU": "sunday",
        }
        return weekday_map.get(code, code.lower())

    def _update_until_button_text(self):
        """Update the until button text with formatted date"""
        try:
            if hasattr(self, "until_date") and self.until_date:
                # Format date according to locale
                formatted_date = self._format_date_with_native_numerals(self.until_date)
                # Add two spaces before text to balance the arrow on the right
                self.until_edit.setText(f"  {formatted_date}  🔽")
            else:
                # Add two spaces before text to balance the arrow on the right
                self.until_edit.setText("  Select Date  🔽")
        except Exception as e:
            logger.warning(f"Error updating until button text: {e}")
            self.until_edit.setText("  Select Date  🔽")

    def _show_until_calendar(self):
        """Show calendar popup for until date selection"""
        try:
            from PySide6.QtWidgets import (
                QCalendarWidget,
                QVBoxLayout,
                QDialog,
                QDialogButtonBox,
            )

            # Create calendar dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(
                self.i18n.get_text("rrule.end.until", default="Until")
            )
            dialog.setModal(True)
            dialog.resize(350, 300)

            layout = QVBoxLayout(dialog)

            # Create calendar widget
            calendar = QCalendarWidget()
            calendar.setLocale(self.qt_locale)

            # Customize calendar navigation buttons with red triangle emojis
            try:
                # Get the navigation bar and customize button text
                nav_bar = calendar.findChild(QWidget, "qt_calendar_navigationbar")
                if nav_bar:
                    # Find previous/next month buttons
                    buttons = nav_bar.findChildren(QPushButton)
                    for button in buttons:
                        if (
                            "previous" in button.objectName().lower()
                            or "left" in button.objectName().lower()
                        ):
                            button.setText("◀️")  # Red left triangle
                        elif (
                            "next" in button.objectName().lower()
                            or "right" in button.objectName().lower()
                        ):
                            button.setText("▶️")  # Red right triangle

                # Alternative approach: set stylesheet for navigation buttons
                calendar.setStyleSheet("""
                    QCalendarWidget QToolButton#qt_calendar_prevmonth {
                        qproperty-text: "◀️";
                        font-size: 14px;
                    }
                    QCalendarWidget QToolButton#qt_calendar_nextmonth {
                        qproperty-text: "▶️";
                        font-size: 14px;
                    }
                """)
            except Exception as e:
                logger.warning(f"Could not customize calendar navigation buttons: {e}")

            # Set current date
            if hasattr(self, "until_date") and self.until_date:
                qdate = QDate(
                    self.until_date.year, self.until_date.month, self.until_date.day
                )
                calendar.setSelectedDate(qdate)

            layout.addWidget(calendar)

            # Add buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            # Show dialog and get result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_qdate = calendar.selectedDate()
                self.until_date = date(
                    selected_qdate.year(), selected_qdate.month(), selected_qdate.day()
                )
                self._update_until_button_text()
                self._update_preview()

        except Exception as e:
            logger.error(f"Error showing calendar: {e}")
            QMessageBox.warning(
                self,
                self.i18n.get_text("error.title", default="Error"),
                f"Failed to show calendar: {e}",
            )

    def get_rrule(self) -> Optional[str]:
        """Get the result RRULE"""
        return None if self.cancelled else self.result_rrule


def show_rrule_dialog(
    parent=None,
    i18n=None,
    initial_rrule: Optional[str] = None,
    start_date: Optional[date] = None,
) -> Optional[str]:
    """Show RRULE dialog and return result"""
    dialog = RRuleDialog(parent, initial_rrule, start_date)
    dialog.exec()
    return dialog.get_rrule()
