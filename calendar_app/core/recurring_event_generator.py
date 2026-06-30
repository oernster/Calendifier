"""
🔄 Recurring Event Generator for Calendifier
Generates event occurrences from RRULE patterns
"""

import logging
from datetime import date, timedelta
from typing import List, Optional, Iterator
from calendar_app.data.models import Event
from calendar_app.core.rrule_parser import (
    RRuleParser,
    RRuleComponents,
    Frequency,
)
import calendar

logger = logging.getLogger(__name__)


class RecurringEventGenerator:
    """Generate event occurrences from RRULE"""

    def __init__(self):
        self.parser = RRuleParser()
        self.max_occurrences = 1000  # Safety limit

    def generate_occurrences(
        self, event: Event, start_date: date, end_date: date
    ) -> List[Event]:
        """Generate event occurrences for date range"""
        if not event.rrule:
            return []

        try:
            logger.debug(
                f"🔄 Generating occurrences for event {event.id} ({event.title}) from {start_date} to {end_date}"  # noqa: E501
            )
            logger.debug(
                f"🔄 Event start date: {event.start_date}, RRULE: {event.rrule}"
            )

            components = self.parser.parse_rrule(event.rrule)
            occurrences = []

            # Generate occurrences
            for occurrence_date in self._generate_dates(
                components, event.start_date, start_date, end_date
            ):
                logger.debug(f"🔄 Generated occurrence date: {occurrence_date}")
                # Create occurrence event
                occurrence = self._create_occurrence(event, occurrence_date)
                if occurrence:
                    occurrences.append(occurrence)

                # Safety check
                if len(occurrences) >= self.max_occurrences:
                    logger.warning(
                        f"Reached maximum occurrences limit: {self.max_occurrences}"
                    )
                    break

            # Handle exception dates
            if event.exception_dates:
                occurrences = self.handle_exceptions(occurrences, event.exception_dates)

            logger.debug(
                f"🔄 Generated {len(occurrences)} occurrences for event {event.id}"
            )
            return occurrences

        except Exception as e:
            logger.error(f"Failed to generate occurrences for event {event.id}: {e}")
            return []

    def generate_occurrences_for_range(
        self, event: Event, start_date: date, end_date: date
    ) -> List[Event]:
        """Generate event occurrences for date range (alias for generate_occurrences)"""
        return self.generate_occurrences(event, start_date, end_date)

    def generate_occurrences_for_date(
        self, event: Event, target_date: date
    ) -> List[Event]:
        """Generate event occurrences for a specific date"""
        return self.generate_occurrences(event, target_date, target_date)

    def get_next_occurrence(self, event: Event, after_date: date) -> Optional[Event]:
        """Get the next occurrence after a specific date"""
        if not event.rrule:
            return None

        try:
            components = self.parser.parse_rrule(event.rrule)

            # Generate occurrences for the next year
            end_date = after_date + timedelta(days=365)

            for occurrence_date in self._generate_dates(
                components, event.start_date, after_date + timedelta(days=1), end_date
            ):
                # Check if this date is not in exceptions
                if occurrence_date not in event.exception_dates:
                    return self._create_occurrence(event, occurrence_date)

            return None

        except Exception as e:
            logger.error(f"Failed to get next occurrence for event {event.id}: {e}")
            return None

    def count_occurrences(self, event: Event, until_date: date) -> int:
        """Count total occurrences until a specific date"""
        if not event.rrule:
            return 0

        try:
            components = self.parser.parse_rrule(event.rrule)
            count = 0

            for occurrence_date in self._generate_dates(
                components, event.start_date, event.start_date, until_date
            ):
                if occurrence_date not in event.exception_dates:
                    count += 1

                # Safety check
                if count >= self.max_occurrences:
                    break

            return count

        except Exception as e:
            logger.error(f"Failed to count occurrences for event {event.id}: {e}")
            return 0

    def handle_exceptions(
        self, occurrences: List[Event], exceptions: List[date]
    ) -> List[Event]:
        """Remove occurrences that fall on exception dates"""
        if not exceptions:
            return occurrences

        exception_set = set(exceptions)
        return [occ for occ in occurrences if occ.start_date not in exception_set]

    def _generate_dates(
        self,
        components: RRuleComponents,
        event_start: date,
        range_start: date,
        range_end: date,
    ) -> Iterator[date]:
        """Generate occurrence dates based on RRULE components"""
        if not event_start:
            return

        # Start from the event's start date
        current_date = event_start

        # Handle different frequencies
        if components.freq == Frequency.DAILY:
            yield from self._generate_daily(
                components, current_date, range_start, range_end
            )
        elif components.freq == Frequency.WEEKLY:
            yield from self._generate_weekly(
                components, current_date, range_start, range_end
            )
        elif components.freq == Frequency.MONTHLY:
            yield from self._generate_monthly(
                components, current_date, range_start, range_end
            )
        elif components.freq == Frequency.YEARLY:
            yield from self._generate_yearly(
                components, current_date, range_start, range_end
            )

    def _generate_daily(
        self,
        components: RRuleComponents,
        start_date: date,
        range_start: date,
        range_end: date,
    ) -> Iterator[date]:
        """Generate daily occurrences"""
        current_date = start_date
        occurrence_count = 0

        # CRITICAL FIX: For COUNT-limited events, we need to generate from start_date
        # and count globally, not just within the requested range
        if components.count:
            # Generate all occurrences from start, then filter by range
            while occurrence_count < components.count:
                # Check if we've reached the until date
                if components.until and current_date > components.until:
                    break

                # Apply BYDAY filter if specified
                if not components.byday or self._matches_weekday(
                    current_date, components.byday
                ):
                    # Only yield if in requested range
                    if range_start <= current_date <= range_end:
                        yield current_date
                    occurrence_count += 1

                    # Stop if we've hit the count limit
                    if occurrence_count >= components.count:
                        break

                # Advance by interval
                current_date += timedelta(days=components.interval)
        else:
            # No COUNT limit - use range-based generation (original logic)
            while current_date <= range_end:
                # Check if we've reached the until date
                if components.until and current_date > components.until:
                    break

                # Check if date is in range
                if current_date >= range_start:
                    # Apply BYDAY filter if specified
                    if not components.byday or self._matches_weekday(
                        current_date, components.byday
                    ):
                        yield current_date

                # Advance by interval
                current_date += timedelta(days=components.interval)

    def _generate_weekly(
        self,
        components: RRuleComponents,
        start_date: date,
        range_start: date,
        range_end: date,
    ) -> Iterator[date]:
        """Generate weekly occurrences"""
        logger.debug(
            f"🔄 _generate_weekly: start_date={start_date}, range_start={range_start}, range_end={range_end}"  # noqa: E501
        )
        logger.debug(
            f"🔄 _generate_weekly: components.byday={components.byday}, interval={components.interval}, count={components.count}"  # noqa: E501
        )

        # If no BYDAY specified, use the start date's weekday
        if not components.byday:
            weekday_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            components.byday = [weekday_map[start_date.weekday()]]
            logger.debug(
                f"🔄 _generate_weekly: No BYDAY specified, using start date weekday: {components.byday}"  # noqa: E501
            )

        # CRITICAL FIX: For COUNT-limited weekly events, we need to count
        # globally from start_date
        # not just within the requested range, similar to daily events
        if components.count:
            logger.debug(
                f"🔄 _generate_weekly: COUNT-limited generation, counting globally from {start_date}"  # noqa: E501
            )
            current_base_date = start_date
            week_count = 0
            global_occurrence_count = 0  # Count ALL occurrences from start

            while global_occurrence_count < components.count:
                logger.debug(
                    f"🔄 _generate_weekly: Processing week {week_count}, base_date={current_base_date}, global_count={global_occurrence_count}"  # noqa: E501
                )

                # Check if we've reached the until date
                if components.until and current_base_date > components.until:
                    logger.debug(
                        f"🔄 _generate_weekly: Reached until date {components.until}"
                    )
                    break

                # Find the start of the week containing current_base_date
                days_since_monday = current_base_date.weekday()
                week_start = current_base_date - timedelta(days=days_since_monday)

                # Generate occurrences for this week
                for weekday in components.byday:
                    if global_occurrence_count >= components.count:
                        break

                    weekday_index = self._weekday_to_index(weekday)
                    occurrence_date = week_start + timedelta(days=weekday_index)
                    logger.debug(
                        f"🔄 _generate_weekly: Checking {weekday} ({weekday_index}) -> {occurrence_date}"  # noqa: E501
                    )

                    # Check if this occurrence should be counted (>= start_date)
                    if occurrence_date >= start_date and (
                        not components.until or occurrence_date <= components.until
                    ):
                        # This is a valid occurrence - count it globally
                        global_occurrence_count += 1
                        logger.debug(
                            f"🔄 _generate_weekly: Valid occurrence #{global_occurrence_count}: {occurrence_date}"  # noqa: E501
                        )

                        # Only yield if it's also in the requested range
                        if range_start <= occurrence_date <= range_end:
                            logger.debug(
                                f"🔄 _generate_weekly: ✅ Yielding occurrence: {occurrence_date}"  # noqa: E501
                            )
                            yield occurrence_date
                        else:
                            logger.debug(
                                f"🔄 _generate_weekly: ❌ Occurrence {occurrence_date} outside range ({range_start} to {range_end})"  # noqa: E501
                            )

                        # Stop if we've hit the count limit
                        if global_occurrence_count >= components.count:
                            logger.debug(
                                f"🔄 _generate_weekly: Hit global count limit {components.count}"  # noqa: E501
                            )
                            break
                    else:
                        logger.debug(
                            f"🔄 _generate_weekly: ❌ Skipping {occurrence_date} (before start or after until)"  # noqa: E501
                        )

                # Advance by interval weeks from the current base date
                current_base_date += timedelta(weeks=components.interval)
                week_count += 1
                logger.debug(
                    f"🔄 _generate_weekly: Advanced to next interval week: {current_base_date}"  # noqa: E501
                )
        elif components.interval > 1:
            # Non-COUNT interval logic (existing logic for intervals without COUNT)
            current_base_date = start_date
            week_count = 0
            occurrence_count = 0
            count_limit_reached = False

            while (
                current_base_date <= range_end + timedelta(days=7)
                and not count_limit_reached
            ):
                logger.debug(
                    f"🔄 _generate_weekly: Processing interval week {week_count}, base_date={current_base_date}"  # noqa: E501
                )

                # Check if we've reached the until date
                if components.until and current_base_date > components.until:
                    logger.debug(
                        f"🔄 _generate_weekly: Reached until date {components.until}"
                    )
                    break

                # Find the start of the week containing current_base_date
                days_since_monday = current_base_date.weekday()
                week_start = current_base_date - timedelta(days=days_since_monday)

                # Generate occurrences for this week
                for weekday in components.byday:
                    weekday_index = self._weekday_to_index(weekday)
                    occurrence_date = week_start + timedelta(days=weekday_index)
                    logger.debug(
                        f"🔄 _generate_weekly: Checking {weekday} ({weekday_index}) -> {occurrence_date}"  # noqa: E501
                    )

                    # Check if date is in range and after/equal to start date
                    if (
                        occurrence_date >= start_date
                        and occurrence_date >= range_start
                        and occurrence_date <= range_end
                        and (
                            not components.until or occurrence_date <= components.until
                        )
                    ):

                        logger.debug(
                            f"🔄 _generate_weekly: ✅ Yielding occurrence: {occurrence_date}"  # noqa: E501
                        )
                        yield occurrence_date
                        occurrence_count += 1
                    else:
                        logger.debug(
                            f"🔄 _generate_weekly: ❌ Skipping {occurrence_date} (out of range or before start)"  # noqa: E501
                        )

                # Advance by interval weeks from the current base date
                current_base_date += timedelta(weeks=components.interval)
                week_count += 1
                logger.debug(
                    f"🔄 _generate_weekly: Advanced to next interval week: {current_base_date}"  # noqa: E501
                )
        else:
            # Interval = 1 (every week) without COUNT restriction
            # Find the start of the week containing start_date
            days_since_monday = start_date.weekday()
            week_start = start_date - timedelta(days=days_since_monday)
            logger.debug(f"🔄 _generate_weekly: week_start={week_start}")

            current_week = week_start

            # Continue until the week start is more than 7 days past the range_end
            while current_week <= range_end + timedelta(days=7):
                logger.debug(
                    f"🔄 _generate_weekly: Processing week starting {current_week}"
                )

                # Check if we've reached the until date
                if components.until and current_week > components.until:
                    logger.debug(
                        f"🔄 _generate_weekly: Reached until date {components.until}"
                    )
                    break

                # Generate occurrences for this week
                for weekday in components.byday:
                    weekday_index = self._weekday_to_index(weekday)
                    occurrence_date = current_week + timedelta(days=weekday_index)
                    logger.debug(
                        f"🔄 _generate_weekly: Checking {weekday} ({weekday_index}) -> {occurrence_date}"  # noqa: E501
                    )

                    # Check if date is in range and after/equal to start date
                    if (
                        occurrence_date >= start_date
                        and occurrence_date >= range_start
                        and occurrence_date <= range_end
                        and (
                            not components.until or occurrence_date <= components.until
                        )
                    ):

                        # Debug logging for UNTIL date issues
                        if components.until:
                            logger.debug(
                                f"🔄 UNTIL check: occurrence_date={occurrence_date}, until={components.until}, passes={occurrence_date <= components.until}"  # noqa: E501
                            )

                        logger.debug(
                            f"🔄 _generate_weekly: ✅ Yielding occurrence: {occurrence_date}"  # noqa: E501
                        )
                        yield occurrence_date
                    else:
                        logger.debug(
                            f"🔄 _generate_weekly: ❌ Skipping {occurrence_date} (out of range or before start)"  # noqa: E501
                        )

                # Advance by interval weeks
                current_week += timedelta(weeks=components.interval)
                logger.debug(
                    f"🔄 _generate_weekly: Advanced to next week: {current_week}"
                )

    def _generate_monthly(
        self,
        components: RRuleComponents,
        start_date: date,
        range_start: date,
        range_end: date,
    ) -> Iterator[date]:
        """Generate monthly occurrences"""
        current_date = start_date
        occurrence_count = 0

        while (
            current_date.year * 12 + current_date.month
            <= range_end.year * 12 + range_end.month
        ):
            # Check if we've reached the count limit
            if components.count and occurrence_count >= components.count:
                break

            # Check if we've reached the until date
            if components.until and current_date > components.until:
                break

            # Generate occurrences for this month
            if components.bymonthday:
                # Specific days of month
                for day in components.bymonthday:
                    occurrence_date = self._get_monthday_date(
                        current_date.year, current_date.month, day
                    )
                    if (
                        occurrence_date
                        and occurrence_date >= max(start_date, range_start)
                        and occurrence_date <= range_end
                        and (
                            not components.until or occurrence_date <= components.until
                        )
                    ):

                        yield occurrence_date
                        occurrence_count += 1

                        if components.count and occurrence_count >= components.count:
                            break

            elif components.byday:
                # Specific weekdays (e.g., first Monday, last Friday)
                for weekday_spec in components.byday:
                    occurrence_dates = self._get_weekday_in_month(
                        current_date.year, current_date.month, weekday_spec
                    )
                    for occurrence_date in occurrence_dates:
                        if (
                            occurrence_date >= max(start_date, range_start)
                            and occurrence_date <= range_end
                            and (
                                not components.until
                                or occurrence_date <= components.until
                            )
                        ):

                            yield occurrence_date
                            occurrence_count += 1

                            if (
                                components.count
                                and occurrence_count >= components.count
                            ):
                                break

            else:
                # Same day of month as start date
                occurrence_date = self._get_monthday_date(
                    current_date.year, current_date.month, start_date.day
                )
                if (
                    occurrence_date
                    and occurrence_date >= max(start_date, range_start)
                    and occurrence_date <= range_end
                    and (not components.until or occurrence_date <= components.until)
                ):

                    yield occurrence_date
                    occurrence_count += 1

            # Advance by interval months
            if current_date.month + components.interval > 12:
                new_year = (
                    current_date.year
                    + (current_date.month + components.interval - 1) // 12
                )
                new_month = (current_date.month + components.interval - 1) % 12 + 1
            else:
                new_year = current_date.year
                new_month = current_date.month + components.interval

            current_date = current_date.replace(year=new_year, month=new_month)

    def _generate_yearly(
        self,
        components: RRuleComponents,
        start_date: date,
        range_start: date,
        range_end: date,
    ) -> Iterator[date]:
        """Generate yearly occurrences"""
        current_year = start_date.year
        occurrence_count = 0

        while current_year <= range_end.year:
            # Check if we've reached the count limit
            if components.count and occurrence_count >= components.count:
                break

            # Check if we've reached the until date
            if components.until and date(current_year, 12, 31) > components.until:
                break

            # Generate occurrence for this year
            try:
                occurrence_date = start_date.replace(year=current_year)

                if (
                    occurrence_date >= max(start_date, range_start)
                    and occurrence_date <= range_end
                    and (not components.until or occurrence_date <= components.until)
                ):

                    yield occurrence_date
                    occurrence_count += 1

            except ValueError:
                # Handle leap year issues (Feb 29)
                if start_date.month == 2 and start_date.day == 29:
                    # Use Feb 28 for non-leap years
                    occurrence_date = date(current_year, 2, 28)

                    if (
                        occurrence_date >= max(start_date, range_start)
                        and occurrence_date <= range_end
                        and (
                            not components.until or occurrence_date <= components.until
                        )
                    ):

                        yield occurrence_date
                        occurrence_count += 1

            # Advance by interval years
            current_year += components.interval

    def _create_occurrence(
        self, master_event: Event, occurrence_date: date
    ) -> Optional[Event]:
        """Create an occurrence event from master event"""
        try:
            # Calculate end date
            if master_event.end_date and master_event.start_date:
                duration = master_event.end_date - master_event.start_date
                end_date = occurrence_date + duration
            else:
                end_date = occurrence_date

            # Create occurrence event
            occurrence = Event(
                id=None,  # Occurrences don't have database IDs
                title=master_event.title,
                description=master_event.description,
                start_date=occurrence_date,
                start_time=master_event.start_time,
                end_date=end_date,
                end_time=master_event.end_time,
                is_all_day=master_event.is_all_day,
                category=master_event.category,
                color=master_event.color,
                is_recurring=False,  # Occurrences are not recurring themselves
                rrule=None,
                recurrence_id=f"{master_event.id}_{occurrence_date.isoformat()}",
                recurrence_master_id=master_event.id,
                exception_dates=[],
                created_at=master_event.created_at,
                updated_at=master_event.updated_at,
            )

            return occurrence

        except Exception as e:
            logger.error(f"Failed to create occurrence for {occurrence_date}: {e}")
            return None

    def _matches_weekday(self, date_obj: date, weekdays: List[str]) -> bool:
        """Check if date matches any of the specified weekdays"""
        weekday_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        date_weekday = weekday_map[date_obj.weekday()]
        return date_weekday in weekdays

    def _weekday_to_index(self, weekday: str) -> int:
        """Convert weekday string to index (0=Monday, 6=Sunday)"""
        weekday_map = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
        return weekday_map.get(weekday, 0)

    def _get_monthday_date(self, year: int, month: int, day: int) -> Optional[date]:
        """Get date for specific day of month, handling edge cases"""
        try:
            if day == -1:
                # Last day of month
                last_day = calendar.monthrange(year, month)[1]
                return date(year, month, last_day)
            elif day > 0:
                # Positive day
                last_day = calendar.monthrange(year, month)[1]
                if day <= last_day:
                    return date(year, month, day)

            return None

        except ValueError:
            return None

    def _get_weekday_in_month(
        self, year: int, month: int, weekday_spec: str
    ) -> List[date]:
        """Get dates for weekday specification like '1MO' (first Monday) or '-1FR' (last Friday)"""  # noqa: E501
        results = []

        try:
            # Parse weekday specification
            if weekday_spec.startswith("-"):
                # Last occurrence (e.g., -1FR)
                position = -1
                weekday = weekday_spec[2:]
            elif weekday_spec[0].isdigit():
                # Specific occurrence (e.g., 1MO, 2TU)
                position = int(weekday_spec[0])
                weekday = weekday_spec[1:]
            else:
                # All occurrences (e.g., MO)
                position = 0
                weekday = weekday_spec

            weekday_index = self._weekday_to_index(weekday)

            # Find all occurrences of this weekday in the month
            first_day = date(year, month, 1)
            last_day = date(year, month, calendar.monthrange(year, month)[1])

            # Find first occurrence
            days_ahead = weekday_index - first_day.weekday()
            if days_ahead < 0:
                days_ahead += 7

            first_occurrence = first_day + timedelta(days=days_ahead)

            # Collect all occurrences
            occurrences = []
            current = first_occurrence
            while current <= last_day:
                occurrences.append(current)
                current += timedelta(days=7)

            # Return based on position
            if position == 0:
                # All occurrences
                results.extend(occurrences)
            elif position == -1:
                # Last occurrence
                if occurrences:
                    results.append(occurrences[-1])
            elif 1 <= position <= len(occurrences):
                # Specific occurrence
                results.append(occurrences[position - 1])

        except (ValueError, IndexError) as e:
            logger.warning(
                f"Failed to parse weekday specification '{weekday_spec}': {e}"
            )

        return results
