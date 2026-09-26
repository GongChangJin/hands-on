"""Secure controls that should not produce findings."""

import os
from pathlib import Path


def safe_user_lookup(cursor, username: str):
    return cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()


def safe_read(base: Path, user_path: str) -> str:
    root = base.resolve()
    candidate = (root / user_path).resolve()
    candidate.relative_to(root)
    return candidate.read_text(encoding="utf-8")


def environment_secret() -> str:
    return os.environ["CONTROL_SECRET"]
