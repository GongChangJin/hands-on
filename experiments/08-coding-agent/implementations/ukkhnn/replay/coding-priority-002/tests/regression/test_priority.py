import pytest

from taskboard.priority import parse_priority


def test_parse_priority_accepts_trimmed_numeric_strings():
    assert parse_priority(" 2 ") == 2


@pytest.mark.parametrize("value", [True, False, 1.5, "6", "high"])
def test_parse_priority_rejects_unsupported_values(value):
    with pytest.raises(ValueError):
        parse_priority(value)
