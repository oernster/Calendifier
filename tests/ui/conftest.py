"""Fixtures for the Qt/UI suite.

These tests drive real PySide6 widgets with a headless ``offscreen`` platform
and NO mocking of Qt. They are intentionally kept out of the primary coverage
gate (see pyproject.toml ``testpaths``) because windowing/event-loop tests are
inherently more fragile than the pure-logic unit tests.

Run them on their own, without the coverage gate, e.g.::

    python -m pytest tests/ui --no-cov -o addopts=""
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Headless Qt before any PySide6 import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make the repo root importable when run standalone.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(scope="session")
def qapp():
    """A single real QApplication for the whole UI session."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
