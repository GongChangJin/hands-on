"""Title formatting."""


def truncate_title(text: str, max_length: int = 40) -> str:
    """Truncate a title with three dots."""

    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
