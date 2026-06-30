"""
📊 Data models for Calendar Application

This module defines the data structures used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional, List, Dict, Any
import json
from version import EVENT_CATEGORY_EMOJIS


@dataclass
class Event:
    """📝 Enhanced Event data model with RRULE support."""

    # Core event fields
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None
    is_all_day: bool = False
    category: str = "default"
    color: str = "#0078d4"

    # RRULE-based recurrence
    is_recurring: bool = False
    rrule: Optional[str] = None  # Full RRULE string (RFC 5545)
    recurrence_id: Optional[str] = None  # For identifying specific occurrences
    exception_dates: List[date] = field(default_factory=list)  # EXDATE equivalent
    recurrence_master_id: Optional[int] = None  # Link to master recurring event

    # Legacy recurrence (deprecated, for migration)
    recurrence_pattern: Optional[str] = None  # Will be removed after migration
    recurrence_end_date: Optional[date] = None  # Will be removed after migration

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize computed fields after creation."""
        if self.start_date is None:
            self.start_date = date.today()
        if self.end_date is None:
            self.end_date = self.start_date
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """🔍 Validate event data and return list of errors."""
        errors = []

        if not self.title or not self.title.strip():
            errors.append("Title is required")

        if len(self.title) > 200:
            errors.append("Title must be 200 characters or less")

        if self.start_date is None:
            errors.append("Start date is required")

        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors.append("End date cannot be before start date")

        if (
            self.start_time
            and self.end_time
            and self.start_date == self.end_date
            and self.end_time <= self.start_time
        ):
            errors.append("End time must be after start time for same-day events")

        if self.category not in EVENT_CATEGORY_EMOJIS:
            errors.append(f"Invalid category: {self.category}")

        # RRULE validation
        if self.is_recurring:
            if not self.rrule:
                errors.append("RRULE is required for recurring events")
            else:
                # Validate RRULE format
                if not self._validate_rrule():
                    errors.append("Invalid RRULE format")

        # Recurrence master validation
        if self.recurrence_master_id and not self.recurrence_id:
            errors.append("Recurrence ID required when master ID is set")

        # Legacy validation (deprecated)
        if self.is_recurring and not self.rrule and not self.recurrence_pattern:
            errors.append("Recurrence pattern or RRULE required for recurring events")

        return errors

    def _validate_rrule(self) -> bool:
        """Validate RRULE string format"""
        if not self.rrule:
            return True

        try:
            from calendar_app.core.rrule_parser import RRuleParser

            parser = RRuleParser()
            return parser.validate_rrule(self.rrule)
        except ImportError:  # pragma: no cover - rrule_parser ships with the app
            # Fallback basic validation
            return self.rrule.startswith("FREQ=")

    def is_occurrence(self) -> bool:
        """Check if this is a recurring event occurrence"""
        return self.recurrence_master_id is not None

    def is_master(self) -> bool:
        """Check if this is a master recurring event"""
        return self.is_recurring and self.recurrence_master_id is None

    def get_recurrence_description(self) -> str:
        """Get human-readable recurrence description"""
        if not self.is_recurring or not self.rrule:
            return ""

        try:
            from calendar_app.core.rrule_parser import RRuleParser

            parser = RRuleParser()
            return parser.get_human_readable_description(self.rrule)
        except ImportError:  # pragma: no cover - rrule_parser ships with the app
            return "Recurring event"

    def to_dict(self) -> Dict[str, Any]:
        """📋 Convert event to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_all_day": self.is_all_day,
            "category": self.category,
            "color": self.color,
            "is_recurring": self.is_recurring,
            "rrule": self.rrule,
            "recurrence_id": self.recurrence_id,
            "exception_dates": [d.isoformat() for d in self.exception_dates],
            "recurrence_master_id": self.recurrence_master_id,
            # Legacy fields (deprecated)
            "recurrence_pattern": self.recurrence_pattern,
            "recurrence_end_date": (
                self.recurrence_end_date.isoformat()
                if self.recurrence_end_date
                else None
            ),
            # Metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """📥 Create event from dictionary."""
        # Parse date/time fields
        start_date = (
            date.fromisoformat(data["start_date"]) if data.get("start_date") else None
        )
        start_time = (
            time.fromisoformat(data["start_time"]) if data.get("start_time") else None
        )
        end_date = (
            date.fromisoformat(data["end_date"]) if data.get("end_date") else None
        )
        end_time = (
            time.fromisoformat(data["end_time"]) if data.get("end_time") else None
        )

        # Parse exception dates
        exception_dates = []
        if data.get("exception_dates"):
            if isinstance(data["exception_dates"], str):
                # Handle JSON string
                try:
                    exception_list = json.loads(data["exception_dates"])
                    exception_dates = [date.fromisoformat(d) for d in exception_list]
                except (json.JSONDecodeError, ValueError):
                    pass
            elif isinstance(data["exception_dates"], list):
                # Handle list
                exception_dates = [
                    date.fromisoformat(d) for d in data["exception_dates"]
                ]

        # Parse legacy fields
        recurrence_end_date = (
            date.fromisoformat(data["recurrence_end_date"])
            if data.get("recurrence_end_date")
            else None
        )
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None
        )

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            is_all_day=data.get("is_all_day", False),
            category=data.get("category", "default"),
            color=data.get("color", "#0078d4"),
            is_recurring=data.get("is_recurring", False),
            rrule=data.get("rrule"),
            recurrence_id=data.get("recurrence_id"),
            exception_dates=exception_dates,
            recurrence_master_id=data.get("recurrence_master_id"),
            # Legacy fields
            recurrence_pattern=data.get("recurrence_pattern"),
            recurrence_end_date=recurrence_end_date,
            # Metadata
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_category_emoji(self) -> str:
        """🎨 Get emoji for event category."""
        return EVENT_CATEGORY_EMOJIS.get(
            self.category, EVENT_CATEGORY_EMOJIS["default"]
        )

    def get_display_title(self) -> str:
        """📝 Get title with category emoji and recurrence indicator."""
        emoji = self.get_category_emoji()
        title = self.title

        # Add recurrence indicator for master events
        if self.is_recurring and not self.is_occurrence():
            title += " 🔄"

        return f"{emoji} {title}"


@dataclass
class Holiday:
    """🌍 Multi-Country Holiday data model."""

    name: str
    date: date
    country_code: str = "GB"  # ISO 3166-1 alpha-2 country code
    type: str = "bank_holiday"  # 'bank_holiday', 'national_day', 'observance'
    description: Optional[str] = None
    is_observed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """📋 Convert holiday to dictionary."""
        return {
            "name": self.name,
            "date": self.date.isoformat(),
            "country_code": self.country_code,
            "type": self.type,
            "description": self.description,
            "is_observed": self.is_observed,
        }

    def get_display_name(self) -> str:
        """🌍 Get holiday name with country flag emoji."""
        from calendar_app.core.multi_country_holiday_provider import (
            MultiCountryHolidayProvider,
        )

        countries = MultiCountryHolidayProvider.get_supported_countries()
        country_info = countries.get(
            self.country_code, {"flag": "🏳️", "name": "Unknown"}
        )
        return f"{country_info['flag']} {self.name}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Holiday":
        """📥 Create holiday from dictionary."""
        holiday_date = (
            date.fromisoformat(data["date"]) if data.get("date") else date.today()
        )

        return cls(
            name=data.get("name", ""),
            date=holiday_date,
            country_code=data.get("country_code", "GB"),
            type=data.get("type", "bank_holiday"),
            description=data.get("description"),
            is_observed=data.get("is_observed", True),
        )


@dataclass
class CalendarDay:
    """📅 Calendar day data model."""

    date: date
    is_today: bool = False
    is_weekend: bool = False
    is_other_month: bool = False
    is_holiday: bool = False
    holiday: Optional[Holiday] = None
    events: List[Event] = field(default_factory=list)

    def get_display_number(self) -> str:
        """📅 Get day number for display."""
        return str(self.date.day)

    def has_events(self) -> bool:
        """📝 Check if day has events."""
        return len(self.events) > 0

    def get_event_indicators(self) -> List[str]:
        """🎨 Get emoji indicators for events."""
        indicators = []

        # Show all indicators if exactly 6 or fewer events
        if len(self.events) <= 6:
            for event in self.events:
                indicators.append(event.get_category_emoji())
        else:
            # Show first 5 indicators plus a "+X" counter for the rest (when > 6).
            for event in self.events[:5]:
                indicators.append(event.get_category_emoji())
            remaining_count = len(self.events) - 5
            indicators.append(f"+{remaining_count}")

        return indicators


@dataclass
class CalendarMonth:
    """📆 Calendar month data model."""

    year: int
    month: int
    weeks: List[List[CalendarDay]] = field(default_factory=list)
    holidays: List[Holiday] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    @property
    def month_name(self) -> str:
        """📅 Get month name."""
        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return month_names[self.month - 1]

    @property
    def days_in_month(self) -> int:
        """📊 Get number of days in month."""
        import calendar

        return calendar.monthrange(self.year, self.month)[1]

    def get_display_title(self) -> str:
        """📅 Get formatted month/year title."""
        return f"📅 {self.month_name} {self.year}"


@dataclass
class AppSettings:
    """⚙️ Application settings data model."""

    theme: str = "dark"
    locale: str = "en_GB"  # Default to UK English
    timezone: str = (
        "auto"  # "auto" for system timezone, or specific timezone like "Europe/London"
    )
    ntp_interval_minutes: int = 5
    ntp_servers: List[str] = field(
        default_factory=lambda: [
            "pool.ntp.org",
            "time.google.com",
            "time.cloudflare.com",
        ]
    )
    window_width: int = 956
    window_height: int = 760
    window_x: int = -1
    window_y: int = -1
    first_day_of_week: int = 0  # 0 = Monday
    show_week_numbers: bool = False
    default_event_duration: int = 60  # minutes
    # ISO 3166-1 alpha-2 country code, or "auto" to derive from the timezone
    holiday_country: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        """📋 Convert settings to dictionary."""
        return {
            "theme": self.theme,
            "locale": self.locale,
            "timezone": self.timezone,
            "ntp_interval_minutes": self.ntp_interval_minutes,
            "ntp_servers": self.ntp_servers,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_x": self.window_x,
            "window_y": self.window_y,
            "first_day_of_week": self.first_day_of_week,
            "show_week_numbers": self.show_week_numbers,
            "default_event_duration": self.default_event_duration,
            "holiday_country": self.holiday_country,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """📥 Create settings from dictionary."""
        return cls(
            theme=data.get("theme", "dark"),
            locale=data.get("locale", "en_GB"),
            timezone=data.get("timezone", "auto"),
            ntp_interval_minutes=data.get("ntp_interval_minutes", 5),
            ntp_servers=data.get(
                "ntp_servers",
                ["pool.ntp.org", "time.google.com", "time.cloudflare.com"],
            ),
            window_width=data.get("window_width", 1200),
            window_height=data.get("window_height", 800),
            window_x=data.get("window_x", -1),
            window_y=data.get("window_y", -1),
            first_day_of_week=data.get("first_day_of_week", 0),
            show_week_numbers=data.get("show_week_numbers", False),
            default_event_duration=data.get("default_event_duration", 60),
            holiday_country=data.get("holiday_country", "auto"),
        )


@dataclass
class NTPStatus:
    """🌐 NTP synchronization status."""

    is_connected: bool = False
    last_sync_time: Optional[datetime] = None
    sync_offset: float = 0.0
    server_used: Optional[str] = None
    error_message: Optional[str] = None

    def get_status_emoji(self) -> str:
        """🌐 Get status emoji."""
        if self.is_connected:
            return "✅"
        elif self.error_message:
            return "❌"
        else:
            return "⏳"

    def get_status_text(self) -> str:
        """📝 Get human-readable status."""
        if self.is_connected:
            return f"✅ Connected to {self.server_used}"
        elif self.error_message:
            return f"❌ {self.error_message}"
        else:
            return "⏳ Connecting..."


@dataclass
class Note:
    """📝 Note data model."""

    id: int
    title: str
    content: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize computed fields after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """📋 Convert note to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """📥 Create note from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None
        )

        return cls(
            id=data["id"],
            title=data["title"],
            content=data.get("content", ""),
            created_at=created_at,
            updated_at=updated_at,
        )
