#!/usr/bin/env python3
"""
📅 Calendar Application - Main Entry Point

A comprehensive calendar application with analog clock, event management,
UK holidays, NTP time synchronization, and dark/light themes.

Author: Calendar App Team
License: MIT
"""

import sys
import os
import io
import logging
from pathlib import Path
from typing import Optional


def _make_windowed_streams_safe() -> None:
    """Make stdout/stderr safe for windowed (no-console) frozen builds.

    A PyInstaller ``--windowed`` build has ``sys.stdout``/``sys.stderr`` set to
    ``None``, so the first log or print at startup raises and the app dies
    silently. Wrap them in a UTF-8 stream (or /dev/null) BEFORE anything writes.
    """
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    if not getattr(sys, "frozen", False):
        return
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        try:
            if stream is None or not hasattr(stream, "buffer"):
                raise AttributeError
            setattr(
                sys,
                name,
                io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="ignore"),
            )
        except (AttributeError, ValueError, OSError):
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


_make_windowed_streams_safe()

# Suppress Qt font warnings BEFORE importing Qt
os.environ["QT_LOGGING_RULES"] = (
    "qt.text.font.db=false;qt.text.font.db.debug=false;qt.text.font.db.warning=false"
)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402
from PySide6.QtCore import QTimer, QThread, Signal, QObject  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402

# Import application components
from version import __version__, UI_EMOJIS  # noqa: E402
from calendar_app.data.database import DatabaseManager  # noqa: E402
from calendar_app.core.event_manager import EventManager  # noqa: E402
from calendar_app.core.calendar_manager import CalendarManager  # noqa: E402
from calendar_app.core.multi_country_holiday_provider import (  # noqa: E402
    MultiCountryHolidayProvider,
)
from calendar_app.utils.ntp_client import NTPClient  # noqa: E402
from calendar_app.config.settings import SettingsManager  # noqa: E402
from calendar_app.config.themes import ThemeManager  # noqa: E402
from calendar_app.ui.main_window import MainWindow  # noqa: E402
from calendar_app.localization import (  # noqa: E402
    I18nManager,
    set_locale,
    LocaleDetector,
)


# CRITICAL: Set locale IMMEDIATELY at import time
def _initialize_startup_locale():
    """Initialize locale before any UI creation."""
    try:
        from calendar_app.config.settings import SettingsManager
        from pathlib import Path

        # Get settings file path
        app_data_dir = Path.home() / ".calendar_app"
        settings_file = app_data_dir / "settings.json"

        # Create temporary settings manager to get saved locale
        temp_settings = SettingsManager(settings_file)
        saved_locale = temp_settings.get_locale()

        # Set the locale immediately and force reload
        set_locale(saved_locale)

        # Force reload the I18n manager to ensure latest translations
        from calendar_app.localization.i18n_manager import get_i18n_manager

        manager = get_i18n_manager()
        manager.reload_translations()

        logging.debug(f"🌍 Early locale initialization: {saved_locale}")
        translation_obj = manager.translations.get(saved_locale)
        if translation_obj:
            logging.debug(f"🌍 Loaded translations for {saved_locale}")
        else:
            logging.debug(f"🌍 No translations found for {saved_locale}")

    except Exception as e:
        logging.warning(f"⚠️ Early locale initialization failed: {e}")
        set_locale("en_GB")  # Use en_GB as fallback to match our default settings


# Initialize locale immediately
_initialize_startup_locale()


