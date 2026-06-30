"""100% coverage for holiday_translations.py (locale holiday name lookup)."""

from __future__ import annotations

from calendar_app.core import holiday_translations as ht

LOCALE = "ru_RU"


def test_empty_inputs_return_original():
    assert ht.get_translated_holiday_name("", LOCALE) == ""
    assert ht.get_translated_holiday_name("Christmas Day", "") == "Christmas Day"


def test_exact_translation_from_locale_file():
    assert ht.get_translated_holiday_name("New Year's Day", LOCALE) == "Новый год"


def test_observed_pattern_is_reconstructed():
    # A base with no exact "(observed)" entry forces the reconstruction path.
    result = ht.get_translated_holiday_name("Totally Unknown Day (observed)", LOCALE)
    assert result.startswith("Totally Unknown Day (")
    assert result.endswith(")")


def test_substituted_pattern_keeps_date():
    # A date with no exact entry forces the reconstruction path.
    result = ht.get_translated_holiday_name(
        "Day off (substituted from 31/12/2099)", LOCALE
    )
    assert "31/12/2099" in result
    assert result.startswith(ht.get_translated_holiday_name("Day off", LOCALE))


def test_substituted_pattern_without_closing_paren():
    # The elif matches but the regex does not -> base/suffix unchanged.
    name = "Day off (substituted from incomplete"
    assert ht.get_translated_holiday_name(name, LOCALE) == name


def test_unknown_holiday_returns_itself():
    assert ht.get_translated_holiday_name("Totally Unknown Day", LOCALE) == (
        "Totally Unknown Day"
    )


def test_missing_locale_file_returns_original():
    assert ht.get_translated_holiday_name("Christmas Day", "zz_ZZ") == "Christmas Day"


def test_internal_alias():
    assert ht._translate_holiday_name("New Year's Day", LOCALE) == "Новый год"
