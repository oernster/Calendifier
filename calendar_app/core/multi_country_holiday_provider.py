"""
🌍 Multi-Country Holiday Provider

This module provides holiday data for the 14 major international countries
corresponding to our supported languages. It includes country support with
flags, names, and holiday codes for the most important international markets.
"""

# Long log/dict-literal strings here cannot wrap without changing content.
# flake8: noqa: E501

import logging
from datetime import date
from typing import Dict, List, Optional, TYPE_CHECKING
import holidays
from calendar_app.core.holiday_translations import get_translated_holiday_name
from calendar_app.core.observance_data import observance_dates

if TYPE_CHECKING:
    from calendar_app.data.models import Holiday

logger = logging.getLogger(__name__)


class MultiCountryHolidayProvider:
    """🌍 Provides holiday data for multiple countries with caching."""

    # Sentinel meaning "derive the holiday region from the selected timezone".
    AUTO_COUNTRY = "auto"

    # NOTE: Holiday filtering is now handled by culturally-specific JSON files
    # Each locale contains only holidays appropriate for that culture
    # No exclusion system needed - single source of truth approach

    # Major international countries matching our supported languages
    SUPPORTED_COUNTRIES = {
        # Core international countries corresponding to our major languages
        "US": {"name": "United States", "flag": "🇺🇸", "code": "US"},  # en_US
        "CA": {"name": "Canada", "flag": "🇨🇦", "code": "CA"},  # fr_CA
        "ES": {"name": "Spain", "flag": "🇪🇸", "code": "ES"},  # es_ES
        "FR": {"name": "France", "flag": "🇫🇷", "code": "FR"},  # fr_FR
        "DE": {"name": "Germany", "flag": "🇩🇪", "code": "DE"},  # de_DE
        "IT": {"name": "Italy", "flag": "🇮🇹", "code": "IT"},  # it_IT
        "BR": {"name": "Brazil", "flag": "🇧🇷", "code": "BR"},  # pt_BR
        "RU": {"name": "Russia", "flag": "🇷🇺", "code": "RU"},  # ru_RU
        "CN": {"name": "China", "flag": "🇨🇳", "code": "CN"},  # zh_CN
        "TW": {"name": "Taiwan", "flag": "🇹🇼", "code": "TW"},  # zh_TW
        "JP": {"name": "Japan", "flag": "🇯🇵", "code": "JP"},  # ja_JP
        "KR": {"name": "South Korea", "flag": "🇰🇷", "code": "KR"},  # ko_KR
        "IN": {"name": "India", "flag": "🇮🇳", "code": "IN"},  # hi_IN
        "SA": {"name": "Saudi Arabia", "flag": "🇸🇦", "code": "SA"},  # ar_SA
        "CZ": {"name": "Czech Republic", "flag": "🇨🇿", "code": "CZ"},  # cs_CZ
        "SE": {"name": "Sweden", "flag": "🇸🇪", "code": "SE"},  # sv_SE
        "NO": {"name": "Norway", "flag": "🇳🇴", "code": "NO"},  # nb_NO
        "DK": {"name": "Denmark", "flag": "🇩🇰", "code": "DK"},  # da_DK
        "FI": {"name": "Finland", "flag": "🇫🇮", "code": "FI"},  # fi_FI
        "NL": {"name": "Netherlands", "flag": "🇳🇱", "code": "NL"},  # nl_NL
        "PL": {"name": "Poland", "flag": "🇵🇱", "code": "PL"},  # pl_PL
        "PT": {"name": "Portugal", "flag": "🇵🇹", "code": "PT"},  # pt_PT
        "TR": {"name": "Turkey", "flag": "🇹🇷", "code": "TR"},  # tr_TR
        "UA": {"name": "Ukraine", "flag": "🇺🇦", "code": "UA"},  # uk_UA
        "GR": {"name": "Greece", "flag": "🇬🇷", "code": "GR"},  # el_GR
        "ID": {"name": "Indonesia", "flag": "🇮🇩", "code": "ID"},  # id_ID
        "VN": {"name": "Vietnam", "flag": "🇻🇳", "code": "VN"},  # vi_VN
        "TH": {"name": "Thailand", "flag": "🇹🇭", "code": "TH"},  # th_TH
        "IL": {"name": "Israel", "flag": "🇮🇱", "code": "IL"},  # he_IL
        "RO": {"name": "Romania", "flag": "🇷🇴", "code": "RO"},  # ro_RO
        "HU": {"name": "Hungary", "flag": "🇭🇺", "code": "HU"},  # hu_HU
        "HR": {"name": "Croatia", "flag": "🇭🇷", "code": "HR"},  # hr_HR
        "BG": {"name": "Bulgaria", "flag": "🇧🇬", "code": "BG"},  # bg_BG
        "SK": {"name": "Slovakia", "flag": "🇸🇰", "code": "SK"},  # sk_SK
        "SI": {"name": "Slovenia", "flag": "🇸🇮", "code": "SI"},  # sl_SI
        "EE": {"name": "Estonia", "flag": "🇪🇪", "code": "EE"},  # et_EE
        "LV": {"name": "Latvia", "flag": "🇱🇻", "code": "LV"},  # lv_LV
        "LT": {"name": "Lithuania", "flag": "🇱🇹", "code": "LT"},  # lt_LT
        "CT": {
            "name": "Catalonia",
            # Catalonia is a region of Spain and has no flag emoji that renders
            # on Windows, so it shares the Spanish flag; the "Catalunya" label
            # distinguishes it from the Spain entry.
            "flag": "🇪🇸",
            "code": "ES",
        },  # ca_ES (Catalan region)
        # Keep GB for backward compatibility (default fallback)
        "GB": {"name": "United Kingdom", "flag": "🇬🇧", "code": "UK"},  # Legacy default
    }

    # Maps an IANA timezone id to one of the SUPPORTED_COUNTRIES keys above, so
    # the holiday region can be inferred from the user's selected timezone.
    # Only zones whose country we actually support are listed; anything else
    # resolves to None and the caller falls back (locale, then GB).
    TIMEZONE_TO_COUNTRY = {
        # Europe
        "Europe/London": "GB",
        "Europe/Paris": "FR",
        "Europe/Berlin": "DE",
        "Europe/Rome": "IT",
        "Europe/Madrid": "ES",
        "Europe/Barcelona": "ES",
        "Europe/Moscow": "RU",
        "Europe/Prague": "CZ",
        "Europe/Stockholm": "SE",
        "Europe/Oslo": "NO",
        "Europe/Copenhagen": "DK",
        "Europe/Helsinki": "FI",
        "Europe/Amsterdam": "NL",
        "Europe/Warsaw": "PL",
        "Europe/Lisbon": "PT",
        "Europe/Istanbul": "TR",
        "Europe/Kyiv": "UA",
        "Europe/Kiev": "UA",
        "Europe/Athens": "GR",
        "Europe/Bucharest": "RO",
        "Europe/Budapest": "HU",
        "Europe/Zagreb": "HR",
        "Europe/Sofia": "BG",
        "Europe/Bratislava": "SK",
        "Europe/Ljubljana": "SI",
        "Europe/Tallinn": "EE",
        "Europe/Riga": "LV",
        "Europe/Vilnius": "LT",
        # Americas (all US zones share the US federal holiday set)
        "America/New_York": "US",
        "America/Detroit": "US",
        "America/Chicago": "US",
        "America/Denver": "US",
        "America/Phoenix": "US",
        "America/Los_Angeles": "US",
        "America/Anchorage": "US",
        "America/Toronto": "CA",
        "America/Montreal": "CA",
        "America/Vancouver": "CA",
        "America/Sao_Paulo": "BR",
        # Asia / Middle East
        "Asia/Tokyo": "JP",
        "Asia/Shanghai": "CN",
        "Asia/Taipei": "TW",
        "Asia/Seoul": "KR",
        "Asia/Kolkata": "IN",
        "Asia/Calcutta": "IN",
        "Asia/Riyadh": "SA",
        "Asia/Jakarta": "ID",
        "Asia/Ho_Chi_Minh": "VN",
        "Asia/Bangkok": "TH",
        "Asia/Jerusalem": "IL",
    }

    # Fallback holiday data for countries not supported by holidays library
    # Note: These will be filtered based on EXCLUDED_HOLIDAYS for each country
    FALLBACK_HOLIDAYS = {"New Year's Day": "01-01", "Christmas Day": "12-25"}

    # Custom holiday data for countries not supported by the holidays library
    # Ukraine is not supported by the Python holidays library, so we provide comprehensive data
    CUSTOM_HOLIDAYS = {
        "UA": {
            # Fixed date holidays
            "New Year's Day": "01-01",
            "Orthodox Christmas Day": "01-07",
            "International Women's Day": "03-08",
            "Labour Day": "05-01",
            "Victory Day": "05-09",
            "Constitution Day": "06-28",
            "Independence Day": "08-24",
            "Defender of Ukraine Day": "10-14",
            "Christmas Day": "12-25",
            # Note: Easter-based holidays are calculated dynamically
            # Orthodox Easter, Easter Monday, etc. will be calculated based on Orthodox calendar
        }
    }

    def __init__(self, country_code: str = "GB"):
        """
        Initialize the multi-country holiday provider.

        Args:
            country_code: ISO 3166-1 alpha-2 country code (defaults to GB for United Kingdom)
        """
        self.country_code = country_code.upper()
        self._holiday_cache: Dict[str, holidays.HolidayBase] = {}
        self._fallback_cache: Dict[str, Dict[date, str]] = {}
        self._observance_cache: Dict[str, Dict[date, str]] = {}

        # Validate country code
        if self.country_code not in self.SUPPORTED_COUNTRIES:
            logger.warning(
                f"⚠️ Country code '{self.country_code}' not supported, falling back to GB"
            )
            self.country_code = "GB"

        logger.debug(
            f"🌍 Initialized holiday provider for {self.get_country_display_name()}"
        )

    def _get_current_locale(self) -> str:
        """Get the current application locale for holiday translations."""
        try:
            # Try multiple sources to get the current locale.
            current_locale = None

            # First, try to get from the I18n manager.
            try:
                from calendar_app.localization.i18n_manager import get_i18n_manager

                i18n_manager = get_i18n_manager()
                current_locale = i18n_manager.current_locale
                logger.debug(f"🌍 Locale from I18n manager: {current_locale}")
            except Exception as i18n_error:  # pragma: no cover - i18n is available
                logger.debug(f"🌍 I18n manager not available: {i18n_error}")

            # If the I18n manager failed, try the settings manager.
            if not current_locale:  # pragma: no cover - i18n provides the locale
                try:
                    from calendar_app.config.settings import SettingsManager
                    from pathlib import Path

                    app_data_dir = Path.home() / ".calendar_app"
                    settings_file = app_data_dir / "settings.json"
                    settings_manager = SettingsManager(settings_file)
                    settings_locale = settings_manager.get_locale()
                    if settings_locale:
                        current_locale = settings_locale
                        logger.debug(f"🌍 Locale from settings: {current_locale}")
                except Exception as settings_error:
                    logger.debug(f"🌍 Settings manager not available: {settings_error}")

            # If still no locale, try system locale detection.
            if not current_locale:  # pragma: no cover - i18n provides the locale
                try:
                    from calendar_app.localization.locale_detector import (
                        LocaleDetector,
                    )

                    detector = LocaleDetector()
                    detected_locale = detector.detect_system_locale()
                    if detected_locale:
                        current_locale = detected_locale
                        logger.debug(f"🌍 Detected system locale: {current_locale}")
                except Exception as detect_error:
                    logger.debug(f"🌍 System locale detection failed: {detect_error}")

            # Final fallback - GB to match our default settings.
            if not current_locale:  # pragma: no cover - i18n provides the locale
                current_locale = "en_GB"
                logger.debug("🌍 Falling back to en_GB locale")

            return current_locale
        except Exception as e:  # pragma: no cover - defensive ultimate fallback
            logger.debug(f"🌍 Falling back to en_GB locale due to error: {e}")
            return "en_GB"

    def _auto_update_country_from_locale(self, locale: str) -> None:
        """Automatically update country to match the current locale."""
        # Mapping of locales to their corresponding countries
        locale_to_country = {
            "en_US": "US",
            "en_GB": "GB",
            "fr_CA": "CA",
            "es_ES": "ES",
            "fr_FR": "FR",
            "de_DE": "DE",
            "it_IT": "IT",
            "pt_BR": "BR",
            "ru_RU": "RU",
            "zh_CN": "CN",
            "zh_TW": "TW",
            "ja_JP": "JP",
            "ko_KR": "KR",
            "hi_IN": "IN",
            "ar_SA": "SA",
            "cs_CZ": "CZ",
            "sv_SE": "SE",
            "nb_NO": "NO",
            "da_DK": "DK",
            "fi_FI": "FI",
            "nl_NL": "NL",
            "pl_PL": "PL",
            "pt_PT": "PT",
            "tr_TR": "TR",
            "uk_UA": "UA",
            "el_GR": "GR",
            "id_ID": "ID",
            "vi_VN": "VN",
            "he_IL": "IL",
            "ro_RO": "RO",
            "hu_HU": "HU",
            "hr_HR": "HR",
            "bg_BG": "BG",
            "sk_SK": "SK",
            "sl_SI": "SI",
            "et_EE": "EE",
            "lv_LV": "LV",
            "lt_LT": "LT",
            "ca_ES": "CT",
        }

        expected_country = locale_to_country.get(locale)
        if expected_country and expected_country != self.country_code:
            logger.debug(
                f"🌍 Auto-updating country from {self.country_code} to {expected_country} to match locale {locale}"
            )
            self.country_code = expected_country
            self._holiday_cache.clear()
            self._fallback_cache.clear()
            self._observance_cache.clear()

    def _translate_holiday_name(self, english_name: str) -> str:
        """Translate holiday name based on the current UI locale."""
        # CRITICAL FIX: Translate holidays based on the current UI locale, not the country
        # Users should see holidays in their chosen UI language
        # This ensures consistency with the rest of the application interface

        # Get the current UI locale for translation
        current_locale = self._get_current_locale()
        return get_translated_holiday_name(english_name, current_locale)

    def get_country_display_name(self) -> str:
        """Get the display name for the current country."""
        country_info = self.SUPPORTED_COUNTRIES.get(
            self.country_code, self.SUPPORTED_COUNTRIES["GB"]
        )
        return f"{country_info['flag']} {country_info['name']}"

    def set_country(self, country_code: str) -> None:
        """
        Change the country for holiday calculations.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
        """
        new_code = country_code.upper()
        if new_code not in self.SUPPORTED_COUNTRIES:
            logger.warning(f"⚠️ Country code '{new_code}' not supported")
            return

        if new_code != self.country_code:
            old_country = self.country_code
            self.country_code = new_code
            self._holiday_cache.clear()
            self._fallback_cache.clear()
            self._observance_cache.clear()
            logger.debug(
                f"🌍 Changed country from {old_country} to {self.get_country_display_name()}"
            )

            # Force refresh locale detection after country change
            current_locale = self._get_current_locale()
            logger.debug(f"🌍 Refreshed locale after country change: {current_locale}")

    # NOTE: Holiday filtering removed - now using culturally-specific JSON files
    # Each locale contains only appropriate holidays, no filtering needed

    def _get_holidays_for_year(self, year: int) -> holidays.HolidayBase:
        """Get holidays for a specific year with caching."""
        cache_key = f"{self.country_code}_{year}"
        if cache_key not in self._holiday_cache:
            try:
                country_info = self.SUPPORTED_COUNTRIES[self.country_code]
                holiday_code = country_info["code"]

                # Special handling for UK to get complete holiday set including Easter Monday and August Bank Holiday
                if holiday_code == "UK":
                    raw_holidays = holidays.UK(subdiv="England", years=year)
                    logger.debug(
                        f"📅 Loaded UK (England) holidays for {country_info['name']} ({year})"
                    )
                else:
                    # Create holidays instance for other countries
                    raw_holidays = holidays.country_holidays(holiday_code, years=year)
                    logger.debug(
                        f"📅 Loaded holidays for {country_info['name']} ({year})"
                    )

                # CRITICAL FIX: Filter out bogus "Sunday" entries from Swedish holidays library
                # The Swedish holidays library incorrectly marks ALL Sundays as holidays
                if self.country_code == "SE":
                    filtered_holidays = holidays.HolidayBase()
                    for holiday_date, holiday_name in raw_holidays.items():
                        # Skip generic "Sunday" entries that are not real holidays
                        if (
                            holiday_name.strip() == "Sunday"
                        ):  # pragma: no cover - SE bare-Sunday entries gone in holidays 0.75
                            logger.debug(
                                f"🚫 Filtering out bogus Sunday holiday: {holiday_date} - {holiday_name}"
                            )
                            continue
                        # Keep legitimate holidays that may contain "Sunday" as part of compound names
                        filtered_holidays[holiday_date] = holiday_name

                    logger.debug(
                        f"📅 Filtered Swedish holidays: {len(raw_holidays)} -> {len(filtered_holidays)} (removed {len(raw_holidays) - len(filtered_holidays)} bogus Sunday entries)"
                    )
                    self._holiday_cache[cache_key] = filtered_holidays
                else:
                    # Use holidays directly for other countries - no filtering needed
                    self._holiday_cache[cache_key] = raw_holidays

            except (
                Exception
            ) as e:  # pragma: no cover - defensive; valid country codes do not raise
                logger.warning(
                    f"⚠️ Failed to load holidays for {self.country_code} ({year}): {e}"
                )
                # Create empty holidays instance as fallback
                self._holiday_cache[cache_key] = holidays.HolidayBase()

        return self._holiday_cache[cache_key]

    def _get_custom_holidays_for_year(self, year: int) -> Dict[date, str]:
        """Get custom holidays for countries not supported by holidays library."""
        cache_key = f"{self.country_code}_custom_{year}"
        if cache_key not in self._fallback_cache:
            custom_holidays = {}

            # Check if we have custom holiday data for this country
            if self.country_code in self.CUSTOM_HOLIDAYS:
                country_holidays = self.CUSTOM_HOLIDAYS[self.country_code]
                for name, date_str in country_holidays.items():
                    try:
                        month, day = map(int, date_str.split("-"))
                        holiday_date = date(year, month, day)
                        custom_holidays[holiday_date] = name
                    except (
                        ValueError
                    ):  # pragma: no cover - defensive; CUSTOM_HOLIDAYS dates are valid
                        continue

                logger.debug(
                    f"📅 Loaded {len(custom_holidays)} custom holidays for {self.country_code} ({year})"
                )

            self._fallback_cache[cache_key] = custom_holidays

        return self._fallback_cache[cache_key]

    def _get_fallback_holidays_for_year(self, year: int) -> Dict[date, str]:
        """Get fallback holidays for a specific year."""
        cache_key = f"{self.country_code}_{year}"
        if cache_key not in self._fallback_cache:
            # First try custom holidays for this country
            custom_holidays = self._get_custom_holidays_for_year(year)
            if custom_holidays:
                # Use custom holidays if available
                self._fallback_cache[cache_key] = custom_holidays
                return custom_holidays

            # Fall back to basic holidays if no custom data
            fallback_holidays = {}
            for name, date_str in self.FALLBACK_HOLIDAYS.items():
                try:
                    month, day = map(int, date_str.split("-"))
                    holiday_date = date(year, month, day)
                    fallback_holidays[holiday_date] = name
                except (
                    ValueError
                ):  # pragma: no cover - defensive; FALLBACK_HOLIDAYS dates are valid
                    continue

            # Use fallback holidays directly - no filtering needed
            self._fallback_cache[cache_key] = fallback_holidays

        return self._fallback_cache[cache_key]

    def _get_observances_for_year(self, year: int) -> Dict[date, str]:
        """Get cultural observances (non-bank-holiday days) for a year.

        Observances (Father's Day, Valentine's Day, ...) are display-only
        markers: they appear in the calendar but are NOT days off, so they are
        deliberately excluded from is_holiday and the working-day calculations.
        """
        cache_key = f"{self.country_code}_obs_{year}"
        if cache_key not in self._observance_cache:
            self._observance_cache[cache_key] = observance_dates(
                self.country_code, year
            )
        return self._observance_cache[cache_key]

    def _resolve_holiday(self, check_date: date) -> Optional[tuple]:
        """Return (english_name, type) for a date, or None.

        Bank/public holidays win over observances when both fall on a date.
        ``type`` is one of 'bank_holiday' or 'observance'.
        """
        holidays_for_year = self._get_holidays_for_year(check_date.year)
        if check_date in holidays_for_year:
            return holidays_for_year[check_date], "bank_holiday"

        fallback_holidays = self._get_fallback_holidays_for_year(check_date.year)
        if check_date in fallback_holidays:
            return fallback_holidays[check_date], "bank_holiday"

        observances = self._get_observances_for_year(check_date.year)
        if check_date in observances:
            return observances[check_date], "observance"

        return None

    def is_holiday(self, check_date: date) -> bool:
        """
        Check if a given date is a holiday.

        Args:
            check_date: The date to check

        Returns:
            True if the date is a holiday, False otherwise
        """
        try:
            holidays_for_year = self._get_holidays_for_year(check_date.year)
            if check_date in holidays_for_year:
                return True

            # Check fallback holidays if not found in main holidays
            fallback_holidays = self._get_fallback_holidays_for_year(check_date.year)
            return check_date in fallback_holidays

        except Exception as e:  # pragma: no cover - defensive guard
            logger.warning(f"⚠️ Error checking holiday for {check_date}: {e}")
            return False

    def get_holiday(self, check_date: date) -> Optional[str]:
        """
        Get the holiday name for a given date.

        Args:
            check_date: The date to check

        Returns:
            Translated holiday name if the date is a holiday, None otherwise
        """
        try:
            resolved = self._resolve_holiday(check_date)
            if resolved is not None:
                return self._translate_holiday_name(resolved[0])
            return None

        except Exception as e:  # pragma: no cover - defensive guard
            logger.warning(f"⚠️ Error getting holiday for {check_date}: {e}")
            return None

    def get_holiday_object(self, check_date: date) -> Optional["Holiday"]:
        """
        Get the Holiday object for a given date.

        Args:
            check_date: The date to check

        Returns:
            Holiday object with translated name if the date is a holiday, None otherwise
        """
        try:
            from calendar_app.data.models import Holiday

            resolved = self._resolve_holiday(check_date)
            if resolved is not None:
                english_name, holiday_type = resolved
                return Holiday(
                    name=self._translate_holiday_name(english_name),
                    date=check_date,
                    country_code=self.country_code,
                    type=holiday_type,
                    is_observed=True,
                )
            return None

        except Exception as e:  # pragma: no cover - defensive guard
            logger.warning(f"⚠️ Error getting holiday object for {check_date}: {e}")
            return None

    def get_holidays_for_month(self, year: int, month: int) -> List["Holiday"]:
        """
        Get all holidays for a specific month.

        Args:
            year: The year
            month: The month (1-12)

        Returns:
            List of Holiday objects with translated names for the month
        """
        try:
            from calendar_app.data.models import Holiday

            holidays_for_year = self._get_holidays_for_year(year)
            fallback_holidays = self._get_fallback_holidays_for_year(year)

            # Combine both holiday sources
            all_holidays = dict(holidays_for_year)
            all_holidays.update(fallback_holidays)

            # Filter for the specific month and create Holiday objects with translated names
            month_holidays = []
            for holiday_date, english_name in all_holidays.items():
                if holiday_date.month == month:
                    translated_name = self._translate_holiday_name(english_name)
                    holiday = Holiday(
                        name=translated_name,
                        date=holiday_date,
                        country_code=self.country_code,
                        type="bank_holiday",
                        is_observed=True,
                    )
                    month_holidays.append(holiday)

            # Add observances (display-only cultural days). A bank holiday on the
            # same date wins, so observances do not override real public holidays.
            observances = self._get_observances_for_year(year)
            for holiday_date, english_name in observances.items():
                if holiday_date.month == month and holiday_date not in all_holidays:
                    month_holidays.append(
                        Holiday(
                            name=self._translate_holiday_name(english_name),
                            date=holiday_date,
                            country_code=self.country_code,
                            type="observance",
                            is_observed=True,
                        )
                    )

            return month_holidays

        except Exception as e:  # pragma: no cover - defensive guard
            logger.warning(f"⚠️ Error getting holidays for {year}-{month:02d}: {e}")
            return []

    def is_weekend(self, check_date: date) -> bool:
        """
        Check if a given date is a weekend.

        Args:
            check_date: The date to check

        Returns:
            True if the date is a weekend (Saturday or Sunday), False otherwise
        """
        # Saturday = 5, Sunday = 6 in Python's weekday() method
        return check_date.weekday() >= 5

    def is_weekend_or_holiday(self, check_date: date) -> bool:
        """
        Check if a given date is a weekend or holiday.

        Args:
            check_date: The date to check

        Returns:
            True if the date is a weekend or holiday, False otherwise
        """
        return self.is_weekend(check_date) or self.is_holiday(check_date)

    def get_working_days_in_month(self, year: int, month: int) -> List[date]:
        """
        Get all working days (non-weekend, non-holiday) in a month.

        Args:
            year: The year
            month: The month (1-12)

        Returns:
            List of working day dates
        """
        try:
            from calendar import monthrange

            working_days = []
            _, last_day = monthrange(year, month)

            for day in range(1, last_day + 1):
                check_date = date(year, month, day)
                if not self.is_weekend_or_holiday(check_date):
                    working_days.append(check_date)

            return working_days

        except Exception as e:  # pragma: no cover - defensive guard
            logger.warning(f"⚠️ Error getting working days for {year}-{month:02d}: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear the holiday cache to free memory."""
        self._holiday_cache.clear()
        self._fallback_cache.clear()
        self._observance_cache.clear()
        logger.debug("🧹 Holiday cache cleared")

    def refresh_translations(self) -> None:
        """🔄 Refresh holiday translations by clearing cache.

        This should be called when the locale changes to ensure
        holiday names are re-translated in the new language.
        """
        # Clear cache to force reload with new locale
        self.clear_cache()

        # Force re-detection of current locale
        current_locale = self._get_current_locale()

        # Pre-load current year holidays to ensure they're available immediately
        from datetime import date

        current_year = date.today().year
        self._get_holidays_for_year(current_year)

        logger.debug(
            f"🌍 Holiday translations refreshed for locale change to: {current_locale}"
        )

    def force_locale_refresh(self) -> None:
        """🔄 Force complete locale refresh - useful during app startup.

        This method should be called after the application is fully initialized
        to ensure the holiday provider uses the correct locale.
        """
        logger.debug("🌍 Forcing complete locale refresh for holiday provider")

        # Clear all caches
        self.clear_cache()

        # Force re-detection of locale and country
        current_locale = self._get_current_locale()

        # Pre-load holidays for current and next year
        from datetime import date

        current_year = date.today().year
        self._get_holidays_for_year(current_year)
        self._get_holidays_for_year(current_year + 1)

        logger.debug(
            f"🌍 Complete locale refresh completed - using locale: {current_locale}, country: {self.country_code}"
        )

    @classmethod
    def get_country_from_timezone(cls, timezone_id: Optional[str]) -> Optional[str]:
        """🌍 Infer a supported holiday-country code from an IANA timezone id.

        Args:
            timezone_id: IANA timezone (e.g. 'Europe/London'), or None.

        Returns:
            A SUPPORTED_COUNTRIES key (e.g. 'GB'), or None when the timezone
            does not map to a country we provide holidays for.
        """
        if not timezone_id:
            return None
        return cls.TIMEZONE_TO_COUNTRY.get(timezone_id)

    @classmethod
    def get_supported_countries(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all supported countries.

        Returns:
            Dictionary of country codes to country information
        """
        return cls.SUPPORTED_COUNTRIES.copy()

    @classmethod
    def get_sorted_countries(cls) -> List[tuple]:
        """
        Get all supported countries sorted alphabetically by name.

        Returns:
            List of tuples (country_code, country_info) sorted by country name
        """
        return sorted(cls.SUPPORTED_COUNTRIES.items(), key=lambda x: x[1]["name"])
