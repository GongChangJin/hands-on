import pytest

from computer_use_agent.io import load_policy
from computer_use_agent.policy import PolicyGuard, PolicyViolation


def guard():
    return PolicyGuard(load_policy())


def test_localhost_url_is_allowed():
    guard().validate_url("http://127.0.0.1:8123/index.html")


def test_external_url_is_blocked():
    with pytest.raises(PolicyViolation, match="disallowed_origin"):
        guard().validate_url("https://example.com")


def test_file_scheme_is_blocked():
    with pytest.raises(PolicyViolation, match="disallowed_origin"):
        guard().validate_url("file:///etc/passwd")


def test_step_limit_is_enforced():
    policy = load_policy()

    with pytest.raises(PolicyViolation, match="step_limit"):
        guard().validate_step(policy.max_steps + 1)


def test_recovery_limit_is_enforced():
    policy = load_policy()

    with pytest.raises(PolicyViolation, match="recovery_limit"):
        guard().validate_recovery(policy.max_recoveries + 1)
