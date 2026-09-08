# 도구 2종: 문서 검색(retriever)과 결정적 계산(calculator).
# 계산은 LLM에 맡기지 않고 AST로 직접 평가한다 (계산 정확도 100% 목표).
from __future__ import annotations

import ast
import json
import operator
import re
from dataclasses import dataclass
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "sample.jsonl"


@dataclass
class Doc:
    doc_id: str
    page: int
    text: str
    source: str = ""

    def cite(self) -> str:
        # 근거 표기 형식. evalkit 의 cited grader 가 이 패턴을 찾는다.
        return f"[{self.doc_id}:p{self.page}]"


def load_corpus(path: str | Path | None = None) -> list[Doc]:
    p = Path(path or CORPUS)
    docs: list[Doc] = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(Doc(**json.loads(line)))
    return docs


def _tokens(text: str) -> list[str]:
    return re.findall(r"[0-9A-Za-z가-힣]+", text.lower())


def retrieve(query: str, k: int = 3, corpus: list[Doc] | None = None) -> list[Doc]:
    # 의존성 없는 키워드 스코어링. 임베딩 검색으로 교체할 수 있게 시그니처를 고정해 둔다.
    docs = corpus if corpus is not None else load_corpus()
    q = set(_tokens(query))
    scored = []
    for d in docs:
        t = _tokens(d.text)
        if not t:
            continue
        overlap = sum(1 for w in t if w in q)
        scored.append((overlap / len(t) ** 0.5, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for score, d in scored[:k] if score > 0]


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression: str) -> float:
    # 산술식만 허용한다. 이름, 호출, 첨자는 전부 거부한다.
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"허용되지 않은 식: {ast.dump(node)}")

    cleaned = expression.replace(",", "").replace("_", "")
    return _eval(ast.parse(cleaned, mode="eval"))
