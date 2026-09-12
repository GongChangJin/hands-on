import pytest

from agent_eval.agent import evaluate_arithmetic, project_status
from agent_eval.providers import provider_spec


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("6 * 7", 42),
        ("(10 + 2) / 3", 4),
        ("2 ** 5", 32),
    ],
)
def test_evaluate_arithmetic(expression: str, expected: int | float) -> None:
    assert evaluate_arithmetic(expression) == expected


def test_evaluate_arithmetic_rejects_code_execution() -> None:
    with pytest.raises(ValueError, match="기본 산술"):
        evaluate_arithmetic("__import__('os').getcwd()")


def test_project_status() -> None:
    assert project_status("01-agent-evaluation")["status"] == "active"


def test_provider_defaults() -> None:
    assert provider_spec("upstage").default_model == "solar-pro4"
    assert provider_spec("deepseek").default_model == "deepseek-v4-flash"
    assert provider_spec("upstage").experiment_concurrency == 3
    assert provider_spec("deepseek").experiment_concurrency == 1


def test_unknown_provider() -> None:
    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        provider_spec("unknown")
