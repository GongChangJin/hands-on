
import pytest

from coding_agent.io import load_issues, load_policy
from coding_agent.models import FileEdit, PatchProposal
from coding_agent.policy import (
    PolicyViolation,
    apply_proposal,
    safe_target,
    validate_proposal,
    validate_python_source,
)


def tags_issue():
    return next(issue for issue in load_issues() if issue.task_id == "coding-tags-001")


def proposal(*edits):
    return PatchProposal(summary="test", plan=["apply test edit"], edits=list(edits))


def test_safe_target_blocks_absolute_and_parent_paths(tmp_path):
    with pytest.raises(PolicyViolation, match="unsafe_path"):
        safe_target(tmp_path, "/tmp/outside.py")
    with pytest.raises(PolicyViolation, match="unsafe_path"):
        safe_target(tmp_path, "../outside.py")


def test_proposal_blocks_disallowed_paths(tmp_path):
    current = proposal(
        FileEdit(path="src/taskboard/tags.py", content="pass"),
        FileEdit(path="secrets.txt", content="no"),
    )

    with pytest.raises(PolicyViolation, match="disallowed_paths"):
        validate_proposal(tmp_path, tags_issue(), load_policy(), current)


def test_proposal_requires_regression_test(tmp_path):
    current = proposal(FileEdit(path="src/taskboard/tags.py", content="pass"))

    with pytest.raises(PolicyViolation, match="missing_regression_test"):
        validate_proposal(tmp_path, tags_issue(), load_policy(), current)


def test_apply_proposal_writes_only_validated_files(tmp_path):
    current = proposal(
        FileEdit(path="src/taskboard/tags.py", content="def normalize_tags(values):\n    return []"),
        FileEdit(path="tests/regression/test_tags.py", content="def test_tags():\n    assert True"),
    )

    changed = apply_proposal(tmp_path, tags_issue(), load_policy(), current)

    assert changed == ["src/taskboard/tags.py", "tests/regression/test_tags.py"]
    assert (tmp_path / "src/taskboard/tags.py").is_file()
    assert (tmp_path / "tests/regression/test_tags.py").is_file()


def test_safe_target_rejects_symlink_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "src").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PolicyViolation, match="symlink_parent"):
        safe_target(tmp_path, "src/taskboard/tags.py")


@pytest.mark.parametrize(
    "content",
    [
        "import subprocess\nsubprocess.run(['git', 'status'])\n",
        "from socket import socket\nsocket().connect(('example.com', 80))\n",
        "open('/tmp/output', 'w')\n",
    ],
)
def test_python_source_gate_rejects_process_network_and_file_access(content):
    with pytest.raises(PolicyViolation):
        validate_python_source("tests/regression/test_escape.py", content)
