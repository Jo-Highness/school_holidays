"""Pure school-holiday date logic (no Home Assistant imports, fully testable)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Period:
    """A single holiday period."""

    start: date
    end: date
    name: str


def _to_date(value) -> date | None:
    """Coerce an ISO 'YYYY-MM-DD' string (or date) into a date."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def parse_periods(raw: list[dict], language: str = "DE") -> list[Period]:
    """Turn the openholidaysapi JSON list into sorted Period objects.

    Each raw item has ``startDate``, ``endDate`` and ``name`` (a list of
    ``{language, text}``). We pick the requested language, else the first name.
    """
    out: list[Period] = []
    for item in raw or []:
        start = _to_date(item.get("startDate"))
        end = _to_date(item.get("endDate"))
        if start is None or end is None:
            continue
        names = item.get("name") or []
        text = ""
        for n in names:
            if str(n.get("language", "")).upper() == language.upper():
                text = n.get("text", "")
                break
        if not text and names:
            text = names[0].get("text", "")
        out.append(Period(start=start, end=end, name=text))
    out.sort(key=lambda p: p.start)
    return out


def period_on(day: date, periods: list[Period]) -> Period | None:
    """The holiday period covering ``day`` (inclusive), or None."""
    for p in periods:
        if p.start <= day <= p.end:
            return p
    return None


def is_holiday(day: date, periods: list[Period]) -> bool:
    """True if ``day`` falls within any holiday period."""
    return period_on(day, periods) is not None


def current_or_next(day: date, periods: list[Period]) -> Period | None:
    """The period covering ``day``, else the soonest period starting after it."""
    covering = period_on(day, periods)
    if covering is not None:
        return covering
    upcoming = [p for p in periods if p.start > day]
    return min(upcoming, key=lambda p: p.start) if upcoming else None


def days_until(day: date, period: Period | None) -> int | None:
    """Whole days from ``day`` until the period starts (0 if already running)."""
    if period is None:
        return None
    if period.start <= day <= period.end:
        return 0
    return (period.start - day).days
