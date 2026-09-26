"""Intentionally unsafe file helpers."""

from pathlib import Path


def read_user_file(base: Path, user_path: str) -> str:
    return (base / user_path).read_text(encoding="utf-8")


def write_report(base: Path, report_name: str, content: str) -> None:
    (base / report_name).write_text(content, encoding="utf-8")
