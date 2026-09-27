import pytest

from taskboard.priority import parse_priority


@pytest.mark.parametrize(("value", "expected"), [(1, 1), (5, 5), (" 2 ", 2)])
def test_parse_priority_accepts_supported_values(value, expected):
    assert parse_priority(value) == expected


@pytest.mark.parametrize("value", [True, False, 1.5, None, "high", "0", "6"])
def test_parse_priority_rejects_unsupported_values(value):
    with pytest.raises(ValueError):
        parse_priority(value)
