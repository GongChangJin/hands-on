import shutil

from conftest import StaticProvider

from coding_agent.agent import CodingAgent
from coding_agent.evaluation import all_changed_paths, evaluate_issue
from coding_agent.io import load_issues, load_policy, shared_dir


def tags_issue():
    return next(issue for issue in load_issues() if issue.task_id == "coding-tags-001")


def test_agent_generates_scoped_patch_and_regression_test(tmp_path):
    base = tmp_path / "base"
    workspace = tmp_path / "workspace"
    shutil.copytree(shared_dir() / "fixture", base)
    shutil.copytree(shared_dir() / "fixture", workspace)
    provider = StaticProvider()

    run = CodingAgent(provider, load_policy()).run(tags_issue(), base, workspace)

    assert run.success
    assert run.changed_paths == ["src/taskboard/tags.py", "tests/regression/test_tags.py"]
    assert "normalize_tags" in run.patch
    assert not run.safety_violations


def test_evaluation_keeps_held_out_tests_out_of_provider_context(tmp_path):
    provider = StaticProvider()
    policy = load_policy()
    run = evaluate_issue(
        tags_issue(),
        policy,
        CodingAgent(provider, policy),
        tmp_path / "results",
    )

    assert run.success
    assert run.held_out_tests_passed
    assert run.regression_test_catches_bug
    assert run.scope_passed
    assert run.forbidden_git_actions == 0
    assert all(not path.startswith("tests/judge") for files in provider.seen_files for path in files)


def test_changed_path_scan_ignores_tool_caches(tmp_path):
    base = tmp_path / "base"
    workspace = tmp_path / "workspace"
    base.mkdir()
    workspace.mkdir()
    (workspace / ".pytest_cache").mkdir()
    (workspace / ".pytest_cache" / "state").write_text("ignored", encoding="utf-8")

    assert all_changed_paths(base, workspace) == []
