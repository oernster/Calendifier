"""
🔄 RRULE Dialog for Desktop Application
Advanced recurring event pattern builder with RFC 5545 RRULE support
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from ..core.rrule_parser import RRuleParser
from ..core.recurring_event_generator import RecurringEventGenerator
from ..localization.i18n_manager import I18nManager

logger = logging.getLogger(__name__)


class RRuleDialog:
    """🔄 Advanced RRULE pattern builder dialog"""

    def __init__(
        self,
        parent: tk.Tk,
        i18n: I18nManager,
        initial_rrule: Optional[str] = None,
        start_date: Optional[date] = None,
    ):
        """Initialize RRULE dialog"""
        self.parent = parent
        self.i18n = i18n
        self.start_date = start_date or date.today()
        self.result_rrule: Optional[str] = None
        self.cancelled = True

        # Initialize RRULE parser and generator
        self.parser = RRuleParser()
        self.generator = RecurringEventGenerator()

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.i18n.get("recurring.title"))
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog on parent
        self._center_dialog()

        # Initialize UI variables
        self._init_variables()

        # Create UI
        self._create_ui()

        # Load initial RRULE if provided
        if initial_rrule:
            self._load_rrule(initial_rrule)
        else:
            self._set_defaults()

        # Update preview
        self._update_preview()

        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Focus on dialog
        self.dialog.focus_set()

    def _center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _init_variables(self):
        """Initialize UI variables"""
        self.frequency_var = tk.StringVar(value="WEEKLY")
        self.interval_var = tk.IntVar(value=1)
        self.count_var = tk.IntVar(value=10)
        self.until_var = tk.StringVar()
        self.end_type_var = tk.StringVar(value="never")

        # Weekday variables
        self.weekday_vars = {
            "MO": tk.BooleanVar(),
            "TU": tk.BooleanVar(),
            "WE": tk.BooleanVar(),
            "TH": tk.BooleanVar(),
            "FR": tk.BooleanVar(),
            "SA": tk.BooleanVar(),
            "SU": tk.BooleanVar(),
        }

        # Monthly options
        self.monthly_type_var = tk.StringVar(value="bymonthday")
        self.monthday_var = tk.IntVar(value=1)
        self.setpos_var = tk.StringVar(value="1")
        self.setpos_weekday_var = tk.StringVar(value="MO")

        # Preview text
        self.preview_text = tk.StringVar()
        self.rrule_text = tk.StringVar()

    def _create_ui(self):
        """Create dialog UI"""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Create sections
        self._create_frequency_section(main_frame, 0)
        self._create_interval_section(main_frame, 1)
        self._create_weekdays_section(main_frame, 2)
        self._create_monthly_section(main_frame, 3)
        self._create_end_condition_section(main_frame, 4)
        self._create_preview_section(main_frame, 5)
        self._create_rrule_section(main_frame, 6)
        self._create_buttons_section(main_frame, 7)

        # Configure row weights
        main_frame.rowconfigure(5, weight=1)  # Preview section expands

    def _create_frequency_section(self, parent: ttk.Frame, row: int):
        """Create frequency selection section"""
        frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.form.frequency"), padding="5"
        )
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        frame.columnconfigure(1, weight=1)

        frequencies = [
            ("DAILY", self.i18n.get("rrule.frequency.daily")),
            ("WEEKLY", self.i18n.get("rrule.frequency.weekly")),
            ("MONTHLY", self.i18n.get("rrule.frequency.monthly")),
            ("YEARLY", self.i18n.get("rrule.frequency.yearly")),
        ]

        for i, (value, text) in enumerate(frequencies):
            rb = ttk.Radiobutton(
                frame,
                text=text,
                variable=self.frequency_var,
                value=value,
                command=self._on_frequency_change,
            )
            rb.grid(row=0, column=i, padx=(0, 10), sticky="w")

    def _create_interval_section(self, parent: ttk.Frame, row: int):
        """Create interval selection section"""
        frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.form.interval"), padding="5"
        )
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        frame.columnconfigure(2, weight=1)

        ttk.Label(frame, text=self.i18n.get("rrule.interval.every")).grid(
            row=0, column=0, padx=(0, 5)
        )

        interval_spin = ttk.Spinbox(
            frame,
            from_=1,
            to=999,
            width=5,
            textvariable=self.interval_var,
            command=self._update_preview,
        )
        interval_spin.grid(row=0, column=1, padx=(0, 5))
        interval_spin.bind("<KeyRelease>", lambda e: self._update_preview())

        self.interval_label = ttk.Label(
            frame, text=self.i18n.get("rrule.interval.weeks")
        )
        self.interval_label.grid(row=0, column=2, sticky="w")

    def _create_weekdays_section(self, parent: ttk.Frame, row: int):
        """Create weekdays selection section"""
        self.weekdays_frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.form.weekdays"), padding="5"
        )
        self.weekdays_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))

        weekdays = [
            ("MO", self.i18n.get("rrule.weekday.short.mon")),
            ("TU", self.i18n.get("rrule.weekday.short.tue")),
            ("WE", self.i18n.get("rrule.weekday.short.wed")),
            ("TH", self.i18n.get("rrule.weekday.short.thu")),
            ("FR", self.i18n.get("rrule.weekday.short.fri")),
            ("SA", self.i18n.get("rrule.weekday.short.sat")),
            ("SU", self.i18n.get("rrule.weekday.short.sun")),
        ]

        for i, (day, text) in enumerate(weekdays):
            cb = ttk.Checkbutton(
                self.weekdays_frame,
                text=text,
                variable=self.weekday_vars[day],
                command=self._update_preview,
            )
            cb.grid(row=0, column=i, padx=(0, 10))

    def _create_monthly_section(self, parent: ttk.Frame, row: int):
        """Create monthly options section"""
        self.monthly_frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.advanced.by_monthday"), padding="5"
        )
        self.monthly_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        self.monthly_frame.columnconfigure(1, weight=1)

        # By month day option
        ttk.Radiobutton(
            self.monthly_frame,
            text=self.i18n.get("recurring.advanced.by_monthday"),
            variable=self.monthly_type_var,
            value="bymonthday",
            command=self._update_preview,
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        monthday_frame = ttk.Frame(self.monthly_frame)
        monthday_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(20, 0))

        ttk.Label(monthday_frame, text=self.i18n.get("recurring.form.monthday")).grid(
            row=0, column=0, padx=(0, 5)
        )
        monthday_spin = ttk.Spinbox(
            monthday_frame,
            from_=1,
            to=31,
            width=5,
            textvariable=self.monthday_var,
            command=self._update_preview,
        )
        monthday_spin.grid(row=0, column=1)
        monthday_spin.bind("<KeyRelease>", lambda e: self._update_preview())

        # By position option
        ttk.Radiobutton(
            self.monthly_frame,
            text=self.i18n.get("recurring.advanced.by_setpos"),
            variable=self.monthly_type_var,
            value="bysetpos",
            command=self._update_preview,
        ).grid(row=2, column=0, sticky="w", pady=(10, 5))

        setpos_frame = ttk.Frame(self.monthly_frame)
        setpos_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(20, 0))

        positions = [
            ("1", self.i18n.get("rrule.position.first")),
            ("2", self.i18n.get("rrule.position.second")),
            ("3", self.i18n.get("rrule.position.third")),
            ("4", self.i18n.get("rrule.position.fourth")),
            ("-1", self.i18n.get("rrule.position.last")),
        ]

        setpos_combo = ttk.Combobox(
            setpos_frame,
            textvariable=self.setpos_var,
            values=[p[0] for p in positions],
            state="readonly",
            width=10,
        )
        setpos_combo.grid(row=0, column=0, padx=(0, 5))
        setpos_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        # Set display values
        for i, (value, text) in enumerate(positions):
            if value == self.setpos_var.get():
                setpos_combo.current(i)
                break

        weekdays_combo = ttk.Combobox(
            setpos_frame,
            textvariable=self.setpos_weekday_var,
            values=["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
            state="readonly",
            width=10,
        )
        weekdays_combo.grid(row=0, column=1)
        weekdays_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

    def _create_end_condition_section(self, parent: ttk.Frame, row: int):
        """Create end condition section"""
        frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.form.end_condition"), padding="5"
        )
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        frame.columnconfigure(1, weight=1)

        # Never end
        ttk.Radiobutton(
            frame,
            text=self.i18n.get("rrule.end.never"),
            variable=self.end_type_var,
            value="never",
            command=self._update_preview,
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # End after count
        ttk.Radiobutton(
            frame,
            text=self.i18n.get("rrule.end.after"),
            variable=self.end_type_var,
            value="count",
            command=self._update_preview,
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        count_frame = ttk.Frame(frame)
        count_frame.grid(row=1, column=1, sticky="w", padx=(10, 0))

        count_spin = ttk.Spinbox(
            count_frame,
            from_=1,
            to=9999,
            width=8,
            textvariable=self.count_var,
            command=self._update_preview,
        )
        count_spin.grid(row=0, column=0, padx=(0, 5))
        count_spin.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(count_frame, text=self.i18n.get("rrule.end.occurrences")).grid(
            row=0, column=1
        )

        # End until date
        ttk.Radiobutton(
            frame,
            text=self.i18n.get("rrule.end.until"),
            variable=self.end_type_var,
            value="until",
            command=self._update_preview,
        ).grid(row=2, column=0, sticky="w", pady=(0, 5))

        until_entry = ttk.Entry(frame, textvariable=self.until_var, width=12)
        until_entry.grid(row=2, column=1, sticky="w", padx=(10, 0))
        until_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        # Set default until date (1 year from start)
        default_until = self.start_date + timedelta(days=365)
        self.until_var.set(default_until.strftime("%Y-%m-%d"))

    def _create_preview_section(self, parent: ttk.Frame, row: int):
        """Create preview section"""
        frame = ttk.LabelFrame(
            parent, text=self.i18n.get("recurring.preview"), padding="5"
        )
        frame.grid(row=row, column=0, sticky="nsew", pady=(0, 5))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Preview description
        preview_label = ttk.Label(frame, textvariable=self.preview_text, wraplength=550)
        preview_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Preview list
        preview_frame = ttk.Frame(frame)
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_listbox = tk.Listbox(preview_frame, height=8)
        self.preview_listbox.grid(row=0, column=0, sticky="nsew")

        preview_scrollbar = ttk.Scrollbar(
            preview_frame, orient="vertical", command=self.preview_listbox.yview
        )
        preview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_listbox.configure(yscrollcommand=preview_scrollbar.set)

    def _create_rrule_section(self, parent: ttk.Frame, row: int):
        """Create RRULE display section"""
        frame = ttk.LabelFrame(parent, text="RRULE", padding="5")
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        frame.columnconfigure(0, weight=1)

        rrule_entry = ttk.Entry(frame, textvariable=self.rrule_text, state="readonly")
        rrule_entry.grid(row=0, column=0, sticky="ew")

    def _create_buttons_section(self, parent: ttk.Frame, row: int):
        """Create buttons section"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))

        # Preset buttons
        preset_frame = ttk.Frame(frame)
        preset_frame.grid(row=0, column=0, sticky="w")

        presets = [
            ("daily", self.i18n.get("recurring.preset.daily")),
            ("weekdays", self.i18n.get("recurring.preset.weekdays")),
            ("weekly", self.i18n.get("recurring.preset.weekly")),
            ("monthly", self.i18n.get("recurring.preset.monthly")),
        ]

        for i, (preset, text) in enumerate(presets):
            btn = ttk.Button(
                preset_frame, text=text, command=lambda p=preset: self._apply_preset(p)
            )
            btn.grid(row=0, column=i, padx=(0, 5))

        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=1, sticky="e")
        frame.columnconfigure(1, weight=1)

        ttk.Button(
            button_frame, text=self.i18n.get("dialog.cancel"), command=self._on_cancel
        ).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(
            button_frame, text=self.i18n.get("dialog.ok"), command=self._on_ok
        ).grid(row=0, column=1)

    def _on_frequency_change(self):
        """Handle frequency change"""
        frequency = self.frequency_var.get()

        # Update interval label
        if frequency == "DAILY":
            self.interval_label.config(text=self.i18n.get("rrule.interval.days"))
            self.weekdays_frame.grid_remove()
            self.monthly_frame.grid_remove()
        elif frequency == "WEEKLY":
            self.interval_label.config(text=self.i18n.get("rrule.interval.weeks"))
            self.weekdays_frame.grid()
            self.monthly_frame.grid_remove()
        elif frequency == "MONTHLY":
            self.interval_label.config(text=self.i18n.get("rrule.interval.months"))
            self.weekdays_frame.grid_remove()
            self.monthly_frame.grid()
        elif frequency == "YEARLY":
            self.interval_label.config(text=self.i18n.get("rrule.interval.years"))
            self.weekdays_frame.grid_remove()
            self.monthly_frame.grid_remove()

        self._update_preview()

    def _apply_preset(self, preset: str):
        """Apply preset configuration"""
        if preset == "daily":
            self.frequency_var.set("DAILY")
            self.interval_var.set(1)
        elif preset == "weekdays":
            self.frequency_var.set("WEEKLY")
            self.interval_var.set(1)
            # Set Monday to Friday
            for day in ["MO", "TU", "WE", "TH", "FR"]:
                self.weekday_vars[day].set(True)
            for day in ["SA", "SU"]:
                self.weekday_vars[day].set(False)
        elif preset == "weekly":
            self.frequency_var.set("WEEKLY")
            self.interval_var.set(1)
            # Set start date weekday
            start_weekday = self.start_date.weekday()  # 0=Monday
            weekday_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            for day in weekday_map:
                self.weekday_vars[day].set(False)
            self.weekday_vars[weekday_map[start_weekday]].set(True)
        elif preset == "monthly":
            self.frequency_var.set("MONTHLY")
            self.interval_var.set(1)
            self.monthly_type_var.set("bymonthday")
            self.monthday_var.set(self.start_date.day)

        self._on_frequency_change()

    def _set_defaults(self):
        """Set default values"""
        self._apply_preset("weekly")

    def _load_rrule(self, rrule: str):
        """Load RRULE into dialog"""
        try:
            components = self.parser.parse_rrule(rrule)

            # Set frequency
            self.frequency_var.set(components.freq.value)

            # Set interval
            if components.interval:
                self.interval_var.set(components.interval)

            # Set weekdays
            if components.byday:
                for day in self.weekday_vars:
                    self.weekday_vars[day].set(False)
                for weekday in components.byday:
                    if weekday in self.weekday_vars:
                        self.weekday_vars[weekday].set(True)

            # Set monthly options
            if components.bymonthday:
                self.monthly_type_var.set("bymonthday")
                self.monthday_var.set(components.bymonthday[0])
            elif components.bysetpos and components.byday:
                self.monthly_type_var.set("bysetpos")
                self.setpos_var.set(str(components.bysetpos[0]))
                self.setpos_weekday_var.set(components.byday[0])

            # Set end condition
            if components.count:
                self.end_type_var.set("count")
                self.count_var.set(components.count)
            elif components.until:
                self.end_type_var.set("until")
                self.until_var.set(components.until.strftime("%Y-%m-%d"))
            else:
                self.end_type_var.set("never")

            self._on_frequency_change()

        except Exception as e:
            logger.error(f"❌ Failed to load RRULE: {e}")
            messagebox.showerror(
                self.i18n.get("error.title"),
                f"{self.i18n.get('recurring.error.invalid_rrule')}: {e}",
            )

    def _build_rrule(self) -> str:
        """Build RRULE from current settings"""
        try:
            # Start with frequency
            rrule_parts = [f"FREQ={self.frequency_var.get()}"]

            # Add interval if not 1
            if self.interval_var.get() != 1:
                rrule_parts.append(f"INTERVAL={self.interval_var.get()}")

            # Add weekdays for weekly frequency
            if self.frequency_var.get() == "WEEKLY":
                selected_days = [
                    day for day, var in self.weekday_vars.items() if var.get()
                ]
                if selected_days:
                    rrule_parts.append(f"BYDAY={','.join(selected_days)}")

            # Add monthly options
            elif self.frequency_var.get() == "MONTHLY":
                if self.monthly_type_var.get() == "bymonthday":
                    rrule_parts.append(f"BYMONTHDAY={self.monthday_var.get()}")
                elif self.monthly_type_var.get() == "bysetpos":
                    rrule_parts.append(f"BYDAY={self.setpos_weekday_var.get()}")
                    rrule_parts.append(f"BYSETPOS={self.setpos_var.get()}")

            # Add end condition
            if self.end_type_var.get() == "count":
                rrule_parts.append(f"COUNT={self.count_var.get()}")
            elif self.end_type_var.get() == "until":
                try:
                    until_date = datetime.strptime(
                        self.until_var.get(), "%Y-%m-%d"
                    ).date()
                    rrule_parts.append(f"UNTIL={until_date.strftime('%Y%m%d')}")
                except ValueError:
                    pass  # Invalid date format, skip

            return ";".join(rrule_parts)

        except Exception as e:
            logger.error(f"❌ Failed to build RRULE: {e}")
            return ""

    def _update_preview(self):
        """Update preview display"""
        try:
            rrule = self._build_rrule()
            self.rrule_text.set(rrule)

            if not rrule:
                self.preview_text.set(self.i18n.get("recurring.error.invalid_rrule"))
                self.preview_listbox.delete(0, tk.END)
                return

            # Generate preview occurrences
            from ..data.models import Event

            # Create temporary event for preview
            temp_event = Event(
                title="Preview Event",
                start_date=self.start_date,
                rrule=rrule,
                is_recurring=True,
            )

            # Generate occurrences for next 3 months
            end_date = self.start_date + timedelta(days=90)
            occurrences = self.generator.generate_occurrences_for_range(
                temp_event, self.start_date, end_date
            )

            # Update preview text
            locale = getattr(self.i18n, "current_locale", "en_GB")
            description = self.parser.get_human_readable_description(rrule, locale)
            self.preview_text.set(description)

            # Update preview list
            self.preview_listbox.delete(0, tk.END)
            for occurrence in occurrences[:20]:  # Show first 20 occurrences
                date_str = occurrence.start_date.strftime("%Y-%m-%d")
                weekday = occurrence.start_date.strftime("%A")
                self.preview_listbox.insert(tk.END, f"{date_str} ({weekday})")

            if len(occurrences) > 20:
                self.preview_listbox.insert(
                    tk.END, f"... and {len(occurrences) - 20} more"
                )

        except Exception as e:
            logger.error(f"❌ Preview update failed: {e}")
            self.preview_text.set(
                f"{self.i18n.get('recurring.error.invalid_rrule')}: {e}"
            )
            self.preview_listbox.delete(0, tk.END)

    def _on_ok(self):
        """Handle OK button"""
        try:
            rrule = self._build_rrule()
            if not rrule:
                messagebox.showerror(
                    self.i18n.get("error.title"),
                    self.i18n.get("recurring.error.invalid_rrule"),
                )
                return

            # Validate RRULE
            if not self.parser.validate_rrule(rrule):
                messagebox.showerror(
                    self.i18n.get("error.title"),
                    self.i18n.get("recurring.error.invalid_rrule"),
                )
                return

            self.result_rrule = rrule
            self.cancelled = False
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"❌ RRULE validation failed: {e}")
            messagebox.showerror(
                self.i18n.get("error.title"),
                f"{self.i18n.get('recurring.error.invalid_rrule')}: {e}",
            )

    def _on_cancel(self):
        """Handle Cancel button"""
        self.cancelled = True
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """Show dialog and return RRULE or None if cancelled"""
        self.dialog.wait_window()
        return None if self.cancelled else self.result_rrule


def show_rrule_dialog(
    parent: tk.Tk,
    i18n: I18nManager,
    initial_rrule: Optional[str] = None,
    start_date: Optional[date] = None,
) -> Optional[str]:
    """Show RRULE dialog and return result"""
    dialog = RRuleDialog(parent, i18n, initial_rrule, start_date)
    return dialog.show()
