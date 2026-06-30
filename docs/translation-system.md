# 🌍 Translation System

This document provides a detailed explanation of the translation system used in Calendifier, including file structure, translation loading, and usage.

## Table of Contents

- [Translation File Structure](#translation-file-structure)
- [Translation Loading](#translation-loading)
- [Translation Usage](#translation-usage)
- [Fallback Mechanism](#fallback-mechanism)
- [Runtime Language Switching](#runtime-language-switching)
- [Translation Management](#translation-management)
- [Adding New Languages](#adding-new-languages)

## Translation File Structure

Calendifier uses JSON files for translations, located in the `calendar_app/localization/translations/` directory. Each language has its own file named with the locale code (e.g., `en_US.json`, `fr_FR.json`).

### Translation File Example

```json
{
  "_metadata": {
    "language": "English (UK)",
    "native_name": "English (UK)",
    "country": "GB",
    "flag": "🇬🇧",
    "completion": "100"
  },
  "app_name": "Calendifier",
  "menu": {
    "file": {
      "title": "File",
      "new": "New",
      "open": "Open",
      "save": "Save",
      "exit": "Exit"
    },
    "edit": {
      "title": "Edit",
      "undo": "Undo",
      "redo": "Redo",
      "cut": "Cut",
      "copy": "Copy",
      "paste": "Paste"
    },
    "view": {
      "title": "View",
      "zoom_in": "Zoom In",
      "zoom_out": "Zoom Out",
      "reset_zoom": "Reset Zoom"
    },
    "help": {
      "title": "Help",
      "about": "About",
      "documentation": "Documentation"
    }
  },
  "calendar": {
    "months": {
      "january": "January",
      "february": "February",
      "march": "March",
      "april": "April",
      "may": "May",
      "june": "June",
      "july": "July",
      "august": "August",
      "september": "September",
      "october": "October",
      "november": "November",
      "december": "December"
    },
    "days": {
      "monday": "Monday",
      "tuesday": "Tuesday",
      "wednesday": "Wednesday",
      "thursday": "Thursday",
      "friday": "Friday",
      "saturday": "Saturday",
      "sunday": "Sunday"
    },
    "days_short": {
      "mon": "Mon",
      "tue": "Tue",
      "wed": "Wed",
      "thu": "Thu",
      "fri": "Fri",
      "sat": "Sat",
      "sun": "Sun"
    }
  },
  "events": {
    "title": "Events",
    "new_event": "New Event",
    "edit_event": "Edit Event",
    "delete_event": "Delete Event",
    "event_title": "Event Title",
    "event_description": "Event Description",
    "event_date": "Event Date",
    "event_time": "Event Time",
    "all_day": "All Day",
    "categories": {
      "default": "Default",
      "work": "Work",
      "personal": "Personal",
      "family": "Family",
      "holiday": "Holiday",
      "other": "Other"
    }
  },
  "notes": {
    "title": "Notes",
    "new_note": "New Note",
    "edit_note": "Edit Note",
    "delete_note": "Delete Note",
    "note_title": "Note Title",
    "note_content": "Note Content"
  },
  "settings": {
    "title": "Settings",
    "language": "Language",
    "theme": "Theme",
    "dark_mode": "Dark Mode",
    "light_mode": "Light Mode",
    "first_day_of_week": "First Day of Week",
    "holiday_country": "Holiday Country",
    "time_format": "Time Format",
    "date_format": "Date Format",
    "save": "Save",
    "cancel": "Cancel"
  },
  "dialogs": {
    "confirmation": {
      "title": "Confirmation",
      "delete_event": "Are you sure you want to delete this event?",
      "delete_note": "Are you sure you want to delete this note?",
      "yes": "Yes",
      "no": "No",
      "cancel": "Cancel"
    },
    "error": {
      "title": "Error",
      "generic": "An error occurred.",
      "event_not_found": "Event not found.",
      "note_not_found": "Note not found.",
      "invalid_date": "Invalid date.",
      "invalid_time": "Invalid time.",
      "required_field": "This field is required."
    }
  }
}
```

### Metadata

Each translation file includes metadata at the top:

```json
"_metadata": {
  "language": "English (UK)",
  "native_name": "English (UK)",
  "country": "GB",
  "flag": "🇬🇧",
  "completion": "100"
}
```

This metadata includes:
- `language`: The language name in English
- `native_name`: The language name in its native script
- `country`: The ISO country code associated with the language
- `flag`: The emoji flag for the country
- `completion`: The percentage of translation completion (0-100)

## Translation Loading

Translations are loaded by the `I18nManager` class in `calendar_app/localization/i18n_manager.py`:

```python
def _load_locale(self, locale_code: str) -> bool:
    """
    Load translations for a specific locale.
    
    Args:
        locale_code: Locale code to load
        
    Returns:
        True if loaded successfully, False otherwise
    """
    if locale_code in self._translations_cache:
        return True
    
    translation_file = self.translations_dir / f"{locale_code}.json"
    
    if not translation_file.exists():
        logger.warning(f"Translation file not found: {translation_file}")
        return False
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            self._translations_cache[locale_code] = translations
            logger.debug(f"Loaded translations for {locale_code}")
            return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading translations for {locale_code}: {e}")
        return False
```

This method:
1. Checks if translations are already cached
2. Loads the translation file for the specified locale
3. Parses the JSON and stores it in the cache
4. Returns success or failure

## Translation Usage

Translations can be accessed using the `get_translation()` method:

```python
def get_translation(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
    """
    Get a translation for the given key.
    
    Args:
        key: Translation key (supports dot notation, e.g., 'menu.file.new')
        locale: Specific locale to use (defaults to current locale)
        **kwargs: Variables for string formatting
        
    Returns:
        Translated string
        
    Raises:
        MissingTranslationError: If translation is not found
    """
    target_locale = locale or self.current_locale
    
    # Try to get translation from target locale
    translation = self._get_translation_from_locale(key, target_locale)
    
    # Fallback to default locale if not found
    if translation is None and target_locale != self.fallback_locale:
        translation = self._get_translation_from_locale(key, self.fallback_locale)
    
    # If still not found, raise error or return key
    if translation is None:
        logger.warning(f"Translation not found for key: {key}")
        return key  # Return key as fallback
    
    # Format string with provided variables
    if kwargs:
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Error formatting translation '{key}': {e}")
            return translation
    
    return translation
```

This method:
1. Gets the translation for the specified key
2. Falls back to the default locale if not found
3. Returns the key itself if no translation is found
4. Formats the translation with variables if provided

### Dot Notation

Translations can be accessed using dot notation:

```python
# Get translation for 'menu.file.new'
new_text = i18n_manager.get_translation('menu.file.new')
```

This will look for the translation at `menu.file.new` in the JSON structure.

### Flattened Keys

Translations can also be accessed using flattened keys:

```python
# Get translation for 'menu.file.new' using flattened key
new_text = i18n_manager.get_translation('menu_file_new')
```

This will look for the translation at `menu_file_new` in the flattened structure.

### Variable Substitution

Translations can include variables using the `{variable}` syntax:

```json
"welcome_message": "Welcome, {username}!"
```

```python
# Get translation with variable substitution
welcome_text = i18n_manager.get_translation('welcome_message', username='John')
# Result: "Welcome, John!"
```

## Fallback Mechanism

The translation system includes a fallback mechanism to handle missing translations:

1. **Primary Locale**: First, try to get the translation from the current locale
2. **Fallback Locale**: If not found, try to get it from the fallback locale (usually `en_GB`)
3. **Key as Fallback**: If still not found, return the key itself as a fallback

```python
def _get_translation_from_locale(self, key: str, locale: str) -> Optional[str]:
    """
    Get translation from a specific locale.
    
    Args:
        key: Translation key
        locale: Locale code
        
    Returns:
        Translation string or None if not found
    """
    # Load locale if not cached
    if locale not in self._translations_cache:
        if not self._load_locale(locale):
            return None
    
    translations = self._translations_cache[locale]
    
    # First try direct lookup for flat keys (new flattened structure)
    if key in translations:
        value = translations[key]
        return value if isinstance(value, str) else None
    
    # Fallback: Support dot notation for nested keys (legacy structure)
    keys = key.split('.')
    current = translations
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return None
    
    return current if isinstance(current, str) else None
```

This method:
1. Loads the locale if not already cached
2. Tries direct lookup for flattened keys
3. Falls back to dot notation for nested keys
4. Returns the translation or None if not found

## Runtime Language Switching

Calendifier supports runtime language switching:

```python
def set_locale(self, locale_code: str) -> bool:
    """
    Set the current locale.
    
    Args:
        locale_code: Locale code to set (e.g., 'en_US', 'fr_FR')
        
    Returns:
        True if locale was set successfully, False otherwise
    """
    if locale_code == self.current_locale:
        return True
        
    if self._load_locale(locale_code):
        old_locale = self.current_locale
        self._current_locale = locale_code
        logger.info(f"Locale changed from {old_locale} to {locale_code}")
        return True
    
    logger.warning(f"Failed to set locale to {locale_code}")
    return False
```

This method:
1. Checks if the locale is already set
2. Loads the translations for the new locale
3. Updates the current locale
4. Returns success or failure

### Language Switching in UI

In the desktop application, language switching is handled by the `SettingsDialog`:

```python
def on_language_changed(self, index):
    locale_code = self.language_combo.itemData(index)
    if locale_code and locale_code != self.current_locale:
        # Update UI immediately
        self.current_locale = locale_code
        self.settings_manager.set_locale(locale_code)
        
        # Reload translations
        from calendar_app.localization import set_locale
        set_locale(locale_code)
        
        # Update UI elements
        self.retranslate_ui()
```

This method:
1. Gets the selected locale code
2. Updates the settings
3. Reloads translations
4. Updates the UI

### Language Switching in Home Assistant

In the Home Assistant integration, language switching is handled by the settings card:

```javascript
async changeLanguage(locale) {
  try {
    // Update settings via API
    await fetch(`${this.getApiBaseUrl()}/api/v1/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ locale })
    });
    
    // Update translation manager
    await this.translationManager.setLocale(locale);
    
    // Notify all cards about locale change
    document.dispatchEvent(new CustomEvent('calendifier-locale-changed', {
      detail: { locale }
    }));
    
    // Show success notification
    this.showNotification(this.t('settings.language_changed_success', 'Language changed successfully'), 'success');
  } catch (error) {
    console.error('Failed to change language:', error);
    this.showNotification(this.t('settings.language_changed_error', 'Failed to change language'), 'error');
  }
}
```

This method:
1. Updates the settings via the API
2. Updates the translation manager
3. Notifies all cards about the locale change
4. Shows a success or error notification

## Translation Management

### Translation Cache

Translations are cached to improve performance:

```python
def clear_cache(self):
    """Clear the translations cache."""
    self._translations_cache.clear()
    self._available_locales = None
    logger.debug("Translation cache cleared")

def reload_locale(self, locale: Optional[str] = None):
    """
    Reload translations for a specific locale.
    
    Args:
        locale: Locale to reload (defaults to current locale)
    """
    target_locale = locale or self.current_locale
    
    if target_locale in self._translations_cache:
        del self._translations_cache[target_locale]
    
    self._load_locale(target_locale)
    logger.debug(f"Reloaded locale: {target_locale}")

def reload_translations(self):
    """
    Reload all translations by clearing cache and reloading current locale.
    """
    self.clear_cache()
    self._load_locale(self.current_locale)
    logger.debug("All translations reloaded")
```

These methods:
1. Clear the translation cache
2. Reload translations for a specific locale
3. Reload all translations

### Available Locales

The translation system can list all available locales:

```python
def get_available_locales(self) -> List[str]:
    """
    Get list of available locales based on translation files.
    
    Returns:
        List of available locale codes
    """
    if self._available_locales is None:
        self._available_locales = []
        
        if self.translations_dir.exists():
            for file_path in self.translations_dir.glob("*.json"):
                locale_code = file_path.stem
                if self._is_valid_locale_file(file_path):
                    self._available_locales.append(locale_code)
        
        # Ensure default locale is included
        if self.default_locale not in self._available_locales:
            self._available_locales.append(self.default_locale)
            
        self._available_locales.sort()
        logger.debug(f"Found {len(self._available_locales)} available locales")
    
    return self._available_locales
```

This method:
1. Scans the translations directory for JSON files
2. Validates each file
3. Returns a sorted list of available locale codes

## Adding New Languages

To add a new language to Calendifier:

1. **Create Translation File**:
   - Create a new JSON file in `calendar_app/localization/translations/`
   - Name it with the locale code (e.g., `es_MX.json` for Mexican Spanish)
   - Include the metadata section

2. **Add Holiday Translations**:
   - Create a new JSON file in `calendar_app/localization/locale_holiday_translations/`
   - Name it with the locale code and `_holidays.json` suffix (e.g., `es_MX_holidays.json`)
   - Include translations for all holidays

3. **Country names**:
   - Country names in the holiday-country selector are NOT translated per UI
     locale. Each country is shown by its own native name (endonym), fixed
     regardless of the interface language.
   - These live in `calendar_app/localization/country_endonyms.py`. When a new
     country is added to `MultiCountryHolidayProvider.SUPPORTED_COUNTRIES`, add
     its endonym there (a structural test enforces that every supported country
     has one).

4. **Update Locale Detector**:
   - Add the new locale to the `SUPPORTED_LOCALES` list in `calendar_app/localization/locale_detector.py`
   - Add the locale-to-country mapping in `calendar_app/localization/locale_detector.py`

5. **Test Language Switching**:
   - Run the application
   - Switch to the new language
   - Verify that all UI elements are properly translated
   - Check that holidays are displayed in the correct language
   - Verify that country names are properly translated

### Translation File Template

```json
{
  "_metadata": {
    "language": "Spanish (Mexico)",
    "native_name": "Español (México)",
    "country": "MX",
    "flag": "🇲🇽",
    "completion": "0"
  },
  "app_name": "Calendifier",
  "menu": {
    "file": {
      "title": "Archivo",
      "new": "Nuevo",
      "open": "Abrir",
      "save": "Guardar",
      "exit": "Salir"
    },
    // More translations...
  }
}
```

### Holiday Translations Template

```json
{
  "_metadata": {
    "locale": "es_MX",
    "language": "Spanish (Mexico)",
    "country": "MX"
  },
  "New Year's Day": "Día de Año Nuevo",
  "Christmas Day": "Navidad",
  // More holiday translations...
}
```

### Country Translations Template

```json
{
  "_metadata": {
    "locale": "es_MX",
    "language": "Spanish (Mexico)",
    "country": "MX"
  },
  "US": "Estados Unidos",
  "GB": "Reino Unido",
  "MX": "México",
  // More country translations...
}