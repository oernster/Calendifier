"""
Holiday translation mappings for all supported locales.

This file contains ONLY locale-specific holiday translations with ZERO
cross-contamination. Each locale translates ONLY holidays that are TRULY
specific to that country/culture. Common holidays like "New Year's Day",
"Christmas Day" and "Labor Day" remain in English unless culturally specific.
"""

import re

# NOTE: Holiday translations are now handled exclusively through JSON files in
# calendar_app/localization/locale_holiday_translations/. This eliminates the
# need for a hardcoded dictionary and provides a single source of truth.


def get_translated_holiday_name(holiday_name: str, locale: str) -> str:
    """
    Get the translated name for a holiday in the specified locale.

    Args:
        holiday_name: The English holiday name
        locale: The target locale (e.g., 'es_ES', 'ru_RU')

    Returns:
        The translated holiday name, or the original name if no translation exists
    """
    if not holiday_name or not locale:
        return holiday_name

    # First, try to get exact translation from the locale file. This handles
    # complete patterns like "Independence Day (observed)" or
    # "Day off (substituted from 01/04/2025)".
    exact_translation = _get_translation_from_locale_file(holiday_name, locale)
    if exact_translation != holiday_name:
        # Found exact translation, return it
        return exact_translation

    # If no exact match, try to parse and reconstruct patterns
    base_holiday = holiday_name
    suffix = ""

    # Check for observed pattern
    if " (observed)" in holiday_name:
        base_holiday = holiday_name.replace(" (observed)", "")
        suffix = " (observed)"

    # Check for substituted pattern
    elif "Day off (substituted from" in holiday_name:
        # Extract date part
        match = re.search(r"Day off \(substituted from (.+?)\)", holiday_name)
        if match:
            date_part = match.group(1)
            base_holiday = "Day off"
            suffix = f" (substituted from {date_part})"

    # Get translation for base holiday
    translated_base = _get_translation_from_locale_file(base_holiday, locale)

    # Handle suffix translation
    if suffix:
        if suffix == " (observed)":
            observed_translation = _get_translation_from_locale_file("observed", locale)
            return f"{translated_base} ({observed_translation})"
        elif "substituted from" in suffix:  # pragma: no branch - suffix is exhaustive
            substituted_translation = _get_translation_from_locale_file(
                "substituted from", locale
            )
            # Extract the date part and keep it as-is
            date_match = re.search(r"substituted from (.+)", suffix)
            if date_match:  # pragma: no branch - suffix always carries the date

                date_part = date_match.group(1)
                return f"{translated_base} ({substituted_translation} {date_part})"

    return translated_base


def _get_translation_from_locale_file(holiday_name: str, locale: str) -> str:
    """
    Get holiday translation from the locale JSON file.

    Args:
        holiday_name: The English holiday name
        locale: The target locale (e.g., 'es_ES', 'ru_RU')

    Returns:
        The translated holiday name, or the original name if no translation exists
    """
    try:
        from pathlib import Path
        import json

        # Load holiday translation file directly (not the main translation file)
        locale_file = (
            Path(__file__).parent.parent
            / "localization"
            / "locale_holiday_translations"
            / f"{locale}_holidays.json"
        )

        if locale_file.exists():
            with open(locale_file, "r", encoding="utf-8") as f:
                holiday_data = json.load(f)
                return holiday_data.get(holiday_name, holiday_name)

    except Exception as e:  # pragma: no cover - valid JSON files ship with the app
        # If anything goes wrong, return original name
        print(f"Error loading holiday translation: {e}")

    return holiday_name


def _translate_holiday_name(holiday_name: str, locale: str) -> str:
    """
    Internal method for translating holiday names.
    This is called by the multi_country_holiday_provider.
    """
    return get_translated_holiday_name(holiday_name, locale)
