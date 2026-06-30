"""
📝 Event Manager for Calendar Application

This module handles event CRUD operations and import/export functionality.
"""

import logging
import json
from pathlib import Path
from datetime import date, datetime, time
from typing import List, Optional, Union
from calendar_app.data.database import DatabaseManager
from calendar_app.data.models import Event
from version import EVENT_CATEGORY_EMOJIS

logger = logging.getLogger(__name__)

try:
    from icalendar import Calendar, Event as ICalEvent, vDatetime, vDate

    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False
    logger.warning("⚠️ icalendar library not available, import/export disabled")


class EventManager:
    """📝 Manages event CRUD operations and data persistence."""

    def __init__(self, database_path: Union[str, Path]):
        """Initialize event manager with database connection."""
        self.db_path = Path(database_path)
        self.db_manager = DatabaseManager(self.db_path)

        logger.info(f"📝 Event Manager initialized with database: {self.db_path}")

    def create_event(self, event: Event) -> int:
        """📝 Create new event and return ID."""
        try:
            event_id = self.db_manager.create_event(event)
            logger.info(
                f"✅ Created event: {event.get_display_title()} (ID: {event_id})"
            )
            return event_id
        except Exception as e:
            logger.error(f"❌ Failed to create event: {e}")
            raise

    def get_event(self, event_id: int) -> Optional[Event]:
        """📋 Get event by ID."""
        try:
            event = self.db_manager.get_event(event_id)
            if event:
                logger.debug(f"📋 Retrieved event: {event.get_display_title()}")
            else:
                logger.debug(f"❌ Event not found: ID {event_id}")
            return event
        except Exception as e:
            logger.error(f"❌ Failed to get event {event_id}: {e}")
            return None

    def get_events_for_date(self, target_date: date) -> List[Event]:
        """📅 Get all events for specific date."""
        try:
            events = self.db_manager.get_events_for_date(target_date)
            logger.debug(f"📅 Found {len(events)} events for {target_date}")
            return events
        except Exception as e:
            logger.error(f"❌ Failed to get events for {target_date}: {e}")
            return []

    def get_events_for_month(self, year: int, month: int) -> List[Event]:
        """📆 Get all events for specific month."""
        try:
            events = self.db_manager.get_events_for_month(year, month)
            logger.debug(f"📆 Found {len(events)} events for {year}-{month:02d}")
            return events
        except Exception as e:
            logger.error(f"❌ Failed to get events for {year}-{month:02d}: {e}")
            return []

    def get_events_for_date_range(
        self, start_date: date, end_date: date
    ) -> List[Event]:
        """📅 Get all events for specific date range."""
        try:
            # Get events for each month in the range
            all_events = []
            current_date = start_date.replace(day=1)  # Start of first month

            while current_date <= end_date:
                month_events = self.db_manager.get_events_for_month(
                    current_date.year, current_date.month
                )
                all_events.extend(month_events)

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            # Filter events to only include those that actually fall within
            # the date range
            filtered_events = []
            for event in all_events:
                if event.start_date and start_date <= event.start_date <= end_date:
                    filtered_events.append(event)

            # Remove duplicates (same event might be returned from multiple months)
            unique_events = []
            seen_ids = set()
            for event in filtered_events:
                # CRITICAL FIX: Use recurrence_id for recurring occurrences
                # to properly deduplicate
                if hasattr(event, "recurrence_id") and event.recurrence_id:
                    # Use recurrence_id for recurring occurrences
                    event_key = event.recurrence_id
                elif event.id:
                    # Use regular ID for non-recurring events
                    event_key = (event.id, event.start_date)
                else:
                    # Fallback for events without ID
                    # (shouldn't happen for non-recurring)
                    event_key = (id(event), event.start_date)

                if event_key not in seen_ids:
                    unique_events.append(event)
                    seen_ids.add(event_key)

            logger.debug(
                f"📅 Found {len(unique_events)} events for range {start_date} to {end_date}"  # noqa: E501
            )
            return unique_events
        except Exception as e:
            logger.error(
                f"❌ Failed to get events for range {start_date} to {end_date}: {e}"
            )
            return []

    def update_event(self, event: Event) -> bool:
        """✏️ Update existing event."""
        try:
            success = self.db_manager.update_event(event)
            if success:
                logger.info(f"✅ Updated event: {event.get_display_title()}")
            else:
                logger.warning(
                    f"⚠️ Failed to update event: {event.get_display_title()}"
                )
            return success
        except Exception as e:
            logger.error(f"❌ Failed to update event: {e}")
            return False

    def delete_event(self, event_id: int) -> bool:
        """🗑️ Delete event by ID."""
        try:
            # Get event info for logging before deletion
            event = self.get_event(event_id)
            success = self.db_manager.delete_event(event_id)

            if success:
                event_title = event.get_display_title() if event else f"ID {event_id}"
                logger.info(f"✅ Deleted event: {event_title}")
            else:
                logger.warning(f"⚠️ Failed to delete event: ID {event_id}")

            return success
        except Exception as e:
            logger.error(f"❌ Failed to delete event {event_id}: {e}")
            return False

    def search_events(self, query: str, limit: int = 100) -> List[Event]:
        """🔍 Search events by title and description."""
        try:
            events = self.db_manager.search_events(query, limit)
            logger.debug(f"🔍 Found {len(events)} events matching '{query}'")
            return events
        except Exception as e:
            logger.error(f"❌ Failed to search events: {e}")
            return []

    def get_events_by_category(self, category: str) -> List[Event]:
        """🏷️ Get events by category."""
        try:
            # This would need a database method - for now, search by category
            all_events = self.search_events("")  # Get all events
            category_events = [e for e in all_events if e.category == category]
            logger.debug(
                f"🏷️ Found {len(category_events)} events in category '{category}'"
            )
            return category_events
        except Exception as e:
            logger.error(f"❌ Failed to get events by category: {e}")
            return []

    def get_recurring_events(self) -> List[Event]:
        """🔄 Get all recurring events."""
        try:
            all_events = self.search_events("")  # Get all events
            recurring_events = [e for e in all_events if e.is_recurring]
            logger.debug(f"🔄 Found {len(recurring_events)} recurring events")
            return recurring_events
        except Exception as e:
            logger.error(f"❌ Failed to get recurring events: {e}")
            return []

    def get_event_count(self) -> int:
        """📊 Get total number of events."""
        try:
            count = self.db_manager.get_event_count()
            logger.debug(f"📊 Total events: {count}")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to get event count: {e}")
            return 0

    def add_exception_date(self, master_event_id: int, exception_date: date) -> bool:
        """➕ Add exception date to recurring event."""
        try:
            success = self.db_manager.add_exception_date(
                master_event_id, exception_date
            )
            if success:
                logger.info(
                    f"✅ Added exception date {exception_date} to event ID {master_event_id}"  # noqa: E501
                )
            else:
                logger.warning(
                    f"⚠️ Failed to add exception date {exception_date} to event ID {master_event_id}"  # noqa: E501
                )
            return success
        except Exception as e:
            logger.error(f"❌ Failed to add exception date: {e}")
            return False

    def remove_exception_date(self, master_event_id: int, exception_date: date) -> bool:
        """➖ Remove exception date from recurring event."""
        try:
            success = self.db_manager.remove_exception_date(
                master_event_id, exception_date
            )
            if success:
                logger.info(
                    f"✅ Removed exception date {exception_date} from event ID {master_event_id}"  # noqa: E501
                )
            else:
                logger.warning(
                    f"⚠️ Failed to remove exception date {exception_date} from event ID {master_event_id}"  # noqa: E501
                )
            return success
        except Exception as e:
            logger.error(f"❌ Failed to remove exception date: {e}")
            return False

    def export_events_to_ics(
        self, events: List[Event], file_path: Union[str, Path]
    ) -> bool:
        """📤 Export events to ICS format."""
        if not ICALENDAR_AVAILABLE:
            logger.error("❌ icalendar library not available for export")
            return False

        try:
            cal = Calendar()
            cal.add("prodid", "-//Calendar Application//Calendar//EN")
            cal.add("version", "2.0")
            cal.add("calscale", "GREGORIAN")
            cal.add("method", "PUBLISH")

            for event in events:
                ical_event = ICalEvent()
                ical_event.add("uid", f"event-{event.id}@calendar-app")
                ical_event.add("summary", event.title)

                if event.description:
                    ical_event.add("description", event.description)

                # Handle date/time
                if event.is_all_day and event.start_date:
                    ical_event.add("dtstart", vDate(event.start_date))
                    if event.end_date and event.end_date != event.start_date:
                        ical_event.add("dtend", vDate(event.end_date))
                else:
                    if event.start_time and event.start_date:
                        start_datetime = datetime.combine(
                            event.start_date, event.start_time
                        )
                        ical_event.add("dtstart", vDatetime(start_datetime))

                        if event.end_time:
                            end_date = event.end_date or event.start_date
                            if end_date:
                                end_datetime = datetime.combine(
                                    end_date, event.end_time
                                )
                                ical_event.add("dtend", vDatetime(end_datetime))
                    elif event.start_date:
                        ical_event.add("dtstart", vDate(event.start_date))

                # Add category and other properties
                ical_event.add("categories", event.category.upper())
                ical_event.add("status", "CONFIRMED")

                if event.created_at:
                    ical_event.add("created", vDatetime(event.created_at))
                if event.updated_at:
                    ical_event.add("last-modified", vDatetime(event.updated_at))

                cal.add_component(ical_event)

            # Write to file
            file_path = Path(file_path)
            with open(file_path, "wb") as f:
                f.write(cal.to_ical())

            logger.info(f"📤 Exported {len(events)} events to {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to export events to ICS: {e}")
            return False

    def import_events_from_ics(self, file_path: Union[str, Path]) -> List[Event]:
        """📥 Import events from ICS format."""
        if not ICALENDAR_AVAILABLE:
            logger.error("❌ icalendar library not available for import")
            return []

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"❌ ICS file not found: {file_path}")
                return []

            with open(file_path, "rb") as f:
                cal_data = f.read()
                cal = Calendar.from_ical(cal_data.decode("utf-8"))

            imported_events = []

            for component in cal.walk():
                if component.name == "VEVENT":
                    try:
                        event = self._ical_component_to_event(component)
                        if event:
                            event_id = self.create_event(event)
                            event.id = event_id
                            imported_events.append(event)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to import event: {e}")
                        continue

            logger.info(f"📥 Imported {len(imported_events)} events from {file_path}")
            return imported_events

        except Exception as e:
            logger.error(f"❌ Failed to import events from ICS: {e}")
            return []

    def _ical_component_to_event(self, component) -> Optional[Event]:
        """🔄 Convert iCalendar component to Event object."""
        try:
            # Extract basic information
            title = str(component.get("summary", ""))
            description = str(component.get("description", ""))

            # Extract date/time information
            dtstart = component.get("dtstart")
            dtend = component.get("dtend")

            if not dtstart:
                return None

            start_date = None
            start_time = None
            end_date = None
            end_time = None
            is_all_day = False

            # Handle start date/time
            if hasattr(dtstart.dt, "date"):
                # It's a datetime
                start_date = dtstart.dt.date()
                start_time = dtstart.dt.time()
            else:
                # It's a date only
                start_date = dtstart.dt
                is_all_day = True

            # Handle end date/time
            if dtend:
                if hasattr(dtend.dt, "date"):
                    end_date = dtend.dt.date()
                    end_time = dtend.dt.time()
                else:
                    end_date = dtend.dt
            else:
                end_date = start_date

            # Extract category
            categories = component.get("categories")
            category = "default"
            if categories:
                cat_str = str(categories).lower()
                for cat_key in EVENT_CATEGORY_EMOJIS.keys():
                    if cat_key in cat_str:
                        category = cat_key
                        break

            # Create event
            event = Event(
                title=title,
                description=description,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                is_all_day=is_all_day,
                category=category,
                color=EVENT_CATEGORY_EMOJIS.get(category, "#0078d4"),
            )

            return event

        except Exception as e:
            logger.warning(f"⚠️ Failed to convert iCal component: {e}")
            return None

    def export_events_to_csv(
        self, events: List[Event], file_path: Union[str, Path]
    ) -> bool:
        """📤 Export events to CSV format."""
        try:
            import csv

            file_path = Path(file_path)

            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "title",
                    "description",
                    "start_date",
                    "start_time",
                    "end_date",
                    "end_time",
                    "is_all_day",
                    "category",
                    "color",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for event in events:
                    writer.writerow(
                        {
                            "title": event.title,
                            "description": event.description,
                            "start_date": (
                                event.start_date.isoformat() if event.start_date else ""
                            ),
                            "start_time": (
                                event.start_time.isoformat() if event.start_time else ""
                            ),
                            "end_date": (
                                event.end_date.isoformat() if event.end_date else ""
                            ),
                            "end_time": (
                                event.end_time.isoformat() if event.end_time else ""
                            ),
                            "is_all_day": event.is_all_day,
                            "category": event.category,
                            "color": event.color,
                        }
                    )

            logger.info(f"📤 Exported {len(events)} events to CSV: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to export events to CSV: {e}")
            return False

    def import_events_from_csv(self, file_path: Union[str, Path]) -> List[Event]:
        """📥 Import events from CSV format."""
        try:
            import csv

            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"❌ CSV file not found: {file_path}")
                return []

            imported_events = []

            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    try:
                        # Parse dates and times
                        start_date = (
                            date.fromisoformat(row["start_date"])
                            if row["start_date"]
                            else None
                        )
                        start_time = (
                            time.fromisoformat(row["start_time"])
                            if row["start_time"]
                            else None
                        )
                        end_date = (
                            date.fromisoformat(row["end_date"])
                            if row["end_date"]
                            else None
                        )
                        end_time = (
                            time.fromisoformat(row["end_time"])
                            if row["end_time"]
                            else None
                        )

                        event = Event(
                            title=row["title"],
                            description=row["description"],
                            start_date=start_date,
                            start_time=start_time,
                            end_date=end_date,
                            end_time=end_time,
                            is_all_day=row["is_all_day"].lower() == "true",
                            category=row["category"],
                            color=row["color"],
                        )

                        event_id = self.create_event(event)
                        event.id = event_id
                        imported_events.append(event)

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to import CSV row: {e}")
                        continue

            logger.info(
                f"📥 Imported {len(imported_events)} events from CSV: {file_path}"
            )
            return imported_events

        except Exception as e:
            logger.error(f"❌ Failed to import events from CSV: {e}")
            return []

    def backup_events(self, backup_path: Union[str, Path]) -> bool:
        """💾 Backup all events to JSON format."""
        try:
            all_events = self.search_events("")  # Get all events

            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "event_count": len(all_events),
                "events": [event.to_dict() for event in all_events],
            }

            backup_path = Path(backup_path)
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Backed up {len(all_events)} events to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to backup events: {e}")
            return False

    def restore_events(
        self, backup_path: Union[str, Path], clear_existing: bool = False
    ) -> int:
        """📥 Restore events from JSON backup."""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                logger.error(f"❌ Backup file not found: {backup_path}")
                return 0

            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            if clear_existing:
                # This would need a method to clear all events
                logger.warning("⚠️ Clear existing events not implemented")

            restored_count = 0
            for event_data in backup_data.get("events", []):
                try:
                    event = Event.from_dict(event_data)
                    event.id = None  # Clear ID for new creation
                    self.create_event(event)
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to restore event: {e}")
                    continue

            logger.info(f"📥 Restored {restored_count} events from backup")
            return restored_count

        except Exception as e:
            logger.error(f"❌ Failed to restore events: {e}")
            return 0