class ApplicationInitializer(QObject):
    """Handles application initialization in a separate thread."""

    initialization_complete = Signal(bool, str)  # success, message
    progress_update = Signal(str)  # status message

    def __init__(self):
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.settings_manager: Optional[SettingsManager] = None
        self.theme_manager: Optional[ThemeManager] = None
        self.event_manager: Optional[EventManager] = None
        self.calendar_manager: Optional[CalendarManager] = None
        self.holiday_provider: Optional[MultiCountryHolidayProvider] = None
        self.ntp_client: Optional[NTPClient] = None
        self.i18n_manager: Optional[I18nManager] = None

    def initialize(self):
        """Initialize all application components."""
        try:
            # Get application data directory
            app_data_dir = Path.home() / ".calendar_app"

            # Step 1: Initialize settings
            self.progress_update.emit(
                f"{UI_EMOJIS['settings']} Initializing settings..."
            )
            settings_file = app_data_dir / "settings.json"
            self.settings_manager = SettingsManager(settings_file)

            # Step 2: Initialize localization FIRST
            self.progress_update.emit(
                f"{UI_EMOJIS['loading']} Initializing localization..."
            )
            saved_locale = self.settings_manager.get_locale()
            if (
                not saved_locale or saved_locale == "en_GB"
            ):  # If no saved locale or default
                # Detect system locale
                locale_detector = LocaleDetector()
                detected_locale = locale_detector.detect_system_locale()
                if (
                    detected_locale != "en_GB"
                ):  # If system locale is different from default
                    saved_locale = detected_locale
                    self.settings_manager.set_locale(
                        saved_locale
                    )  # Save the detected locale

            # Set the global locale IMMEDIATELY before creating any UI
            set_locale(saved_locale)

            # Use the existing global I18n manager instead of creating a new one
            from calendar_app.localization.i18n_manager import get_i18n_manager

            self.i18n_manager = get_i18n_manager()

            # Ensure the global manager is using the correct locale
            self.i18n_manager.set_locale(saved_locale)
            self.i18n_manager.reload_translations()

            logging.debug(f"🌍 Set startup locale to: {saved_locale}")

            # Step 3: Initialize theme manager
            self.progress_update.emit(f"{UI_EMOJIS['theme_dark']} Loading themes...")
            self.theme_manager = ThemeManager()

            # Step 4: Initialize database
            self.progress_update.emit(f"{UI_EMOJIS['loading']} Setting up database...")
            db_path = app_data_dir / "data" / "calendar.db"
            self.db_manager = DatabaseManager(db_path)

            # Step 5: Initialize core managers
            self.progress_update.emit(
                f"{UI_EMOJIS['event']} Initializing event manager..."
            )
            self.event_manager = EventManager(str(db_path))

            self.progress_update.emit(
                f"{UI_EMOJIS['holiday']} Loading holiday provider..."
            )
            # Resolve the holiday region (an explicit country, or "auto" which
            # derives it from the selected timezone, then locale, then GB).
            holiday_country = self.settings_manager.get_effective_holiday_country()
            self.holiday_provider = MultiCountryHolidayProvider(holiday_country)

            self.progress_update.emit(
                f"{UI_EMOJIS['calendar']} Initializing calendar manager..."
            )
            self.calendar_manager = CalendarManager(
                self.event_manager, self.holiday_provider
            )

            # Step 6: Initialize NTP client
            self.progress_update.emit(
                f"{UI_EMOJIS['ntp_status']} Initializing time synchronization..."
            )
            self.ntp_client = NTPClient()

            self.progress_update.emit(
                f"{UI_EMOJIS['success']} Initialization complete!"
            )
            self.initialization_complete.emit(
                True, "Application initialized successfully"
            )

        except Exception as e:
            error_msg = f"Failed to initialize application: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.initialization_complete.emit(False, error_msg)


