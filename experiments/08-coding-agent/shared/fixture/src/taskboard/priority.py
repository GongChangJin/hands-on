"""Priority parsing."""


def parse_priority(value: object) -> int:
    """Parse a priority from one to five."""

    priority = int(value)
    if not 1 <= priority <= 5:
        raise ValueError("priority must be between 1 and 5")
    return priority
