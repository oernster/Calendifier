"""100% coverage for number_formatter.py (localized numerals)."""

from __future__ import annotations

from calendar_app.localization import number_formatter as nf


def test_format_number_native_systems():
    fmt = nf.NumberFormatter()
    assert fmt.format_number(123, "ar_SA") == "١٢٣"
    assert fmt.format_number(90, "hi_IN") == "९०"
    assert fmt.format_number(7, "th_TH") == "๗"


def test_format_number_western_and_default():
    fmt = nf.NumberFormatter()
    # Western-Arabic locale keeps plain digits.
    assert fmt.format_number(42, "de_DE") == "42"
    # Unknown locale defaults to plain digits.
    assert fmt.format_number(42, "en_US") == "42"
    # Native locale but use_native disabled -> western/default branch.
    assert fmt.format_number(42, "ar_SA", use_native=False) == "42"


def test_format_ordinal_native_locales():
    fmt = nf.NumberFormatter()
    assert fmt.format_ordinal(3, "ar_SA") == "٣"
    assert fmt.format_ordinal(2, "hi_IN") == "२वां"
    assert fmt.format_ordinal(1, "hi_IN") == "१ला"
    assert fmt.format_ordinal(5, "th_TH") == "ที่ ๕"


def test_format_ordinal_non_native():
    fmt = nf.NumberFormatter()
    assert fmt.format_ordinal(5, "en_US") == "5"


def test_is_native_and_supported_locales():
    fmt = nf.NumberFormatter()
    assert fmt.is_native_number_locale("th_TH") is True
    assert fmt.is_native_number_locale("de_DE") is False
    supported = fmt.get_supported_locales()
    assert "ar_SA" in supported
    assert "de_DE" in supported


def test_module_level_helpers():
    assert nf.format_number(8, "th_TH") == "๘"
    assert nf.format_ordinal(5, "th_TH") == "ที่ ๕"
    assert nf.is_native_number_locale("hi_IN") is True
    assert nf.is_native_number_locale("fr_FR") is False
