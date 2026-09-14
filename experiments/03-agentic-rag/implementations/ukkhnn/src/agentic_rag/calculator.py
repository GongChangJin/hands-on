"""A deterministic arithmetic tool with a deliberately narrow grammar."""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable


Number = int | float
BinaryOperator = Callable[[Number, Number], Number]
UnaryOperator = Callable[[Number], Number]

_BINARY: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY: dict[type[ast.unaryop], UnaryOperator] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_arithmetic(expression: str) -> Number:
    if len(expression) > 120:
        raise ValueError("계산식이 너무 깁니다.")
    tree = ast.parse(expression.replace("^", "**"), mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 50:
        raise ValueError("계산식이 너무 복잡합니다.")

    def evaluate(node: ast.AST) -> Number:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value: Number = node.value
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            value = _UNARY[type(node.op)](evaluate(node.operand))
        elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("지수의 절댓값은 12 이하여야 합니다.")
            value = _BINARY[type(node.op)](left, right)
        else:
            raise ValueError("숫자와 기본 산술 연산만 사용할 수 있습니다.")
        if not math.isfinite(float(value)) or abs(float(value)) > 1_000_000_000_000:
            raise ValueError("계산 결과의 허용 범위를 벗어났습니다.")
        return value

    return evaluate(tree.body)


def format_number(value: Number) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.12g}" if isinstance(value, float) else str(value)
