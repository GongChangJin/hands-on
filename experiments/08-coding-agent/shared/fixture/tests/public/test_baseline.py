from taskboard import (
    business_days_between,
    merge_preferences,
    normalize_tags,
    parse_priority,
    truncate_title,
)


def test_existing_tag_behavior():
    assert normalize_tags(["News", "Tech"]) == ["news", "tech"]


def test_existing_priority_behavior():
    assert parse_priority("3") == 3


def test_existing_preference_behavior():
    assert merge_preferences({"theme": "light"}, {"theme": "dark"}) == {"theme": "dark"}


def test_existing_date_behavior():
    assert business_days_between("2026-09-21", "2026-09-24") == 3


def test_existing_title_behavior():
    assert truncate_title("Short", 10) == "Short"
