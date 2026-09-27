from pathlib import Path

from security_lab.controls import safe_read, safe_user_lookup
from security_lab.paths import read_user_file, write_report
from security_lab.sql import find_order, find_user


class Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, parameters=None):
        self.calls.append((query, parameters))
        return self

    def fetchall(self):
        return ["row"]


def test_sql_helpers_return_rows():
    cursor = Cursor()
    assert find_user(cursor, "alice") == ["row"]
    assert find_order(cursor, "42") == ["row"]
    assert safe_user_lookup(cursor, "alice") == ["row"]


def test_file_helpers_work_inside_base(tmp_path: Path):
    (tmp_path / "note.txt").write_text("note", encoding="utf-8")
    assert read_user_file(tmp_path, "note.txt") == "note"
    assert safe_read(tmp_path, "note.txt") == "note"
    write_report(tmp_path, "report.txt", "report")
    assert (tmp_path / "report.txt").read_text(encoding="utf-8") == "report"
