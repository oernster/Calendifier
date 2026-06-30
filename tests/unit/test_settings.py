"""Unit tests for calendar_app.config.settings.SettingsManager.

All tests use real objects and real inputs. No mocking is used: isolation is
achieved by pointing each SettingsManager at a tmp_path settings file, and
determinism is achieved by always passing an explicit ``timezone_id`` to
``get_effective_holiday_country``.
"""

import json

import pytest

from calendar_app.config.settings import SettingsManager


@pytest.fixture
def settings_file(tmp_path):
    """Return a fresh, non-existent settings file path inside tmp_path."""
    return tmp_path / "settings.json"


@pytest.fixture
def manager(settings_file):
    """Return a SettingsManager backed by a fresh tmp_path file."""
    return SettingsManager(settings_file)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construction_creates_default_file(settings_file):
    """A missing settings file is created with defaults on construction."""
    assert not settings_file.exists()
    mgr = SettingsManager(settings_file)
    assert settings_file.exists()
    assert mgr.get_theme() == "dark"


def test_construction_creates_missing_parent_directory(tmp_path):
    """Parent directories are created when they do not already exist."""
    nested = tmp_path / "a" / "b" / "settings.json"
    mgr = SettingsManager(nested)
    assert nested.exists()
    assert mgr.get_theme() == "dark"


def test_construction_loads_existing_file(settings_file):
    """An existing settings file is loaded rather than overwritten."""
    settings_file.write_text(
        json.dumps({"theme": "light", "first_day_of_week": 3}),
        encoding="utf-8",
    )
    mgr = SettingsManager(settings_file)
    assert mgr.get_theme() == "light"
    assert mgr.get_calendar_settings()["first_day_of_week"] == 3


def test_construction_with_string_path(tmp_path):
    """A string path (not Path) is accepted and converted."""
    path = tmp_path / "string_settings.json"
    mgr = SettingsManager(str(path))
    assert path.exists()
    assert mgr.get_theme() == "dark"


def test_load_malformed_json_falls_back_to_defaults(settings_file):
    """Malformed JSON triggers the load-error branch and uses defaults."""
    settings_file.write_text("{ this is not valid json", encoding="utf-8")
    mgr = SettingsManager(settings_file)
    # Defaults restored despite the corrupt file.
    assert mgr.get_theme() == "dark"
    assert mgr.get_locale() == "en_GB"


# ---------------------------------------------------------------------------
# get_setting / set_setting / get_all_settings / update_settings
# ---------------------------------------------------------------------------


def test_get_setting_known_key(manager):
    assert manager.get_setting("theme") == "dark"


def test_get_setting_unknown_key_returns_default(manager):
    assert manager.get_setting("does_not_exist", "fallback") == "fallback"


def test_set_setting_known_key(manager):
    assert manager.set_setting("theme", "light") is True
    assert manager.get_theme() == "light"


def test_set_setting_unknown_key_returns_false(manager):
    assert manager.set_setting("does_not_exist", 123) is False


def test_get_all_settings(manager):
    data = manager.get_all_settings()
    assert isinstance(data, dict)
    assert data["theme"] == "dark"


def test_update_settings_known_and_unknown(manager):
    ok = manager.update_settings(
        {"theme": "light", "first_day_of_week": 2, "unknown_key": "x"}
    )
    assert ok is True
    assert manager.get_theme() == "light"
    assert manager.get_calendar_settings()["first_day_of_week"] == 2


# ---------------------------------------------------------------------------
# reset_to_defaults
# ---------------------------------------------------------------------------


def test_reset_to_defaults(manager):
    manager.set_theme("light")
    assert manager.reset_to_defaults() is True
    assert manager.get_theme() == "dark"


# ---------------------------------------------------------------------------
# backup / restore
# ---------------------------------------------------------------------------


def test_backup_settings(manager, tmp_path):
    backup = tmp_path / "backup.json"
    assert manager.backup_settings(backup) is True
    data = json.loads(backup.read_text(encoding="utf-8"))
    assert "settings" in data
    assert "backup_timestamp" in data


def test_backup_settings_failure(manager, tmp_path):
    """Pointing backup at a directory triggers the error branch."""
    a_dir = tmp_path / "a_directory"
    a_dir.mkdir()
    assert manager.backup_settings(a_dir) is False


