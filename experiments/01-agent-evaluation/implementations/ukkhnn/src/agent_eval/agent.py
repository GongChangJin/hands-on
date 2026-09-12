"""A deliberately small Agent whose tool choices are easy to inspect."""

from __future__ import annotations

import ast
import json
import operator
from collections.abc import Callable

from agents import Agent, Model, function_tool


BinaryOperator = Callable[[int | float, int | float], int | float]
UnaryOperator = Callable[[int | float], int | float]

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
    """정확한 산술 계산이 필요할 때 사용합니다."""

    return str(evaluate_arithmetic(expression))


PROJECTS = {
    "01-agent-evaluation": {
        "status": "active",
        "purpose": "Agent 관측과 평가 기술스택을 비교하고 익힌다.",
    }
}


def project_status(project_name: str) -> dict[str, str]:
    """Return local project metadata used by the demo tool."""

    try:
        return PROJECTS[project_name]
    except KeyError as exc:
        raise ValueError(f"알 수 없는 프로젝트입니다: {project_name}") from exc


@function_tool
def lookup_project_status(project_name: str) -> str:
    """핸즈온 프로젝트의 현재 상태와 목적을 조회합니다."""

    return json.dumps(project_status(project_name), ensure_ascii=False)


def build_agent(model: str | Model) -> Agent:
    return Agent(
        name="Hands-on Evaluation Agent",
        model=model,
        instructions=(
            "당신은 핸즈온 프로젝트 도우미입니다. 산술 계산에는 반드시 calculator를 사용하고, "
            "프로젝트 상태 질문에는 반드시 lookup_project_status를 사용하세요. "
            "도구 결과를 바꾸거나 추측하지 말고 간결한 한국어로 답하세요."
        ),
        tools=[calculator, lookup_project_status],
    )
