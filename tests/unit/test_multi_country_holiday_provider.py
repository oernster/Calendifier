"""100% coverage for multi_country_holiday_provider.py (real holidays lib)."""

from __future__ import annotations

from datetime import date

from calendar_app.core.multi_country_holiday_provider import (
    MultiCountryHolidayProvider as Provider,
)
from calendar_app.core.observance_data import observance_dates

YEAR = 2026


def test_init_valid_and_invalid_country():
    assert Provider("US").country_code == "US"
    # Unsupported code falls back to GB with a warning.
    assert Provider("ZZ").country_code == "GB"
    # Lower-case is upper-cased.
    assert Provider("fr").country_code == "FR"


def test_country_from_timezone():
    assert Provider.get_country_from_timezone("Europe/London") == "GB"
    assert Provider.get_country_from_timezone("Asia/Tokyo") == "JP"
    assert Provider.get_country_from_timezone("Australia/Sydney") is None
    assert Provider.get_country_from_timezone(None) is None


def test_display_name():
    assert "United States" in Provider("US").get_country_display_name()


def test_set_country_transitions():
    p = Provider("US")
    p.set_country("FR")
    assert p.country_code == "FR"
    p.set_country("FR")  # same code -> no-op branch
    assert p.country_code == "FR"
    p.set_country("ZZ")  # invalid -> warning, unchanged
    assert p.country_code == "FR"


def test_us_holidays_hit_and_miss():
    p = Provider("US")
    assert p.is_holiday(date(YEAR, 7, 4)) is True
    assert "Independence Day" in p.get_holiday(date(YEAR, 7, 4))
    obj = p.get_holiday_object(date(YEAR, 7, 4))
    assert obj is not None and obj.country_code == "US"
    # A clearly non-holiday weekday.
    assert p.is_holiday(date(YEAR, 2, 3)) is False
    assert p.get_holiday(date(YEAR, 2, 3)) is None
    assert p.get_holiday_object(date(YEAR, 2, 3)) is None


def test_uk_england_holidays():
    p = Provider("GB")  # internal code "UK" -> holidays.UK(state="England")
    assert p.is_holiday(date(YEAR, 12, 25)) is True
    month = p.get_holidays_for_month(YEAR, 12)
    assert any("Christmas" in h.name for h in month)


def test_sweden_sunday_filtering():
    p = Provider("SE")
    holidays_for_year = p._get_holidays_for_year(YEAR)
    # The bogus generic "Sunday" entries are filtered out.
    assert "Sunday" not in set(holidays_for_year.values())


def test_ukraine_custom_holidays():
    p = Provider("UA")
    # Independence Day is provided via CUSTOM_HOLIDAYS (08-24).
    assert p.is_holiday(date(YEAR, 8, 24)) is True
    assert p.get_holiday(date(YEAR, 8, 24)) is not None
    custom = p._get_custom_holidays_for_year(YEAR)
    assert date(YEAR, 8, 24) in custom


def test_fallback_basic_when_no_custom():
    p = Provider("US")
    fallback = p._get_fallback_holidays_for_year(YEAR)
    # US has no CUSTOM_HOLIDAYS, so the basic FALLBACK_HOLIDAYS are used.
    assert date(YEAR, 1, 1) in fallback


def test_weekend_and_working_days():
    p = Provider("GB")
    assert p.is_weekend(date(YEAR, 1, 3)) is True  # Saturday
    assert p.is_weekend(date(YEAR, 1, 1)) is False  # Thursday
    assert p.is_weekend_or_holiday(date(YEAR, 12, 25)) is True
    working = p.get_working_days_in_month(YEAR, 1)
    assert date(YEAR, 1, 1) not in working  # New Year's Day excluded


def test_cache_and_locale_refresh():
    p = Provider("US")
    p._get_holidays_for_year(YEAR)
    p.clear_cache()
    p.refresh_translations()
    p.force_locale_refresh()
    # Still functional after refresh.
    assert p.is_holiday(date(YEAR, 12, 25)) is True


def test_auto_update_country_from_locale():
    p = Provider("GB")
    p._auto_update_country_from_locale("fr_FR")
    assert p.country_code == "FR"
    p._auto_update_country_from_locale("zz_ZZ")  # unknown -> unchanged
    assert p.country_code == "FR"


def test_current_locale_and_translate():
    p = Provider("FR")
    assert isinstance(p._get_current_locale(), str)
    assert isinstance(p._translate_holiday_name("Christmas Day"), str)


def test_supported_and_sorted_countries():
    assert "US" in Provider.get_supported_countries()
    sorted_countries = Provider.get_sorted_countries()
    names = [info["name"] for _, info in sorted_countries]
    assert names == sorted(names)


def test_uk_observances_appear_with_observance_type():
    p = Provider("GB")
    fathers_day = next(
        d for d, name in observance_dates("GB", YEAR).items() if name == "Father's Day"
    )
    # Resolvable by name and tagged as an observance, not a bank holiday.
    name = p.get_holiday(fathers_day)
    assert name is not None and "Father" in name
    obj = p.get_holiday_object(fathers_day)
    assert obj is not None and obj.type == "observance"
    # Shows up in the month list as an observance.
    month = p.get_holidays_for_month(fathers_day.year, fathers_day.month)
    assert any(h.type == "observance" and "Father" in h.name for h in month)


def test_observance_is_not_a_day_off():
    p = Provider("GB")
    april_fools = date(YEAR, 4, 1)  # Wednesday 2026 - a normal working day
    assert p.is_holiday(april_fools) is False
    assert p.is_weekend(april_fools) is False
    assert p.get_holiday(april_fools) == "April Fool's Day"
    # Observances must NOT be removed from the working-day set.
    assert april_fools in p.get_working_days_in_month(YEAR, 4)


def test_observance_cache_and_clear():
    p = Provider("GB")
    first = p._get_observances_for_year(YEAR)
    assert first is p._get_observances_for_year(YEAR)  # cached identity
    p.set_country("US")  # changing country clears the observance cache
    assert f"GB_obs_{YEAR}" not in p._observance_cache


def test_researched_country_has_observances():
    # France is one of the researched countries; its observances are now live.
    p = Provider("FR")
    obs = p._get_observances_for_year(YEAR)
    assert obs  # non-empty
    # They surface through the calendar tagged as observances.
    has_observance = any(
        h.type == "observance"
        for month in range(1, 13)
        for h in p.get_holidays_for_month(YEAR, month)
    )
    assert has_observance
