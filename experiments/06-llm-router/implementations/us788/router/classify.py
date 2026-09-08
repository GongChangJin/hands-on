# 라우팅 분류: 규칙 기반 / LLM 기반 / 하이브리드 세 가지를 같은 인터페이스로 비교한다.
from __future__ import annotations

import re
from dataclasses import dataclass, field

ROUTES = ("small", "balanced", "frontier", "local")

# 논리 라우트 판단 신호. 실제 모델 ID는 여기 등장하지 않는다 (models.yaml 이 담당).
HARD_MARKERS = ["증명", "설계", "아키텍처", "최적화", "리팩터", "왜 그런지", "trade-off", "step by step"]
TOOL_MARKERS = ["계산", "검색", "조회", "실행", "api", "sql"]
EASY_MARKERS = ["뜻", "무엇", "요약", "번역", "맞나요", "yes or no"]
SENSITIVE_MARKERS = ["사내", "개인정보", "비공개", "로컬에서만"]


@dataclass
class Decision:
    route: str
    confidence: float
    reason: str
    strategy: str = "rule"
    signals: dict[str, bool] = field(default_factory=dict)


def _has(text: str, markers: list[str]) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in markers)


def rule_classify(prompt: str) -> Decision:
    signals = {
        "long": len(prompt) > 400,
        "hard": _has(prompt, HARD_MARKERS),
        "tool": _has(prompt, TOOL_MARKERS),
        "easy": _has(prompt, EASY_MARKERS),
        "sensitive": _has(prompt, SENSITIVE_MARKERS),
        "multiline": prompt.count("\n") > 5,
        "code": bool(re.search(r"```|def |class |SELECT ", prompt)),
    }
    if signals["sensitive"]:
        return Decision("local", 0.9, "민감 신호 감지 - 로컬 처리", "rule", signals)
    if signals["hard"] or signals["code"] or signals["long"]:
        return Decision("frontier", 0.75, "고난도 신호", "rule", signals)
    if signals["easy"] and not signals["tool"]:
        return Decision("small", 0.7, "단순 질의", "rule", signals)
    return Decision("balanced", 0.45, "명확한 신호 없음", "rule", signals)


def llm_classify(prompt: str, route: str = "small") -> Decision:
    # 분류 자체의 비용도 측정 대상이다 (라우터 비용 제외 금지).
    from evalkit.models import make_chat_model

    model = make_chat_model(route=route)
    instruction = (
        "다음 질문을 처리할 모델 등급을 하나만 고르라. "
        f"선택지: {', '.join(ROUTES)}. 등급 이름만 출력하라.\n[질문] {prompt}"
    )
    raw = str(model.invoke(instruction).content).strip().lower()
    picked = next((r for r in ROUTES if r in raw), "balanced")
    return Decision(picked, 0.8, f"LLM 판정: {raw[:40]}", "llm")


def hybrid_classify(prompt: str, threshold: float = 0.6) -> Decision:
    # 규칙이 확신할 때는 규칙으로 끝내고, 애매할 때만 LLM을 부른다.
    decision = rule_classify(prompt)
    if decision.confidence >= threshold:
        decision.strategy = "hybrid(rule)"
        return decision
    llm = llm_classify(prompt)
    llm.strategy = "hybrid(llm)"
    llm.signals = decision.signals
    return llm


STRATEGIES = {
    "rule": rule_classify,
    "llm": llm_classify,
    "hybrid": hybrid_classify,
    "all_frontier": lambda prompt: Decision("frontier", 1.0, "기준선", "baseline"),
}


def classify(prompt: str, strategy: str = "hybrid") -> Decision:
    if strategy not in STRATEGIES:
        raise KeyError(f"알 수 없는 전략: {strategy} (사용 가능: {sorted(STRATEGIES)})")
    return STRATEGIES[strategy](prompt)