class CalendarApplication(QApplication):
    """Main application class with dependency injection and lifecycle management."""

    def __init__(self, argv):
        super().__init__(argv)

        # Set application metadata
        self.setApplicationName("Calendar Application")
        self.setApplicationVersion(__version__)
        self.setOrganizationName("Calendar App Team")
        self.setOrganizationDomain("calendar-app.local")

        # Configure logging
        self._setup_logging()

        # Application components
        self.main_window: Optional[MainWindow] = None
        self.splash = None
        self.initializer: Optional[ApplicationInitializer] = None
        self.init_thread: Optional[QThread] = None

        # Managers (will be injected from initializer)
        self.db_manager: Optional[DatabaseManager] = None
        self.settings_manager: Optional[SettingsManager] = None
        self.theme_manager: Optional[ThemeManager] = None
        self.event_manager: Optional[EventManager] = None
        self.calendar_manager: Optional[CalendarManager] = None
        self.holiday_provider: Optional[MultiCountryHolidayProvider] = None
        self.ntp_client: Optional[NTPClient] = None
        self.i18n_manager: Optional[I18nManager] = None

        # Show the splash FIRST, before the icon/taskbar/style setup. The first
        # top-level window a process shows pays a one-time window-system
        # initialisation cost, so showing the splash first makes it appear as
        # early as possible and absorbs that cost while the rest initialises.
        self._show_splash()

        # Setup application (icon, taskbar, style) while the splash is visible.
        self._setup_application()

    def _show_splash(self):
        """🪟 Create and show the startup splash screen."""
        try:
            from calendar_app.ui.splash import make_splash

            self.splash = make_splash()
            self.splash.show()
            # Force an immediate paint so the splash is visible right away
            # rather than only after the next event-loop iteration.
            self.splash.repaint()
            self.processEvents()
        except Exception as e:
            logging.warning(f"Could not show splash screen: {e}")
            self.splash = None

    def _setup_logging(self):
        """Configure application logging."""
        log_dir = Path.home() / ".calendar_app" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "calendar_app.log"

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # The log file captures full INFO detail; the console stays quiet
        # (WARNING and above) so day-to-day runs are not flooded. Raise console
        # verbosity with CALENDIFIER_LOG_LEVEL=INFO (or DEBUG) when diagnosing.
        console_level_name = os.environ.get("CALENDIFIER_LOG_LEVEL", "WARNING").upper()
        console_level = getattr(logging, console_level_name, logging.WARNING)

        # Create file handler with UTF-8 encoding
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

        # Create console handler with UTF-8 encoding and error handling
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)

        # Only add console handler if the console encoding can represent the
        # emoji used in log messages. Probe by encoding, not by writing to
        # stdout (writing here would print a stray character before any logs).
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            "📅".encode(encoding)
            root_logger.addHandler(console_handler)
        except (UnicodeEncodeError, LookupError):
            # Console can't handle Unicode, create a safe console handler
            import io

            safe_console_handler = logging.StreamHandler(
                io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            )
            safe_console_handler.setFormatter(console_formatter)
            safe_console_handler.setLevel(console_level)
            root_logger.addHandler(safe_console_handler)

        logger = logging.getLogger(__name__)
        logger.info(
            f"{UI_EMOJIS['app_icon']} Starting Calendar Application v{__version__}"
        )

    def _setup_application(self):
        """Setup application properties and styling."""
        # Set Windows-specific properties for proper taskbar icon
        self._setup_windows_taskbar()

        # Set application icon
        self._set_application_icon()

        # Set application style
        self.setStyle("Fusion")  # Modern cross-platform style

        # Handle application quit
        self.aboutToQuit.connect(self._cleanup)

    def _setup_windows_taskbar(self):
        """🪟 Setup Windows-specific taskbar properties."""
        try:
            import platform

            if platform.system() == "Windows":
                # Set Application User Model ID to separate from Python
                import ctypes

                # Define the AppUserModelID
                app_id = f"CalendarApp.Desktop.Calendar.{__version__}"

                # Set the AppUserModelID
                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                        app_id
                    )
                    logging.info(f"🪟 Windows AppUserModelID set: {app_id}")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to set AppUserModelID: {e}")

        except Exception as e:
            logging.warning(f"⚠️ Failed to setup Windows taskbar properties: {e}")

    def _set_application_icon(self):
        """📅 Set application icon for taskbar."""
        try:
            from PySide6.QtGui import QPixmap, QPainter, QFont
            from PySide6.QtCore import Qt

            # Try to use the .ico file first (best for Windows taskbar)
            icon_path = project_root / "assets" / "calendar_icon.ico"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.setWindowIcon(icon)
                logging.info(f"📅 Application icon loaded from: {icon_path}")
                return

            # Fallback: create icon from emoji
            from version import APP_ICON

            # Create multiple sizes for better icon quality
            sizes = [16, 24, 32, 48, 64, 128, 256]
            icon = QIcon()

            for size in sizes:
                # Create a pixmap with the calendar emoji
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.GlobalColor.transparent)

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

                # Use a system font that supports emojis
                font = QFont()
                font.setFamily("Segoe UI Emoji")  # Windows emoji font
                font.setPixelSize(
                    int(size * 0.8)
                )  # Slightly smaller than the icon size
                painter.setFont(font)

                # Draw emoji centered
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, APP_ICON)
                painter.end()

                # Add this size to the icon
                icon.addPixmap(pixmap)

            # Set the icon for the entire application (this affects taskbar)
            self.setWindowIcon(icon)

            logging.info(f"📅 Application icon created with calendar emoji: {APP_ICON}")

        except Exception as e:
            logging.warning(f"⚠️ Failed to set application icon: {e}")
            # Fallback: try to set a simple icon
            try:
                from PySide6.QtGui import QPixmap
                from PySide6.QtCore import Qt

                # Create a simple colored square as fallback
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.blue)
                icon = QIcon(pixmap)
                self.setWindowIcon(icon)
            except Exception:
                pass

    def initialize_async(self):
        """Initialize application components asynchronously."""
        logging.info(f"{UI_EMOJIS['loading']} Starting asynchronous initialization...")

        # Create initializer and thread
        self.initializer = ApplicationInitializer()
        self.init_thread = QThread()

        # Move initializer to thread
        self.initializer.moveToThread(self.init_thread)

        # Connect signals
        self.init_thread.started.connect(self.initializer.initialize)
        self.initializer.initialization_complete.connect(
            self._on_initialization_complete
        )
        self.initializer.progress_update.connect(self._on_progress_update)

        # Start initialization
        self.init_thread.start()

    def _on_progress_update(self, message: str):
        """Handle initialization progress updates."""
        logging.info(message)
        if self.splash is not None:
            from calendar_app.ui.splash import splash_message

            splash_message(self.splash, message)
            self.processEvents()

    def _on_initialization_complete(self, success: bool, message: str):
        """Handle initialization completion."""
        if success:
            logging.info(f"{UI_EMOJIS['success']} {message}")
            self._inject_dependencies()
            self._create_main_window()
        else:
            logging.error(f"{UI_EMOJIS['error']} {message}")
            self._show_error_and_exit(message)

        # Clean up initialization thread
        if self.init_thread:
            self.init_thread.quit()
            self.init_thread.wait()
            self.init_thread = None

    def _inject_dependencies(self):
        """Inject dependencies from initializer to application."""
        if not self.initializer:
            return

        self.db_manager = self.initializer.db_manager
        self.settings_manager = self.initializer.settings_manager
        self.theme_manager = self.initializer.theme_manager
        self.event_manager = self.initializer.event_manager
        self.calendar_manager = self.initializer.calendar_manager
        self.holiday_provider = self.initializer.holiday_provider
        self.ntp_client = self.initializer.ntp_client
        self.i18n_manager = self.initializer.i18n_manager

    def _create_main_window(self):
        """Create and show the main application window."""
        try:
            logging.info(f"{UI_EMOJIS['app_icon']} Creating main window...")

            # Ensure we have valid managers
            if not self.settings_manager or not self.theme_manager:
                raise Exception("Required managers not initialized")

            # Create main window with dependency injection
            self.main_window = MainWindow(
                settings_manager=self.settings_manager, theme_manager=self.theme_manager
            )

            # Inject dependencies into components after main window is created
            self._inject_component_dependencies()

            # Apply initial theme
            if self.theme_manager:
                qss = self.theme_manager.generate_qss_stylesheet()
                self.setStyleSheet(qss)

            # Show main window
            self.main_window.show()

            # Close the splash now that the window is up.
            if self.splash is not None:
                self.splash.finish(self.main_window)
                self.splash = None

            # Start periodic updates
            self._start_periodic_updates()

            logging.info(f"{UI_EMOJIS['success']} Application ready!")

        except Exception as e:
            error_msg = f"Failed to create main window: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self._show_error_and_exit(error_msg)

    def _inject_component_dependencies(self):
        """Inject dependencies into main window components."""
        if not self.main_window:
            return

        # Get component references
        try:
            clock_widget = self.main_window.get_clock_widget()
            calendar_widget = self.main_window.get_calendar_widget()
            self.main_window.get_event_panel()
        except Exception as e:
            logging.error(f"Failed to get component references: {e}")
            return

        # Inject calendar manager into calendar widget via main window
        try:
            if self.main_window and self.calendar_manager:
                if hasattr(self.main_window, "set_calendar_manager"):
                    self.main_window.set_calendar_manager(self.calendar_manager)
                    logging.debug(
                        "✅ Injected calendar manager and applied all "
                        "settings via main window"
                    )
        except Exception as e:
            logging.warning(f"⚠️ Failed to inject calendar manager: {e}")

        # Inject event manager into event panel via main window
        try:
            if self.main_window and self.event_manager:
                if hasattr(self.main_window, "set_event_manager"):
                    self.main_window.set_event_manager(self.event_manager)
                    logging.debug(
                        "✅ Injected event manager into event panel via main window"
                    )
        except Exception as e:
            logging.warning(f"⚠️ Failed to inject event manager: {e}")

        # Inject holiday provider into main window for locale-aware translations
        try:
            if self.main_window and self.holiday_provider:
                if hasattr(self.main_window, "set_holiday_provider"):
                    self.main_window.set_holiday_provider(self.holiday_provider)
                    logging.debug("✅ Injected holiday provider into main window")

                # CRITICAL FIX: Force locale refresh after app is fully initialized
                # This ensures holidays are displayed in the correct language
                # from startup
                self.holiday_provider.force_locale_refresh()
                logging.debug(
                    "✅ Forced holiday provider locale refresh after app initialization"
                )

                # NUITKA FIX: Treat compiled executable launch like a locale switch
                # This ensures holidays library data is properly loaded in
                # compiled environment
                import sys

                if getattr(sys, "frozen", False):
                    logging.debug(
                        "🔥 Detected Nuitka compiled environment - "
                        "performing additional holiday refresh"
                    )
                    # Add a small delay to ensure all systems are ready
                    QTimer.singleShot(500, lambda: self._nuitka_holiday_refresh())

                # Also refresh the calendar widget to show translated holidays
                calendar_widget = self.main_window.get_calendar_widget()
                if calendar_widget and hasattr(calendar_widget, "refresh_calendar"):
                    calendar_widget.refresh_calendar()
                    logging.debug(
                        "✅ Refreshed calendar widget to show translated holidays"
                    )
        except Exception as e:
            logging.warning(f"⚠️ Failed to inject holiday provider: {e}")

        # Inject NTP client into clock widget with TimeManager
        try:
            if clock_widget and self.ntp_client:
                from calendar_app.utils.ntp_client import TimeManager

                time_manager = TimeManager()
                clock_widget.set_time_manager(time_manager)
                clock_widget.set_ntp_client(self.ntp_client)
                logging.debug(
                    "✅ Injected NTP client and time manager into clock widget"
                )
        except Exception as e:
            logging.warning(f"⚠️ Failed to inject NTP client: {e}")

    def _nuitka_holiday_refresh(self):
        """🔥 Special holiday refresh for Nuitka compiled environments."""
        try:
            if self.holiday_provider:
                logging.debug("🔥 Performing Nuitka-specific holiday provider refresh")
                # Clear cache and force complete reload
                self.holiday_provider.clear_cache()
                self.holiday_provider.force_locale_refresh()

                # Refresh calendar widget to show updated holidays
                if self.main_window:
                    calendar_widget = self.main_window.get_calendar_widget()
                    if calendar_widget and hasattr(calendar_widget, "refresh_calendar"):
                        calendar_widget.refresh_calendar()
                        logging.debug(
                            "✅ Nuitka holiday refresh completed - calendar updated"
                        )
        except Exception as e:
            logging.warning(f"⚠️ Nuitka holiday refresh failed: {e}")

    def _start_periodic_updates(self):
        """Start periodic background updates."""
        # NTP sync timer (every 30 minutes)
        if self.ntp_client:
            ntp_timer = QTimer()
            ntp_timer.timeout.connect(lambda: self._sync_ntp_safe())
            ntp_timer.start(30 * 60 * 1000)  # 30 minutes

            # Initial sync
            QTimer.singleShot(1000, self._sync_ntp_safe)  # Delay initial sync

        # Holiday cache clear timer (daily at midnight)
        if self.holiday_provider:
            holiday_timer = QTimer()
            holiday_timer.timeout.connect(self.holiday_provider.clear_cache)
            holiday_timer.start(24 * 60 * 60 * 1000)  # 24 hours

    def _sync_ntp_safe(self):
        """🌐 Safely sync NTP time without async issues."""
        if self.ntp_client:
            try:
                # Use synchronous NTP sync
                result = self.ntp_client.sync_time()

                # Update clock widget with NTP status
                if self.main_window:
                    clock_widget = self.main_window.get_clock_widget()
                    if clock_widget:
                        clock_widget.update_ntp_status(result)

                if result.success:
                    logging.debug(
                        f"✅ NTP sync successful: {result.server} "
                        f"(offset: {result.offset:.3f}s)"
                    )
                else:
                    logging.warning(f"⚠️ NTP sync failed: {result.error}")

            except Exception as e:
                logging.warning(f"⚠️ NTP sync failed: {e}")

    def _show_error_and_exit(self, message: str):
        """Show error message and exit application."""
        QMessageBox.critical(
            None,
            f"{UI_EMOJIS['error']} Application Error",
            f"Failed to start Calendar Application:\n\n{message}\n\n"
            f"Please check the log file for more details.",
        )
        self.quit()

    def _cleanup(self):
        """Clean up resources before application exit."""
        logging.info(f"{UI_EMOJIS['loading']} Cleaning up application resources...")

        try:
            # Settings are auto-saved, no explicit save needed

            # Close database connections
            if self.db_manager:
                # Database connections are handled automatically
                pass

            # Clean up threads
            if self.init_thread and self.init_thread.isRunning():
                self.init_thread.quit()
                self.init_thread.wait()

            logging.info(f"{UI_EMOJIS['success']} Cleanup complete")

        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}", exc_info=True)


