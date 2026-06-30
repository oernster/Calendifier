#!/usr/bin/env python3
"""
Calendifier API Server with NTP Support
Provides REST API for calendar events, notes, holidays, and system management
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import ntplib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import holidays library directly
try:
    import holidays  # noqa: F401  (imported to test availability)

    HOLIDAYS_LIBRARY_AVAILABLE = True
    print("✅ Successfully imported holidays library")
except ImportError as e:
    HOLIDAYS_LIBRARY_AVAILABLE = False
    print(f"⚠️ Holidays library not available: {e}")

# Import the sophisticated holiday system from the main app
try:
    from calendar_app.core.multi_country_holiday_provider import (
        MultiCountryHolidayProvider,
    )

    HOLIDAY_PROVIDER_AVAILABLE = True
    print("✅ Successfully imported MultiCountryHolidayProvider")
except ImportError as e:
    HOLIDAY_PROVIDER_AVAILABLE = False
    print(f"⚠️ Multi-country holiday provider not available: {e}")
    print("⚠️ Using direct holidays library")
except Exception as e:
    HOLIDAY_PROVIDER_AVAILABLE = False
    print(f"⚠️ Error importing holiday provider: {e}")
    print("⚠️ Using direct holidays library")

# Import version information
try:
    from version import (
        __version__,
        get_version_string,
        DEFAULT_NTP_SERVERS,
        get_about_text,
    )
except ImportError:
    __version__ = "1.1.0"
    DEFAULT_NTP_SERVERS = [
        "pool.ntp.org",
        "time.google.com",
        "time.cloudflare.com",
        "time.windows.com",
        "time.apple.com",
    ]

    def get_version_string():
        return f"📅 Calendifier API v{__version__}"

    def get_about_text():
        return f"📅 Calendifier API v{__version__}\nCross-platform calendar integration"


class Event(BaseModel):
    """Event model for calendar events with optional recurring support"""

    id: Optional[int] = Field(
        None, description="Unique event identifier (auto-generated)"
    )
    title: str = Field(..., description="Event title", example="Team Meeting")
    start_date: str = Field(
        ..., description="Event start date in YYYY-MM-DD format", example="2025-01-15"
    )
    start_time: Optional[str] = Field(
        None, description="Event start time in HH:MM format", example="14:30"
    )
    end_date: Optional[str] = Field(
        None, description="Event end date in YYYY-MM-DD format", example="2025-01-15"
    )
    end_time: Optional[str] = Field(
        None, description="Event end time in HH:MM format", example="15:30"
    )
    description: Optional[str] = Field(
        None, description="Event description", example="Weekly team standup meeting"
    )
    category: str = Field("default", description="Event category", example="work")
    is_all_day: bool = Field(False, description="Whether the event is all-day")
    rrule: Optional[str] = Field(
        None,
        description="RFC 5545 RRULE pattern for recurring events",
        example="FREQ=WEEKLY;BYDAY=MO",
    )


class Note(BaseModel):
    """Note model for text notes with categorization"""

    id: Optional[int] = Field(
        None, description="Unique note identifier (auto-generated)"
    )
    title: str = Field(..., description="Note title", example="Meeting Notes")
    content: str = Field(
        ...,
        description="Note content",
        example="Discussed project timeline and deliverables",
    )
    category: str = Field("general", description="Note category", example="work")
    date: str = Field(
        ..., description="Note date in YYYY-MM-DD format", example="2025-01-15"
    )
    tags: Optional[str] = Field(
        None, description="Comma-separated tags", example="meeting,project,timeline"
    )


class Settings(BaseModel):
    """Application settings model"""

    locale: str = Field("en_GB", description="Application locale", example="en_US")
    timezone: str = Field(
        "Europe/London", description="Timezone identifier", example="America/New_York"
    )
    theme: str = Field("dark", description="UI theme", example="light")
    holiday_country: str = Field(
        "GB", description="Country code for holidays", example="US"
    )
    first_day_of_week: int = Field(
        1, description="First day of week (0=Sunday, 1=Monday)", example=0
    )
    show_week_numbers: bool = Field(False, description="Show week numbers in calendar")
    date_format: str = Field(
        "YYYY-MM-DD", description="Date format preference", example="MM/DD/YYYY"
    )
    time_format: str = Field("24h", description="Time format preference", example="12h")
    notifications_enabled: bool = Field(True, description="Enable notifications")
    auto_sync: bool = Field(True, description="Enable automatic NTP synchronization")
    sync_interval: int = Field(
        30, description="NTP sync interval in minutes", example=60
    )
    accent_color: str = Field(
        "#0078d4", description="UI accent color", example="#ff6b35"
    )
    compact_mode: bool = Field(False, description="Enable compact UI mode")
    show_emojis: bool = Field(True, description="Show emojis in UI")
    debug_mode: bool = Field(False, description="Enable debug mode")


# API description rendered in the OpenAPI/Swagger docs. Built from adjacent
# string literals so each source line stays within the line-length limit while
# the concatenated value remains byte-for-byte identical to the original.
API_DESCRIPTION = (
    "\n"
    "## Calendifier API Server\n"
    "\n"
    "A comprehensive calendar and event management API with multi-language "
    "support, holidays, and NTP synchronization.\n"
    "\n"
    "### Features\n"
    "- 📋 **Event Management**: Create, read, update, delete events with "
    "recurring support (RRULE)\n"
    "- 📝 **Notes**: Organize notes with categories and tags\n"
    "- 🎉 **Holidays**: Support for 28+ countries with localized names\n"
    "- 🌍 **Internationalization**: 28+ languages with full translation support\n"
    "- 🕐 **NTP Synchronization**: Accurate time synchronization\n"
    "- 📤📥 **Import/Export**: JSON-based data exchange\n"
    "- ⚙️ **Settings**: Comprehensive configuration management\n"
    "\n"
    "### Authentication\n"
    "This API is designed for Home Assistant integration and uses CORS for "
    "cross-origin requests.\n"
    "\n"
    "### Rate Limiting\n"
    "No rate limiting is currently implemented. Use responsibly.\n"
    "\n"
    "### Error Handling\n"
    "All endpoints return standard HTTP status codes with JSON error messages.\n"
    "            "
)


class CalendifierAPI:
    def __init__(self, db_path: str = "calendifier.db"):
        self.db_path = db_path
        self.app = FastAPI(
            title="📅 Calendifier API",
            description=API_DESCRIPTION,
            version=__version__,
            contact={
                "name": "Oliver Ernster",
                "email": "oliver@example.com",
            },
            license_info={
                "name": "GPL-3.0",
                "url": "https://www.gnu.org/licenses/gpl-3.0.html",
            },
            tags_metadata=[
                {
                    "name": "events",
                    "description": "Event management operations including "
                    "recurring events with RRULE support",
                },
                {
                    "name": "notes",
                    "description": "Note management operations with "
                    "categorization and tagging",
                },
                {
                    "name": "holidays",
                    "description": "Holiday information for 28+ countries with "
                    "localized names",
                },
                {
                    "name": "settings",
                    "description": "Application configuration and preferences",
                },
                {
                    "name": "translations",
                    "description": "Internationalization and localization support",
                },
                {
                    "name": "ntp",
                    "description": "Network Time Protocol synchronization",
                },
                {
                    "name": "import-export",
                    "description": "Data import and export operations",
                },
                {
                    "name": "system",
                    "description": "System information and health checks",
                },
            ],
        )
        self.setup_cors()
        self.setup_database()
        self.setup_routes()
        self.ntp_client = ntplib.NTPClient()
        self.last_ntp_sync = None
        self.ntp_synced = False
        self._last_successful_server = None
        self._last_ntp_result = None

        # Initialize the holiday system - REQUIRE sophisticated provider
        if not HOLIDAY_PROVIDER_AVAILABLE:
            raise Exception(
                "CRITICAL: MultiCountryHolidayProvider is required but not available"
            )

        self.holiday_provider = MultiCountryHolidayProvider()
        self.use_sophisticated_provider = True
        print("✅ Multi-country holiday provider initialized - NO FALLBACKS")

        # Detect and store current locale for holiday translations
        try:
            from calendar_app.localization.locale_detector import LocaleDetector

            detector = LocaleDetector()
            detected_locale = detector.detect_system_locale()
            self._current_locale = detected_locale
            print(f"🌍 API Server detected system locale: {detected_locale}")
        except Exception as e:
            print(f"⚠️ Could not detect system locale: {e}, using en_GB fallback")
            self._current_locale = "en_GB"

    def setup_cors(self):
        """Setup CORS middleware for Home Assistant integration"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

    def setup_database(self):
        """Initialize SQLite database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_date TEXT NOT NULL,
                start_time TEXT,
                end_date TEXT,
                end_time TEXT,
                description TEXT,
                category TEXT DEFAULT 'default',
                is_all_day BOOLEAN DEFAULT 0,
                rrule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add rrule column to existing events table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN rrule TEXT")
            print("✅ Added rrule column to events table")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                date TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default settings
        default_settings = Settings()
        for key, value in default_settings.model_dump().items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )

        # Database tables created - no sample data inserted
        # Users can add their own events and notes through the interface

        conn.commit()
        conn.close()

    def expand_rrule(
        self,
        rrule: str,
        start_date: datetime.date,
        range_start: datetime.date,
        range_end: datetime.date,
    ) -> List[datetime.date]:
        """Expand an RRULE pattern into individual occurrence dates within \
