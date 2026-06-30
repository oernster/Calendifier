"""100% coverage for calendar_app/shared/resources.py (icon discovery)."""

from __future__ import annotations

import sys
from pathlib import Path

from calendar_app.shared import resources


def test_find_app_icon_path_resolves_repo_ico():
    path = resources.find_app_icon_path()
    assert path is not None
    assert path.name == "calendar_icon.ico"
    assert path.is_file()


def test_find_qt_window_icon_path_resolves():
    path = resources.find_qt_window_icon_path()
    assert path is not None
    assert path.is_file()


def test_candidate_roots_dedup_and_assets_expansion(tmp_path):
    roots = resources._candidate_roots(tmp_path)
    # The explicit project_root and its assets/ subdir come first, in order.
    assert roots[0] == tmp_path
    assert roots[1] == tmp_path / "assets"
    # No duplicates.
    assert len(roots) == len({str(r) for r in roots})


def test_candidate_roots_without_project_root():
    roots = resources._candidate_roots(None)
    assert any(r.name == "assets" for r in roots)


def test_candidate_roots_includes_meipass_when_frozen(tmp_path, monkeypatch):
    # sys._MEIPASS is the PyInstaller-frozen unpack dir flag.
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    roots = resources._candidate_roots(None)
    assert tmp_path in roots


def test_first_existing_returns_none_when_absent():
    assert resources._first_existing(("does_not_exist.zzz",), None) is None


def test_first_existing_finds_named_file(tmp_path):
    target = tmp_path / "assets" / "calendar_icon.png"
    target.parent.mkdir()
    target.write_bytes(b"x")
    found = resources._first_existing(("calendar_icon.png",), tmp_path)
    assert found == target


def test_find_helpers_accept_explicit_root(tmp_path):
    ico = tmp_path / "calendar_icon.ico"
    ico.write_bytes(b"x")
    assert resources.find_app_icon_path(project_root=tmp_path) == ico
    assert isinstance(resources.find_qt_window_icon_path(project_root=tmp_path), Path)
