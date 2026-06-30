"""100% coverage for rrule_parser.py (RFC 5545 RRULE handling)."""

from __future__ import annotations

from datetime import date

import pytest

from calendar_app.core.rrule_parser import (
    Frequency,
    RRuleComponents,
    RRuleParser,
    Weekday,
)


@pytest.fixture
def parser():
    return RRuleParser()


def test_parse_rrule_empty_raises(parser):
    with pytest.raises(ValueError):
        parser.parse_rrule("")


def test_parse_rrule_missing_freq_raises(parser):
    with pytest.raises(ValueError):
        parser.parse_rrule("INTERVAL=2")


def test_parse_rrule_invalid_freq_raises(parser):
    with pytest.raises(ValueError):
        parser.parse_rrule("FREQ=NOPE")


def test_parse_rrule_full(parser):
    c = parser.parse_rrule(
        "RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=5;BYDAY=MO,WE;"
        "BYMONTHDAY=1,15;BYYEARDAY=100;BYWEEKNO=2;BYMONTH=6;BYSETPOS=1;WKST=SU"
    )
    assert c.freq == Frequency.WEEKLY
    assert c.interval == 2
    assert c.count == 5
    assert c.byday == ["MO", "WE"]
    assert c.bymonthday == [1, 15]
    assert c.bymonth == [6]
    assert c.wkst == Weekday.SUNDAY
    # A bare token without "=" is ignored.
    assert parser.parse_rrule("FREQ=DAILY;JUNK").freq == Frequency.DAILY


def test_parse_until_date_and_datetime(parser):
    assert parser.parse_rrule("FREQ=DAILY;UNTIL=20261231").until == date(2026, 12, 31)
    assert parser.parse_rrule("FREQ=DAILY;UNTIL=20261231T235900Z").until == date(
        2026, 12, 31
    )


def test_parse_int_list_invalid_returns_empty(parser):
    assert parser.parse_rrule("FREQ=DAILY;BYMONTHDAY=x,y").bymonthday == []


def test_generate_rrule_round_trip_and_defaults(parser):
    # Minimal: only FREQ.
    assert parser.generate_rrule(RRuleComponents(freq=Frequency.DAILY)) == "FREQ=DAILY"
    # Everything set, including non-default WKST.
    full = RRuleComponents(
        freq=Frequency.WEEKLY,
        interval=3,
        count=4,
        until=date(2026, 1, 1),
        byday=["MO"],
        bymonthday=[1],
        byyearday=[2],
        byweekno=[3],
        bymonth=[4],
        bysetpos=[1],
        wkst=Weekday.SUNDAY,
    )
    out = parser.generate_rrule(full)
    assert "FREQ=WEEKLY" in out
    assert "INTERVAL=3" in out
    assert "COUNT=4" in out
    assert "UNTIL=20260101" in out
    assert "BYDAY=MO" in out
    assert "BYMONTHDAY=1" in out
    assert "BYYEARDAY=2" in out
    assert "BYWEEKNO=3" in out
    assert "BYMONTH=4" in out
    assert "BYSETPOS=1" in out
    assert "WKST=SU" in out


def test_validate_rrule(parser):
    assert parser.validate_rrule("FREQ=DAILY;COUNT=3") is True
    assert parser.validate_rrule("FREQ=DAILY;COUNT=0") is False
    assert parser.validate_rrule("FREQ=DAILY;INTERVAL=0") is False
    assert parser.validate_rrule("FREQ=DAILY;COUNT=2;UNTIL=20261231") is False
    assert parser.validate_rrule("not an rrule") is False


def test_migrate_legacy_pattern(parser):
    assert parser.migrate_legacy_pattern("weekly") == "FREQ=WEEKLY"
    assert parser.migrate_legacy_pattern("unknown") == "FREQ=DAILY"


def test_description_simple_and_interval(parser):
    assert "Daily" in parser.get_human_readable_description("FREQ=DAILY")
    assert "Every" in parser.get_human_readable_description("FREQ=WEEKLY;INTERVAL=2")
    # Interval>1 for each unit, plus a frequency with no dedicated unit word.
    for rule in ("FREQ=DAILY", "FREQ=MONTHLY", "FREQ=YEARLY", "FREQ=HOURLY"):
        assert parser.get_human_readable_description(f"{rule};INTERVAL=2")


def test_description_weekly_monthly_and_ends(parser):
    assert parser.get_human_readable_description("FREQ=WEEKLY;BYDAY=MO,WE")
    assert parser.get_human_readable_description("FREQ=MONTHLY;BYMONTHDAY=15")
    # Monthly by set position: a mapped one and an unmapped one.
    assert parser.get_human_readable_description("FREQ=MONTHLY;BYSETPOS=1;BYDAY=MO")
    assert parser.get_human_readable_description("FREQ=MONTHLY;BYSETPOS=5;BYDAY=MO")
    assert parser.get_human_readable_description("FREQ=DAILY;COUNT=3")
    assert parser.get_human_readable_description("FREQ=DAILY;UNTIL=20261231")


def test_description_invalid_returns_error_text(parser):
    assert parser.get_human_readable_description("FREQ=NOPE")


def test_text_and_number_fallbacks_without_i18n(parser):
    # With no i18n manager, _get_text/_format_number use their plain fallbacks.
    parser.i18n_manager = None
    assert parser._get_text("any.key", "fallback") == "fallback"
    assert parser._format_number(7) == "7"


def test_weekday_name_known_and_unknown(parser):
    assert parser._get_weekday_name("MO") == "monday"
    assert parser._get_weekday_name("ZZ") == "zz"
