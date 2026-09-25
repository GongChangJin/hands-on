import pytest

from taskboard.titles import truncate_title


def test_truncate_title_uses_single_ellipsis_and_exact_limit():
    assert truncate_title("Alpha Beta Gamma", 11) == "Alpha Beta…"
    assert len(truncate_title("가나다라마바사", 5)) == 5
    assert truncate_title("가나다라마바사", 5).endswith("…")


def test_truncate_title_handles_small_limits():
    assert truncate_title("Long", 1) == "…"
    with pytest.raises(ValueError):
        truncate_title("Long", 0)
