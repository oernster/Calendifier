"""Headless Qt smoke tests for the desktop UI (no mocks, real widgets).

Covers the three behaviours changed in this work: responsive analog clock,
sequentially renumbered notes, and the top-bar holiday-country selector, plus
the file-based window icon. Not part of the 100% gate (see module docstring in
conftest.py).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def main_window(qapp):
    """A real MainWindow backed by a throwaway settings file."""
    from calendar_app.config.settings import SettingsManager
    from calendar_app.config.themes import ThemeManager
    from calendar_app.ui.main_window import MainWindow

    settings_path = Path(tempfile.mkdtemp()) / "settings.json"
    window = MainWindow(SettingsManager(settings_path), ThemeManager())
    yield window
    window.close()


def test_window_icon_loads_from_file(main_window):
    icon = main_window.windowIcon()
    assert not icon.isNull()
    sizes = {(s.width(), s.height()) for s in icon.availableSizes()}
    assert (256, 256) in sizes


def test_analog_clock_is_responsive(main_window):
    clock = main_window.clock_widget.analog_clock
    assert clock.minimumWidth() == clock.MINIMUM_SIZE
    assert clock.maximumHeight() == clock.PREFERRED_SIZE
    assert clock.sizeHint().width() == clock.PREFERRED_SIZE


def test_country_selector_left_of_language(main_window):
    main_window.resize(960, 760)
    main_window._position_language_selector()
    assert main_window.country_combo.count() == 42
    assert main_window.country_widget.x() < main_window.language_widget.x()


def test_country_selector_persists_choice(main_window):
    combo = main_window.country_combo
    combo.setCurrentIndex(combo.findData("FR"))
    assert main_window.settings_manager.get_holiday_country() == "FR"


def test_notes_renumber_on_load_add_and_delete(qapp):
    from calendar_app.ui.notes_widget import NotesWidget

    notes = NotesWidget()
    # Seed legacy gappy numbering directly, then reload.
    notes.notes_file = str(Path(tempfile.mkdtemp()) / "notes.json")
    with open(notes.notes_file, "w", encoding="utf-8") as handle:
        json.dump(
            [
                {"id": 9, "title": "9", "content": "a"},
                {"id": 11, "title": "11", "content": "b"},
            ],
            handle,
        )
    notes._load_notes()
    assert [n.title for n in notes.notes] == ["1", "2"]

    notes._add_note()
    assert [n.title for n in notes.notes] == ["1", "2", "3"]

    # Remove the middle note via the same core path the dialog uses.
    notes.notes.pop(1)
    notes.tab_widget.removeTab(1)
    notes._renumber_notes()
    notes._refresh_tab_titles()
    assert [n.title for n in notes.notes] == ["1", "2"]
    labels = [notes.tab_widget.tabText(i) for i in range(notes.tab_widget.count())]
    assert labels == ["1", "2"]
