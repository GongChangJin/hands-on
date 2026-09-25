"""Date helpers."""

from collections.abc import Iterable
from datetime import date, timedelta


def business_days_between(start: str, end: str, holidays: Iterable[str] = ()) -> int:
    """Return business days in the half-open interval from start to end."""

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end must not be earlier than start")
    holiday_dates = {date.fromisoformat(value) for value in holidays}
    current = start_date
    count = 0
    while current < end_date:
        if current.weekday() < 5 and current not in holiday_dates:
            count += 1
        current += timedelta(days=1)
    return count