def test_restore_settings_missing_file(manager, tmp_path):
    assert manager.restore_settings(tmp_path / "nope.json") is False


def test_restore_settings_invalid_format(manager, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not_settings": True}), encoding="utf-8")
    assert manager.restore_settings(bad) is False


def test_restore_settings_success(manager, tmp_path):
    backup = tmp_path / "backup.json"
    manager.set_theme("light")
    manager.backup_settings(backup)
    manager.set_theme("dark")
    assert manager.restore_settings(backup) is True
    assert manager.get_theme() == "light"


def test_restore_settings_corrupt_json(manager, tmp_path):
    """Corrupt JSON in the backup hits the restore exception branch."""
    bad = tmp_path / "corrupt.json"
    bad.write_text("{not json", encoding="utf-8")
    assert manager.restore_settings(bad) is False


# ---------------------------------------------------------------------------
# save error handling (real input: settings path replaced by a directory)
# ---------------------------------------------------------------------------


def test_save_error_branch_is_swallowed(settings_file):
    """A save against a path that is a directory hits the save-error branch.

    set_setting still reports success because _save_settings swallows the
    OSError internally; the in-memory value is updated regardless.
    """
    mgr = SettingsManager(settings_file)
    settings_file.unlink()
    settings_file.mkdir()
    assert mgr.set_setting("theme", "light") is True
    assert mgr.get_theme() == "light"


# ---------------------------------------------------------------------------
# theme
# ---------------------------------------------------------------------------


def test_set_theme_valid(manager):
    assert manager.set_theme("light") is True
    assert manager.get_theme() == "light"


def test_set_theme_invalid(manager):
    assert manager.set_theme("rainbow") is False
    assert manager.get_theme() == "dark"


# ---------------------------------------------------------------------------
# window geometry
# ---------------------------------------------------------------------------


def test_get_window_geometry(manager):
    geo = manager.get_window_geometry()
    assert set(geo) == {"width", "height", "x", "y"}


def test_set_window_geometry_clamps_minimums(manager):
    assert manager.set_window_geometry(100, 100) is True
    geo = manager.get_window_geometry()
    assert geo["width"] == 800
    assert geo["height"] == 600
    assert geo["x"] == -1
    assert geo["y"] == -1


def test_set_window_geometry_explicit_position(manager):
    assert manager.set_window_geometry(1000, 700, x=50, y=60) is True
    geo = manager.get_window_geometry()
    assert geo == {"width": 1000, "height": 700, "x": 50, "y": 60}


def test_set_window_geometry_error_branch(manager):
    """A non-numeric width makes max() raise TypeError, hitting the except."""
    assert manager.set_window_geometry(None, 700) is False


# ---------------------------------------------------------------------------
# NTP
# ---------------------------------------------------------------------------


def test_get_ntp_settings(manager):
    ntp = manager.get_ntp_settings()
    assert ntp["interval_minutes"] == 5
    assert isinstance(ntp["servers"], list)


def test_set_ntp_interval_valid(manager):
    assert manager.set_ntp_interval(30) is True
    assert manager.get_ntp_settings()["interval_minutes"] == 30


def test_set_ntp_interval_invalid_low(manager):
    assert manager.set_ntp_interval(0) is False


def test_set_ntp_interval_invalid_high(manager):
    assert manager.set_ntp_interval(2000) is False


def test_add_ntp_server_new(manager):
    assert manager.add_ntp_server("time.example.com") is True
    assert "time.example.com" in manager.get_ntp_settings()["servers"]


def test_add_ntp_server_duplicate(manager):
    existing = manager.get_ntp_settings()["servers"][0]
    before = len(manager.get_ntp_settings()["servers"])
    assert manager.add_ntp_server(existing) is True
    assert len(manager.get_ntp_settings()["servers"]) == before


def test_remove_ntp_server_present(manager):
    existing = manager.get_ntp_settings()["servers"][0]
    assert manager.remove_ntp_server(existing) is True
    assert existing not in manager.get_ntp_settings()["servers"]


def test_remove_ntp_server_absent(manager):
    assert manager.remove_ntp_server("not.a.server") is False


def test_add_ntp_server_error_branch(manager):
    """A non-iterable ntp_servers makes the membership test raise TypeError."""
    manager.set_setting("ntp_servers", 123)
    assert manager.add_ntp_server("x") is False


def test_remove_ntp_server_error_branch(manager):
    """A non-iterable ntp_servers makes the membership test raise TypeError."""
    manager.set_setting("ntp_servers", 123)
    assert manager.remove_ntp_server("x") is False


# ---------------------------------------------------------------------------
# calendar settings
# ---------------------------------------------------------------------------


def test_get_calendar_settings(manager):
    cal = manager.get_calendar_settings()
    assert set(cal) == {
        "first_day_of_week",
        "show_week_numbers",
        "default_event_duration",
        "holiday_country",
    }


def test_set_first_day_of_week_valid(manager):
    assert manager.set_first_day_of_week(6) is True
    assert manager.get_calendar_settings()["first_day_of_week"] == 6


def test_set_first_day_of_week_invalid(manager):
    assert manager.set_first_day_of_week(7) is False


def test_set_show_week_numbers(manager):
    assert manager.set_show_week_numbers(True) is True
    assert manager.get_calendar_settings()["show_week_numbers"] is True


def test_set_default_event_duration_valid(manager):
    assert manager.set_default_event_duration(90) is True
    assert manager.get_calendar_settings()["default_event_duration"] == 90


def test_set_default_event_duration_invalid_low(manager):
    assert manager.set_default_event_duration(5) is False


def test_set_default_event_duration_invalid_high(manager):
    assert manager.set_default_event_duration(5000) is False


# ---------------------------------------------------------------------------
# holiday country
# ---------------------------------------------------------------------------


def test_get_holiday_country_default_auto(manager):
    assert manager.get_holiday_country() == "auto"


def test_set_holiday_country_auto(manager):
    assert manager.set_holiday_country("auto") is True
    assert manager.get_holiday_country() == "auto"


def test_set_holiday_country_valid_uppercased(manager):
    assert manager.set_holiday_country("fr") is True
    assert manager.get_holiday_country() == "FR"


def test_set_holiday_country_invalid(manager):
    assert manager.set_holiday_country("ZZ") is False


# ---------------------------------------------------------------------------
# get_effective_holiday_country (always called with explicit timezone_id)
# ---------------------------------------------------------------------------


def test_effective_country_explicit_overrides_timezone(manager):
    """An explicit country wins regardless of the timezone_id passed."""
    manager.set_holiday_country("FR")
    assert manager.get_effective_holiday_country(timezone_id="America/New_York") == "FR"


def test_effective_country_auto_us(manager):
    manager.set_holiday_country("auto")
    assert manager.get_effective_holiday_country(timezone_id="America/New_York") == "US"


def test_effective_country_auto_gb(manager):
    manager.set_holiday_country("auto")
    assert manager.get_effective_holiday_country(timezone_id="Europe/London") == "GB"


def test_effective_country_auto_jp(manager):
    manager.set_holiday_country("auto")
    assert manager.get_effective_holiday_country(timezone_id="Asia/Tokyo") == "JP"


def test_effective_country_auto_unmappable_falls_back_to_locale(manager):
    """Unmappable timezone falls back to the locale's (supported) country."""
    manager.set_holiday_country("auto")
    manager.set_locale("fr_FR")
    assert manager.get_effective_holiday_country(timezone_id="Australia/Sydney") == "FR"


def test_effective_country_auto_locale_unsupported_falls_back_to_gb(manager):
    """Unmappable timezone + unsupported-locale-country falls back to GB."""
    manager.set_holiday_country("auto")
    # set_setting bypasses locale validation so we can store a locale whose
    # country code is not in SUPPORTED_COUNTRIES, exercising the final branch.
    manager.set_setting("locale", "xx_ZZ")
    assert manager.get_effective_holiday_country(timezone_id="Australia/Sydney") == "GB"


def test_effective_country_auto_resolves_timezone_when_none(manager):
    """timezone_id=None executes the live-resolution call site (line 311).

    The system timezone is involved, so we only assert a tz-independent
    invariant: the result is always one of the supported country codes or
    the GB fallback, never empty.
    """
    from calendar_app.core.multi_country_holiday_provider import (
        MultiCountryHolidayProvider,
    )

    manager.set_holiday_country("auto")
    result = manager.get_effective_holiday_country(timezone_id=None)
    supported = MultiCountryHolidayProvider.get_supported_countries()
    assert result == "GB" or result in supported


# ---------------------------------------------------------------------------
# locale
# ---------------------------------------------------------------------------


def test_get_locale_default(manager):
    assert manager.get_locale() == "en_GB"


def test_set_locale_valid(manager):
    assert manager.set_locale("fr_FR") is True
    assert manager.get_locale() == "fr_FR"


def test_set_locale_invalid(manager):
    assert manager.set_locale("zz_ZZ") is False
    assert manager.get_locale() == "en_GB"


# ---------------------------------------------------------------------------
# timezone
# ---------------------------------------------------------------------------


def test_get_timezone_default_auto(manager):
    assert manager.get_timezone() == "auto"


def test_set_timezone_auto(manager):
    assert manager.set_timezone("auto") is True
    assert manager.get_timezone() == "auto"


def test_set_timezone_valid(manager):
    assert manager.set_timezone("Europe/London") is True
    assert manager.get_timezone() == "Europe/London"


def test_set_timezone_invalid(manager):
    assert manager.set_timezone("Not/AZone") is False
    assert manager.get_timezone() == "auto"


# ---------------------------------------------------------------------------
# export / import
# ---------------------------------------------------------------------------


def test_export_settings(manager, tmp_path):
    out = tmp_path / "export.json"
    assert manager.export_settings(out) is True
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["calendar_app_settings"] is True
    assert "theme" in data["settings"]


def test_export_settings_failure(manager, tmp_path):
    a_dir = tmp_path / "exp_dir"
    a_dir.mkdir()
    assert manager.export_settings(a_dir) is False


def test_import_settings_missing_file(manager, tmp_path):
    assert manager.import_settings(tmp_path / "missing.json") is False


def test_import_settings_invalid_format(manager, tmp_path):
    path = tmp_path / "bad_import.json"
    path.write_text(json.dumps({"not_ours": True}), encoding="utf-8")
    assert manager.import_settings(path) is False


def test_import_settings_success(manager, tmp_path):
    path = tmp_path / "good_import.json"
    path.write_text(
        json.dumps(
            {
                "calendar_app_settings": True,
                "settings": {"theme": "light", "first_day_of_week": 4},
            }
        ),
        encoding="utf-8",
    )
    assert manager.import_settings(path) is True
    assert manager.get_theme() == "light"


def test_import_settings_no_valid_keys(manager, tmp_path):
    """A file with only unknown keys imports zero settings and returns False."""
    path = tmp_path / "empty_import.json"
    path.write_text(
        json.dumps({"calendar_app_settings": True, "settings": {"unknown_key": "x"}}),
        encoding="utf-8",
    )
    assert manager.import_settings(path) is False


def test_import_settings_corrupt_json(manager, tmp_path):
    path = tmp_path / "corrupt_import.json"
    path.write_text("{ broken", encoding="utf-8")
    assert manager.import_settings(path) is False


# ---------------------------------------------------------------------------
# validate_settings
# ---------------------------------------------------------------------------


def test_validate_settings_clean(manager):
    assert manager.validate_settings() == {}


def test_validate_settings_auto_holiday_country_accepted(manager):
    manager.set_holiday_country("auto")
    issues = manager.validate_settings()
    assert "holiday_country" not in issues


def test_validate_settings_all_issues(manager):
    """Set invalid values directly so validation flags every category."""
    manager.set_setting("theme", "rainbow")
    manager.set_setting("ntp_interval_minutes", 0)
    manager.set_setting("window_width", 100)
    manager.set_setting("window_height", 100)
    manager.set_setting("first_day_of_week", 9)
    manager.set_setting("default_event_duration", 5)
    manager.set_setting("holiday_country", "ZZ")

    issues = manager.validate_settings()
    assert set(issues) == {
        "theme",
        "ntp_interval",
        "window_width",
        "window_height",
        "first_day_of_week",
        "event_duration",
        "holiday_country",
    }


# ---------------------------------------------------------------------------
# get_settings_summary
# ---------------------------------------------------------------------------


def test_get_settings_summary_known_country(manager):
    manager.set_holiday_country("FR")
    summary = manager.get_settings_summary()
    assert "Settings Summary" in summary
    assert "France" in summary


def test_get_settings_summary_auto_country_uses_default_label(manager):
    """'auto' is not a country key, so the default Unknown label is used."""
    manager.set_holiday_country("auto")
    summary = manager.get_settings_summary()
    assert "Unknown" in summary
