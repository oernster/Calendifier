"""Native country names (endonyms) for the holiday-country selector.

Each country is shown in its own primary language, fixed and independent of the
application's UI locale, so changing the interface language never changes the
country dropdown. This deliberately avoids a per-UI-language translation matrix:
a Japanese user sees Japan as 日本 and Germany as Deutschland, not Germany in
Japanese.

One primary endonym per country. Genuinely multilingual countries use their most
widely-used official name rather than a slash-joined list.
"""

from __future__ import annotations

# Country code (matching MultiCountryHolidayProvider.SUPPORTED_COUNTRIES) ->
# the country's name in its own primary language.
ENDONYMS: dict[str, str] = {
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "ES": "España",
    "FR": "France",
    "DE": "Deutschland",
    "IT": "Italia",
    "BR": "Brasil",
    "RU": "Россия",
    "CN": "中国",
    "TW": "台灣",
    "JP": "日本",
    "KR": "대한민국",
    "IN": "भारत",
    "SA": "السعودية",
    "CZ": "Česko",
    "SE": "Sverige",
    "NO": "Norge",
    "DK": "Danmark",
    "FI": "Suomi",
    "NL": "Nederland",
    "PL": "Polska",
    "PT": "Portugal",
    "TR": "Türkiye",
    "UA": "Україна",
    "GR": "Ελλάδα",
    "ID": "Indonesia",
    "VN": "Việt Nam",
    "TH": "ไทย",
    "IL": "ישראל",
    "RO": "România",
    "HU": "Magyarország",
    "HR": "Hrvatska",
    "BG": "България",
    "SK": "Slovensko",
    "SI": "Slovenija",
    "EE": "Eesti",
    "LV": "Latvija",
    "LT": "Lietuva",
    "CT": "Catalunya",
}


def endonym(country_code: str, fallback: str = "") -> str:
    """Return a country's native name, or ``fallback`` if it is not defined."""
    return ENDONYMS.get(country_code.upper(), fallback)
