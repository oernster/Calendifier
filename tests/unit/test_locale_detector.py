"""100% coverage for locale_detector.py (no mocks; env vars only)."""

from __future__ import annotations

import pytest

from calendar_app.localization.locale_detector import (
    LocaleDetector,
    get_environment_locale,
)


def test_get_environment_locale(monkeypatch):
    for var in ("LC_ALL", "LC_CTYPE", "LANG", "LANGUAGE"):
        monkeypatch.delenv(var, raising=False)
    # No relevant variable set.
    assert get_environment_locale() is None
    # 'C'/'POSIX' are ignored.
    monkeypatch.setenv("LC_ALL", "C")
    assert get_environment_locale() is None
    # Encoding, modifier and LANGUAGE-list suffixes are stripped.
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "en_GB.UTF-8")
    assert get_environment_locale() == "en_GB"
    monkeypatch.setenv("LANG", "fr_FR@euro")
    assert get_environment_locale() == "fr_FR"
    monkeypatch.setenv("LANG", "de_DE:en_US")
    assert get_environment_locale() == "de_DE"


@pytest.fixture
def detector():
    return LocaleDetector()


def test_detect_system_locale_caches(detector, monkeypatch):
    # Control the environment so detection is deterministic regardless of the
    # host: with LANG set, Method 1 (the environment-variable path) always
    # resolves, so the result does not depend on ambient OS locale settings.
    for var in ("LC_ALL", "LC_CTYPE", "LANGUAGE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LANG", "en_GB.UTF-8")
    first = detector.detect_system_locale()
    assert first == "en_GB"
    # Second call returns the cached value without re-detecting.
    assert detector.detect_system_locale() == first
    assert detector.is_supported(first)


def test_normalize_locale_variants(detector):
    assert detector._normalize_locale("") == "en_GB"
    assert detector._normalize_locale("en_US") == "en_US"
    assert detector._normalize_locale("en_US.UTF-8") == "en_US"
    assert detector._normalize_locale("en_US@variant") == "en_US"
    # Underscore with unsupported country falls back to the language match.
    assert detector._normalize_locale("en_ZZ") == "en_US"
    # Underscore with an unknown language falls through to the default.
    assert detector._normalize_locale("qq_ZZ") == "en_GB"
    # Dash format.
    assert detector._normalize_locale("fr-FR") == "fr_FR"
    # Dash with unsupported country has no language fallback -> default.
    assert detector._normalize_locale("fr-ZZ") == "en_GB"
    # Language only.
    assert detector._normalize_locale("de").startswith("de_")
    # Completely unknown -> default.
    assert detector._normalize_locale("zz") == "en_GB"


def test_support_queries(detector):
    assert detector.is_supported("en_GB") is True
    assert detector.is_supported("zz_ZZ") is False
    assert "en_GB" in detector.get_supported_locales()


def test_sorted_locales_have_flags(detector):
    sorted_locales = LocaleDetector.get_sorted_locales()
    codes = [code for code, _ in sorted_locales]
    assert "en_GB" in codes
    assert all("flag" in info for _, info in sorted_locales)


def test_flag_emoji_known_and_unknown():
    assert LocaleDetector._get_flag_emoji("US") == "🇺🇸"
    assert LocaleDetector._get_flag_emoji("ZZ") == "🏳️"


def test_get_locale_info_classmethod():
    info = LocaleDetector.get_locale_info("en_GB")
    assert info is not None and info["flag"] == "🇬🇧"
    assert LocaleDetector.get_locale_info("zz_ZZ") is None


def test_batches(detector):
    assert "en_GB" in detector.get_locales_by_batch(1)
    assert isinstance(detector.get_batch_info(), dict)


def test_find_best_match(detector):
    assert detector.find_best_match(["fr_FR"]) == "fr_FR"
    # An unknown code normalizes to the default, which is supported.
    assert detector.find_best_match(["zz_ZZ"]) == "en_GB"
    # Empty list hits the final fallback.
    assert detector.find_best_match([]) == "en_GB"


def test_language_variants_and_rtl(detector):
    variants = detector.get_language_variants("en")
    assert "en_US" in variants and "en_GB" in variants
    assert "ar_SA" in detector.get_rtl_locales()
    assert detector.is_rtl("ar_SA") is True
    assert detector.is_rtl("en_US") is False


def test_country_from_locale():
    assert LocaleDetector.get_country_from_locale("en_US") == "US"
    assert LocaleDetector.get_country_from_locale("nocountry") == "GB"
