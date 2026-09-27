"""Tag helpers."""


def normalize_tags(values: list[str]) -> list[str]:
    """Return lowercase tags."""

    return [value.lower() for value in values if value]
