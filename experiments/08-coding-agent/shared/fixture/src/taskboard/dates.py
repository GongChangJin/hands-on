"""Date helpers."""

from collections.abc import Iterable
from datetime import date


def business_days_between(start: str, end: str, holidays: Iterable[str] = ()) -> int:
    """Return the number of calendar days in the half-open interval."""

    del holidays
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    return max(0, (end_date - start_date).days)
