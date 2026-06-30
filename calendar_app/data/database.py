"""
🗄️ Database operations for Calendar Application

This module handles SQLite database operations with proper schema management.
Enhanced with RRULE support for RFC 5545 compliant recurring events.
"""

# E501 is suppressed file-wide: the long lines are inside multi-line SQL string
# literals (and single-string log messages) that cannot be wrapped without
# altering query/string contents, and cannot carry an inline noqa.
# flake8: noqa: E501

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
from contextlib import contextmanager

from .models import Event
from ..core.recurring_event_generator import RecurringEventGenerator

logger = logging.getLogger(__name__)


class DatabaseManager:
    """🗄️ SQLite database manager with schema versioning."""

    SCHEMA_VERSION = 2

    def __init__(self, db_path: Path):
        """Initialize database manager."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """🚀 Initialize database with schema."""
        with self.get_connection() as conn:
            # Create schema version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check current schema version
            current_version = self._get_schema_version(conn)

            if current_version < self.SCHEMA_VERSION:
                self._migrate_schema(conn, current_version)

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """📊 Get current schema version."""
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int):
        """🔄 Migrate database schema."""
        logger.info(
            f"🔄 Migrating database schema from version {from_version} to {self.SCHEMA_VERSION}"
        )

        if from_version < 1:
            self._create_initial_schema(conn)
            conn.execute("INSERT INTO schema_version (version) VALUES (1)")

        if from_version < 2:
            self._migrate_to_rrule_schema(conn)
            conn.execute("INSERT INTO schema_version (version) VALUES (2)")

        conn.commit()
        logger.info("✅ Database migration completed")

    def _create_initial_schema(self, conn: sqlite3.Connection):
        """🏗️ Create initial database schema."""

        # Events table
        conn.execute("""
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                start_time TIME,
                end_date DATE,
                end_time TIME,
                is_all_day BOOLEAN DEFAULT FALSE,
                category TEXT DEFAULT 'default',
                color TEXT DEFAULT '#0078d4',
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern TEXT,
                recurrence_end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_dates CHECK (end_date >= start_date),
                CONSTRAINT valid_times CHECK (
                    (start_time IS NULL AND end_time IS NULL) OR
                    (start_date != end_date) OR
                    (end_time >= start_time)
                )
            )
        """)

        # Create indexes for performance
        conn.execute("CREATE INDEX idx_events_start_date ON events(start_date)")
        conn.execute("CREATE INDEX idx_events_category ON events(category)")
        conn.execute("CREATE INDEX idx_events_recurring ON events(is_recurring)")
        conn.execute(
            "CREATE INDEX idx_events_date_range ON events(start_date, end_date)"
        )

        # Settings table
        conn.execute("""
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Event categories table
        conn.execute("""
            CREATE TABLE event_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT NOT NULL,
                description TEXT,
                is_system BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default categories
        default_categories = [
            ("work", "#0078d4", "Work-related events", True),
            ("personal", "#16c60c", "Personal appointments", True),
            ("holiday", "#d13438", "Holidays and vacations", True),
            ("meeting", "#ffb900", "Meetings and conferences", True),
            ("meal", "#8a8a8a", "Meals and dining", True),
            ("travel", "#6b69d6", "Travel and transportation", True),
            ("health", "#00bcf2", "Health and medical", True),
            ("education", "#ca5010", "Education and learning", True),
            ("celebration", "#e3008c", "Celebrations and parties", True),
            ("reminder", "#5d5a58", "Reminders and tasks", True),
            ("default", "#0078d4", "Default category", True),
        ]

        conn.executemany(
            """
            INSERT INTO event_categories (name, color, description, is_system)
            VALUES (?, ?, ?, ?)
        """,
            default_categories,
        )

        # Insert default settings
        default_settings = [
            ("theme", "dark", "string"),
            ("ntp_interval_minutes", "5", "integer"),
            (
                "ntp_servers",
                '["pool.ntp.org", "time.google.com", "time.cloudflare.com"]',
                "json",
            ),
            ("window_width", "956", "integer"),
            ("window_height", "760", "integer"),
            ("window_x", "-1", "integer"),
            ("window_y", "-1", "integer"),
            ("first_day_of_week", "0", "integer"),
            ("show_week_numbers", "false", "boolean"),
            ("default_event_duration", "60", "integer"),
        ]

        conn.executemany(
            """
            INSERT INTO settings (key, value, data_type)
            VALUES (?, ?, ?)
        """,
            default_settings,
        )

    def _migrate_to_rrule_schema(self, conn: sqlite3.Connection):
        """🔄 Migrate to RRULE schema (version 2)."""
        logger.info("🔄 Adding RRULE support to events table")

        # Add new RRULE columns to events table
        try:
            conn.execute("ALTER TABLE events ADD COLUMN rrule TEXT")
            logger.info("✅ Added rrule column")
        except sqlite3.OperationalError:
            logger.info("ℹ️ rrule column already exists")

        try:
            conn.execute("ALTER TABLE events ADD COLUMN recurrence_id TEXT")
            logger.info("✅ Added recurrence_id column")
        except sqlite3.OperationalError:
            logger.info("ℹ️ recurrence_id column already exists")

        try:
            conn.execute("ALTER TABLE events ADD COLUMN exception_dates TEXT")
            logger.info("✅ Added exception_dates column")
        except sqlite3.OperationalError:
            logger.info("ℹ️ exception_dates column already exists")

        try:
            conn.execute("ALTER TABLE events ADD COLUMN recurrence_master_id INTEGER")
            logger.info("✅ Added recurrence_master_id column")
        except sqlite3.OperationalError:
            logger.info("ℹ️ recurrence_master_id column already exists")

        # Create indexes for RRULE fields
        try:
            conn.execute("CREATE INDEX idx_events_rrule ON events(rrule)")
            conn.execute(
                "CREATE INDEX idx_events_recurrence_master ON events(recurrence_master_id)"
            )
            conn.execute(
                "CREATE INDEX idx_events_recurrence_id ON events(recurrence_id)"
            )
            logger.info("✅ Created RRULE indexes")
        except sqlite3.OperationalError:
            logger.info("ℹ️ RRULE indexes already exist")

        # Add foreign key constraint for recurrence master
        try:
            conn.execute("""
                CREATE TRIGGER fk_recurrence_master_id
                BEFORE INSERT ON events
                FOR EACH ROW
                WHEN NEW.recurrence_master_id IS NOT NULL
                BEGIN
                    SELECT CASE
                        WHEN (SELECT id FROM events WHERE id = NEW.recurrence_master_id) IS NULL
                        THEN RAISE(ABORT, 'Foreign key constraint failed: recurrence_master_id')
                    END;
                END
            """)
            logger.info("✅ Created recurrence master foreign key trigger")
        except sqlite3.OperationalError:
            logger.info("ℹ️ Recurrence master trigger already exists")

    @contextmanager
    def get_connection(self):
        """🔗 Get database connection with proper cleanup."""
        conn = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            conn.close()

    def create_event(self, event: Event) -> int:
        """📝 Create new event and return ID."""
        errors = event.validate()
        if errors:
            raise ValueError(f"Event validation failed: {', '.join(errors)}")

        # Serialize exception_dates list to JSON string
        exception_dates_json = None
        if event.exception_dates:
            import json

            exception_dates_json = json.dumps(
                [d.isoformat() for d in event.exception_dates]
            )

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (
                    title, description, start_date, start_time, end_date, end_time,
                    is_all_day, category, color, is_recurring, recurrence_pattern,
                    recurrence_end_date, rrule, recurrence_id, exception_dates,
                    recurrence_master_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.title,
                    event.description,
                    event.start_date,
                    event.start_time.strftime("%H:%M:%S") if event.start_time else None,
                    event.end_date,
                    event.end_time.strftime("%H:%M:%S") if event.end_time else None,
                    event.is_all_day,
                    event.category,
                    event.color,
                    event.is_recurring,
                    event.recurrence_pattern,
                    event.recurrence_end_date,
                    event.rrule,
                    event.recurrence_id,
                    exception_dates_json,
                    event.recurrence_master_id,
                    datetime.now(),
                ),
            )

            event_id = cursor.lastrowid
            conn.commit()
            logger.info(f"✅ Created event: {event.title} (ID: {event_id})")
            return event_id or 0

    def get_event(self, event_id: int) -> Optional[Event]:
        """📋 Get event by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM events WHERE id = ?
            """,
                (event_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_event(row)
            return None

    def get_events_for_date(self, target_date: date) -> List[Event]:
        """📅 Get all events for specific date."""
        with self.get_connection() as conn:
            # Use the same enhanced logic as get_events_for_month for consistency
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE (
                    -- Non-recurring events: use original date range logic
                    (is_recurring = 0 AND (
                        start_date <= ? AND (end_date >= ? OR end_date IS NULL)
                    ))
                    -- Recurring events: include all that could potentially have occurrences on this date
                    OR (is_recurring = 1 AND (
                        -- Event starts before or on the date AND (no end date OR end date is after or on the date)
                        start_date <= ? AND (recurrence_end_date IS NULL OR recurrence_end_date >= ?)
                    ))
                )
                ORDER BY start_time, title
            """,
                (target_date, target_date, target_date, target_date),
            )

            events = []
            for row in cursor.fetchall():
                event = self._row_to_event(row)

                # Handle recurring events
                if event.is_recurring:
                    logger.info(
                        f"🔄 Processing recurring event {event.id} ({event.title}) for date {target_date}"
                    )
                    logger.info(
                        f"🔄 Event start_date: {event.start_date}, target_date: {target_date}"
                    )

                    # Generate recurring occurrences - these will include the start date if it matches
                    recurring_events = self._generate_recurring_events(
                        event, target_date
                    )
                    logger.info(
                        f"🔄 Generated {len(recurring_events)} recurring events"
                    )

                    # CRITICAL FIX: Only add generated occurrences, never the master event itself
                    # The generator will create an occurrence for the start date if it matches the pattern
                    for rec_event in recurring_events:
                        events.append(rec_event)
                        logger.info(
                            f"🔄 Generated event: {rec_event.title} on {rec_event.start_date} (master_id: {getattr(rec_event, 'recurrence_master_id', None)})"
                        )
                else:
                    # Non-recurring event - always add
                    events.append(event)
                    logger.info(
                        f"📅 Added non-recurring event {event.id} ({event.title})"
                    )

            logger.info(f"📅 Final event list for {target_date}: {len(events)} events")
            for i, event in enumerate(events):
                logger.info(
                    f"📅 Event {i+1}: {event.id} - {event.title} (master_id: {getattr(event, 'recurrence_master_id', None)})"
                )

            return events

    def get_events_for_month(self, year: int, month: int) -> List[Event]:
        """📆 Get all events for specific month."""
        from calendar import monthrange

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        logger.debug(
            f"📆 Getting events for month {year}-{month:02d} (range: {start_date} to {end_date})"
        )

        with self.get_connection() as conn:
            # For recurring events, we need to include ALL recurring events that could have occurrences in this month,
            # regardless of when they started. For non-recurring events, use the original date range logic.
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE (
                    -- Non-recurring events: use original date range logic
                    (is_recurring = 0 AND (
                        (start_date >= ? AND start_date <= ?)
                        OR (end_date >= ? AND start_date <= ?)
                        OR (start_date <= ? AND end_date >= ?)
                    ))
                    -- Recurring events: include all that could potentially have occurrences in this month
                    OR (is_recurring = 1 AND (
                        -- Event starts before or during the month AND (no end date OR end date is after month start)
                        start_date <= ? AND (recurrence_end_date IS NULL OR recurrence_end_date >= ?)
                    ))
                )
                ORDER BY start_date, start_time, title
            """,
                (
                    start_date,
                    end_date,
                    start_date,
                    end_date,
                    start_date,
                    end_date,
                    end_date,
                    start_date,
                ),
            )

            events = []
            for row in cursor.fetchall():
                event = self._row_to_event(row)
                logger.debug(
                    f"📆 Found event: {event.id} ({event.title}) - recurring: {event.is_recurring}"
                )

                # Handle recurring events for the month
                if event.is_recurring:
                    # CRITICAL FIX: Only add generated occurrences, never the master event itself
                    # The master recurring event should not appear on the calendar
                    recurring_events = self._generate_recurring_events_for_range(
                        event, start_date, end_date
                    )
                    events.extend(recurring_events)
                    logger.debug(
                        f"📆 Generated {len(recurring_events)} recurring occurrences for master event {event.id}"
                    )
                else:
                    # Non-recurring events should be added normally
                    events.append(event)

            logger.debug(f"📆 Total events for {year}-{month:02d}: {len(events)}")
            return events

    def update_event(self, event: Event) -> bool:
        """✏️ Update existing event."""
        if not event.id:
            raise ValueError("Event ID is required for update")

        errors = event.validate()
        if errors:
            raise ValueError(f"Event validation failed: {', '.join(errors)}")

        # Serialize exception_dates list to JSON string
        exception_dates_json = None
        if event.exception_dates:
            import json

            exception_dates_json = json.dumps(
                [d.isoformat() for d in event.exception_dates]
            )

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE events SET
                    title = ?, description = ?, start_date = ?, start_time = ?,
                    end_date = ?, end_time = ?, is_all_day = ?, category = ?,
                    color = ?, is_recurring = ?, recurrence_pattern = ?,
                    recurrence_end_date = ?, rrule = ?, recurrence_id = ?,
                    exception_dates = ?, recurrence_master_id = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    event.title,
                    event.description,
                    event.start_date,
                    event.start_time.strftime("%H:%M:%S") if event.start_time else None,
                    event.end_date,
                    event.end_time.strftime("%H:%M:%S") if event.end_time else None,
                    event.is_all_day,
                    event.category,
                    event.color,
                    event.is_recurring,
                    event.recurrence_pattern,
                    event.recurrence_end_date,
                    event.rrule,
                    event.recurrence_id,
                    exception_dates_json,
                    event.recurrence_master_id,
                    datetime.now(),
                    event.id,
                ),
            )

            success = cursor.rowcount > 0
            if success:
                conn.commit()
                logger.info(f"✅ Updated event: {event.title} (ID: {event.id})")
            else:
                logger.warning(f"⚠️ Event not found for update: ID {event.id}")

            return success

    def delete_event(self, event_id: int) -> bool:
        """🗑️ Delete event by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            success = cursor.rowcount > 0

            if success:
                conn.commit()
                logger.info(f"✅ Deleted event ID: {event_id}")
            else:
                logger.warning(f"⚠️ Event not found for deletion: ID {event_id}")

            return success

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """🔄 Convert database row to Event object."""
        # Convert string time values back to time objects
        start_time = None
        if row["start_time"]:
            try:
                start_time = datetime.strptime(row["start_time"], "%H:%M:%S").time()
            except (ValueError, TypeError):
                start_time = None

        end_time = None
        if row["end_time"]:
            try:
                end_time = datetime.strptime(row["end_time"], "%H:%M:%S").time()
            except (ValueError, TypeError):
                end_time = None

        # Handle RRULE fields with backward compatibility
        rrule = None
        recurrence_id = None
        exception_dates = []
        recurrence_master_id = None

        try:
            rrule = row["rrule"]
            recurrence_id = row["recurrence_id"]
            recurrence_master_id = row["recurrence_master_id"]

            # Deserialize exception_dates from JSON string
            if row["exception_dates"]:
                try:
                    import json

                    exception_dates_list = json.loads(row["exception_dates"])
                    exception_dates = [
                        date.fromisoformat(d) for d in exception_dates_list
                    ]
                except (json.JSONDecodeError, ValueError, TypeError):
                    exception_dates = []
        except (KeyError, IndexError):
            # Handle older database schema without RRULE fields
            pass

        return Event(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            start_date=row["start_date"],
            start_time=start_time,
            end_date=row["end_date"],
            end_time=end_time,
            is_all_day=bool(row["is_all_day"]),
            category=row["category"],
            color=row["color"],
            is_recurring=bool(row["is_recurring"]),
            recurrence_pattern=row["recurrence_pattern"],
            recurrence_end_date=row["recurrence_end_date"],
            rrule=rrule,
            recurrence_id=recurrence_id,
            exception_dates=exception_dates,
            recurrence_master_id=recurrence_master_id,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _generate_recurring_events(
        self, base_event: Event, target_date: date
    ) -> List[Event]:
        """🔄 Generate recurring event instances for specific date using RRULE."""
        if not base_event.is_recurring:
            return []

        # Use RRULE if available, otherwise fall back to legacy pattern
        if base_event.rrule:
            try:
                generator = RecurringEventGenerator()
                occurrences = generator.generate_occurrences_for_date(
                    base_event, target_date
                )
                return occurrences
            except Exception as e:
                logger.error(
                    f"❌ RRULE generation failed for event {base_event.id}: {e}"
                )
                # Fall back to legacy generation
                return self._generate_legacy_recurring_events(base_event, target_date)
        else:
            return self._generate_legacy_recurring_events(base_event, target_date)

    def _generate_recurring_events_for_range(
        self, base_event: Event, start_date: date, end_date: date
    ) -> List[Event]:
        """🔄 Generate recurring event instances for date range using RRULE."""
        if not base_event.is_recurring:
            return []

        logger.debug(
            f"🔄 Generating recurring events for {base_event.id} ({base_event.title}) from {start_date} to {end_date}"
        )
        logger.debug(
            f"🔄 Base event start_date: {base_event.start_date}, rrule: {base_event.rrule}"
        )

        # Use RRULE if available, otherwise fall back to legacy pattern
        if base_event.rrule:
            try:
                generator = RecurringEventGenerator()
                occurrences = generator.generate_occurrences_for_range(
                    base_event, start_date, end_date
                )
                logger.debug(
                    f"🔄 Generated {len(occurrences)} recurring occurrences for event {base_event.id}"
                )
                return occurrences
            except Exception as e:
                logger.error(
                    f"❌ RRULE generation failed for event {base_event.id}: {e}"
                )
                # Fall back to legacy generation
                return self._generate_legacy_recurring_events_for_range(
                    base_event, start_date, end_date
                )
        else:
            logger.debug(
                f"🔄 No RRULE found, using legacy generation for event {base_event.id}"
            )
            return self._generate_legacy_recurring_events_for_range(
                base_event, start_date, end_date
            )

    def _generate_legacy_recurring_events(
        self, base_event: Event, target_date: date
    ) -> List[Event]:
        """🔄 Legacy recurring event generation for backward compatibility."""
        if not base_event.recurrence_pattern:
            return []

        recurring_events = []

        if base_event.recurrence_pattern == "daily":
            if base_event.start_date is None:
                return []
            days_diff = (target_date - base_event.start_date).days
            if days_diff > 0 and days_diff % 1 == 0:
                if (
                    not base_event.recurrence_end_date
                    or target_date <= base_event.recurrence_end_date
                ):
                    recurring_event = Event(
                        id=None,
                        title=base_event.title,
                        description=base_event.description,
                        start_date=target_date,
                        start_time=base_event.start_time,
                        end_date=target_date,
                        end_time=base_event.end_time,
                        is_all_day=base_event.is_all_day,
                        category=base_event.category,
                        color=base_event.color,
                        is_recurring=False,
                    )
                    recurring_events.append(recurring_event)

        elif base_event.recurrence_pattern == "weekly":
            if base_event.start_date is None:
                return []
            days_diff = (target_date - base_event.start_date).days
            if days_diff > 0 and days_diff % 7 == 0:
                if (
                    not base_event.recurrence_end_date
                    or target_date <= base_event.recurrence_end_date
                ):
                    recurring_event = Event(
                        id=None,
                        title=base_event.title,
                        description=base_event.description,
                        start_date=target_date,
                        start_time=base_event.start_time,
                        end_date=target_date,
                        end_time=base_event.end_time,
                        is_all_day=base_event.is_all_day,
                        category=base_event.category,
                        color=base_event.color,
                        is_recurring=False,
                    )
                    recurring_events.append(recurring_event)

        return recurring_events

    def _generate_legacy_recurring_events_for_range(
        self, base_event: Event, start_date: date, end_date: date
    ) -> List[Event]:
        """🔄 Legacy recurring event generation for date range."""
        if not base_event.recurrence_pattern:
            return []

        recurring_events = []
        if base_event.start_date is None:
            return []

        current_date = base_event.start_date

        while current_date <= end_date:
            if current_date >= start_date and current_date != base_event.start_date:
                if (
                    not base_event.recurrence_end_date
                    or current_date <= base_event.recurrence_end_date
                ):
                    recurring_event = Event(
                        id=None,
                        title=base_event.title,
                        description=base_event.description,
                        start_date=current_date,
                        start_time=base_event.start_time,
                        end_date=current_date,
                        end_time=base_event.end_time,
                        is_all_day=base_event.is_all_day,
                        category=base_event.category,
                        color=base_event.color,
                        is_recurring=False,
                    )
                    recurring_events.append(recurring_event)

            # Advance to next occurrence
            if base_event.recurrence_pattern == "daily":
                current_date = date.fromordinal(current_date.toordinal() + 1)
            elif base_event.recurrence_pattern == "weekly":
                current_date = date.fromordinal(current_date.toordinal() + 7)
            elif base_event.recurrence_pattern == "monthly":
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            else:
                break

        return recurring_events

    def get_event_count(self) -> int:
        """📊 Get total number of events."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM events")
            return cursor.fetchone()[0]

    def search_events(self, query: str, limit: int = 100) -> List[Event]:
        """🔍 Search events by title and description."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY start_date DESC, start_time
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_recurring_master_events(self) -> List[Event]:
        """🔄 Get all master recurring events (events with RRULE but no recurrence_master_id)."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM events
                WHERE is_recurring = 1
                AND (recurrence_master_id IS NULL OR recurrence_master_id = 0)
                ORDER BY start_date, start_time
            """)

            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_event_occurrences(self, master_event_id: int) -> List[Event]:
        """🔄 Get all occurrence events for a master recurring event."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE recurrence_master_id = ?
                ORDER BY start_date, start_time
            """,
                (master_event_id,),
            )

            return [self._row_to_event(row) for row in cursor.fetchall()]

    def delete_recurring_series(self, master_event_id: int) -> bool:
        """🗑️ Delete entire recurring series (master + all occurrences)."""
        with self.get_connection() as conn:
            # Delete all occurrences first
            cursor = conn.execute(
                "DELETE FROM events WHERE recurrence_master_id = ?", (master_event_id,)
            )
            occurrences_deleted = cursor.rowcount

            # Delete master event
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (master_event_id,))
            master_deleted = cursor.rowcount > 0

            if master_deleted:
                conn.commit()
                logger.info(
                    f"✅ Deleted recurring series: master ID {master_event_id}, {occurrences_deleted} occurrences"
                )
            else:
                logger.warning(
                    f"⚠️ Master event not found for deletion: ID {master_event_id}"
                )

            return master_deleted

    def add_exception_date(self, master_event_id: int, exception_date: date) -> bool:
        """➕ Add exception date to recurring event."""
        event = self.get_event(master_event_id)
        if not event or not event.is_recurring:
            return False

        # Work with the exception_dates list directly (it's already a list of date objects)
        exception_dates = event.exception_dates.copy() if event.exception_dates else []

        # Add new exception date if not already present
        if exception_date not in exception_dates:
            exception_dates.append(exception_date)
            exception_dates.sort()

            # Update event with new exception dates
            event.exception_dates = exception_dates
            return self.update_event(event)

        return True  # Already exists

    def remove_exception_date(self, master_event_id: int, exception_date: date) -> bool:
        """➖ Remove exception date from recurring event."""
        event = self.get_event(master_event_id)
        if not event or not event.is_recurring:
            return False

        # Work with the exception_dates list directly (it's already a list of date objects)
        exception_dates = event.exception_dates.copy() if event.exception_dates else []

        # Remove exception date if present
        if exception_date in exception_dates:
            exception_dates.remove(exception_date)

            # Update event with modified exception dates
            event.exception_dates = exception_dates if exception_dates else []
            return self.update_event(event)

        return True  # Already removed
