"""Path and edit policy for generated patches."""

from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath

from .models import CodingIssue, CodingPolicy, PatchProposal


class PolicyViolation(RuntimeError):
    pass


FORBIDDEN_IMPORTS = {
    "httpx",
    "importlib",
    "os",
    "pathlib",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "tempfile",
    "urllib",
}
FORBIDDEN_CALLS = {"__import__", "compile", "eval", "exec", "open"}


def validate_python_source(relative_path: str, content: str) -> None:
    if not relative_path.endswith(".py"):
        return
    try:
        tree = ast.parse(content, filename=relative_path)
    except SyntaxError as error:
        raise PolicyViolation(f"invalid_python:{relative_path}:{error.lineno}") from error
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.partition(".")[0] for alias in node.names}
            if blocked := roots & FORBIDDEN_IMPORTS:
                raise PolicyViolation(f"forbidden_import:{relative_path}:{min(blocked)}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").partition(".")[0]
            if root in FORBIDDEN_IMPORTS:
                raise PolicyViolation(f"forbidden_import:{relative_path}:{root}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                raise PolicyViolation(f"forbidden_call:{relative_path}:{node.func.id}")


def safe_target(workspace: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise PolicyViolation(f"unsafe_path:{relative_path}")
    root = workspace.resolve()
    target = (workspace / Path(*pure.parts)).resolve(strict=False)
    if not target.is_relative_to(root):
        raise PolicyViolation(f"outside_workspace:{relative_path}")
    current = root
    for part in pure.parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise PolicyViolation(f"symlink_parent:{relative_path}")
    if target.exists() and target.is_symlink():
        raise PolicyViolation(f"symlink_target:{relative_path}")
    return target


def validate_proposal(
    workspace: Path,
    issue: CodingIssue,
    policy: CodingPolicy,
    proposal: PatchProposal,
) -> list[tuple[Path, str, str]]:
    if len(proposal.edits) > policy.max_changed_files:
        raise PolicyViolation("changed_file_limit")
    paths = {edit.path for edit in proposal.edits}
    allowed = set(issue.allowed_paths)
    if not paths <= allowed:
        disallowed = sorted(paths - allowed)
        raise PolicyViolation(f"disallowed_paths:{','.join(disallowed)}")
    if issue.regression_test_path not in paths:
        raise PolicyViolation("missing_regression_test")
    implementation_paths = allowed - {issue.regression_test_path}
    if not paths & implementation_paths:
        raise PolicyViolation("missing_implementation_edit")
    validated: list[tuple[Path, str, str]] = []
    for edit in proposal.edits:
        encoded = edit.content.encode("utf-8")
        if len(encoded) > policy.max_file_bytes:
            raise PolicyViolation(f"file_size_limit:{edit.path}")
        if "\x00" in edit.content:
            raise PolicyViolation(f"null_byte:{edit.path}")
        validate_python_source(edit.path, edit.content)
        content = edit.content if edit.content.endswith("\n") else edit.content + "\n"
        validated.append((safe_target(workspace, edit.path), edit.path, content))
    return validated


def apply_proposal(
    workspace: Path,
    issue: CodingIssue,
    policy: CodingPolicy,
    proposal: PatchProposal,
) -> list[str]:
    validated = validate_proposal(workspace, issue, policy, proposal)
    for target, _, content in validated:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return [relative for _, relative, _ in validated]