def setup_environment():
    """Setup application environment and directories."""
    # Create application data directory
    app_data_dir = Path.home() / ".calendar_app"
    app_data_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (app_data_dir / "data").mkdir(exist_ok=True)
    (app_data_dir / "logs").mkdir(exist_ok=True)
    (app_data_dir / "exports").mkdir(exist_ok=True)
    (app_data_dir / "backups").mkdir(exist_ok=True)

    # Set environment variables
    os.environ["CALENDAR_APP_DATA_DIR"] = str(app_data_dir)


def main():
    """Main application entry point."""
    try:
        # Setup environment
        setup_environment()

        # Create application
        app = CalendarApplication(sys.argv)

        # Handle high DPI displays
        from PySide6.QtCore import Qt

        # These attributes are deprecated in Qt6 and enabled by default
        # Only set them for Qt5 compatibility if needed
        try:
            from PySide6.QtCore import QT_VERSION_STR

            qt_version = int(QT_VERSION_STR.split(".")[0])
            if qt_version < 6:
                # Only set for Qt5
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            # Qt6 has these enabled by default, no need to set them
        except Exception:
            # If we can't determine Qt version, skip setting these attributes
            pass

        # Initialize application asynchronously
        app.initialize_async()

        # Run application event loop
        exit_code = app.exec()

        logging.info(
            f"{UI_EMOJIS['app_icon']} Application exited with code {exit_code}"
        )
        return exit_code

    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"{UI_EMOJIS['error']} Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
