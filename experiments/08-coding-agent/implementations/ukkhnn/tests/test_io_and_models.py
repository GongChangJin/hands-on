from coding_agent.contracts import validate
from coding_agent.evaluation import task_request
from coding_agent.io import load_issues, load_policy
from coding_agent.models import FileEdit, PatchProposal
from coding_agent.provider import ReplayPatchProvider, estimate_solar_pro4_cost


def test_shared_corpus_has_five_unique_issues():
    issues = load_issues()

    assert len(issues) == 5
    assert len({issue.task_id for issue in issues}) == 5
    assert all(issue.regression_test_path in issue.allowed_paths for issue in issues)


def test_policy_bounds_attempts_files_and_tools():
    policy = load_policy()

    assert policy.max_attempts == 2
    assert policy.max_changed_files == 2
    assert "git_push" in policy.forbidden_actions
    assert "repository.write" in policy.allowed_tools


def test_every_issue_adapts_to_task_request_contract():
    policy = load_policy()

    for issue in load_issues():
        validate("task-request", task_request(issue, policy))


def test_patch_proposal_rejects_duplicate_paths():
    try:
        PatchProposal(
            summary="duplicate",
            plan=["test duplicate validation"],
            edits=[FileEdit(path="x.py", content="x"), FileEdit(path="x.py", content="y")],
        )
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate paths should fail validation")


def test_cost_uses_provider_reported_tokens():
    assert estimate_solar_pro4_cost(1000, 200, 500) == 0.000852


def test_replay_provider_has_a_scoped_patch_for_every_issue():
    provider = ReplayPatchProvider()

    for issue in load_issues():
        result = provider.propose(issue, {}, [], 1)

        assert result.model == "reference-replay-v1"
        assert {edit.path for edit in result.proposal.edits} == set(issue.allowed_paths)
        assert result.cost_usd == 0
