"""
ℹ️ About Dialog for Calendar Application

This module contains the about dialog with application information.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap

from version import (
    APP_ICON,
    APP_NAME,
    __version__,
    __author__,
    __copyright__,
    __license__,
)
from calendar_app.localization import get_i18n_manager
from calendar_app.shared.resources import find_qt_window_icon_path

logger = logging.getLogger(__name__)

# Size (px) of the real app icon shown in the About header.
_ABOUT_ICON_PX = 64


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that always uses current locale."""
    default = kwargs.pop("default", None)
    try:
        return get_i18n_manager().get_text(key, **kwargs)
    except Exception:
        return default if default is not None else key


class AboutDialog(QDialog):
    """ℹ️ About dialog with application information."""

    def __init__(self, parent=None):
        """Initialize about dialog."""
        super().__init__(parent)

        self._setup_ui()

        logger.debug("ℹ️ About dialog initialized")

    def _setup_ui(self):
        """🏗️ Setup about dialog UI."""
        # Use the working approach from the old version but with translation support
        app_name = APP_NAME
        self.setWindowTitle(_("about_dialog_title").format(app_name=app_name))
        self.setModal(True)
        self.setFixedSize(500, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # App icon: use the real application icon, falling back to the emoji
        # glyph only if the icon file cannot be found.
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(80, 80)
        icon_path = find_qt_window_icon_path()
        pixmap = (
            QIcon(str(icon_path)).pixmap(_ABOUT_ICON_PX, _ABOUT_ICON_PX)
            if icon_path is not None
            else QPixmap()
        )
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText(APP_ICON)
            from calendar_app.utils.font_manager import get_emoji_font

            icon_label.setFont(get_emoji_font(48))
        header_layout.addWidget(icon_label)

        # Title and version
        title_layout = QVBoxLayout()

        title_label = QLabel(APP_NAME)
        from calendar_app.utils.font_manager import get_ui_font

        title_label.setFont(get_ui_font(18, QFont.Weight.Bold))
        title_layout.addWidget(title_label)

        version_label = QLabel(f"Version {__version__}")
        version_label.setFont(get_ui_font(12))
        version_label.setProperty("class", "secondary")
        title_layout.addWidget(version_label)

        description_label = QLabel(_("app_description"))
        description_label.setFont(get_ui_font(10))
        description_label.setProperty("class", "secondary")
        description_label.setWordWrap(True)
        title_layout.addWidget(description_label)

        title_layout.addStretch()
        header_layout.addLayout(title_layout, 1)

        layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Information sections
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        info_widget = QLabel()
        info_widget.setWordWrap(True)
        info_widget.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_widget.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        info_text = f"""
<h3>{_('about_features')}</h3>
<ul>
<li><b>{_('feature_analog_clock')}</b></li>
<li><b>{_('feature_calendar_view')}</b></li>
<li><b>{_('feature_international_holidays')}</b></li>
<li><b>{_('feature_event_management')}</b></li>
<li><b>{_('feature_note_taking')}</b></li>
<li><b>{_('feature_ntp_sync')}</b></li>
<li><b>{_('feature_themes')}</b></li>
<li><b>{_('feature_import_export')}</b></li>
<li><b>{_('feature_data_persistence')}</b></li>
<li><b>{_('feature_cross_platform')}</b></li>
</ul>

<h3>{_('about_technical_details')}</h3>
<ul>
<li><b>{_('tech_framework')}</b> {_('tech_framework_value')}</li>
<li><b>{_('tech_language')}</b> {_('tech_language_value')}</li>
<li><b>{_('tech_architecture')}</b> {_('tech_architecture_value')}</li>
<li><b>{_('tech_database')}</b> {_('tech_database_value')}</li>
<li><b>{_('tech_notes_storage')}</b> {_('tech_notes_storage_value')}</li>
<li><b>{_('tech_time_sync')}</b> {_('tech_time_sync_value')}</li>
<li><b>{_('tech_themes')}</b> {_('tech_themes_value')}</li>
</ul>

<h3>{_('about_system_requirements')}</h3>
<ul>
<li><b>{_('sys_python')}</b> {_('sys_python_value')}</li>
<li><b>{_('sys_memory')}</b> {_('sys_memory_value')}</li>
<li><b>{_('sys_storage')}</b> {_('sys_storage_value')}</li>
<li><b>{_('sys_display')}</b> {_('sys_display_value')}</li>
<li><b>{_('sys_network')}</b> {_('sys_network_value')}</li>
</ul>

<h3>{_('about_keyboard_shortcuts')}</h3>
<ul>
<li><b>Ctrl+T:</b> {_('shortcut_today')}</li>
<li><b>Ctrl+I:</b> {_('shortcut_import')}</li>
<li><b>Ctrl+E:</b> {_('shortcut_export')}</li>
<li><b>Ctrl+,:</b> {_('shortcut_settings')}</li>
<li><b>Ctrl+Q:</b> {_('shortcut_exit')}</li>
</ul>

<h3>{_('about_libraries_used')}</h3>
<ul>
<li><b>PySide6:</b> {_('lib_pyside6')}</li>
<li><b>ntplib:</b> {_('lib_ntplib')}</li>
<li><b>python-dateutil:</b> {_('lib_dateutil')}</li>
<li><b>holidays:</b> {_('lib_holidays')}</li>
<li><b>icalendar:</b> {_('lib_icalendar')}</li>
</ul>

<h3>{_('about_license')}</h3>
<p><b>{__license__}</b></p>
<p>{__copyright__}</p>

<h3>{_('about_development')}</h3>
<p><b>{_('dev_author')}</b> {__author__}</p>
<p><b>{_('dev_testing')}</b> {_('dev_testing_value')}</p>
<p><b>{_('dev_built_with')}</b> {_('dev_built_with_value')}</p>

<h3>{_('about_support')}</h3>
<p>{_('support_text')}</p>

<h3>{_('about_acknowledgments')}</h3>
<p>{_('acknowledgments_text')}</p>
"""

        info_widget.setText(info_text)
        info_scroll.setWidget(info_widget)

        layout.addWidget(info_scroll, 1)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton(_("close"))
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def showEvent(self, event):
        """📺 Handle show event."""
        super().showEvent(event)

        # Center the dialog on parent
        from PySide6.QtWidgets import QWidget

        parent_widget = self.parent()
        if parent_widget and isinstance(parent_widget, QWidget):
            parent_geometry = parent_widget.geometry()
            dialog_geometry = self.geometry()

            x = (
                parent_geometry.x()
                + (parent_geometry.width() - dialog_geometry.width()) // 2
            )
            y = (
                parent_geometry.y()
                + (parent_geometry.height() - dialog_geometry.height()) // 2
            )

            self.move(x, y)

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update window title
            app_name = APP_NAME
            self.setWindowTitle(_("about_dialog_title").format(app_name=app_name))

            # If dialog is visible, close it to avoid layout conflicts
            # The user can reopen it to see the new translations
            if self.isVisible():
                logger.debug(
                    "🔄 Closing visible about dialog to avoid layout conflicts"
                )
                self.close()
                return

            # If dialog is not visible, we can safely rebuild it
            # Clear existing layout and rebuild UI with new translations
            if self.layout():
                # Remove all widgets from the layout
                while self.layout().count():
                    child = self.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                    elif child.layout():
                        self._clear_layout(child.layout())

                # Delete the layout
                self.layout().deleteLater()

            # Rebuild the UI with new translations
            self._setup_ui()

            logger.debug("🔄 About dialog UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh about dialog UI text: {e}")
            # Fallback if translation fails
            try:
                self.setWindowTitle("ℹ️ About Calendar Application")
            except Exception:
                pass

    def _clear_layout(self, layout):
        """🧹 Recursively clear a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
