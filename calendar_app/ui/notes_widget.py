"""
📝 Notes Widget for Calendar Application

This module contains a tab-based note-taking widget with post-it note styling.
"""

import logging
import json
import os
from typing import List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTextEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Signal

from calendar_app.data.models import Note
from calendar_app.localization import get_i18n_manager
from calendar_app.localization.i18n_manager import convert_numbers

logger = logging.getLogger(__name__)


def _(key: str, **kwargs) -> str:
    """Dynamic translation function that gets current locale text."""
    try:
        # Extract default before passing to get_text
        default = kwargs.pop("default", key)
        result = get_i18n_manager().get_text(key, **kwargs)
        # If result is the same as key, it means translation wasn't found
        if result == key and default != key:
            return default
        return result
    except Exception:
        # Fallback to default or key if translation fails
        return kwargs.get("default", key)


class NotesWidget(QWidget):
    """📝 Tab-based notes widget with post-it note styling."""

    # Signals
    notes_changed = Signal()

    def __init__(self, parent=None):
        """Initialize notes widget."""
        super().__init__(parent)

        self.notes: List[Note] = []
        self.notes_file = os.path.expanduser("~/.calendar_app/notes.json")

        self._setup_ui()
        self._load_notes()
        self._apply_styling()

        logger.debug("📝 Notes widget initialized")

    def _setup_ui(self):
        """🏗️ Setup notes widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)  # We'll handle closing manually
        self.tab_widget.setMovable(False)

        # Create custom tab bar to handle the plus button
        self.tab_bar = self.tab_widget.tabBar()

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)

        # Add note button
        self.add_note_btn = QPushButton(f"+ {_('notes.new_note', default='New Note')}")
        self.add_note_btn.clicked.connect(self._add_note)
        button_layout.addWidget(self.add_note_btn)

        # Delete note button
        self.delete_note_btn = QPushButton(
            f"🗑️ {_('dialogs.delete', default='Delete')}"
        )
        self.delete_note_btn.clicked.connect(self._delete_current_note)
        self.delete_note_btn.setEnabled(False)
        button_layout.addWidget(self.delete_note_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Set platform-specific height for the notes widget
        import platform

        if platform.system() == "Linux":
            # Smaller height for Linux to ensure buttons are visible on smaller screens
            self.setFixedHeight(176)
        else:
            # Standard height for Windows/macOS (scaled for 13" MacBook)
            self.setFixedHeight(224)

    def _apply_styling(self):
        """🎨 Apply post-it note styling."""
        # Post-it note yellow background with dark text
        style = """
        QTabWidget::pane {
            border: 2px solid #d4af37;
            background-color: #ffffe0;
            border-radius: 4px;
        }

        QTabWidget::tab-bar {
            alignment: left;
        }

        QTabBar::tab {
            background-color: #fff8dc;
            border: 1px solid #d4af37;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 4px 8px;
            margin-right: 2px;
            color: #333333;
            font-weight: bold;
        }

        QTabBar::tab:selected {
            background-color: #ffffe0;
            border-bottom: 2px solid #ffffe0;
        }

        QTabBar::tab:hover {
            background-color: #fffacd;
        }

        QTextEdit {
            background-color: #ffffe0;
            border: none;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 11pt;
            padding: 8px;
        }

        QPushButton {
            background-color: #fff8dc;
            border: 1px solid #d4af37;
            border-radius: 3px;
            padding: 4px 8px;
            color: #333333;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #fffacd;
        }

        QPushButton:pressed {
            background-color: #f0e68c;
        }

        QPushButton:disabled {
            background-color: #f5f5dc;
            color: #999999;
            border-color: #cccccc;
        }
        """
        self.setStyleSheet(style)

    def _load_notes(self):
        """📥 Load notes from file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)

            if os.path.exists(self.notes_file):
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    notes_data = json.load(f)
                    self.notes = [Note.from_dict(note_data) for note_data in notes_data]

            # If no notes exist, create the first default note with empty content
            if not self.notes:
                self.notes = [Note(id=1, title="1", content="")]

            # Always present notes as a contiguous 1..N sequence, repairing any
            # legacy gaps (e.g. tabs showing 9, 11) left by past deletions.
            self._renumber_notes()

            # Create tabs for all notes
            self._refresh_tabs()

            logger.debug(f"📥 Loaded {len(self.notes)} notes")

        except Exception as e:
            logger.error(f"❌ Failed to load notes: {e}")
            # Create default note on error
            self.notes = [Note(id=1, title="1", content="")]
            self._refresh_tabs()

    def _save_notes(self):
        """💾 Save notes to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)

            # Save current note content before saving
            self._save_current_note_content()

            notes_data = [note.to_dict() for note in self.notes]
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(notes_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 Saved {len(self.notes)} notes")

        except Exception as e:
            logger.error(f"❌ Failed to save notes: {e}")

    def _refresh_tabs(self):
        """🔄 Refresh all tabs."""
        # Clear existing tabs
        self.tab_widget.clear()

        # Add tabs for all notes
        for note in self.notes:
            text_edit = QTextEdit()
            text_edit.setPlainText(note.content)
            text_edit.textChanged.connect(self._on_text_changed)

            # Convert tab title to locale-appropriate numerals for display
            converted_title = convert_numbers(note.title)
            self.tab_widget.addTab(text_edit, converted_title)

        # Update delete button state
        self._update_delete_button()

    def _add_note(self):
        """➕ Add a new note."""
        try:
            # The new note takes the next sequential number (1..N, no gaps).
            new_number = len(self.notes) + 1

            # Create new note
            new_note = Note(id=new_number, title=str(new_number), content="")
            self.notes.append(new_note)

            # Add new tab
            text_edit = QTextEdit()
            text_edit.setPlainText(new_note.content)
            text_edit.textChanged.connect(self._on_text_changed)

            # Convert tab title to locale-appropriate numerals for display
            converted_title = convert_numbers(new_note.title)
            tab_index = self.tab_widget.addTab(text_edit, converted_title)

            # Keep ids/titles a contiguous 1..N sequence and refresh tab labels
            self._renumber_notes()
            self._refresh_tab_titles()

            # Switch to new tab
            self.tab_widget.setCurrentIndex(tab_index)

            # Focus on the text area
            text_edit.setFocus()

            # Update delete button state
            self._update_delete_button()

            # Save notes
            self._save_notes()

            logger.debug(f"➕ Added new note: {new_note.title}")

        except Exception as e:
            logger.error(f"❌ Failed to add note: {e}")

    def _delete_current_note(self):
        """🗑️ Delete the current note."""
        try:
            current_index = self.tab_widget.currentIndex()
            if current_index < 0 or current_index >= len(self.notes):
                return

            # Don't allow deleting the last note
            if len(self.notes) <= 1:
                QMessageBox.information(
                    self,
                    _("dialogs.error_title", default="Cannot Delete"),
                    _(
                        "notes.message_must_have_one_note",
                        default="You must have at least one note.",
                    ),
                )
                return

            # Confirm deletion with custom Arabic buttons
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(_("notes.delete_note", default="Delete Note"))
            msg_box.setText(
                _(
                    "dialogs.confirm_delete_note",
                    default="Are you sure you want to delete this note?",
                )
            )
            msg_box.setIcon(QMessageBox.Icon.Question)

            # Create custom buttons with Arabic text
            yes_button = msg_box.addButton(
                _("Yes", default="Yes"), QMessageBox.ButtonRole.YesRole
            )
            no_button = msg_box.addButton(
                _("No", default="No"), QMessageBox.ButtonRole.NoRole
            )
            msg_box.setDefaultButton(no_button)

            msg_box.exec()
            clicked_button = msg_box.clickedButton()

            if clicked_button == yes_button:
                # Remove note from list
                deleted_note = self.notes.pop(current_index)

                # Remove tab
                self.tab_widget.removeTab(current_index)

                # Renumber the survivors so they stay a contiguous 1..N sequence
                self._renumber_notes()
                self._refresh_tab_titles()

                # Update delete button state
                self._update_delete_button()

                # Save notes
                self._save_notes()

                logger.debug(f"🗑️ Deleted note: {deleted_note.title}")

        except Exception as e:
            logger.error(f"❌ Failed to delete note: {e}")

    def _on_tab_changed(self, index: int):
        """📑 Handle tab change."""
        # Update delete button state
        self._update_delete_button()

    def _on_text_changed(self):
        """📝 Handle text change in current note."""
        # Save will happen when switching tabs or closing
        pass

    def _save_current_note_content(self):
        """💾 Save current note content."""
        try:
            current_index = self.tab_widget.currentIndex()
            if current_index >= 0 and current_index < len(self.notes):
                current_widget = self.tab_widget.currentWidget()
                if isinstance(current_widget, QTextEdit):
                    self.notes[current_index].content = current_widget.toPlainText()
                    # Update timestamp
                    from datetime import datetime

                    self.notes[current_index].updated_at = datetime.now()

        except Exception as e:
            logger.error(f"❌ Failed to save current note content: {e}")

    def _update_delete_button(self):
        """🔄 Update delete button state."""
        # Enable delete button only if there's more than one note
        self.delete_note_btn.setEnabled(len(self.notes) > 1)

    def save_all_notes(self):
        """💾 Save all notes (called when application closes)."""
        self._save_current_note_content()
        self._save_notes()
        self.notes_changed.emit()

    def refresh_ui_text(self):
        """🔄 Refresh UI text after language change."""
        try:
            # Update button texts
            self.add_note_btn.setText(f"+ {_('notes.new_note', default='New Note')}")
            self.delete_note_btn.setText(f"🗑️ {_('dialogs.delete', default='Delete')}")

            # Update tab titles with locale-appropriate numerals
            self._refresh_tab_titles()

            # Don't update note content during language changes -
            # keep notes as user entered them

            # Force button updates
            self.add_note_btn.update()
            self.delete_note_btn.update()

            logger.debug("🔄 Notes widget UI text refreshed")

        except Exception as e:
            logger.error(f"❌ Failed to refresh notes widget UI text: {e}")

    def _renumber_notes(self):
        """🔢 Reassign sequential ids/titles so notes are always numbered 1..N.

        Notes are identified purely by position, so deleting one renumbers the
        rest (deleting note 2 of 1,2,3 leaves 1,2). This repairs any historical
        gaps in the persisted data as well as keeping new additions contiguous.
        """
        for index, note in enumerate(self.notes):
            number = index + 1
            note.id = number
            note.title = str(number)

    def _refresh_tab_titles(self):
        """🔄 Refresh tab titles with locale-appropriate numerals."""
        try:
            for i, note in enumerate(self.notes):
                if i < self.tab_widget.count():
                    # Convert tab title to locale-appropriate numerals
                    converted_title = convert_numbers(note.title)
                    self.tab_widget.setTabText(i, converted_title)

        except Exception as e:
            logger.error(f"❌ Failed to refresh tab titles: {e}")
