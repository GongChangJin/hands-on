"""Title formatting."""


def truncate_title(text: str, max_length: int = 40) -> str:
    """Truncate a title with one Unicode ellipsis within the length limit."""

    if max_length < 1:
        raise ValueError("max_length must be at least 1")
    if len(text) <= max_length:
        return text
    if max_length == 1:
        return "…"
    return text[: max_length - 1].rstrip() + "…"
