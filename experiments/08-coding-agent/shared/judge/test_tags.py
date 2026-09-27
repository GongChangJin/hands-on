import pytest

from taskboard.tags import normalize_tags


def test_normalize_tags_strips_casefolds_and_deduplicates_in_order():
    assert normalize_tags([" News ", "news", "", " TECH ", "Straße", "STRASSE"]) == [
        "news",
        "tech",
        "strasse",
    ]


def test_normalize_tags_rejects_non_strings():
    with pytest.raises(TypeError):
        normalize_tags(["valid", 1])
