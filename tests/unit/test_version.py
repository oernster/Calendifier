"""100% coverage for version.py (central version source of truth)."""

from __future__ import annotations

import sys

import version


def test_module_version_matches_version_file():
    expected = (
        (version.Path(version.__file__).parent / "VERSION")
        .read_text(encoding="utf-8")
        .strip()
    )
    assert version.__version__ == expected
    assert version.__version_info__ == version._parse_version_info(expected)


def test_identity_constants():
    assert version.APP_NAME == "Calendifier"
    assert version.LEGACY_APP_NAME == "Calendifier"
    assert version.APP_AUTHOR == version.__author__
    assert version.APP_COPYRIGHT == version.__copyright__
    assert version.APP_APPUSERMODELID == "com.oliverernster.calendifier"
    assert version.__license__ == "LGPL-3.0"


def test_read_version_from_source_checkout():
    assert version._read_version() == version.__version__


def test_read_version_prefers_meipass(tmp_path, monkeypatch):
    (tmp_path / "VERSION").write_text("9.9.9", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version._read_version() == "9.9.9"


def test_read_version_skips_empty_meipass_then_uses_source(tmp_path, monkeypatch):
    # Empty bundle VERSION -> the `if text` guard is false -> fall through to source.
    (tmp_path / "VERSION").write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version._read_version() == version.__version__


def test_read_version_handles_unreadable_candidate(tmp_path, monkeypatch):
    # A directory named VERSION makes read_text raise OSError -> except -> continue.
    (tmp_path / "VERSION").mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version._read_version() == version.__version__


def test_parse_version_info_variants():
    assert version._parse_version_info("1.7.0") == (1, 7, 0)
    assert version._parse_version_info("1.7.0-dev") == (1, 7, 0)
    assert version._parse_version_info("2.3") == (2, 3, 0)
    assert version._parse_version_info("1.x.0") == (1, 0, 0)
    assert version._parse_version_info("") == (0, 0, 0)


def test_get_version_string_and_about_text():
    assert version.__version__ in version.get_version_string()
    about = version.get_about_text()
    assert version.__version__ in about
    assert version.__author__ in about
