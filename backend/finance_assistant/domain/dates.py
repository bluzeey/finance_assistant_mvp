"""Dataset-anchored date resolution helpers."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum


class DateResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class CalendarBasis(StrEnum):
    EXPLICIT = "explicit"
    CALENDAR = "calendar"
    FISCAL = "fiscal"
    ROLLING = "rolling"


@dataclass(frozen=True, slots=True)
class ResolvedDateRange:
    start: date
    end_exclusive: date
    date_field: str
    source_phrase: str
    anchor_date: date
    calendar_basis: CalendarBasis


@dataclass(frozen=True, slots=True)
class DateResolution:
    status: DateResolutionStatus
    date_range: ResolvedDateRange | None
    reason: str | None = None
    choices: tuple[str, ...] = ()


def resolve_period(
    phrase: str,
    anchor: date,
    date_field: str,
    fiscal_year_start_month: int = 4,
    requested_basis: CalendarBasis | None = None,
) -> DateResolution:
    """Resolve supported period phrases using the dataset anchor, never wall-clock time."""
    normalized = " ".join(phrase.strip().lower().split())
    basis = requested_basis or CalendarBasis.CALENDAR

    if normalized in {"last month", "previous month"}:
        first_this_month = anchor.replace(day=1)
        last_month_end = first_this_month
        last_month_start = (first_this_month - timedelta(days=1)).replace(day=1)
        return _resolved(
            last_month_start,
            last_month_end,
            date_field,
            phrase,
            anchor,
            CalendarBasis.CALENDAR,
        )

    if normalized in {"this month", "month to date", "mtd"}:
        return _resolved(
            anchor.replace(day=1),
            anchor + timedelta(days=1),
            date_field,
            phrase,
            anchor,
            basis,
        )

    if normalized in {"last 30 days", "past 30 days"}:
        return _resolved(
            anchor - timedelta(days=29),
            anchor + timedelta(days=1),
            date_field,
            phrase,
            anchor,
            CalendarBasis.ROLLING,
        )

    if normalized == "recent":
        return DateResolution(
            status=DateResolutionStatus.AMBIGUOUS,
            date_range=None,
            reason="recent has no accepted default",
            choices=("last 7 days", "last 30 days", "current month-to-date"),
        )

    if normalized == "q2":
        return DateResolution(
            status=DateResolutionStatus.AMBIGUOUS,
            date_range=None,
            reason="bare Q2 lacks calendar/fiscal basis and year",
            choices=("calendar Q2 with year", "fiscal Q2 with year"),
        )

    explicit_month = _parse_month_year(normalized)
    if explicit_month is not None:
        year, month = explicit_month
        start = date(year, month, 1)
        end = _first_day_next_month(start)
        explicit_basis = requested_basis or CalendarBasis.EXPLICIT
        return _resolved(start, end, date_field, phrase, anchor, explicit_basis)

    if normalized.startswith("fiscal q"):
        quarter = _parse_fiscal_quarter(normalized)
        if quarter is not None:
            year, quarter_number = quarter
            start_month = ((fiscal_year_start_month - 1) + (quarter_number - 1) * 3) % 12 + 1
            start_year = year if start_month >= fiscal_year_start_month else year + 1
            start = date(start_year, start_month, 1)
            end = _add_months(start, 3)
            return _resolved(start, end, date_field, phrase, anchor, CalendarBasis.FISCAL)

    return DateResolution(
        status=DateResolutionStatus.UNSUPPORTED,
        date_range=None,
        reason=f"Unsupported period phrase: {phrase}",
    )


def _resolved(
    start: date,
    end_exclusive: date,
    date_field: str,
    phrase: str,
    anchor: date,
    basis: CalendarBasis,
) -> DateResolution:
    return DateResolution(
        status=DateResolutionStatus.RESOLVED,
        date_range=ResolvedDateRange(
            start=start,
            end_exclusive=end_exclusive,
            date_field=date_field,
            source_phrase=phrase,
            anchor_date=anchor,
            calendar_basis=basis,
        ),
    )


def _parse_month_year(normalized: str) -> tuple[int, int] | None:
    parts = normalized.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    month_lookup = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
    month_lookup.update(
        {name.lower(): index for index, name in enumerate(calendar.month_abbr) if name}
    )
    month = month_lookup.get(parts[0])
    if month is None:
        return None
    return int(parts[1]), month


def _parse_fiscal_quarter(normalized: str) -> tuple[int, int] | None:
    # Supported explicit shape: "fiscal q2 2026".
    parts = normalized.split()
    if len(parts) != 3 or not parts[1].startswith("q") or not parts[2].isdigit():
        return None
    quarter_text = parts[1].removeprefix("q")
    if quarter_text not in {"1", "2", "3", "4"}:
        return None
    return int(parts[2]), int(quarter_text)


def _first_day_next_month(value: date) -> date:
    return _add_months(value, 1)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    return date(value.year + month_index // 12, month_index % 12 + 1, 1)
