from coding_agent.models import FileEdit, PatchProposal, ProviderResult

TAGS_SOURCE = '''"""Tag helpers."""


def normalize_tags(values: list[str]) -> list[str]:
    """Normalize tags while preserving first occurrence order."""

    normalized_tags: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("tags must be strings")
        normalized = value.strip().casefold()
        if normalized and normalized not in seen:
            seen.add(normalized)
            normalized_tags.append(normalized)
    return normalized_tags
'''


TAGS_TEST = '''import pytest

from taskboard.tags import normalize_tags


def test_normalize_tags_handles_whitespace_duplicates_and_types():
    assert normalize_tags([" News ", "news", "", " TECH "]) == ["news", "tech"]
    with pytest.raises(TypeError):
        normalize_tags(["ok", 1])
'''


class StaticProvider:
    def __init__(self):
        self.seen_files: list[set[str]] = []

    def propose(self, issue, files, feedback, attempt):
        self.seen_files.append(set(files))
        return ProviderResult(
            proposal=PatchProposal(
                summary="normalize tags and add regression coverage",
                plan=["normalize tag values", "add focused regression coverage"],
                edits=[
                    FileEdit(path="src/taskboard/tags.py", content=TAGS_SOURCE),
                    FileEdit(path="tests/regression/test_tags.py", content=TAGS_TEST),
                ],
            ),
            model="fake-model",
            latency_ms=1,
            input_tokens=10,
            cached_input_tokens=0,
            output_tokens=20,
            cost_usd=0.001,
        )
