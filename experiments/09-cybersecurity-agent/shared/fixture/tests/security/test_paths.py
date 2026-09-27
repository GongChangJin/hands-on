from pathlib import Path

import pytest

from security_lab.paths import read_user_file, write_report


def test_read_rejects_parent_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        read_user_file(tmp_path, "../outside.txt")


def test_write_rejects_parent_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        write_report(tmp_path, "../outside.txt", "blocked")
