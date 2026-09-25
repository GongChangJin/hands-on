"""Priority parsing."""


def parse_priority(value: object) -> int:
    """Parse an integer priority from one to five."""

    if isinstance(value, bool):
        raise ValueError("priority must be an integer or numeric string")
    if isinstance(value, int):
        priority = value
    elif isinstance(value, str) and value.strip() in {"1", "2", "3", "4", "5"}:
        priority = int(value.strip())
    else:
        raise ValueError("priority must be an integer or numeric string")
    if not 1 <= priority <= 5:
        raise ValueError("priority must be between 1 and 5")
    return priority
