"""
⚙️ Settings Dialog for Calendar Application

This module contains the settings configuration dialog.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDialogButtonBox,
    QInputDialog,
)
from PySide6.QtCore import Signal

from calendar_app.config.settings import SettingsManager
from calendar_app.config.themes import ThemeManager
from calendar_app.core.multi_country_holiday_provider import (
    MultiCountryHolidayProvider,
)
from calendar_app.localization.i18n_manager import get_i18n_manager


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


class GeneralSettingsWidget(QWidget):
    """⚙️ General settings tab."""

    def __init__(
        self,
        settings_manager: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ):
        """Initialize general settings widget."""
        super().__init__(parent)

        self.settings_manager = settings_manager
        self.theme_manager = theme_manager

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """🏗️ Setup general settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Theme settings
        theme_group = QGroupBox(f"🎨 {_('settings_appearance')}")
        theme_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(10)

        # Theme row
        theme_row = QHBoxLayout()
        theme_label = QLabel(f"{_('label_theme')}")
        theme_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(
            f"{UI_EMOJIS['theme_dark']} {_('button_theme_dark')}", "dark"
        )
        self.theme_combo.addItem(
            f"{UI_EMOJIS['theme_light']} {_('button_theme_light')}", "light"
        )
        self.theme_combo.setMinimumWidth(150)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)

        layout.addWidget(theme_group)

        # Calendar settings
        calendar_group = QGroupBox(f"📅 {_('settings_calendar_settings')}")
        calendar_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        calendar_layout = QVBoxLayout(calendar_group)
        calendar_layout.setSpacing(10)

        # First day of week row
        first_day_row = QHBoxLayout()
        first_day_label = QLabel(f"{_('label_first_day_of_week')}")
        first_day_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.first_day_combo = QComboBox()
        days = [
            _("day_monday"),
            _("day_tuesday"),
            _("day_wednesday"),
            _("day_thursday"),
            _("day_friday"),
            _("day_saturday"),
            _("day_sunday"),
        ]
        for i, day in enumerate(days):
            self.first_day_combo.addItem(day, i)
        self.first_day_combo.setMinimumWidth(150)
        first_day_row.addWidget(first_day_label)
        first_day_row.addWidget(self.first_day_combo)
        first_day_row.addStretch()
        calendar_layout.addLayout(first_day_row)

        # Display options row - removed week numbers toggle (always enabled)

        # Default duration row
        duration_row = QHBoxLayout()
        duration_label = QLabel(f"{_('label_default_event_duration')}")
        duration_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.default_duration = QSpinBox()
        self.default_duration.setRange(15, 1440)
        self.default_duration.setSuffix(f" {_('time_minutes')}")
        self.default_duration.setValue(60)
        self.default_duration.setMinimumWidth(150)
        duration_row.addWidget(duration_label)
        duration_row.addWidget(self.default_duration)
        duration_row.addStretch()
        calendar_layout.addLayout(duration_row)

        # Holiday country row - which country's public holidays are shown
        holiday_row = QHBoxLayout()
        holiday_label = QLabel(
            f"{_('label_holiday_country', default='Public holidays')}"
        )
        holiday_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.holiday_country_combo = QComboBox()
        self.holiday_country_combo.setMinimumWidth(180)
        self._populate_holiday_country_combo()
        holiday_row.addWidget(holiday_label)
        holiday_row.addWidget(self.holiday_country_combo)
        holiday_row.addStretch()
        calendar_layout.addLayout(holiday_row)

        # Holiday country hint
        holiday_hint = QLabel(
            _(
                "info_holiday_country",
                default="Choose 'Auto' to follow your timezone, or pick a specific country.",  # noqa: E501
            )
        )
        holiday_hint.setStyleSheet("font-size: 10px; color: #cccccc; margin-top: 2px;")
        holiday_hint.setWordWrap(True)
        calendar_layout.addWidget(holiday_hint)

        layout.addWidget(calendar_group)

        # Add stretch
        layout.addStretch()

    def _populate_holiday_country_combo(self):
        """🌍 Populate the holiday-country combo (Auto + every supported country)."""
        self.holiday_country_combo.clear()
        self.holiday_country_combo.addItem(
            f"🌍 {_('holiday_country_auto', default='Auto (from timezone)')}",
            MultiCountryHolidayProvider.AUTO_COUNTRY,
        )
        self.holiday_country_combo.insertSeparator(1)
        for country_code, info in MultiCountryHolidayProvider.get_sorted_countries():
            self.holiday_country_combo.addItem(
                f"{info['flag']} {info['name']}", country_code
            )

    def _load_settings(self):
        """📥 Load current settings."""
        # Theme
        current_theme = self.settings_manager.get_theme()
        theme_index = self.theme_combo.findData(current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        # Calendar settings
        calendar_settings = self.settings_manager.get_calendar_settings()

        first_day_index = self.first_day_combo.findData(
            calendar_settings["first_day_of_week"]
        )
        if first_day_index >= 0:
            self.first_day_combo.setCurrentIndex(first_day_index)

        self.default_duration.setValue(calendar_settings["default_event_duration"])

        # Holiday country ("auto" or a specific country code)
        holiday_country = self.settings_manager.get_holiday_country()
        holiday_index = self.holiday_country_combo.findData(holiday_country)
        if holiday_index >= 0:
            self.holiday_country_combo.setCurrentIndex(holiday_index)

    def save_settings(self):
        """💾 Save settings."""
        try:
            # Theme
            theme_data = self.theme_combo.currentData()
            if theme_data:
                self.settings_manager.set_theme(theme_data)

            # Calendar settings
            first_day_data = self.first_day_combo.currentData()
            if first_day_data is not None:
                self.settings_manager.set_first_day_of_week(first_day_data)

            self.settings_manager.set_default_event_duration(
                self.default_duration.value()
            )

            # Holiday country
            holiday_country_data = self.holiday_country_combo.currentData()
            if holiday_country_data:
                self.settings_manager.set_holiday_country(holiday_country_data)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to save general settings: {e}")
            return False

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update group box titles
            for widget in self.findChildren(QGroupBox):
                text = widget.title()
                if "🎨" in text:
                    widget.setTitle(f"🎨 {_('settings_appearance')}")
                elif "📅" in text:
                    widget.setTitle(f"📅 {_('settings_calendar_settings')}")

            # Update labels
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if _("label_theme") in text or "Theme" in text:
                    widget.setText(_("label_theme"))
                elif _("label_first_day_of_week") in text or "First day" in text:
                    widget.setText(_("label_first_day_of_week"))
                elif _("label_display_options") in text or "Display" in text:
                    widget.setText(_("label_display_options"))
                elif _("label_default_event_duration") in text or "Default" in text:
                    widget.setText(_("label_default_event_duration"))
                elif _("label_holiday_country") in text or "Public holidays" in text:
                    widget.setText(
                        _("label_holiday_country", default="Public holidays")
                    )

            # Update holiday country combo (preserve selection, retranslate Auto)
            if hasattr(self, "holiday_country_combo"):
                current_data = self.holiday_country_combo.currentData()
                self._populate_holiday_country_combo()
                if current_data:
                    index = self.holiday_country_combo.findData(current_data)
                    if index >= 0:
                        self.holiday_country_combo.setCurrentIndex(index)

            # Update theme combo box
            if hasattr(self, "theme_combo"):
                current_data = self.theme_combo.currentData()
                self.theme_combo.clear()
                self.theme_combo.addItem(
                    f"{UI_EMOJIS['theme_dark']} {_('button_theme_dark')}", "dark"
                )
                self.theme_combo.addItem(
                    f"{UI_EMOJIS['theme_light']} {_('button_theme_light')}", "light"
                )
                if current_data:
                    index = self.theme_combo.findData(current_data)
                    if index >= 0:
                        self.theme_combo.setCurrentIndex(index)

            # Update first day combo box
            if hasattr(self, "first_day_combo"):
                current_data = self.first_day_combo.currentData()
                self.first_day_combo.clear()
                days = [
                    _("day_monday"),
                    _("day_tuesday"),
                    _("day_wednesday"),
                    _("day_thursday"),
                    _("day_friday"),
                    _("day_saturday"),
                    _("day_sunday"),
                ]
                for i, day in enumerate(days):
                    self.first_day_combo.addItem(day, i)
                if current_data is not None:
                    index = self.first_day_combo.findData(current_data)
                    if index >= 0:
                        self.first_day_combo.setCurrentIndex(index)

            # Week numbers checkbox removed - always enabled

            # Update spinbox suffix
            if hasattr(self, "default_duration"):
                self.default_duration.setSuffix(f" {_('time_minutes')}")

            logger.debug("🔄 General settings UI text refreshed")
        except Exception as e:
            logger.error(f"❌ Failed to refresh general settings UI text: {e}")


class NTPSettingsWidget(QWidget):
    """🌐 NTP settings tab."""

    def __init__(self, settings_manager: SettingsManager, parent=None):
        """Initialize NTP settings widget."""
        super().__init__(parent)

        self.settings_manager = settings_manager

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """🏗️ Setup NTP settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Sync settings
        sync_group = QGroupBox(f"🌐 {_('settings_time_synchronization')}")
        sync_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        sync_layout = QVBoxLayout(sync_group)
        sync_layout.setSpacing(10)

        # Sync interval row
        sync_row = QHBoxLayout()
        sync_label = QLabel(f"{_('label_sync_interval')}")
        sync_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.sync_interval = QSpinBox()
        self.sync_interval.setRange(1, 1440)
        self.sync_interval.setSuffix(f" {_('time_minutes')}")
        self.sync_interval.setValue(5)
        self.sync_interval.setMinimumWidth(150)
        sync_row.addWidget(sync_label)
        sync_row.addWidget(self.sync_interval)
        sync_row.addStretch()
        sync_layout.addLayout(sync_row)

        layout.addWidget(sync_group)

        # Timezone settings
        timezone_group = QGroupBox(
            f"🌍 {_('settings_timezone', default='Timezone Settings')}"
        )
        timezone_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        timezone_layout = QVBoxLayout(timezone_group)
        timezone_layout.setSpacing(10)

        # Timezone row
        timezone_row = QHBoxLayout()
        timezone_label = QLabel(f"{_('label_timezone', default='Timezone')}")
        timezone_label.setStyleSheet("border: none; padding: 0; margin: 0;")
        self.timezone_combo = QComboBox()
        self.timezone_combo.setMinimumWidth(200)

        # Populate timezone options
        self._populate_timezone_combo()

        timezone_row.addWidget(timezone_label)
        timezone_row.addWidget(self.timezone_combo)
        timezone_row.addStretch()
        timezone_layout.addLayout(timezone_row)

        # Timezone info label
        timezone_info = QLabel(
            _(
                "info_timezone_setting",
                default="Select 'Auto' to use system timezone, or choose a specific timezone",  # noqa: E501
            )
        )
        timezone_info.setStyleSheet("font-size: 10px; color: #cccccc; margin-top: 5px;")
        timezone_layout.addWidget(timezone_info)

        layout.addWidget(timezone_group)

        # NTP servers
        servers_group = QGroupBox(f"🌐 {_('settings_ntp_servers')}")
        servers_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        servers_layout = QVBoxLayout(servers_group)
        servers_layout.setSpacing(10)

        # Server list label
        servers_layout.addWidget(QLabel(_("info_configure_ntp_servers")))

        self.servers_list = QListWidget()
        self.servers_list.setMinimumHeight(120)
        self.servers_list.setMaximumHeight(150)
        servers_layout.addWidget(self.servers_list)

        # Server buttons
        server_buttons = QHBoxLayout()
        server_buttons.setSpacing(10)

        self.add_server_btn = QPushButton(f"➕ {_('button_add_server')}")
        self.add_server_btn.setMinimumWidth(120)
        self.add_server_btn.clicked.connect(self._add_server)
        server_buttons.addWidget(self.add_server_btn)

        self.remove_server_btn = QPushButton(f"➖ {_('button_remove_server')}")
        self.remove_server_btn.setMinimumWidth(120)
        self.remove_server_btn.clicked.connect(self._remove_server)
        server_buttons.addWidget(self.remove_server_btn)

        self.reset_servers_btn = QPushButton(f"🔄 {_('button_reset_servers')}")
        self.reset_servers_btn.setMinimumWidth(140)
        self.reset_servers_btn.clicked.connect(self._reset_servers)
        server_buttons.addWidget(self.reset_servers_btn)

        server_buttons.addStretch()
        servers_layout.addLayout(server_buttons)

        layout.addWidget(servers_group)

        # Add stretch
        layout.addStretch()

    def _populate_timezone_combo(self):
        """🌍 Populate timezone combo box with common timezones."""
        # Add auto option first
        self.timezone_combo.addItem(
            f"🌍 {_('timezone_auto', default='Auto (System Timezone)')}", "auto"
        )

        # Add separator
        self.timezone_combo.insertSeparator(1)

        # Common timezones organized by region
        common_timezones = [
            # Europe
            ("🇬🇧 London (GMT/BST)", "Europe/London"),
            ("🇫🇷 Paris (CET/CEST)", "Europe/Paris"),
            ("🇩🇪 Berlin (CET/CEST)", "Europe/Berlin"),
            ("🇮🇹 Rome (CET/CEST)", "Europe/Rome"),
            ("🇪🇸 Madrid (CET/CEST)", "Europe/Madrid"),
            ("🇷🇺 Moscow (MSK)", "Europe/Moscow"),
            # Americas
            ("🇺🇸 New York (EST/EDT)", "America/New_York"),
            ("🇺🇸 Chicago (CST/CDT)", "America/Chicago"),
            ("🇺🇸 Denver (MST/MDT)", "America/Denver"),
            ("🇺🇸 Los Angeles (PST/PDT)", "America/Los_Angeles"),
            ("🇧🇷 São Paulo (BRT/BRST)", "America/Sao_Paulo"),
            # Asia
            ("🇯🇵 Tokyo (JST)", "Asia/Tokyo"),
            ("🇨🇳 Shanghai (CST)", "Asia/Shanghai"),
            ("🇹🇼 Taipei (CST)", "Asia/Taipei"),
            ("🇰🇷 Seoul (KST)", "Asia/Seoul"),
            ("🇮🇳 Kolkata (IST)", "Asia/Kolkata"),
            ("🇸🇦 Riyadh (AST)", "Asia/Riyadh"),
            # Others
            ("🇦🇺 Sydney (AEST/AEDT)", "Australia/Sydney"),
            ("🌍 UTC", "UTC"),
        ]

        for display_name, timezone_id in common_timezones:
            self.timezone_combo.addItem(display_name, timezone_id)

    def _load_settings(self):
        """📥 Load current NTP settings."""
        ntp_settings = self.settings_manager.get_ntp_settings()

        self.sync_interval.setValue(ntp_settings["interval_minutes"])

        # Load timezone setting
        current_timezone = self.settings_manager.get_timezone()
        timezone_index = self.timezone_combo.findData(current_timezone)
        if timezone_index >= 0:
            self.timezone_combo.setCurrentIndex(timezone_index)
        else:
            # If timezone not found, default to auto
            auto_index = self.timezone_combo.findData("auto")
            if auto_index >= 0:
                self.timezone_combo.setCurrentIndex(auto_index)

        # Load servers
        self.servers_list.clear()
        for server in ntp_settings["servers"]:
            self.servers_list.addItem(server)

    def _add_server(self):
        """➕ Add NTP server."""
        server, ok = QInputDialog.getText(
            self,
            f"➕ {_('button_add_server')}",
            f"🌐 {_('prompt_enter_ntp_server')}:",
            text="pool.ntp.org",
        )

        if ok and server.strip():
            server = server.strip()
            if self.settings_manager.add_ntp_server(server):
                self._load_settings()
                QMessageBox.information(
                    self,
                    f"✅ {_('info_server_added')}",
                    f"{_('info_ntp_server_added_successfully', server=server)}",
                )
            else:
                QMessageBox.warning(
                    self,
                    f"⚠️ {_('warning_server_error')}",
                    f"{_('warning_failed_to_add_server', server=server)}",
                )

    def _remove_server(self):
        """➖ Remove selected NTP server."""
        current_item = self.servers_list.currentItem()
        if current_item:
            server = current_item.text()
            # Create custom confirmation dialog with Arabic buttons
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(f"➖ {_('button_remove_server')}")
            msg_box.setText(f"{_('confirm_remove_ntp_server', server=server)}")
            msg_box.setIcon(QMessageBox.Icon.Question)

            # Create custom buttons with Arabic text
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
                self.settings_manager.remove_ntp_server(server)
                self._load_settings()

    def _reset_servers(self):
        """🔄 Reset to default NTP servers."""
        # Create custom confirmation dialog with Arabic buttons
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"🔄 {_('button_reset_servers')}")
        msg_box.setText(_("confirm_reset_servers"))
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Create custom buttons with Arabic text
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
            # Reset to defaults
            from version import DEFAULT_NTP_SERVERS

            # Clear current servers
            current_servers = self.settings_manager.get_ntp_settings()["servers"].copy()
            for server in current_servers:
                self.settings_manager.remove_ntp_server(server)

            # Add default servers
            for server in DEFAULT_NTP_SERVERS:
                self.settings_manager.add_ntp_server(server)

            self._load_settings()

    def save_settings(self):
        """💾 Save NTP settings."""
        try:
            self.settings_manager.set_ntp_interval(self.sync_interval.value())

            # Save timezone setting
            timezone_data = self.timezone_combo.currentData()
            if timezone_data:
                self.settings_manager.set_timezone(timezone_data)

                # Refresh timezone in time manager if it exists
                try:
                    from calendar_app.utils.ntp_client import get_effective_timezone

                    # Force refresh of timezone
                    get_effective_timezone()
                    logger.debug(f"🌍 Timezone setting saved: {timezone_data}")
                except Exception as tz_error:
                    logger.warning(f"⚠️ Failed to refresh timezone: {tz_error}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to save NTP settings: {e}")
            return False

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update group box titles
            for widget in self.findChildren(QGroupBox):
                text = widget.title()
                if "🌐" in text and ("sync" in text.lower() or "time" in text.lower()):
                    widget.setTitle(f"🌐 {_('settings_time_synchronization')}")
                elif "🌍" in text and "timezone" in text.lower():
                    widget.setTitle(
                        f"🌍 {_('settings_timezone', default='Timezone Settings')}"
                    )
                elif "🌐" in text and "server" in text.lower():
                    widget.setTitle(f"🌐 {_('settings_ntp_servers')}")

            # Update labels
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if "sync" in text.lower() and "interval" in text.lower():
                    widget.setText(_("label_sync_interval"))
                elif "timezone" in text.lower() and "auto" not in text.lower():
                    widget.setText(_("label_timezone", default="Timezone"))
                elif "auto" in text.lower() and "system" in text.lower():
                    widget.setText(
                        _(
                            "info_timezone_setting",
                            default="Select 'Auto' to use system timezone, or choose a specific timezone",  # noqa: E501
                        )
                    )
                elif "configure" in text.lower() or "ntp" in text.lower():
                    widget.setText(_("info_configure_ntp_servers"))

            # Update spinbox suffix
            if hasattr(self, "sync_interval"):
                self.sync_interval.setSuffix(f" {_('time_minutes')}")

            # Update button texts
            if hasattr(self, "add_server_btn"):
                self.add_server_btn.setText(f"➕ {_('button_add_server')}")
            if hasattr(self, "remove_server_btn"):
                self.remove_server_btn.setText(f"➖ {_('button_remove_server')}")
            if hasattr(self, "reset_servers_btn"):
                self.reset_servers_btn.setText(f"🔄 {_('button_reset_servers')}")

            # Update timezone combo box
            if hasattr(self, "timezone_combo"):
                current_data = self.timezone_combo.currentData()
                self.timezone_combo.clear()
                self._populate_timezone_combo()
                if current_data:
                    index = self.timezone_combo.findData(current_data)
                    if index >= 0:
                        self.timezone_combo.setCurrentIndex(index)

            logger.debug("🔄 NTP settings UI text refreshed")
        except Exception as e:
            logger.error(f"❌ Failed to refresh NTP settings UI text: {e}")


class HolidaySettingsWidget(QWidget):
    """🌍 Holiday settings tab - REMOVED to eliminate confusion."""

    def __init__(self, settings_manager: SettingsManager, parent=None):
        """Initialize holiday settings widget."""
        super().__init__(parent)

        self.settings_manager = settings_manager

        self._setup_ui()

    def _setup_ui(self):
        """🏗️ Setup holiday settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Holiday preview section (only section now)
        preview_group = QGroupBox(
            f"📅 {_('settings_holiday_preview', default='Holiday Preview for Current Year')}"  # noqa: E501
        )
        preview_group.setStyleSheet(
            "QGroupBox { font-weight: bold; padding-top: 10px; border: none; }"
        )
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(10)

        # Preview info label
        preview_info = QLabel(
            _(
                "settings_holiday_preview_info",
                default="These are the holidays that will be displayed in your calendar:",  # noqa: E501
            )
        )
        preview_info.setStyleSheet(
            "font-size: 11px; color: #cccccc; margin-bottom: 5px;"
        )
        preview_layout.addWidget(preview_info)

        # Holiday list
        self.holiday_list = QListWidget()
        self.holiday_list.setMinimumHeight(160)
        self.holiday_list.setMaximumHeight(180)
        self.holiday_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 2px;
                font-size: 11px;
                margin: 0px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #404040;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
        """)
        preview_layout.addWidget(self.holiday_list)

        # No refresh button needed - holidays load automatically

        layout.addWidget(preview_group)

        # Load initial holiday preview
        self._refresh_holiday_preview()

    def _refresh_holiday_preview(self):
        """🔄 Refresh the holiday preview list."""
        try:
            from calendar_app.core.multi_country_holiday_provider import (
                MultiCountryHolidayProvider,
            )
            from datetime import date

            # Clear existing items
            self.holiday_list.clear()

            # Get current year
            current_year = date.today().year

            # Create holiday provider to get current holidays
            provider = MultiCountryHolidayProvider()

            # Get all holidays for the current year
            all_holidays = []
            for month in range(1, 13):
                month_holidays = provider.get_holidays_for_month(current_year, month)
                all_holidays.extend(month_holidays)

            # Sort holidays by date
            all_holidays.sort(key=lambda h: h.date)

            if all_holidays:
                # Add holidays to the list
                for holiday in all_holidays:
                    # Format: "जनवरी 1 - New Year's Day" (using translated month names)
                    try:
                        # Get translated month names
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

                        # Get translated weekday names for tooltip
                        weekday_names = [
                            _("calendar.days.monday", default="Monday"),
                            _("calendar.days.tuesday", default="Tuesday"),
                            _("calendar.days.wednesday", default="Wednesday"),
                            _("calendar.days.thursday", default="Thursday"),
                            _("calendar.days.friday", default="Friday"),
                            _("calendar.days.saturday", default="Saturday"),
                            _("calendar.days.sunday", default="Sunday"),
                        ]

                        month = month_names[holiday.date.month - 1]
                        date_str = f"{month} {holiday.date.day}"
                        item_text = f"{date_str} - {holiday.name}"

                        # Create tooltip with translated weekday and month
                        weekday = weekday_names[holiday.date.weekday()]
                        tooltip_str = (
                            f"{weekday}, {holiday.date.day} {month} "
                            f"{holiday.date.year}\n{holiday.name}"
                        )

                        item = QListWidgetItem(item_text)
                        item.setToolTip(tooltip_str)
                        self.holiday_list.addItem(item)
                    except Exception as date_error:
                        logger.warning(
                            f"⚠️ Failed to format holiday date: {date_error}"
                        )
                        # Fallback to English formatting
                        date_str = holiday.date.strftime("%B %d")
                        item_text = f"{date_str} - {holiday.name}"
                        item = QListWidgetItem(item_text)
                        item.setToolTip(
                            f"{holiday.date.strftime('%A, %B %d, %Y')}\n{holiday.name}"
                        )
                        self.holiday_list.addItem(item)

                logger.debug(f"🔄 Loaded {len(all_holidays)} holidays for preview")
            else:
                # No holidays found
                no_holidays_item = QListWidgetItem(
                    _(
                        "settings_no_holidays",
                        default="No holidays found for current locale",
                    )
                )
                no_holidays_item.setToolTip(
                    _(
                        "settings_no_holidays_tooltip",
                        default="This may be normal for some locales or regions",
                    )
                )
                self.holiday_list.addItem(no_holidays_item)
                logger.debug("🔄 No holidays found for current locale")

        except Exception as e:
            logger.error(f"❌ Failed to refresh holiday preview: {e}")
            # Add error item
            error_item = QListWidgetItem(
                _("settings_holiday_error", default="Error loading holidays")
            )
            error_item.setToolTip(str(e))
            self.holiday_list.addItem(error_item)

    def save_settings(self):
        """💾 Save holiday settings - no settings to save anymore."""
        return True

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update group box titles
            for widget in self.findChildren(QGroupBox):
                title = widget.title()
                if "📅" in title:
                    widget.setTitle(
                        f"📅 {_('settings_holiday_preview', default='Holiday Preview for Current Year')}"  # noqa: E501
                    )

            # Update labels
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if (
                    "These are the holidays" in text
                    or "preview_info" in widget.objectName()
                ):
                    widget.setText(
                        _(
                            "settings_holiday_preview_info",
                            default="These are the holidays that will be displayed in your calendar:",  # noqa: E501
                        )
                    )

            # Refresh the holiday preview with new language
            self._refresh_holiday_preview()

            logger.debug("🔄 Holiday settings UI text refreshed")
        except Exception as e:
            logger.error(f"❌ Failed to refresh holiday settings UI text: {e}")


class SettingsDialog(QDialog):
    """⚙️ Settings configuration dialog."""

    settings_changed = Signal()

    def __init__(
        self,
        settings_manager: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ):
        """Initialize settings dialog."""
        super().__init__(parent)

        self.settings_manager = settings_manager
        self.theme_manager = theme_manager

        self._setup_ui()

        logger.debug("⚙️ Settings dialog initialized")

    def _setup_ui(self):
        """🏗️ Setup settings dialog UI."""
        self.setWindowTitle(
            f"{UI_EMOJIS['settings']} "
            f"{_('settings_dialog_title', app_name=_('app_name'))}"
        )
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title_label = QLabel(
            f"{UI_EMOJIS['settings']} {_('settings_dialog_title', app_name='')}"
        )
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(title_label)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #404040;
            }
            QTabBar::tab {
                padding: 12px 20px;
                margin-right: 2px;
                background-color: #2d2d2d;
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #cccccc;
                font-size: 11px;
                font-weight: normal;
            }
            QTabBar::tab:selected {
                background-color: #404040;
                color: #ffffff;
                font-weight: bold;
                border-bottom: 2px solid #404040;
            }
            QTabBar::tab:hover:!selected {
                background-color: #353535;
                color: #ffffff;
            }
        """)

        # General settings tab
        self.general_tab = GeneralSettingsWidget(
            self.settings_manager, self.theme_manager
        )
        self.tab_widget.addTab(self.general_tab, f"⚙️ {_('settings_general')}")

        # NTP settings tab
        self.ntp_tab = NTPSettingsWidget(self.settings_manager)
        self.tab_widget.addTab(self.ntp_tab, f"🌐 {_('settings_time_sync')}")

        # Holiday settings tab REMOVED - was causing translation issues

        layout.addWidget(self.tab_widget)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.setStyleSheet("QPushButton { min-width: 80px; padding: 6px; }")

        # Localize button texts
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText(_("button_ok"))

        self.cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        self.cancel_button.setText(_("button_cancel"))

        self.apply_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Apply
        )
        self.apply_button.setText(_("button_apply"))

        self.button_box.accepted.connect(self._accept)
        self.button_box.rejected.connect(self.reject)
        self.apply_button.clicked.connect(self._apply)

        layout.addWidget(self.button_box)

    def _accept(self):
        """✅ Accept and save settings."""
        if self._save_all_settings():
            self.settings_changed.emit()
            self.accept()

    def _apply(self):
        """✅ Apply settings without closing."""
        if self._save_all_settings():
            self.settings_changed.emit()

    def _save_all_settings(self) -> bool:
        """💾 Save all settings from all tabs."""
        try:
            success = True

            # Save general settings
            if not self.general_tab.save_settings():
                success = False

            # Save NTP settings
            if not self.ntp_tab.save_settings():
                success = False

            # Holiday settings tab removed

            if success:
                logger.debug("✅ All settings saved successfully")
            else:
                QMessageBox.warning(
                    self,
                    f"⚠️ {_('warning_settings_warning')}",
                    _("warning_some_settings_not_saved"),
                )

            return success

        except Exception as e:
            logger.error(f"❌ Failed to save settings: {e}")
            QMessageBox.critical(
                self,
                f"❌ {_('error_settings_error')}",
                f"{_('error_failed_to_save_settings')}\n{str(e)}",
            )
            return False

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update window title
            self.setWindowTitle(
                f"{UI_EMOJIS['settings']} "
                f"{_('settings_dialog_title', app_name=_('app_name'))}"
            )

            # Update tab names
            self.tab_widget.setTabText(0, f"⚙️ {_('settings_general')}")
            self.tab_widget.setTabText(1, f"🌐 {_('settings_time_sync')}")

            # Update button texts
            if hasattr(self, "ok_button") and self.ok_button:
                self.ok_button.setText(_("button_ok"))

            if hasattr(self, "cancel_button") and self.cancel_button:
                self.cancel_button.setText(_("button_cancel"))

            if hasattr(self, "apply_button") and self.apply_button:
                self.apply_button.setText(_("button_apply"))

            # Refresh individual tabs
            if hasattr(self.general_tab, "refresh_ui_text"):
                self.general_tab.refresh_ui_text()
            if hasattr(self.ntp_tab, "refresh_ui_text"):
                self.ntp_tab.refresh_ui_text()
            # Holiday tab removed

            logger.debug("🔄 Settings dialog UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh settings dialog UI text: {e}")
