"""
🇬🇧 UK Holiday Provider for Calendar Application

This module provides UK holiday data and integration.
"""

import logging
from datetime import date
from typing import List, Dict, Optional
from calendar_app.data.models import Holiday

logger = logging.getLogger(__name__)

try:
    import holidays

    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False
    logger.warning("⚠️ holidays library not available, using fallback holiday data")


class UKHolidayProvider:
    """🇬🇧 Provides UK holiday data with caching."""

    def __init__(self):
        """Initialize UK holiday provider."""
        self._cache: Dict[int, Dict[date, Holiday]] = {}
        self._uk_holidays = None

        if HOLIDAYS_AVAILABLE:
            try:
                self._uk_holidays = holidays.UK()
                logger.info("✅ UK holidays library initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize holidays library: {e}")
                self._uk_holidays = None

        # Fallback holiday data for common UK holidays
        self._fallback_holidays = self._get_fallback_holidays()

    def get_holidays_for_year(self, year: int) -> Dict[date, Holiday]:
        """🗓️ Get all UK holidays for specified year."""
        if year in self._cache:
            return self._cache[year]

        holidays_dict = {}

        if self._uk_holidays:
            # Use holidays library
            try:
                uk_year_holidays = self._uk_holidays.get(year, {})
                for holiday_date, holiday_name in uk_year_holidays.items():
                    if isinstance(holiday_date, date):
                        holiday = Holiday(
                            name=holiday_name,
                            date=holiday_date,
                            type="bank_holiday",
                            description=f"UK {holiday_name}",
                            is_observed=True,
                        )
                        holidays_dict[holiday_date] = holiday

                logger.debug(f"📅 Loaded {len(holidays_dict)} holidays for {year}")

            except Exception as e:
                logger.warning(f"⚠️ Error loading holidays for {year}: {e}")
                holidays_dict = self._get_fallback_holidays_for_year(year)
        else:
            # Use fallback data
            holidays_dict = self._get_fallback_holidays_for_year(year)

        # Cache the results
        self._cache[year] = holidays_dict
        return holidays_dict

    def get_holidays_for_month(self, year: int, month: int) -> List[Holiday]:
        """📅 Get UK holidays for specified month."""
        year_holidays = self.get_holidays_for_year(year)

        month_holidays = []
        for holiday_date, holiday in year_holidays.items():
            if holiday_date.month == month:
                month_holidays.append(holiday)

        # Sort by date
        month_holidays.sort(key=lambda h: h.date)
        return month_holidays

    def is_holiday(self, check_date: date) -> bool:
        """🇬🇧 Check if specific date is a UK holiday."""
        year_holidays = self.get_holidays_for_year(check_date.year)
        return check_date in year_holidays

    def get_holiday(self, check_date: date) -> Optional[Holiday]:
        """🇬🇧 Get holiday information for specific date."""
        year_holidays = self.get_holidays_for_year(check_date.year)
        return year_holidays.get(check_date)

    def get_holiday_name(self, check_date: date) -> Optional[str]:
        """📝 Get holiday name for specific date."""
        holiday = self.get_holiday(check_date)
        return holiday.name if holiday else None

    def _get_fallback_holidays(self) -> Dict[str, Dict[int, List[tuple]]]:
        """📋 Get fallback holiday data when holidays library unavailable."""
        # Basic UK holidays with approximate dates
        # Format: {holiday_name: {month: [(day, description)]}}
        return {
            "New Year's Day": {1: [(1, "New Year's Day")]},
            "Good Friday": {
                3: [(29, "Good Friday (approximate)")],
                4: [(18, "Good Friday (approximate)")],
            },
            "Easter Monday": {
                3: [(1, "Easter Monday (approximate)")],
                4: [(21, "Easter Monday (approximate)")],
            },
            "Early May Bank Holiday": {
                5: [(6, "Early May Bank Holiday (first Monday)")]
            },
            "Spring Bank Holiday": {
                5: [(27, "Spring Bank Holiday (last Monday)")],
                6: [(3, "Spring Bank Holiday (last Monday)")],
            },
            "Summer Bank Holiday": {8: [(26, "Summer Bank Holiday (last Monday)")]},
            "Christmas Day": {12: [(25, "Christmas Day")]},
            "Boxing Day": {12: [(26, "Boxing Day")]},
        }

    def _get_fallback_holidays_for_year(self, year: int) -> Dict[date, Holiday]:
        """📅 Generate fallback holidays for specific year."""
        holidays_dict = {}

        # Fixed date holidays
        fixed_holidays = [
            (1, 1, "New Year's Day"),
            (12, 25, "Christmas Day"),
            (12, 26, "Boxing Day"),
        ]

        for month, day, name in fixed_holidays:
            try:
                holiday_date = date(year, month, day)
                holiday = Holiday(
                    name=name,
                    date=holiday_date,
                    type="bank_holiday",
                    description=f"UK {name}",
                    is_observed=True,
                )
                holidays_dict[holiday_date] = holiday
            except ValueError:
                # Invalid date (e.g., Feb 29 in non-leap year)
                continue

        # Bank holidays (approximate - would need proper calculation for exact dates)
        bank_holidays = [
            (5, 6, "Early May Bank Holiday"),  # First Monday in May (approximate)
            (5, 27, "Spring Bank Holiday"),  # Last Monday in May (approximate)
            (8, 26, "Summer Bank Holiday"),  # Last Monday in August (approximate)
        ]

        for month, day, name in bank_holidays:
            try:
                # Adjust to nearest Monday (simplified)
                holiday_date = date(year, month, day)
                # Find the Monday closest to this date
                days_to_monday = (7 - holiday_date.weekday()) % 7
                if (
                    days_to_monday > 3
                ):  # If more than 3 days away, go to previous Monday
                    days_to_monday -= 7

                actual_date = date.fromordinal(
                    holiday_date.toordinal() + days_to_monday
                )

                holiday = Holiday(
                    name=name,
                    date=actual_date,
                    type="bank_holiday",
                    description=f"UK {name}",
                    is_observed=True,
                )
                holidays_dict[actual_date] = holiday
            except ValueError:
                continue

        logger.info(f"📅 Generated {len(holidays_dict)} fallback holidays for {year}")
        return holidays_dict

    def clear_cache(self):
        """🗑️ Clear holiday cache."""
        self._cache.clear()
        logger.debug("🗑️ Cleared holiday cache")

    def get_cached_years(self) -> List[int]:
        """📊 Get list of years with cached holiday data."""
        return list(self._cache.keys())

    def preload_years(self, years: List[int]):
        """⚡ Preload holiday data for multiple years."""
        for year in years:
            if year not in self._cache:
                self.get_holidays_for_year(year)

        logger.info(f"⚡ Preloaded holidays for {len(years)} years")

    def get_next_holiday(self, from_date: date) -> Optional[Holiday]:
        """➡️ Get next upcoming holiday from given date."""
        # Check current year first
        year_holidays = self.get_holidays_for_year(from_date.year)

        for holiday_date in sorted(year_holidays.keys()):
            if holiday_date > from_date:
                return year_holidays[holiday_date]

        # Check next year
        next_year_holidays = self.get_holidays_for_year(from_date.year + 1)
        if next_year_holidays:
            next_date = min(next_year_holidays.keys())
            return next_year_holidays[next_date]

        return None

    def get_previous_holiday(self, from_date: date) -> Optional[Holiday]:
        """⬅️ Get previous holiday before given date."""
        # Check current year first
        year_holidays = self.get_holidays_for_year(from_date.year)

        for holiday_date in sorted(year_holidays.keys(), reverse=True):
            if holiday_date < from_date:
                return year_holidays[holiday_date]

        # Check previous year
        prev_year_holidays = self.get_holidays_for_year(from_date.year - 1)
        if prev_year_holidays:
            prev_date = max(prev_year_holidays.keys())
            return prev_year_holidays[prev_date]

        return None

    def is_weekend(self, check_date: date) -> bool:
        """🏖️ Check if date is weekend (Saturday or Sunday)."""
        return check_date.weekday() >= 5  # 5=Saturday, 6=Sunday

    def is_weekend_or_holiday(self, check_date: date) -> bool:
        """🏖️🇬🇧 Check if date is weekend or UK holiday."""
        return self.is_weekend(check_date) or self.is_holiday(check_date)

    def get_working_days_in_month(self, year: int, month: int) -> int:
        """💼 Get number of working days in month (excluding weekends and holidays)."""
        from calendar import monthrange

        _, days_in_month = monthrange(year, month)
        working_days = 0

        for day in range(1, days_in_month + 1):
            check_date = date(year, month, day)
            if not self.is_weekend_or_holiday(check_date):
                working_days += 1

        return working_days

    def get_holiday_summary(self, year: int) -> Dict[str, int]:
        """📊 Get summary of holidays by type for the year."""
        year_holidays = self.get_holidays_for_year(year)

        summary = {
            "total": len(year_holidays),
            "bank_holiday": 0,
            "national_day": 0,
            "observance": 0,
        }

        for holiday in year_holidays.values():
            summary[holiday.type] = summary.get(holiday.type, 0) + 1

        return summary


# Global instance for easy access
uk_holidays = UKHolidayProvider()
