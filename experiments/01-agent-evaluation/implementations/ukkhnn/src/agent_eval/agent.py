"""A deliberately small Agent whose tool choices are easy to inspect."""

from __future__ import annotations

import ast
import json
import operator
from collections.abc import Callable
from typing import Literal

from agents import Agent, Model, function_tool, handoff
from agents.extensions import handoff_filters


BinaryOperator = Callable[[int | float, int | float], int | float]
UnaryOperator = Callable[[int | float], int | float]
Architecture = Literal["single", "handoff"]
ARCHITECTURES: tuple[Architecture, ...] = ("single", "handoff")
PROMPT_VERSION = "v2"

_BINARY_OPERATORS: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], UnaryOperator] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_arithmetic(expression: str) -> int | float:
    """Evaluate arithmetic expressions without allowing names or function calls."""

    expression = expression.replace("^", "**")

    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            return _BINARY_OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _UNARY_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("숫자와 기본 산술 연산만 사용할 수 있습니다.")

    parsed = ast.parse(expression, mode="eval")
    return evaluate(parsed.body)


@function_tool
def calculator(expression: str) -> str:
    """정확한 산술 계산에 사용합니다. 거듭제곱은 ^ 또는 **로 입력할 수 있습니다."""

    return str(evaluate_arithmetic(expression))


PROJECTS = {
    "01-agent-evaluation": {
        "status": "active",
        "purpose": "Agent 관측과 평가 기술스택을 비교하고 익힌다.",
    }
}


def project_status(project_name: str) -> dict[str, str]:
    """Return local project metadata used by the demo tool."""

    if project_name.strip() in {"프로젝트", "핸즈온 프로젝트", "현재 프로젝트"}:
        project_name = "01-agent-evaluation"

    try:
        return PROJECTS[project_name]
    except KeyError as exc:
        raise ValueError(f"알 수 없는 프로젝트입니다: {project_name}") from exc


@function_tool
def lookup_project_status(project_name: str) -> str:
    """핸즈온 프로젝트의 현재 상태와 목적을 조회합니다."""

    return json.dumps(project_status(project_name), ensure_ascii=False)


def _single_agent(model: str | Model) -> Agent:
    return Agent(
        name="Hands-on Evaluation Agent",
        model=model,
        instructions=(
            "당신은 핸즈온 프로젝트 도우미입니다. 산술 계산에는 반드시 calculator를 사용하고, "
            "프로젝트 상태 질문에는 반드시 lookup_project_status를 사용하세요. "
            "질문에 두 작업이 모두 있으면 두 도구를 모두 호출하세요. "
            "프로젝트명이 생략되면 현재 프로젝트인 01-agent-evaluation을 조회하세요. "
            "도구 결과를 바꾸거나 추측하지 말고 간결한 한국어로 답하세요."
        ),
        tools=[calculator, lookup_project_status],
    )


def _handoff_agent(model: str | Model) -> Agent:
    calculator_agent = Agent(
        name="Calculator Specialist",
        handoff_description="산술 계산만 요청한 경우 이 Agent로 전달합니다.",
        model=model,
        instructions=(
            "당신은 계산 전문 Agent입니다. 암산으로 답하지 마세요. 답변 전에 calculator를 "
            "정확히 한 번 호출해야 합니다. 거듭제곱은 ^ 또는 **로 전달할 수 있습니다. "
            "도구 결과를 그대로 간결한 한국어로 답하세요."
        ),
        tools=[calculator],
    )
    project_agent = Agent(
        name="Project Specialist",
        handoff_description="프로젝트 상태나 목적만 요청한 경우 이 Agent로 전달합니다.",
        model=model,
        instructions=(
            "당신은 프로젝트 조회 전문 Agent입니다. 반드시 lookup_project_status를 사용하고 "
            "프로젝트명이 생략되면 01-agent-evaluation을 조회하세요. 도구가 반환한 상태와 "
            "목적만 간결한 한국어로 답하세요."
        ),
        tools=[lookup_project_status],
    )
    combined_agent = Agent(
        name="Combined Specialist",
        handoff_description="계산과 프로젝트 조회를 한 요청에서 모두 요구한 경우 이 Agent로 전달합니다.",
        model=model,
        instructions=(
            "당신은 복합 요청 전문 Agent입니다. 계산에는 calculator, 프로젝트 정보에는 "
            "lookup_project_status를 답변 전에 반드시 각각 호출하세요. 프로젝트명이 생략되면 "
            "01-agent-evaluation을 조회하세요. 두 도구 결과를 모두 간결한 한국어로 답하세요."
        ),
        tools=[calculator, lookup_project_status],
    )
    return Agent(
        name="Triage Agent",
        model=model,
        instructions=(
            "사용자 요청을 직접 답하지 말고 정확히 하나의 전문 Agent로 즉시 전달하세요. "
            "계산만 있으면 Calculator Specialist, 프로젝트 질문만 있으면 Project Specialist, "
            "두 종류가 함께 있으면 Combined Specialist로 전달하세요."
        ),
        handoffs=[
            handoff(calculator_agent, input_filter=handoff_filters.remove_all_tools),
            handoff(project_agent, input_filter=handoff_filters.remove_all_tools),
            handoff(combined_agent, input_filter=handoff_filters.remove_all_tools),
        ],
    )


def build_agent(model: str | Model, architecture: Architecture = "single") -> Agent:
    """Build either the baseline single Agent or the handoff comparison Agent."""

    if architecture == "single":
        return _single_agent(model)
    if architecture == "handoff":
        return _handoff_agent(model)
    raise ValueError(f"지원하지 않는 Agent 구조입니다: {architecture}")
