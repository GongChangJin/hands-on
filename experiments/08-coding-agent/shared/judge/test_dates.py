import pytest

from taskboard.dates import business_days_between


def test_business_days_excludes_weekends_and_holidays():
    assert business_days_between(
        "2026-09-25",
        "2026-10-03",
        holidays=["2026-09-28", "2026-10-01"],
    ) == 4


def test_business_days_handles_empty_interval():
    assert business_days_between("2026-09-25", "2026-09-25") == 0


def test_business_days_rejects_reversed_or_invalid_dates():
    with pytest.raises(ValueError):
        business_days_between("2026-09-26", "2026-09-25")
    with pytest.raises(ValueError):
        business_days_between("not-a-date", "2026-09-25")
