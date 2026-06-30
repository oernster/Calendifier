"""100% coverage for country_endonyms.py plus a completeness invariant."""

from __future__ import annotations

from calendar_app.core.multi_country_holiday_provider import (
    MultiCountryHolidayProvider,
)
from calendar_app.localization.country_endonyms import ENDONYMS, endonym


def test_every_supported_country_has_an_endonym():
    # Invariant: any country offered in the holiday selector must have a native
    # name, so the dropdown never falls back to an English label.
    supported = set(MultiCountryHolidayProvider.get_supported_countries())
    missing = supported - set(ENDONYMS)
    assert not missing, f"countries without an endonym: {sorted(missing)}"


def test_endonym_known_and_unknown():
    assert endonym("DE") == "Deutschland"
    assert endonym("jp") == "日本"  # case-insensitive
    # Unknown code returns the provided fallback (used as a safety net).
    assert endonym("ZZ", "Fallback") == "Fallback"
    assert endonym("ZZ") == ""
