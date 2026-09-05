from __future__ import annotations

from datetime import date

from finance_assistant.domain.dates import DateResolutionStatus, resolve_period

ANCHOR = date(2026, 9, 3)


def test_last_month_uses_dataset_anchor_and_half_open_range() -> None:
    resolution = resolve_period("last month", ANCHOR, date_field="payout_date")

    assert resolution.status == DateResolutionStatus.RESOLVED
    assert resolution.date_range is not None
    assert resolution.date_range.start == date(2026, 8, 1)
    assert resolution.date_range.end_exclusive == date(2026, 9, 1)
    assert resolution.date_range.anchor_date == ANCHOR


def test_this_month_ends_at_data_as_of_plus_one_day() -> None:
    resolution = resolve_period("this month", ANCHOR, date_field="posting_date")

    assert resolution.date_range is not None
    assert resolution.date_range.start == date(2026, 9, 1)
    assert resolution.date_range.end_exclusive == date(2026, 9, 4)


def test_last_30_days_includes_anchor_date_as_half_open_range() -> None:
    resolution = resolve_period("last 30 days", ANCHOR, date_field="posting_date")

    assert resolution.date_range is not None
    assert resolution.date_range.start == date(2026, 8, 5)
    assert resolution.date_range.end_exclusive == date(2026, 9, 4)


def test_recent_and_bare_q2_are_ambiguous_and_do_not_resolve_numbers() -> None:
    recent = resolve_period("recent", ANCHOR, date_field="posting_date")
    q2 = resolve_period("Q2", ANCHOR, date_field="posting_date")

    assert recent.status == DateResolutionStatus.AMBIGUOUS
    assert recent.date_range is None
    assert q2.status == DateResolutionStatus.AMBIGUOUS
    assert q2.date_range is None


def test_explicit_month_year_resolves_calendar_month() -> None:
    resolution = resolve_period("August 2026", ANCHOR, date_field="payout_date")

    assert resolution.date_range is not None
    assert resolution.date_range.start == date(2026, 8, 1)
    assert resolution.date_range.end_exclusive == date(2026, 9, 1)
