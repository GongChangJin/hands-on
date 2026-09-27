import pytest

from taskboard.tags import normalize_tags


def test_normalize_tags_handles_whitespace_case_and_duplicates():
    assert normalize_tags([" News ", "news", "", " TECH "]) == ["news", "tech"]


def test_normalize_tags_rejects_non_string_values():
    with pytest.raises(TypeError):
        normalize_tags(["valid", 1])
