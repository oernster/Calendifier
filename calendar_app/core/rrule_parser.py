"""
🔄 RRULE Parser for Calendifier
RFC 5545 compliant recurrence rule parsing and generation
"""

import logging
from datetime import date, datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import number formatter for native number systems
try:
    from ..localization.number_formatter import (
        format_number,
        format_ordinal,
        is_native_number_locale,
    )
except ImportError:  # pragma: no cover - number_formatter ships with the app
    # Fallback if number formatter is not available
    def format_number(
        number: int, locale: str = "en_US", use_native: bool = True
    ) -> str:
        return str(number)

    def format_ordinal(number: int, locale: str = "en_US") -> str:
        return str(number)

    def is_native_number_locale(locale: str) -> bool:
        return False


logger = logging.getLogger(__name__)


class Frequency(Enum):
    """RRULE frequency values"""

    SECONDLY = "SECONDLY"
    MINUTELY = "MINUTELY"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class Weekday(Enum):
    """Weekday values for RRULE"""

    MONDAY = "MO"
    TUESDAY = "TU"
    WEDNESDAY = "WE"
    THURSDAY = "TH"
    FRIDAY = "FR"
    SATURDAY = "SA"
    SUNDAY = "SU"


@dataclass
class RRuleComponents:
    """Components of an RRULE"""

    freq: Frequency
    interval: int = 1
    count: Optional[int] = None
    until: Optional[date] = None
    byday: List[str] = field(default_factory=list)
    bymonthday: List[int] = field(default_factory=list)
    byyearday: List[int] = field(default_factory=list)
    byweekno: List[int] = field(default_factory=list)
    bymonth: List[int] = field(default_factory=list)
    bysetpos: List[int] = field(default_factory=list)
    wkst: Weekday = Weekday.MONDAY


