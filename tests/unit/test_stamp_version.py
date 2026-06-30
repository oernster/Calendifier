"""100% coverage for stamp_version.py (doc version stamper)."""

from __future__ import annotations

from pathlib import Path

import stamp_version

OPEN = "<!--VERSION-->"
CLOSE = "<!--/VERSION-->"


def test_read_version_matches_file():
    expected = (
        (Path(stamp_version.__file__).parent / "VERSION")
        .read_text(encoding="utf-8")
        .strip()
    )
    assert stamp_version.read_version() == expected


def test_stamp_file_updates_token(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text(f"x {OPEN}0.0.1{CLOSE} y", encoding="utf-8")
    assert stamp_version.stamp_file(doc, "1.2.3") is True
    assert doc.read_text(encoding="utf-8") == f"x {OPEN}1.2.3{CLOSE} y"


def test_stamp_file_no_token_is_noop(tmp_path):
    doc = tmp_path / "b.md"
    doc.write_text("no token here", encoding="utf-8")
    assert stamp_version.stamp_file(doc, "1.2.3") is False


def test_stamp_file_already_current_is_noop(tmp_path):
    doc = tmp_path / "c.md"
    doc.write_text(f"{OPEN}1.2.3{CLOSE}", encoding="utf-8")
    assert stamp_version.stamp_file(doc, "1.2.3") is False


def test_stamp_file_unreadable_returns_false(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff\xfe\x00invalid utf-8")
    assert stamp_version.stamp_file(bad, "1.2.3") is False


def test_target_files_with_and_without_docs(tmp_path):
    (tmp_path / "root.md").write_text("x", encoding="utf-8")
    # No docs dir yet.
    assert (tmp_path / "root.md") in stamp_version._target_files(tmp_path)

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.html").write_text("x", encoding="utf-8")
    (docs / "guide.md").write_text("x", encoding="utf-8")
    found = stamp_version._target_files(tmp_path)
    assert docs / "page.html" in found
    assert docs / "guide.md" in found


def test_main_stamps_changed_files(tmp_path, capsys):
    version = stamp_version.read_version()
    (tmp_path / "x.md").write_text(f"{OPEN}old{CLOSE}", encoding="utf-8")
    stamp_version.main(tmp_path)
    assert (tmp_path / "x.md").read_text(encoding="utf-8") == f"{OPEN}{version}{CLOSE}"
    assert "Stamped version" in capsys.readouterr().out


def test_main_noop_when_current(tmp_path, capsys):
    version = stamp_version.read_version()
    (tmp_path / "x.md").write_text(f"{OPEN}{version}{CLOSE}", encoding="utf-8")
    stamp_version.main(tmp_path)
    assert "already current" in capsys.readouterr().out
