"""100% coverage for observances.py (pure date math, no mocks)."""

from __future__ import annotations

from datetime import date

from calendar_app.core.observances import (
    MONDAY,
    SUNDAY,
    FRIDAY,
    Observance,
    easter_sunday,
    orthodox_easter_sunday,
)
from calendar_app.core.observance_data import (
    OBSERVANCES_BY_COUNTRY,
    observance_dates,
    observances_for_country,
)


def test_easter_sunday_known_years():
    # Western (Gregorian) Easter for several reference years.
    assert easter_sunday(2024) == date(2024, 3, 31)
    assert easter_sunday(2025) == date(2025, 4, 20)
    assert easter_sunday(2026) == date(2026, 4, 5)


def test_orthodox_easter_known_years():
    # Eastern Orthodox Easter (Gregorian date) for several reference years.
    assert orthodox_easter_sunday(2024) == date(2024, 5, 5)
    assert orthodox_easter_sunday(2025) == date(2025, 4, 20)
    assert orthodox_easter_sunday(2026) == date(2026, 4, 12)


def test_orthodox_easter_relative_observance():
    # An observance 2 days after Orthodox Easter (e.g. Orthodox Easter Tuesday).
    obs = Observance.orthodox_easter("Orthodox Easter +2", 2)
    assert obs.date_for(2026) == date(2026, 4, 14)


def test_fixed_observance():
    obs = Observance.fixed("Valentine's Day", 2, 14)
    assert obs.date_for(2026) == date(2026, 2, 14)


def test_nth_weekday_observance():
    # 3rd Sunday of June 2026 (Father's Day).
    obs = Observance.nth_weekday("Father's Day", 6, SUNDAY, 3)
    result = obs.date_for(2026)
    assert result.month == 6
    assert result.weekday() == SUNDAY
    assert 15 <= result.day <= 21  # the third Sunday falls in this window


def test_nth_weekday_first_occurrence():
    # 1st Monday of September 2026.
    obs = Observance.nth_weekday("First Monday", 9, MONDAY, 1)
    result = obs.date_for(2026)
    assert result.month == 9
    assert result.weekday() == MONDAY
    assert result.day <= 7


def test_last_weekday_observance_midyear():
    # Last Monday of May 2026 (else-branch: month is not December).
    obs = Observance.last_weekday("Last Monday May", 5, MONDAY)
    result = obs.date_for(2026)
    assert result.month == 5
    assert result.weekday() == MONDAY
    assert result.day >= 25  # last Monday is always in the final week


def test_last_weekday_observance_december():
    # Last Friday of December 2026 (December branch crosses the year boundary).
    obs = Observance.last_weekday("Last Friday Dec", 12, FRIDAY)
    result = obs.date_for(2026)
    assert result.month == 12
    assert result.weekday() == FRIDAY
    assert result.day >= 25


def test_easter_relative_observance():
    # Mothering Sunday is 21 days before Easter (2026 Easter is 5 April).
    obs = Observance.easter("Mothering Sunday", -21)
    assert obs.date_for(2026) == date(2026, 3, 15)


def test_observances_for_country_known_and_unknown():
    assert observances_for_country("GB")  # non-empty
    assert observances_for_country("gb")  # case-insensitive
    assert observances_for_country("ZZ") == ()  # unknown -> empty


def test_observance_dates_includes_fathers_day():
    dates = observance_dates("GB", 2026)
    assert date(2026, 6, 21) in dates
    assert dates[date(2026, 6, 21)] == "Father's Day"
    # Valentine's Day and Halloween are present too.
    assert dates[date(2026, 2, 14)] == "Valentine's Day"
    assert dates[date(2026, 10, 31)] == "Halloween"


def test_every_defined_observance_computes_for_multiple_years():
    # Data integrity: every observance in every country resolves to a real date.
    for country, observances in OBSERVANCES_BY_COUNTRY.items():
        for observance in observances:
            for year in (2024, 2025, 2026):
                resolved = observance.date_for(year)
                assert isinstance(resolved, date)
                assert resolved.year in (year, year + 1) or resolved.year == year