class RRuleParser:
    """RFC 5545 compliant RRULE parser and generator"""

    def __init__(self):
        self.weekday_map = {
            "MO": Weekday.MONDAY,
            "TU": Weekday.TUESDAY,
            "WE": Weekday.WEDNESDAY,
            "TH": Weekday.THURSDAY,
            "FR": Weekday.FRIDAY,
            "SA": Weekday.SATURDAY,
            "SU": Weekday.SUNDAY,
        }

        self.frequency_map = {
            "SECONDLY": Frequency.SECONDLY,
            "MINUTELY": Frequency.MINUTELY,
            "HOURLY": Frequency.HOURLY,
            "DAILY": Frequency.DAILY,
            "WEEKLY": Frequency.WEEKLY,
            "MONTHLY": Frequency.MONTHLY,
            "YEARLY": Frequency.YEARLY,
        }

        # Initialize i18n manager
        try:
            from ..localization.i18n_manager import get_i18n_manager

            self.i18n_manager = get_i18n_manager()
        except ImportError:  # pragma: no cover - i18n_manager ships with the app
            self.i18n_manager = None

    def parse_rrule(self, rrule_string: str) -> RRuleComponents:
        """Parse RRULE string into components"""
        if not rrule_string:
            raise ValueError("RRULE string cannot be empty")

        # Remove RRULE: prefix if present
        if rrule_string.startswith("RRULE:"):
            rrule_string = rrule_string[6:]

        # Parse components
        components = {}
        for part in rrule_string.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                components[key.upper()] = value

        # Validate required frequency
        if "FREQ" not in components:
            raise ValueError("FREQ is required in RRULE")

        freq_str = components["FREQ"].upper()
        if freq_str not in self.frequency_map:
            raise ValueError(f"Invalid frequency: {freq_str}")

        freq = self.frequency_map[freq_str]

        # Parse optional components
        interval = int(components.get("INTERVAL", 1))
        count = int(components["COUNT"]) if "COUNT" in components else None
        until = (
            self._parse_until_date(components.get("UNTIL"))
            if "UNTIL" in components
            else None
        )

        # Parse BY* rules
        byday = self._parse_byday(components.get("BYDAY", ""))
        bymonthday = self._parse_int_list(components.get("BYMONTHDAY", ""))
        byyearday = self._parse_int_list(components.get("BYYEARDAY", ""))
        byweekno = self._parse_int_list(components.get("BYWEEKNO", ""))
        bymonth = self._parse_int_list(components.get("BYMONTH", ""))
        bysetpos = self._parse_int_list(components.get("BYSETPOS", ""))

        # Parse week start
        wkst_str = components.get("WKST", "MO")
        wkst = self.weekday_map.get(wkst_str, Weekday.MONDAY)

        return RRuleComponents(
            freq=freq,
            interval=interval,
            count=count,
            until=until,
            byday=byday,
            bymonthday=bymonthday,
            byyearday=byyearday,
            byweekno=byweekno,
            bymonth=bymonth,
            bysetpos=bysetpos,
            wkst=wkst,
        )

    def generate_rrule(self, components: RRuleComponents) -> str:
        """Generate RRULE string from components"""
        parts = [f"FREQ={components.freq.value}"]

        if components.interval != 1:
            parts.append(f"INTERVAL={components.interval}")

        if components.count is not None:
            parts.append(f"COUNT={components.count}")

        if components.until is not None:
            until_str = components.until.strftime("%Y%m%d")
            parts.append(f"UNTIL={until_str}")

        if components.byday:
            parts.append(f"BYDAY={','.join(components.byday)}")

        if components.bymonthday:
            parts.append(f"BYMONTHDAY={','.join(map(str, components.bymonthday))}")

        if components.byyearday:
            parts.append(f"BYYEARDAY={','.join(map(str, components.byyearday))}")

        if components.byweekno:
            parts.append(f"BYWEEKNO={','.join(map(str, components.byweekno))}")

        if components.bymonth:
            parts.append(f"BYMONTH={','.join(map(str, components.bymonth))}")

        if components.bysetpos:
            parts.append(f"BYSETPOS={','.join(map(str, components.bysetpos))}")

        if components.wkst != Weekday.MONDAY:
            parts.append(f"WKST={components.wkst.value}")

        return ";".join(parts)

    def validate_rrule(self, rrule_string: str) -> bool:
        """Validate RRULE string"""
        try:
            components = self.parse_rrule(rrule_string)

            # Additional validation rules
            if components.count is not None and components.count <= 0:
                return False

            if components.interval <= 0:
                return False

            if components.until is not None and components.count is not None:
                # Cannot have both UNTIL and COUNT
                return False

            return True

        except Exception as e:
            logger.warning(f"RRULE validation failed: {e}")
            return False

    def migrate_legacy_pattern(self, pattern: str) -> str:
        """Convert legacy recurrence pattern to RRULE"""
        pattern_map = {
            "daily": "FREQ=DAILY",
            "weekly": "FREQ=WEEKLY",
            "monthly": "FREQ=MONTHLY",
            "yearly": "FREQ=YEARLY",
        }

        return pattern_map.get(pattern.lower(), "FREQ=DAILY")

    def _parse_until_date(self, until_str: str) -> date:
        """Parse UNTIL date string"""
        # Handle different date formats
        if "T" in until_str:
            # DateTime format
            dt = datetime.strptime(until_str.split("T")[0], "%Y%m%d")
            return dt.date()
        else:
            # Date format
            return datetime.strptime(until_str, "%Y%m%d").date()

    def _parse_byday(self, byday_str: str) -> List[str]:
        """Parse BYDAY component"""
        if not byday_str:
            return []

        return [day.strip() for day in byday_str.split(",")]

    def _parse_int_list(self, value_str: str) -> List[int]:
        """Parse comma-separated integer list"""
        if not value_str:
            return []

        try:
            return [int(x.strip()) for x in value_str.split(",")]
        except ValueError:
            return []

    def get_human_readable_description(self, rrule: str, locale: str = "en_GB") -> str:
        """
        Generate human-readable description of RRULE

        Args:
            rrule: RRULE string
            locale: Target locale for description

        Returns:
            Human-readable description
        """
        try:
            components = self.parse_rrule(rrule)
            if not components:  # pragma: no cover - parse_rrule never returns falsy
                return self._get_text(
                    "recurring.error.invalid_rrule", "Invalid recurrence pattern"
                )

            # Build description parts
            parts = []

            # Frequency and interval
            freq = components.freq.value.lower()
            interval = components.interval or 1

            if interval == 1:
                # Simple frequency
                freq_key = f"rrule.frequency.{freq}"
                freq_text = self._get_text(freq_key, freq.capitalize())
                parts.append(freq_text)
            else:
                # With interval
                every_text = self._get_text("rrule.interval.every", "Every")
                interval_text = self._format_number(interval)

                if freq == "daily":
                    unit_text = self._get_text("rrule.interval.days", "days")
                elif freq == "weekly":
                    unit_text = self._get_text("rrule.interval.weeks", "weeks")
                elif freq == "monthly":
                    unit_text = self._get_text("rrule.interval.months", "months")
                elif freq == "yearly":
                    unit_text = self._get_text("rrule.interval.years", "years")
                else:
                    unit_text = freq

                parts.append(f"{every_text} {interval_text} {unit_text}")

            # Add weekdays for weekly frequency
            if components.freq == Frequency.WEEKLY and components.byday:
                weekday_names = []
                for day in components.byday:
                    day_key = f"rrule.weekday.{self._get_weekday_name(day)}"
                    day_name = self._get_text(day_key, day)
                    weekday_names.append(day_name)

                if weekday_names:  # pragma: no branch - byday is non-empty here
                    on_text = self._get_text("rrule.description.on", "on")
                    parts.append(f"{on_text} {', '.join(weekday_names)}")

            # Add monthly details
            if components.freq == Frequency.MONTHLY:
                if components.bymonthday:
                    day_text = self._get_text("rrule.description.on_day", "on day")
                    day_num = self._format_number(components.bymonthday[0])
                    parts.append(f"{day_text} {day_num}")
                elif components.bysetpos and components.byday:
                    pos_map = {
                        1: self._get_text("rrule.position.first", "first"),
                        2: self._get_text("rrule.position.second", "second"),
                        3: self._get_text("rrule.position.third", "third"),
                        4: self._get_text("rrule.position.fourth", "fourth"),
                        -1: self._get_text("rrule.position.last", "last"),
                    }
                    pos_text = pos_map.get(
                        components.bysetpos[0], str(components.bysetpos[0])
                    )
                    day_key = (
                        f"rrule.weekday.{self._get_weekday_name(components.byday[0])}"
                    )
                    day_name = self._get_text(day_key, components.byday[0])
                    on_text = self._get_text("rrule.description.on_the", "on the")
                    parts.append(f"{on_text} {pos_text} {day_name}")

            # Add end condition
            if components.count:
                for_text = self._get_text("rrule.description.for", "for")
                count_num = self._format_number(components.count)
                times_text = self._get_text("rrule.end.occurrences", "occurrences")
                parts.append(f"{for_text} {count_num} {times_text}")
            elif components.until:
                until_text = self._get_text("rrule.description.until", "until")
                date_str = components.until.strftime("%Y-%m-%d")
                parts.append(f"{until_text} {date_str}")

            return " ".join(parts)

        except Exception as e:
            logger.error(f"Error generating human readable description: {e}")
            return self._get_text(
                "recurring.error.invalid_rrule", "Invalid recurrence pattern"
            )

    def _get_text(self, key: str, default: str) -> str:
        """Get translated text with fallback"""
        if self.i18n_manager:
            return self.i18n_manager.get_text(key, default=default)
        return default

    def _format_number(self, number: int) -> str:
        """Format number with fallback"""
        if self.i18n_manager:
            return self.i18n_manager.format_number(number)
        return str(number)

    def _get_weekday_name(self, weekday_code: str) -> str:
        """Convert weekday code to name for translation key"""
        weekday_map = {
            "MO": "monday",
            "TU": "tuesday",
            "WE": "wednesday",
            "TH": "thursday",
            "FR": "friday",
            "SA": "saturday",
            "SU": "sunday",
        }
        return weekday_map.get(weekday_code, weekday_code.lower())
