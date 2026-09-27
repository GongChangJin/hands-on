"""Contained file helpers."""

from pathlib import Path


def _contained(base: Path, user_path: str) -> Path:
    root = base.resolve()
    candidate = (root / user_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("path escapes the allowed base") from error
    return candidate


def read_user_file(base: Path, user_path: str) -> str:
    return _contained(base, user_path).read_text(encoding="utf-8")


def write_report(base: Path, report_name: str, content: str) -> None:
    _contained(base, report_name).write_text(content, encoding="utf-8")
