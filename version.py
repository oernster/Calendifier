"""
📅 Calendar Application Version Information

This module contains version information and emoji constants used across the app.
The single source of truth for the version is the ``VERSION`` file at the repo root;
nothing here hardcodes a release number.
"""

import sys
from pathlib import Path

# Sentinel used when the VERSION file cannot be located (e.g. partial checkout).
_DEV_VERSION = "0.0.0-dev"


def _read_version() -> str:
    """Read the version string from the root VERSION file (frozen-aware)."""
    candidates = []
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / "VERSION")
    candidates.append(Path(__file__).resolve().parent / "VERSION")
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return text
    return _DEV_VERSION  # pragma: no cover - VERSION is always present in real builds


def _parse_version_info(version: str) -> tuple:
    """Turn '1.7.0' (or '1.7.0-dev') into a (major, minor, patch) tuple."""
    parts = []
    for component in version.split("-")[0].split(".")[:3]:
        try:
            parts.append(int(component))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


__version__ = _read_version()
__version_info__ = _parse_version_info(__version__)
__app_name__ = "📅 Calendifier"
__author__ = "Oliver Ernster"
__description__ = (
    "Cross-platform calendar system with Home Assistant integration, "
    "analog clock, event handling, note taking, and holidays"
)
__copyright__ = "© 2026 Oliver Ernster"
__license__ = "LGPL-3.0"

# 📦 Packaging identity (consumed by the build scripts and the bespoke installer).
# Plain display name without the emoji, for exe/registry/shortcut/bundle naming.
APP_NAME = "Calendifier"
# Previous per-user data folder name; kept equal as there is no rename to migrate.
LEGACY_APP_NAME = "Calendifier"
APP_AUTHOR = __author__
APP_COPYRIGHT = __copyright__
# Stable Windows AppUserModelID for taskbar grouping / pinned-icon identity.
APP_APPUSERMODELID = "com.oliverernster.calendifier"

# 📅 Application metadata
APP_ICON = "📅"
CLOCK_ICON = "🕐"
SETTINGS_ICON = "⚙️"
THEME_DARK_ICON = "🌙"
THEME_LIGHT_ICON = "☀️"

# 🌐 NTP Configuration
DEFAULT_NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.windows.com",
    "time.apple.com",
]

# 🇬🇧 UK Holiday Configuration
HOLIDAY_COUNTRY = "UK"
HOLIDAY_ICON = "🇬🇧"

# 🎨 UI element emojis
UI_EMOJIS = {
    # 🏠 Main application
    "app_icon": "📅",
    "window_title": "📅",
    # 🕐 Time components
    "clock": "🕐",
    "time_display": "🕐",
    "ntp_status": "🌐",
    "sync_success": "✅",
    "sync_failed": "❌",
    # 📅 Calendar components
    "calendar": "📅",
    "today": "📅",
    "weekend": "🏖️",
    "holiday": "🇬🇧",
    "navigation_prev": "◀",
    "navigation_next": "▶",
    # 📝 Event management
    "event": "📝",
    "add_event": "➕",
    "edit_event": "✏️",
    "delete_event": "🗑️",
    "event_work": "💼",
    "event_meeting": "👥",
    "event_meal": "🍽️",
    "event_personal": "🏠",
    # 🎨 Theme and settings
    "theme_dark": "🌙",
    "theme_light": "☀️",
    "settings": "⚙️",
    "about": "ℹ️",
    # 📤📥 Import/Export
    "export": "📤",
    "import": "📥",
    "file": "📄",
    # 🔧 Status indicators
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
}

# Event category emoji system
EVENT_CATEGORY_EMOJIS = {
    "work": "💼",
    "meeting": "👥",
    "personal": "🏠",
    "meal": "🍽️",
    "travel": "🚗",
    "health": "🏥",
    "education": "📚",
    "celebration": "🎉",
    "reminder": "🎯",
    "holiday": "🇬🇧",
    "default": "📝",
}

# Status and feedback emojis
STATUS_EMOJIS = {
    # 🌐 Network status
    "ntp_connected": "✅",
    "ntp_disconnected": "❌",
    "ntp_syncing": "⏳",
    # 💾 Database status
    "db_connected": "✅",
    "db_error": "❌",
    "db_saving": "💾",
    # 📁 File operations
    "file_saved": "✅",
    "file_error": "❌",
    "file_loading": "⏳",
    # 🎨 Theme status
    "theme_applied": "✅",
    "theme_error": "❌",
}


def get_version_string() -> str:
    """Get formatted version string for display."""
    return f"📅 Calendar Application v{__version__}"


def get_about_text() -> str:
    """Get formatted about text for dialog."""
    return f"""
{APP_ICON} {__app_name__}
Version: {__version__}
{__description__}

🏠 Home Assistant Integration Available
🖥️ Desktop Application Mode
🌐 40 Languages & 40 Countries Supported

{__copyright__}
License: {__license__}

Author: {__author__}
Testing: Ramon Rodriguez

Built with FastAPI, Home Assistant & Python
Deploy as web dashboard or desktop application
"""
