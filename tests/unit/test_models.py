"""100% coverage for data/models.py (domain data models)."""

from __future__ import annotations

from datetime import date, datetime, time

from calendar_app.data.models import (
    AppSettings,
    CalendarDay,
    CalendarMonth,
    Event,
    Holiday,
    NTPStatus,
    Note,
)

# ── Event ──────────────────────────────────────────────────────────────────


def test_event_post_init_defaults():
    e = Event(title="x")
    assert e.start_date == date.today()
    assert e.end_date == e.start_date
    assert isinstance(e.created_at, datetime)
    assert isinstance(e.updated_at, datetime)


def test_event_validate_collects_errors():
    assert "Title is required" in Event(title="").validate()
    assert any("200 characters" in m for m in Event(title="a" * 201).validate())

    no_start = Event(title="x")
    no_start.start_date = None
    assert "Start date is required" in no_start.validate()

    bad_range = Event(title="x", start_date=date(2026, 1, 2), end_date=date(2026, 1, 1))
    assert "End date cannot be before start date" in bad_range.validate()

    same_day = Event(
        title="x",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        start_time=time(10),
        end_time=time(9),
    )
    assert any("End time must be after" in m for m in same_day.validate())

    assert any(
        "Invalid category" in m for m in Event(title="x", category="zzz").validate()
    )


def test_event_validate_recurrence_rules():
    assert (
        "RRULE is required for recurring events"
        in Event(title="x", is_recurring=True).validate()
    )
    assert (
        "Invalid RRULE format"
        in Event(title="x", is_recurring=True, rrule="FREQ=BOGUS").validate()
    )
    assert (
        "Recurrence ID required when master ID is set"
        in Event(title="x", recurrence_master_id=5).validate()
    )
    assert Event(title="x", is_recurring=True, rrule="FREQ=DAILY").validate() == []


def test_event_recurrence_helpers():
    master = Event(title="x", is_recurring=True, rrule="FREQ=DAILY")
    assert master.is_master() is True
    assert master.is_occurrence() is False
    assert master.get_recurrence_description() != ""

    occ = Event(
        title="x", is_recurring=True, rrule="FREQ=DAILY", recurrence_master_id=1
    )
    assert occ.is_occurrence() is True
    assert occ.is_master() is False

    assert Event(title="x").get_recurrence_description() == ""
    assert Event(title="x")._validate_rrule() is True


def test_event_to_from_dict_round_trip():
    e = Event(
        id=1,
        title="Meeting",
        start_date=date(2026, 6, 1),
        start_time=time(9, 30),
        end_date=date(2026, 6, 1),
        end_time=time(10, 30),
        category="work",
        is_recurring=True,
        rrule="FREQ=WEEKLY",
        exception_dates=[date(2026, 6, 8)],
        recurrence_end_date=date(2026, 12, 1),
    )
    restored = Event.from_dict(e.to_dict())
    assert restored.title == "Meeting"
    assert restored.start_time == time(9, 30)
    assert restored.exception_dates == [date(2026, 6, 8)]
    assert restored.recurrence_end_date == date(2026, 12, 1)


def test_event_from_dict_exception_dates_as_json_and_bad_json():
    good = Event.from_dict({"title": "x", "exception_dates": '["2026-01-01"]'})
    assert good.exception_dates == [date(2026, 1, 1)]

    bad = Event.from_dict({"title": "x", "exception_dates": "not-json"})
    assert bad.exception_dates == []

    # Absent key, and a value that is neither a JSON string nor a list.
    assert Event.from_dict({"title": "x"}).exception_dates == []
    assert Event.from_dict({"title": "x", "exception_dates": 123}).exception_dates == []


def test_event_display_helpers():
    assert Event(title="x", category="work").get_category_emoji()
    plain = Event(title="Lunch", category="meal").get_display_title()
    assert "Lunch" in plain and "🔄" not in plain
    recurring = Event(
        title="Standup", category="work", is_recurring=True, rrule="FREQ=DAILY"
    ).get_display_title()
    assert "🔄" in recurring


# ── Holiday ────────────────────────────────────────────────────────────────


def test_holiday_to_dict_display_and_from_dict():
    h = Holiday(name="Christmas Day", date=date(2026, 12, 25), country_code="GB")
    d = h.to_dict()
    assert d["name"] == "Christmas Day" and d["country_code"] == "GB"
    assert "Christmas Day" in h.get_display_name()
    assert Holiday.from_dict(d).date == date(2026, 12, 25)
    # Missing date defaults to today.
    assert Holiday.from_dict({"name": "X"}).date == date.today()


# ── CalendarDay / CalendarMonth ────────────────────────────────────────────


def test_calendar_day_indicators():
    day = CalendarDay(date=date(2026, 1, 1))
    assert day.get_display_number() == "1"
    assert day.has_events() is False

    few = CalendarDay(
        date=date(2026, 1, 1),
        events=[Event(title=str(i), category="work") for i in range(6)],
    )
    assert len(few.get_event_indicators()) == 6
    assert all(not s.startswith("+") for s in few.get_event_indicators())

    many = CalendarDay(
        date=date(2026, 1, 1),
        events=[Event(title=str(i), category="work") for i in range(8)],
    )
    indicators = many.get_event_indicators()
    assert indicators[-1] == "+3"
    assert len(indicators) == 6


def test_calendar_month():
    m = CalendarMonth(year=2026, month=6)
    assert m.month_name == "June"
    assert m.days_in_month == 30
    assert "June" in m.get_display_title()


# ── AppSettings ────────────────────────────────────────────────────────────


def test_app_settings_round_trip():
    s = AppSettings(theme="light", locale="fr_FR", holiday_country="FR")
    restored = AppSettings.from_dict(s.to_dict())
    assert restored.theme == "light"
    assert restored.holiday_country == "FR"
    # Empty dict falls back to all defaults.
    assert AppSettings.from_dict({}).theme == "dark"


# ── NTPStatus ──────────────────────────────────────────────────────────────


def test_ntp_status_emoji_and_text():
    connected = NTPStatus(is_connected=True, server_used="pool.ntp.org")
    assert connected.get_status_emoji() == "✅"
    assert "pool.ntp.org" in connected.get_status_text()

    failed = NTPStatus(error_message="boom")
    assert failed.get_status_emoji() == "❌"
    assert "boom" in failed.get_status_text()

    connecting = NTPStatus()
    assert connecting.get_status_emoji() == "⏳"
    assert "Connecting" in connecting.get_status_text()


# ── Note ───────────────────────────────────────────────────────────────────


def test_note_round_trip_and_defaults():
    n = Note(id=1, title="1", content="hello")
    assert isinstance(n.created_at, datetime)
    d = n.to_dict()
    assert d["content"] == "hello"
    restored = Note.from_dict(d)
    assert restored.title == "1"
    # Missing timestamps default on construction.
    minimal = Note.from_dict({"id": 2, "title": "2"})
    assert isinstance(minimal.created_at, datetime)
