import pytest

from taskboard.dates import business_days_between


def test_business_days_excludes_weekends_and_holidays():
    assert business_days_between(
        "2026-09-25",
        "2026-10-03",
        holidays=["2026-09-28", "2026-10-01"],
    ) == 4


def test_business_days_rejects_reversed_range():
    with pytest.raises(ValueError):
        business_days_between("2026-09-26", "2026-09-25")