the given range"""
        try:
            # Parse RRULE components
            parts = rrule.split(";")
            rules = {}
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    rules[key] = value

            frequency = rules.get("FREQ", "WEEKLY")
            interval = int(rules.get("INTERVAL", "1"))
            count = int(rules.get("COUNT", "100")) if "COUNT" in rules else None
            until = None

            if "UNTIL" in rules:
                until_str = rules["UNTIL"]
                if len(until_str) == 8:  # YYYYMMDD format
                    until = datetime.strptime(until_str, "%Y%m%d").date()

            occurrences = []
            current = start_date
            generated = 0
            max_occurrences = count if count else 100  # Limit to prevent infinite loops

            # Generate occurrences
            while len(occurrences) < max_occurrences and current <= range_end:
                # Stop if we've reached the until date
                if until and current > until:
                    break

                # Add occurrence if it's within our range
                if range_start <= current <= range_end:
                    occurrences.append(current)

                generated += 1
                if count and generated >= count:
                    break

                # Calculate next occurrence based on frequency
                if frequency == "DAILY":
                    current = current + timedelta(days=interval)
                elif frequency == "WEEKLY":
                    # Handle BYDAY for weekly events
                    if "BYDAY" in rules:
                        weekdays = rules["BYDAY"].split(",")
                        weekday_map = {
                            "MO": 0,
                            "TU": 1,
                            "WE": 2,
                            "TH": 3,
                            "FR": 4,
                            "SA": 5,
                            "SU": 6,
                        }
                        target_weekdays = [
                            weekday_map[day] for day in weekdays if day in weekday_map
                        ]

                        if target_weekdays:
                            # Find next occurrence on specified weekdays
                            next_date = current + timedelta(days=1)
                            while next_date.weekday() not in target_weekdays:
                                next_date += timedelta(days=1)
                                if next_date > range_end + timedelta(
                                    days=7
                                ):  # Prevent infinite loop
                                    break
                            current = next_date
                        else:
                            current = current + timedelta(weeks=interval)
                    else:
                        current = current + timedelta(weeks=interval)
                elif frequency == "MONTHLY":
                    # Simple monthly increment (same day of month)
                    try:
                        if current.month == 12:
                            current = current.replace(year=current.year + 1, month=1)
                        else:
                            current = current.replace(month=current.month + interval)
                    except ValueError:
                        # Handle cases like Feb 31 -> Feb 28
                        next_month = current.month + interval
                        next_year = current.year
                        while next_month > 12:
                            next_month -= 12
                            next_year += 1

                        # Find last day of target month if original day doesn't exist
                        import calendar

                        last_day = calendar.monthrange(next_year, next_month)[1]
                        target_day = min(current.day, last_day)
                        current = datetime(next_year, next_month, target_day).date()
                elif frequency == "YEARLY":
                    try:
                        current = current.replace(year=current.year + interval)
                    except ValueError:
                        # Handle leap year edge case (Feb 29)
                        current = current.replace(year=current.year + interval, day=28)
                else:
                    # Unknown frequency, break to prevent infinite loop
                    break

                # Safety check to prevent infinite loops
                if generated > 1000:
                    break

            return occurrences

        except Exception as e:
            print(f"Error expanding RRULE '{rrule}': {e}")
            return [start_date] if range_start <= start_date <= range_end else []

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get(
            "/",
            tags=["system"],
            summary="API Root",
            description="Get basic API information",
        )
        async def root():
            """Get basic API information and status"""
            return {
                "message": "Calendifier API Server",
                "version": __version__,
                "status": "running",
            }

        @self.app.get(
            "/health",
            tags=["system"],
            summary="Health Check",
            description="Check API health and NTP sync status",
        )
        async def health_check():
            """
            Health check endpoint for monitoring and load balancers.

            Returns:
            - API status
            - Current timestamp
            - NTP synchronization status
            - Last NTP sync time
            """
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "ntp_synced": self.ntp_synced,
                "last_ntp_sync": self.last_ntp_sync,
            }

        # Events endpoints
        @self.app.get(
            "/api/v1/events",
            tags=["events"],
            summary="Get All Events",
            description="Retrieve all events with calculated days until",
        )
        async def get_events():
            """
            Get all events from the database.

            Returns:
            - List of all events
            - Each event includes days_until calculation
            - Events are sorted by start_date and start_time
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY start_date, start_time")
            events = []
            for row in cursor.fetchall():
                event = {
                    "id": row[0],
                    "title": row[1],
                    "start_date": row[2],
                    "start_time": row[3],
                    "end_date": row[4],
                    "end_time": row[5],
                    "description": row[6],
                    "category": row[7],
                    "is_all_day": bool(row[8]),
                    "rrule": row[9] if len(row) > 9 else None,
                }
                # Calculate days until
                event_date = datetime.strptime(row[2], "%Y-%m-%d").date()
                today = datetime.now().date()
                event["days_until"] = (event_date - today).days
                events.append(event)
            conn.close()
            return {"events": events}

        @self.app.post(
            "/api/v1/events",
            tags=["events"],
            summary="Create Event",
            description="Create a new event with optional recurring pattern",
        )
        async def create_event(event: Event):
            """
            Create a new event.

            Parameters:
            - **event**: Event object with all required fields

            Returns:
            - Created event ID
            - Success message

            Example RRULE patterns:
            - `FREQ=DAILY` - Daily recurrence
            - `FREQ=WEEKLY;BYDAY=MO,WE,FR` - Every Monday, Wednesday, Friday
            - `FREQ=MONTHLY;INTERVAL=2` - Every 2 months
            - `FREQ=YEARLY` - Annual recurrence
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (title, start_date, start_time, end_date, "
                "end_time, description, category, is_all_day, rrule) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.title,
                    event.start_date,
                    event.start_time,
                    event.end_date,
                    event.end_time,
                    event.description,
                    event.category,
                    event.is_all_day,
                    event.rrule,
                ),
            )
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {"id": event_id, "message": "Event created successfully"}

        @self.app.put(
            "/api/v1/events/{event_id}",
            tags=["events"],
            summary="Update Event",
            description="Update an existing event",
        )
        async def update_event(event_id: int, event: Event):
            """
            Update an existing event.

            Parameters:
            - **event_id**: ID of the event to update
            - **event**: Updated event data

            Returns:
            - Success message

            Raises:
            - 404: Event not found
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE events SET title = ?, start_date = ?, start_time = ?, "
                "end_date = ?, end_time = ?, description = ?, category = ?, "
                "is_all_day = ?, rrule = ? WHERE id = ?",
                (
                    event.title,
                    event.start_date,
                    event.start_time,
                    event.end_date,
                    event.end_time,
                    event.description,
                    event.category,
                    event.is_all_day,
                    event.rrule,
                    event_id,
                ),
            )
            if cursor.rowcount == 0:
                conn.close()
                raise HTTPException(status_code=404, detail="Event not found")
            conn.commit()
            conn.close()
            return {"message": "Event updated successfully"}

        @self.app.delete(
            "/api/v1/events/{event_id}",
            tags=["events"],
            summary="Delete Event",
            description="Delete an event",
        )
        async def delete_event(event_id: int):
            """
            Delete an event.

            Parameters:
            - **event_id**: ID of the event to delete

            Returns:
            - Success message

            Raises:
            - 404: Event not found
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            if cursor.rowcount == 0:
                conn.close()
                raise HTTPException(status_code=404, detail="Event not found")
            conn.commit()
            conn.close()
            return {"message": "Event deleted successfully"}

        @self.app.get(
            "/api/v1/events/expanded",
            tags=["events"],
            summary="Get Expanded Events",
            description="Get events with recurring events expanded into "
            "individual occurrences",
        )
        async def get_expanded_events(start_date: str = None, end_date: str = None):
            """
            Get events with recurring events expanded into individual occurrences.

            This endpoint takes recurring events (those with RRULE patterns)
            and expands them into individual occurrences within the specified
            date range.

            Parameters:
            - **start_date**: Start date for expansion (YYYY-MM-DD). Defaults
              to current month start.
            - **end_date**: End date for expansion (YYYY-MM-DD). Defaults to
              current month end.

            Returns:
            - List of expanded events (recurring events become multiple entries)
            - Date range used for expansion
            - Total count of expanded events

            Example:
            A weekly recurring event will appear as separate entries for each
            week in the range.
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY start_date, start_time")

            # Set default date range if not provided (current month)
            if not start_date:
                start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            if not end_date:
                next_month = datetime.now().replace(day=28) + timedelta(days=4)
                end_date = (next_month - timedelta(days=next_month.day)).strftime(
                    "%Y-%m-%d"
                )

            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

            expanded_events = []

            for row in cursor.fetchall():
                base_event = {
                    "id": row[0],
                    "title": row[1],
                    "start_date": row[2],
                    "start_time": row[3],
                    "end_date": row[4],
                    "end_time": row[5],
                    "description": row[6],
                    "category": row[7],
                    "is_all_day": bool(row[8]),
                    "rrule": row[9] if len(row) > 9 else None,
                    "is_recurring": bool(row[9] if len(row) > 9 else None),
                }

                event_start = datetime.strptime(row[2], "%Y-%m-%d").date()

                # If event has no rrule or is outside date range, add as single event
                if not base_event["rrule"] or not base_event["rrule"].strip():
                    if start_dt <= event_start <= end_dt:
                        today = datetime.now().date()
                        base_event["days_until"] = (event_start - today).days
                        expanded_events.append(base_event)
                else:
                    # Expand recurring event
                    try:
                        occurrences = self.expand_rrule(
                            base_event["rrule"], event_start, start_dt, end_dt
                        )
                        for occurrence_date in occurrences:
                            occurrence_event = base_event.copy()
                            occurrence_event["start_date"] = occurrence_date.strftime(
                                "%Y-%m-%d"
                            )
                            occurrence_event["end_date"] = occurrence_date.strftime(
                                "%Y-%m-%d"
                            )
                            today = datetime.now().date()
                            occurrence_event["days_until"] = (
                                occurrence_date - today
                            ).days
                            expanded_events.append(occurrence_event)
                    except Exception as e:
                        print(
                            f"Error expanding RRULE for event {base_event['id']}: {e}"
                        )
                        # Fall back to single event if RRULE expansion fails
                        if start_dt <= event_start <= end_dt:
                            today = datetime.now().date()
                            base_event["days_until"] = (event_start - today).days
                            expanded_events.append(base_event)

            conn.close()

            # Sort by date and time
            expanded_events.sort(key=lambda x: (x["start_date"], x["start_time"] or ""))

            return {
                "events": expanded_events,
                "date_range": {"start": start_date, "end": end_date},
                "total_count": len(expanded_events),
            }

        # Notes endpoints
        @self.app.get(
            "/api/v1/notes",
            tags=["notes"],
            summary="Get All Notes",
            description="Retrieve all notes ordered by creation date",
        )
        async def get_notes():
            """
            Get all notes from the database.

            Returns:
            - List of all notes
            - Notes are sorted by creation date (newest first)
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
            notes = []
            for row in cursor.fetchall():
                notes.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "category": row[3],
                        "date": row[4],
                        "tags": row[5],
                        "created_at": row[6],
                    }
                )
            conn.close()
            return {"notes": notes}

        @self.app.post(
            "/api/v1/notes",
            tags=["notes"],
            summary="Create Note",
            description="Create a new note",
        )
        async def create_note(note: Note):
            """
            Create a new note.

            Parameters:
            - **note**: Note object with all required fields

            Returns:
            - Created note ID
            - Success message
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (title, content, category, date, tags) "
                "VALUES (?, ?, ?, ?, ?)",
                (note.title, note.content, note.category, note.date, note.tags),
            )
            note_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {"id": note_id, "message": "Note created successfully"}

        @self.app.delete(
            "/api/v1/notes/{note_id}",
            tags=["notes"],
            summary="Delete Note",
            description="Delete a note",
        )
        async def delete_note(note_id: int):
            """
            Delete a note.

            Parameters:
            - **note_id**: ID of the note to delete

            Returns:
            - Success message

            Raises:
            - 404: Note not found
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            if cursor.rowcount == 0:
                conn.close()
                raise HTTPException(status_code=404, detail="Note not found")
            conn.commit()
            conn.close()
            return {"message": "Note deleted successfully"}

        # Settings endpoints
        @self.app.get(
            "/api/v1/settings",
            tags=["settings"],
            summary="Get Settings",
            description="Retrieve all application settings",
        )
        async def get_settings():
            """
            Get all application settings.

            Returns:
            - Dictionary of all settings with their current values
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = {}
            for key, value in cursor.fetchall():
                settings[key] = json.loads(value)
            conn.close()
            return settings

        @self.app.put(
            "/api/v1/settings",
            tags=["settings"],
            summary="Update Settings",
            description="Update application settings",
        )
        async def update_settings(settings: dict):
            """
            Update application settings.

            Parameters:
            - **settings**: Dictionary of settings to update

            Returns:
            - Success message

            Note:
            - Only provided settings will be updated
            - Locale changes will clear holiday cache
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if locale is being updated
            locale_changed = False
            if "locale" in settings:
                # Get current locale
                cursor.execute("SELECT value FROM settings WHERE key = 'locale'")
                current_result = cursor.fetchone()
                current_locale = (
                    json.loads(current_result[0]) if current_result else "en_GB"
                )
                new_locale = settings["locale"]

                if current_locale != new_locale:
                    locale_changed = True
                    self._current_locale = new_locale
                    print(f"🌍 Locale changed from {current_locale} to {new_locale}")

            # Update all settings
            for key, value in settings.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value, updated_at) "
                    "VALUES (?, ?, ?)",
                    (key, json.dumps(value), datetime.now().isoformat()),
                )
            conn.commit()
            conn.close()

            # Clear holiday cache if locale changed to force re-translation
            if locale_changed and self.holiday_provider:
                self.holiday_provider.clear_cache()
                print("🔄 Holiday cache cleared due to locale change")

            return {"message": "Settings updated successfully"}

        @self.app.get(
            "/api/v1/holidays/{country}/{year}/{month}",
            tags=["holidays"],
            summary="Get Holidays for Month",
            description="Get holidays for a specific country, year, and month",
        )
        async def get_holidays(country: str, year: int, month: int):
            """
            Get holidays for a specific country, year, and month.

            Parameters:
            - **country**: ISO country code (e.g., 'US', 'GB', 'DE')
            - **year**: Year (e.g., 2025)
            - **month**: Month (1-12)

            Returns:
            - List of holidays for the specified month
            - Each holiday includes name, date, type, and country
            """
            return await self.get_holidays_for_period(country, year, month)

        @self.app.get(
            "/api/v1/holidays/auto/{year}",
            tags=["holidays"],
            summary="Get Auto-Detected Holidays for Year",
            description="Get all holidays for a year using locale-based "
            "country detection",
        )
        async def get_holidays_auto_year(year: int):
            """
            Get all holidays for the current year using backend-determined country.

            The country is automatically determined from the current locale setting.
            This ensures users see holidays relevant to their location.

            Parameters:
            - **year**: Year to get holidays for

            Returns:
            - List of all holidays for the year
            - Country code used
            - Locale used for translation
            - Total count of holidays

            Raises:
            - 400: Unsupported locale
            """
            # Get current locale from settings
            current_locale = await self._get_current_locale_from_settings()
            print(f"🌍 Current locale from settings: {current_locale}")

            # STRICT locale-to-country mapping - NO DEFAULTS
            locale_to_country = {
                "en_US": "US",
                "en_GB": "GB",
                "fr_CA": "CA",
                "ca_ES": "ES",
                "es_ES": "ES",
                "fr_FR": "FR",
                "de_DE": "DE",
                "it_IT": "IT",
                "pt_BR": "BR",
                "ru_RU": "RU",
                "zh_CN": "CN",
                "zh_TW": "TW",
                "ja_JP": "JP",
                "ko_KR": "KR",
                "hi_IN": "IN",
                "ar_SA": "SA",
                "cs_CZ": "CZ",
                "sv_SE": "SE",
                "nb_NO": "NO",
                "da_DK": "DK",
                "fi_FI": "FI",
                "nl_NL": "NL",
                "pl_PL": "PL",
                "pt_PT": "PT",
                "tr_TR": "TR",
                "uk_UA": "UA",
                "el_GR": "GR",
                "id_ID": "ID",
                "vi_VN": "VN",
                "th_TH": "TH",
                "he_IL": "IL",
                "ro_RO": "RO",
                "hu_HU": "HU",
                "hr_HR": "HR",
                "bg_BG": "BG",
                "sk_SK": "SK",
                "sl_SI": "SI",
                "et_EE": "EE",
                "lv_LV": "LV",
                "lt_LT": "LT",
            }

            # REQUIRE exact locale match - NO FALLBACKS
            if current_locale not in locale_to_country:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported locale: {current_locale}. "
                    f"Supported locales: {list(locale_to_country.keys())}",
                )

            country = locale_to_country[current_locale]
            print(f"🌍 STRICT mapping: locale {current_locale} -> country {country}")

            # Force clear ALL holiday caches before getting holidays
            if self.holiday_provider:
                self.holiday_provider.clear_cache()
                print(f"🔄 Cleared holiday cache before fetching {country} holidays")

            # Get all holidays for the year using the correct method
            all_holidays = []
            for month in range(1, 13):
                month_holidays = await self.get_holidays_for_period(
                    country, year, month, add_days_until=False
                )
                all_holidays.extend(month_holidays["holidays"])

            # Sort by date
            all_holidays.sort(key=lambda x: x["date"])

            # Add days until for each holiday
            today = datetime.now().date()
            for holiday in all_holidays:
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                holiday["days_until"] = (holiday_date - today).days

            print(
                f"✅ Returning {len(all_holidays)} holidays "
                f"for {country} ({current_locale})"
            )
            return {
                "holidays": all_holidays,
                "country": country.upper(),
                "year": year,
                "locale": current_locale,
                "total_count": len(all_holidays),
            }

        @self.app.get(
            "/api/v1/holidays/auto/{year}/{month}",
            tags=["holidays"],
            summary="Get Auto-Detected Holidays for Month",
            description="Get holidays for a specific month using locale-based "
            "country detection",
        )
        async def get_holidays_auto_month(year: int, month: int):
            """
            Get holidays for a specific month using backend-determined country.

            Parameters:
            - **year**: Year (e.g., 2025)
            - **month**: Month (1-12)

            Returns:
            - List of holidays for the specified month
            - Country automatically determined from locale
            """
            # Get current locale from settings
            current_locale = await self._get_current_locale_from_settings()

            # Map locale to country
            locale_to_country = {
                "en_US": "US",
                "en_GB": "GB",
                "fr_CA": "CA",
                "ca_ES": "ES",
                "es_ES": "ES",
                "fr_FR": "FR",
                "de_DE": "DE",
                "it_IT": "IT",
                "pt_BR": "BR",
                "ru_RU": "RU",
                "zh_CN": "CN",
                "zh_TW": "TW",
                "ja_JP": "JP",
                "ko_KR": "KR",
                "hi_IN": "IN",
                "ar_SA": "SA",
                "cs_CZ": "CZ",
                "sv_SE": "SE",
                "nb_NO": "NO",
                "da_DK": "DK",
                "fi_FI": "FI",
                "nl_NL": "NL",
                "pl_PL": "PL",
                "pt_PT": "PT",
                "tr_TR": "TR",
                "uk_UA": "UA",
                "el_GR": "GR",
                "id_ID": "ID",
                "vi_VN": "VN",
                "th_TH": "TH",
                "he_IL": "IL",
                "ro_RO": "RO",
                "hu_HU": "HU",
                "hr_HR": "HR",
                "bg_BG": "BG",
                "sk_SK": "SK",
                "sl_SI": "SI",
                "et_EE": "EE",
                "lv_LV": "LV",
                "lt_LT": "LT",
            }

            country = locale_to_country.get(current_locale, "GB")
            print(f"🌍 Auto-determined country {country} from locale {current_locale}")

            # Use the existing holiday logic
            return await self.get_holidays_for_period(country, year, month)

        @self.app.get(
            "/api/v1/holidays/{country}/{year}",
            tags=["holidays"],
            summary="Get Holidays for Year",
            description="Get all holidays for a specific country and year",
        )
        async def get_holidays_year(country: str, year: int):
            """
            Get all holidays for a specific country and year.

            Note: The country parameter is overridden by the current locale setting
            to ensure users see holidays relevant to their configured location.

            Parameters:
            - **country**: ISO country code (will be overridden by locale)
            - **year**: Year to get holidays for

            Returns:
            - List of all holidays for the year
            - Actual country used (based on locale)
            - Locale used for translation
            """
            # FORCE: Ignore the country parameter and use current locale instead
            current_locale = await self._get_current_locale_from_settings()

            # Map locale to correct country
            locale_to_country = {
                "en_US": "US",
                "en_GB": "GB",
                "fr_CA": "CA",
                "ca_ES": "ES",
                "es_ES": "ES",
                "fr_FR": "FR",
                "de_DE": "DE",
                "it_IT": "IT",
                "pt_BR": "BR",
                "ru_RU": "RU",
                "zh_CN": "CN",
                "zh_TW": "TW",
                "ja_JP": "JP",
                "ko_KR": "KR",
                "hi_IN": "IN",
                "ar_SA": "SA",
                "cs_CZ": "CZ",
                "sv_SE": "SE",
                "nb_NO": "NO",
                "da_DK": "DK",
                "fi_FI": "FI",
                "nl_NL": "NL",
                "pl_PL": "PL",
                "pt_PT": "PT",
                "tr_TR": "TR",
                "uk_UA": "UA",
                "el_GR": "GR",
                "id_ID": "ID",
                "vi_VN": "VN",
                "th_TH": "TH",
                "he_IL": "IL",
                "ro_RO": "RO",
                "hu_HU": "HU",
                "hr_HR": "HR",
                "bg_BG": "BG",
                "sk_SK": "SK",
                "sl_SI": "SI",
                "et_EE": "EE",
                "lv_LV": "LV",
                "lt_LT": "LT",
            }

            actual_country = locale_to_country.get(current_locale, country)
            print(
                f"🔄 OVERRIDE: Requested {country} but using {actual_country} "
                f"based on locale {current_locale}"
            )

            all_holidays = []
            for month in range(1, 13):
                month_holidays = await self.get_holidays_for_period(
                    actual_country, year, month, add_days_until=False
                )
                all_holidays.extend(month_holidays["holidays"])

            # Sort by date
            all_holidays.sort(key=lambda x: x["date"])

            # Add days until for each holiday
            today = datetime.now().date()
            for holiday in all_holidays:
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                holiday["days_until"] = (holiday_date - today).days

            return {
                "holidays": all_holidays,
                "country": actual_country.upper(),
                "year": year,
                "locale": current_locale,
                "total_count": len(all_holidays),
            }

        @self.app.get(
            "/api/v1/holidays/countries",
            tags=["holidays"],
            summary="Get Supported Countries",
            description="Get list of all supported countries for holiday data",
        )
        async def get_supported_countries():
            """
            Get list of supported countries for holidays.

            Returns:
            - List of countries with codes, names, and flag emojis
            - Covers 28+ countries worldwide
            """
            return {
                "countries": [
                    {"code": "US", "name": "United States", "flag": "🇺🇸"},
                    {"code": "CA", "name": "Canada", "flag": "🇨🇦"},
                    {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧"},
                    {"code": "DE", "name": "Germany", "flag": "🇩🇪"},
                    {"code": "ES", "name": "Spain", "flag": "🇪🇸"},
                    {"code": "FR", "name": "France", "flag": "🇫🇷"},
                    {"code": "IT", "name": "Italy", "flag": "🇮🇹"},
                    {"code": "JP", "name": "Japan", "flag": "🇯🇵"},
                    {"code": "KR", "name": "South Korea", "flag": "🇰🇷"},
                    {"code": "CN", "name": "China", "flag": "🇨🇳"},
                    {"code": "TW", "name": "Taiwan", "flag": "🇹🇼"},
                    {"code": "BR", "name": "Brazil", "flag": "🇧🇷"},
                    {"code": "RU", "name": "Russia", "flag": "🇷🇺"},
                    {"code": "IN", "name": "India", "flag": "🇮🇳"},
                    {"code": "SA", "name": "Saudi Arabia", "flag": "🇸🇦"},
                    {"code": "CZ", "name": "Czech Republic", "flag": "🇨🇿"},
                    {"code": "SE", "name": "Sweden", "flag": "🇸🇪"},
                    {"code": "NO", "name": "Norway", "flag": "🇳🇴"},
                    {"code": "DK", "name": "Denmark", "flag": "🇩🇰"},
                    {"code": "FI", "name": "Finland", "flag": "🇫🇮"},
                    {"code": "NL", "name": "Netherlands", "flag": "🇳🇱"},
                    {"code": "PL", "name": "Poland", "flag": "🇵🇱"},
                    {"code": "PT", "name": "Portugal", "flag": "🇵🇹"},
                    {"code": "TR", "name": "Turkey", "flag": "🇹🇷"},
                    {"code": "UA", "name": "Ukraine", "flag": "🇺🇦"},
                    {"code": "GR", "name": "Greece", "flag": "🇬🇷"},
                    {"code": "ID", "name": "Indonesia", "flag": "🇮🇩"},
                    {"code": "VN", "name": "Vietnam", "flag": "🇻🇳"},
                    {"code": "TH", "name": "Thailand", "flag": "🇹🇭"},
                    {"code": "IL", "name": "Israel", "flag": "🇮🇱"},
                    {"code": "RO", "name": "Romania", "flag": "🇷🇴"},
                    {"code": "HU", "name": "Hungary", "flag": "🇭🇺"},
                    {"code": "HR", "name": "Croatia", "flag": "🇭🇷"},
                    {"code": "BG", "name": "Bulgaria", "flag": "🇧🇬"},
                    {"code": "SK", "name": "Slovakia", "flag": "🇸🇰"},
                    {"code": "SI", "name": "Slovenia", "flag": "🇸🇮"},
                    {"code": "EE", "name": "Estonia", "flag": "🇪🇪"},
                    {"code": "LV", "name": "Latvia", "flag": "🇱🇻"},
                    {"code": "LT", "name": "Lithuania", "flag": "🇱🇹"},
                ]
            }

        # Translations endpoints
        @self.app.get(
            "/api/v1/translations",
            tags=["translations"],
            summary="Get Available Translations",
            description="Get list of all available translation locales",
        )
        async def get_available_translations():
            """
            Get list of available translation locales.

            Returns:
            - List of supported locales with codes, native names, and flag emojis
            - Covers 28+ languages worldwide
            """
            return {
                "locales": [
                    {"code": "ar_SA", "name": "العربية", "flag": "🇸🇦"},
                    {"code": "id_ID", "name": "Bahasa Indonesia", "flag": "🇮🇩"},
                    {"code": "bg_BG", "name": "Български", "flag": "🇧🇬"},
                    {"code": "ca_ES", "name": "Català", "flag": "🇪🇸"},
                    {"code": "cs_CZ", "name": "Čeština", "flag": "🇨🇿"},
                    {"code": "da_DK", "name": "Dansk", "flag": "🇩🇰"},
                    {"code": "de_DE", "name": "Deutsch", "flag": "🇩🇪"},
                    {"code": "et_EE", "name": "Eesti", "flag": "🇪🇪"},
                    {"code": "en_GB", "name": "English (UK)", "flag": "🇬🇧"},
                    {"code": "en_US", "name": "English (US)", "flag": "🇺🇸"},
                    {"code": "es_ES", "name": "Español", "flag": "🇪🇸"},
                    {"code": "fr_FR", "name": "Français", "flag": "🇫🇷"},
                    {"code": "fr_CA", "name": "Français (Québec)", "flag": "🇨🇦"},
                    {"code": "hr_HR", "name": "Hrvatski", "flag": "🇭🇷"},
                    {"code": "it_IT", "name": "Italiano", "flag": "🇮🇹"},
                    {"code": "hu_HU", "name": "Magyar", "flag": "🇭🇺"},
                    {"code": "nl_NL", "name": "Nederlands", "flag": "🇳🇱"},
                    {"code": "nb_NO", "name": "Norsk (bokmål)", "flag": "🇳🇴"},
                    {"code": "pl_PL", "name": "Polski", "flag": "🇵🇱"},
                    {"code": "pt_BR", "name": "Português (Brasil)", "flag": "🇧🇷"},
                    {"code": "pt_PT", "name": "Português (Portugal)", "flag": "🇵🇹"},
                    {"code": "ro_RO", "name": "Română", "flag": "🇷🇴"},
                    {"code": "ru_RU", "name": "Русский", "flag": "🇷🇺"},
                    {"code": "sk_SK", "name": "Slovenčina", "flag": "🇸🇰"},
                    {"code": "sl_SI", "name": "Slovenščina", "flag": "🇸🇮"},
                    {"code": "fi_FI", "name": "Suomi", "flag": "🇫🇮"},
                    {"code": "sv_SE", "name": "Svenska", "flag": "🇸🇪"},
                    {"code": "th_TH", "name": "ไทย", "flag": "🇹🇭"},
                    {"code": "vi_VN", "name": "Tiếng Việt", "flag": "🇻🇳"},
                    {"code": "tr_TR", "name": "Türkçe", "flag": "🇹🇷"},
                    {"code": "uk_UA", "name": "Українська", "flag": "🇺🇦"},
                    {"code": "he_IL", "name": "עברית", "flag": "🇮🇱"},
                    {"code": "el_GR", "name": "Ελληνικά", "flag": "🇬🇷"},
                    {"code": "hi_IN", "name": "हिन्दी", "flag": "🇮🇳"},
                    {"code": "zh_CN", "name": "中文 (简体)", "flag": "🇨🇳"},
                    {"code": "zh_TW", "name": "中文 (繁體)", "flag": "🇹🇼"},
                    {"code": "ja_JP", "name": "日本語", "flag": "🇯🇵"},
                    {"code": "ko_KR", "name": "한국어", "flag": "🇰🇷"},
                    {"code": "lv_LV", "name": "Latviešu", "flag": "🇱🇻"},
                    {"code": "lt_LT", "name": "Lietuvių", "flag": "🇱🇹"},
                ]
            }

        @self.app.get(
            "/api/v1/translations/{locale}",
            tags=["translations"],
            summary="Get Translations for Locale",
            description="Get all translations for a specific locale",
        )
        async def get_translations_enhanced(locale: str):
            """
            Get translations for a specific locale.

            Parameters:
            - **locale**: Locale code (e.g., 'en_US', 'de_DE', 'ja_JP')

            Returns:
            - Locale code
            - Dictionary of all translations
            - Format information
            - Key count and support information

            The translations support both dot notation (e.g., 'settings.about')
            and flattened keys (e.g., 'settings_about') for maximum compatibility.
            """
            try:
                # Try to load from calendar_app translations if available
                translation_file = Path(
                    f"calendar_app/localization/translations/{locale}.json"
                )
                if translation_file.exists():
                    with open(translation_file, "r", encoding="utf-8") as f:
                        raw_translations = json.load(f)

                    # Normalize translations to support both formats
                    normalized = self.normalize_translation_keys(raw_translations)

                    return {
                        "locale": locale,
                        "translations": normalized,
                        "format": "normalized",
                        "key_count": len(normalized),
                        "supports_dot_notation": True,
                        "supports_flattened": True,
                        "original_key_count": len(raw_translations),
                    }
                else:
                    # Fallback to basic translations
                    basic_translations = {
                        "app_name": "📅 Calendifier",
                        "clock": "🕐 Clock",
                        "events": "📋 Events",
                        "calendar": "📅 Calendar",
                        "notes": "📝 Notes",
                        "holidays": "🎉 Holidays",
                        "settings": "⚙️ Settings",
                        "today": "Today",
                        "tomorrow": "Tomorrow",
                        "yesterday": "Yesterday",
                        "add_event": "Add Event",
                        "add_note": "Add Note",
                        "delete": "Delete",
                        "edit": "Edit",
                        "save": "Save",
                        "cancel": "Cancel",
                        "loading": "Loading...",
                        "error": "Error",
                        "success": "Success",
                        "ntp_synced": "NTP Synced",
                        "ntp_not_synced": "NTP Not Synced",
                        "sync_time": "Sync Time",
                        "timezone": "Timezone",
                        "time_format": "Time Format",
                        "12_hour": "12 Hour",
                        "24_hour": "24 Hour",
                        "world_clocks": "World Clocks",
                        "upcoming_events": "Upcoming Events",
                        "no_events": "No events",
                        "no_notes": "No notes",
                        "no_holidays": "No holidays",
                        "days_until": "days until",
                        "all_day": "All day",
                        "category": "Category",
                        "description": "Description",
                        "title": "Title",
                        "content": "Content",
                        "date": "Date",
                        "time": "Time",
                        # Add dot notation versions
                        "settings.about": "About",
                        "toolbar.today": "Today",
                        "calendar.months.january": "January",
                    }
                    normalized = self.normalize_translation_keys(basic_translations)
                    return {
                        "locale": locale,
                        "translations": normalized,
                        "format": "normalized_fallback",
                    }
            except Exception as e:
                print(f"Translation error for {locale}: {e}")
                return {"locale": locale, "translations": {}, "error": str(e)}

        # Import/Export endpoints
        @self.app.get(
            "/api/v1/export/events",
            tags=["import-export"],
            summary="Export Events",
            description="Export all events as JSON",
        )
        async def export_events():
            """
            Export all events as JSON.

            Returns:
            - List of all events
            - Export timestamp
            - Total count

            Useful for:
            - Data backup
            - Migration to other systems
            - Data analysis
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY start_date, start_time")
            events = []
            for row in cursor.fetchall():
                events.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "start_date": row[2],
                        "start_time": row[3],
                        "end_date": row[4],
                        "end_time": row[5],
                        "description": row[6],
                        "category": row[7],
                        "is_all_day": bool(row[8]),
                        "created_at": row[9],
                    }
                )
            conn.close()
            return {
                "events": events,
                "exported_at": datetime.now().isoformat(),
                "total_count": len(events),
            }

        @self.app.get(
            "/api/v1/export/notes",
            tags=["import-export"],
            summary="Export Notes",
            description="Export all notes as JSON",
        )
        async def export_notes():
            """
            Export all notes as JSON.

            Returns:
            - List of all notes
            - Export timestamp
            - Total count
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
            notes = []
            for row in cursor.fetchall():
                notes.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "category": row[3],
                        "date": row[4],
                        "tags": row[5],
                        "created_at": row[6],
                    }
                )
            conn.close()
            return {
                "notes": notes,
                "exported_at": datetime.now().isoformat(),
                "total_count": len(notes),
            }

        @self.app.get(
            "/api/v1/export/all",
            tags=["import-export"],
            summary="Export All Data",
            description="Export all data (events, notes, settings) as JSON",
        )
        async def export_all():
            """
            Export all data (events, notes, settings) as JSON.

            Returns:
            - Complete data export including:
              - All events
              - All notes
              - All settings
              - Export metadata

            This is the recommended endpoint for full data backup.
            """
            # Get events
            events_response = await export_events()
            # Get notes
            notes_response = await export_notes()
            # Get settings
            settings_response = await get_settings()

            return {
                "calendifier_export": {
                    "version": __version__,
                    "exported_at": datetime.now().isoformat(),
                    "events": events_response["events"],
                    "notes": notes_response["notes"],
                    "settings": settings_response,
                    "metadata": {
                        "total_events": len(events_response["events"]),
                        "total_notes": len(notes_response["notes"]),
                        "export_format": "calendifier_json_v1",
                    },
                }
            }

        @self.app.post(
            "/api/v1/import/events",
            tags=["import-export"],
            summary="Import Events",
            description="Import events from JSON data",
        )
        async def import_events(import_data: dict):
            """
            Import events from JSON data.

            Parameters:
            - **import_data**: Dictionary containing 'events' array

            Returns:
            - Import statistics (imported, skipped, total processed)

            Notes:
            - Duplicate events (same title and date) are skipped
            - Invalid events are skipped with error logging
            """
            try:
                events = import_data.get("events", [])
                if not events:
                    raise HTTPException(
                        status_code=400, detail="No events data provided"
                    )

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                imported_count = 0
                skipped_count = 0

                for event in events:
                    try:
                        # Skip if event already exists (by title and date)
                        cursor.execute(
                            "SELECT id FROM events WHERE title = ? AND start_date = ?",
                            (event.get("title"), event.get("start_date")),
                        )
                        if cursor.fetchone():
                            skipped_count += 1
                            continue

                        # Insert new event
                        cursor.execute(
                            "INSERT INTO events (title, start_date, "
                            "start_time, end_date, end_time, description, "
                            "category, is_all_day) VALUES (?, ?, ?, ?, ?, ?, "
                            "?, ?)",
                            (
                                event.get("title"),
                                event.get("start_date"),
                                event.get("start_time"),
                                event.get("end_date"),
                                event.get("end_time"),
                                event.get("description"),
                                event.get("category", "default"),
                                event.get("is_all_day", False),
                            ),
                        )
                        imported_count += 1
                    except Exception as e:
                        print(f"Error importing event: {e}")
                        continue

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "total_processed": len(events),
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

        @self.app.post(
            "/api/v1/import/notes",
            tags=["import-export"],
            summary="Import Notes",
            description="Import notes from JSON data",
        )
        async def import_notes(import_data: dict):
            """
            Import notes from JSON data.

            Parameters:
            - **import_data**: Dictionary containing 'notes' array

            Returns:
            - Import statistics (imported, skipped, total processed)
            """
            try:
                notes = import_data.get("notes", [])
                if not notes:
                    raise HTTPException(
                        status_code=400, detail="No notes data provided"
                    )

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                imported_count = 0
                skipped_count = 0

                for note in notes:
                    try:
                        # Skip if note already exists (by title and date)
                        cursor.execute(
                            "SELECT id FROM notes WHERE title = ? AND date = ?",
                            (note.get("title"), note.get("date")),
                        )
                        if cursor.fetchone():
                            skipped_count += 1
                            continue

                        # Insert new note
                        cursor.execute(
                            "INSERT INTO notes (title, content, category, "
                            "date, tags) VALUES (?, ?, ?, ?, ?)",
                            (
                                note.get("title"),
                                note.get("content"),
                                note.get("category", "general"),
                                note.get("date"),
                                note.get("tags"),
                            ),
                        )
                        imported_count += 1
                    except Exception as e:
                        print(f"Error importing note: {e}")
                        continue

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "total_processed": len(notes),
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

        # NTP endpoints
        @self.app.get(
            "/api/v1/ntp/status",
            tags=["ntp"],
            summary="Get NTP Status",
            description="Get current NTP synchronization status",
        )
        async def get_ntp_status():
            """
            Get current NTP synchronization status.

            Returns:
            - NTP sync status
            - Last sync time
            - Last successful server
            - Time difference information
            """
            return {
                "ntp_synced": self.ntp_synced,
                "last_sync": self.last_ntp_sync,
                "last_successful_server": self._last_successful_server,
                "sync_result": self._last_ntp_result,
                "current_time": datetime.now().isoformat(),
            }

        @self.app.post(
            "/api/v1/ntp/sync",
            tags=["ntp"],
            summary="Sync NTP Time",
            description="Manually trigger NTP time synchronization",
        )
        async def sync_ntp():
            """
            Manually trigger NTP time synchronization.

            Returns:
            - Sync result
            - Time difference
            - Server used
            - Success status

            This endpoint attempts to synchronize with multiple NTP servers
            and returns detailed information about the synchronization process.
            """
            return await self.sync_time_with_ntp()

        @self.app.get(
            "/api/v1/ntp/servers",
            tags=["ntp"],
            summary="Get NTP Servers",
            description="Get list of configured NTP servers",
        )
        async def get_ntp_servers():
            """
            Get list of configured NTP servers.

            Returns:
            - List of NTP servers
            - Default servers
            - Priority order
            """
            return {
                "servers": DEFAULT_NTP_SERVERS,
                "default_count": len(DEFAULT_NTP_SERVERS),
                "priority_order": "First available server is used",
            }

        # About endpoint
        @self.app.get(
            "/api/v1/about",
            tags=["system"],
            summary="Get Application Information",
            description="Get application name, version, and feature information",
        )
        async def get_about():
            """
            Get application information including version, features, and
            technical details.

            Returns:
            - Application name and version
            - Feature list
            - Technical specifications
            - License information
            """
            return {
                "app_name": "📅 Calendifier",
                "version": __version__,
                "description": "Cross-platform desktop calendar with analog "
                "clock, event handling, note taking, and holidays",
                "features": [
                    "🕐 Analog Clock Display",
                    "📅 Interactive Calendar View",
                    "🌍 International Holidays",
                    "📝 Event Management",
                    "📋 Note Taking System",
                    "🌐 NTP Time Synchronization",
                    "🎨 Multiple Themes",
                    "📤📥 Data Import/Export",
                    "💾 Data Persistence",
                    "💻 Cross-Platform Support",
                ],
                "technical_details": {
                    "framework": "FastAPI + Home Assistant",
                    "language": "Python + JavaScript",
                    "architecture": "REST API + Lovelace Cards",
                    "database": "SQLite",
                    "time_sync": "NTP Protocol",
                },
                "libraries": {
                    "FastAPI": "Modern Python web framework",
                    "SQLite": "Lightweight database engine",
                    "ntplib": "Network Time Protocol client",
                    "python-dateutil": "Date/time parsing utilities",
                    "holidays": "International holiday data",
                },
                "license": "MIT License",
                "copyright": "© 2025 Oliver Ernster",
                "author": "Oliver Ernster",
            }

    async def _get_current_locale_from_settings(self):
        """Get current locale from settings database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'locale'")
            result = cursor.fetchone()
            conn.close()

            if result:
                return json.loads(result[0])
            else:
                return self._current_locale  # Fallback to detected locale
        except Exception as e:
            print(f"Error getting locale from settings: {e}")
            return self._current_locale  # Fallback to detected locale

    def normalize_translation_keys(self, translations):
        """Normalize translation keys to support both dot notation and flattened keys"""
        normalized = {}

        def flatten_dict(d, parent_key="", sep="_"):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        # Add original keys
        normalized.update(translations)

        # Add flattened keys (dot notation to underscore)
        flattened = flatten_dict(translations, sep="_")
        normalized.update(flattened)

        # Add dot notation keys (underscore to dot)
        for key, value in list(normalized.items()):
            if "_" in key:
                dot_key = key.replace("_", ".")
                normalized[dot_key] = value

        return normalized

    async def get_holidays_for_period(
        self, country: str, year: int, month: int, add_days_until: bool = True
    ):
        """Get holidays for a specific period using the sophisticated \
holiday provider"""
        try:
            if not self.use_sophisticated_provider or not self.holiday_provider:
                raise Exception("Sophisticated holiday provider not available")

            # Get current locale for translations
            current_locale = await self._get_current_locale_from_settings()

            # Get holidays using the sophisticated provider
            holidays_data = self.holiday_provider.get_holidays_for_month(
                country=country.upper(), year=year, month=month, locale=current_locale
            )

            # Convert to API format
            holidays_list = []
            for holiday_date, holiday_info in holidays_data.items():
                holiday_entry = {
                    "date": holiday_date.strftime("%Y-%m-%d"),
                    "name": holiday_info.get("name", "Unknown Holiday"),
                    "type": holiday_info.get("type", "public"),
                    "country": country.upper(),
                    "locale": current_locale,
                }

                # Add days until if requested
                if add_days_until:
                    today = datetime.now().date()
                    holiday_entry["days_until"] = (holiday_date - today).days

                holidays_list.append(holiday_entry)

            # Sort by date
            holidays_list.sort(key=lambda x: x["date"])

            return {
                "holidays": holidays_list,
                "country": country.upper(),
                "year": year,
                "month": month,
                "locale": current_locale,
                "total_count": len(holidays_list),
            }

        except Exception as e:
            print(f"Error getting holidays for {country}/{year}/{month}: {e}")
            return {
                "holidays": [],
                "country": country.upper(),
                "year": year,
                "month": month,
                "error": str(e),
                "total_count": 0,
            }

    async def sync_time_with_ntp(self):
        """Synchronize time with NTP servers"""
        try:
            for server in DEFAULT_NTP_SERVERS:
                try:
                    print(f"🕐 Attempting NTP sync with {server}...")
                    response = self.ntp_client.request(server, version=3, timeout=5)

                    # Calculate time difference
                    ntp_time = datetime.fromtimestamp(response.tx_time)
                    local_time = datetime.now()
                    time_diff = (ntp_time - local_time).total_seconds()

                    # Update sync status
                    self.ntp_synced = True
                    self.last_ntp_sync = datetime.now().isoformat()
                    self._last_successful_server = server
                    self._last_ntp_result = {
                        "server": server,
                        "ntp_time": ntp_time.isoformat(),
                        "local_time": local_time.isoformat(),
                        "time_difference_seconds": time_diff,
                        "stratum": response.stratum,
                        "precision": response.precision,
                    }

                    print(f"✅ NTP sync successful with {server}")
                    print(f"   Time difference: {time_diff:.3f} seconds")

                    return {
                        "success": True,
                        "server": server,
                        "ntp_time": ntp_time.isoformat(),
                        "local_time": local_time.isoformat(),
                        "time_difference_seconds": time_diff,
                        "stratum": response.stratum,
                        "message": f"Successfully synced with {server}",
                    }

                except Exception as server_error:
                    print(f"❌ Failed to sync with {server}: {server_error}")
                    continue

            # All servers failed
            self.ntp_synced = False
            error_msg = "Failed to sync with any NTP server"
            print(f"❌ {error_msg}")

            return {
                "success": False,
                "error": error_msg,
                "servers_tried": DEFAULT_NTP_SERVERS,
                "local_time": datetime.now().isoformat(),
            }

        except Exception as e:
            self.ntp_synced = False
            error_msg = f"NTP sync error: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "success": False,
                "error": error_msg,
                "local_time": datetime.now().isoformat(),
            }


def create_app():
    """Factory function to create the FastAPI application"""
    api = CalendifierAPI()
    return api.app


def run_server():
    """Run the API server"""
    import uvicorn

    print(f"\n{get_version_string()}")
    print("🚀 Starting Calendifier API Server...")
    print("📚 Swagger documentation will be available at: http://localhost:8000/docs")
    print("🔧 ReDoc documentation will be available at: http://localhost:8000/redoc")
    print("🌐 API root endpoint: http://localhost:8000/")

    app = create_app()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", access_log=True)
    except KeyboardInterrupt:
        print("\n👋 Calendifier API Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    run_server()
