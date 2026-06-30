"""🗓️ Cultural observances that are not public/bank holidays.

Observances are days that are widely marked but are not public or bank holidays
(Father's Day, Valentine's Day, Halloween, ...). The Python ``holidays`` library
provides only public/bank holidays, so these are supplied here.

This module is domain-pure: standard library only, no I/O and no wall-clock
reads. Dates are always computed for an explicit year passed in by the caller.

Three rule kinds cover every observance:

* fixed        - a fixed month and day (Valentine's Day, 14 February).
* nth_weekday  - the Nth weekday of a month (Father's Day, 3rd Sunday of June).
* last_weekday - the last given weekday of a month.
* easter       - Easter Sunday plus a (possibly negative) day offset
                 (Mothering Sunday, 21 days before Easter).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# Rule kinds.
RULE_FIXED = "fixed"
RULE_NTH_WEEKDAY = "nth_weekday"
RULE_LAST_WEEKDAY = "last_weekday"
RULE_EASTER = "easter"
RULE_EASTER_ORTHODOX = "orthodox_easter"

# Python's date.weekday(): Monday is 0 ... Sunday is 6.
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)

_DAYS_PER_WEEK = 7
_FIRST_DAY_OF_MONTH = 1
_LAST_MONTH = 12
_JANUARY = 1


def easter_sunday(year: int) -> date:
    """Return the date of Western (Gregorian) Easter Sunday for ``year``.

    Uses the Anonymous Gregorian computus. The integer literals below are the
    fixed constants of that algorithm, not domain magic numbers.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def orthodox_easter_sunday(year: int) -> date:
    """Return the Gregorian date of Eastern Orthodox Easter for ``year``.

    Uses Meeus's Julian algorithm to find Easter in the Julian calendar, then
    converts to the Gregorian calendar. The conversion offset is derived from
    ``year`` rather than hard-coded, so it stays correct across centuries.
    """
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = ((d + e + 114) % 31) + 1
    julian_easter = date(year, month, day)
    century = year // 100
    julian_to_gregorian_days = century - century // 4 - 2
    return julian_easter + timedelta(days=julian_to_gregorian_days)


@dataclass(frozen=True, slots=True)
class Observance:
    """A single observance and the rule that places it within a year."""

    name: str
    rule: str
    month: int = 0
    day: int = 0
    weekday: int = 0
    ordinal: int = 0
    offset: int = 0

    @classmethod
    def fixed(cls, name: str, month: int, day: int) -> "Observance":
        """An observance on a fixed month and day."""
        return cls(name=name, rule=RULE_FIXED, month=month, day=day)

    @classmethod
    def nth_weekday(
        cls, name: str, month: int, weekday: int, ordinal: int
    ) -> "Observance":
        """The ``ordinal``-th ``weekday`` of ``month`` (ordinal counts from 1)."""
        return cls(
            name=name,
            rule=RULE_NTH_WEEKDAY,
            month=month,
            weekday=weekday,
            ordinal=ordinal,
        )

    @classmethod
    def last_weekday(cls, name: str, month: int, weekday: int) -> "Observance":
        """The last ``weekday`` of ``month``."""
        return cls(name=name, rule=RULE_LAST_WEEKDAY, month=month, weekday=weekday)

    @classmethod
    def easter(cls, name: str, offset: int) -> "Observance":
        """Western Easter Sunday shifted by ``offset`` days (negative is before)."""
        return cls(name=name, rule=RULE_EASTER, offset=offset)

    @classmethod
    def orthodox_easter(cls, name: str, offset: int) -> "Observance":
        """Orthodox Easter Sunday shifted by ``offset`` days (negative is before)."""
        return cls(name=name, rule=RULE_EASTER_ORTHODOX, offset=offset)

    def date_for(self, year: int) -> date:
        """Return the date this observance falls on in ``year``."""
        if self.rule == RULE_FIXED:
            return date(year, self.month, self.day)
        if self.rule == RULE_NTH_WEEKDAY:
            return _nth_weekday_of_month(year, self.month, self.weekday, self.ordinal)
        if self.rule == RULE_LAST_WEEKDAY:
            return _last_weekday_of_month(year, self.month, self.weekday)
        if self.rule == RULE_EASTER:
            return easter_sunday(year) + timedelta(days=self.offset)
        # RULE_EASTER_ORTHODOX is the only remaining kind.
        return orthodox_easter_sunday(year) + timedelta(days=self.offset)


def _nth_weekday_of_month(year: int, month: int, weekday: int, ordinal: int) -> date:
    """Return the ``ordinal``-th ``weekday`` of ``month`` in ``year``."""
    first = date(year, month, _FIRST_DAY_OF_MONTH)
    days_to_first = (weekday - first.weekday()) % _DAYS_PER_WEEK
    week_offset = (ordinal - 1) * _DAYS_PER_WEEK
    return first + timedelta(days=days_to_first + week_offset)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Return the last ``weekday`` of ``month`` in ``year``."""
    if month == _LAST_MONTH:
        first_of_next = date(year + 1, _JANUARY, _FIRST_DAY_OF_MONTH)
    else:
        first_of_next = date(year, month + 1, _FIRST_DAY_OF_MONTH)
    last_day = first_of_next - timedelta(days=1)
    days_back = (last_day.weekday() - weekday) % _DAYS_PER_WEEK
    return last_day - timedelta(days=days_back)
