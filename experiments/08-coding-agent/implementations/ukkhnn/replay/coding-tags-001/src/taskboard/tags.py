"""Tag helpers."""


def normalize_tags(values: list[str]) -> list[str]:
    """Normalize unique tags while preserving their first-seen order."""

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("tags must be strings")
        tag = value.strip().casefold()
        if tag and tag not in seen:
            normalized.append(tag)
            seen.add(tag)
    return normalized
