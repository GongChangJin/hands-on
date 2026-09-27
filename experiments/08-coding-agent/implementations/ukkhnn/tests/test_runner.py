import shutil

from coding_agent.io import shared_dir
from coding_agent.runner import _safe_environment, run_lint, run_tests


def test_subprocess_environment_excludes_api_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("UPSTAGE_API_KEY", "secret")

    environment = _safe_environment(tmp_path)

    assert "UPSTAGE_API_KEY" not in environment
    assert environment["PYTHONPATH"] == str(tmp_path / "src")


def test_fixture_public_tests_and_lint_pass(tmp_path):
    workspace = tmp_path / "workspace"
    shutil.copytree(shared_dir() / "fixture", workspace)

    assert run_tests(workspace, 30, include_regression=False).passed
    assert run_lint(workspace, 30).passed
