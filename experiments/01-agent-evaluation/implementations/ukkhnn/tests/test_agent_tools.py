import pytest

from datetime import datetime, timezone

from agent_eval.agent import build_agent, evaluate_arithmetic, project_status
from agent_eval.providers import estimate_cost_usd, provider_spec


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("6 * 7", 42),
        ("(10 + 2) / 3", 4),
        ("2 ** 5", 32),
        ("9^2", 81),
    ],
)
def test_evaluate_arithmetic(expression: str, expected: int | float) -> None:
    assert evaluate_arithmetic(expression) == expected


def test_evaluate_arithmetic_rejects_code_execution() -> None:
    with pytest.raises(ValueError, match="기본 산술"):
        evaluate_arithmetic("__import__('os').getcwd()")


def test_project_status() -> None:
    assert project_status("01-agent-evaluation")["status"] == "active"
    assert project_status("현재 프로젝트")["status"] == "active"


def test_provider_defaults() -> None:
    assert provider_spec("upstage").default_model == "solar-pro4"
    assert provider_spec("deepseek").default_model == "deepseek-v4-flash"
    assert provider_spec("upstage").experiment_concurrency == 3
    assert provider_spec("deepseek").experiment_concurrency == 1


def test_unknown_provider() -> None:
    with pytest.raises(ValueError, match="지원하지 않는 provider"):
        provider_spec("unknown")


def test_agent_architectures() -> None:
    single = build_agent("test-model", "single")
    handoff = build_agent("test-model", "handoff")

    assert single.name == "Hands-on Evaluation Agent"
    assert [target.agent_name for target in handoff.handoffs] == [
        "Calculator Specialist",
        "Project Specialist",
        "Combined Specialist",
    ]


def test_published_provider_cost_estimates() -> None:
    upstage = estimate_cost_usd(
        "upstage",
        "solar-pro4",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    deepseek_off_peak = estimate_cost_usd(
        "deepseek",
        "deepseek-v4-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        at=datetime(2026, 9, 13, tzinfo=timezone.utc),
    )

    assert upstage == pytest.approx(1.50)
    assert deepseek_off_peak == pytest.approx(0.88)
    assert (
        estimate_cost_usd("upstage", "unknown", input_tokens=1, output_tokens=1)
        is None
    )
