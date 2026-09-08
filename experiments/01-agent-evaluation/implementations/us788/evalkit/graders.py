# grader 3계층: 결정적 검사 / 규칙 기반 검사 / LLM grader.
# 실험 규칙상 LLM grader 단독으로 성공을 판정하지 않는다.
from __future__ import annotations

import json
import re
from typing import Callable

from .schema import AgentResult, Grade, Task

GraderFn = Callable[[Task, AgentResult], Grade]
GRADERS: dict[str, GraderFn] = {}


def register_grader(name: str) -> Callable[[GraderFn], GraderFn]:
    def deco(fn: GraderFn) -> GraderFn:
        GRADERS[name] = fn
        return fn

    return deco


def get_grader(name: str) -> GraderFn:
    if name not in GRADERS:
        raise KeyError(f"등록되지 않은 grader: {name} (사용 가능: {sorted(GRADERS)})")
    return GRADERS[name]


@register_grader("exact")
def exact_match(task: Task, result: AgentResult) -> Grade:
    expected = str(task.expected).strip()
    got = result.output.strip()
    ok = expected == got
    return Grade("exact", ok, 1.0 if ok else 0.0, "" if ok else f"기대 {expected!r} / 실제 {got!r}")


@register_grader("contains")
def contains(task: Task, result: AgentResult) -> Grade:
    needles = task.expected if isinstance(task.expected, list) else [task.expected]
    missing = [n for n in needles if str(n) not in result.output]
    ok = not missing
    return Grade("contains", ok, 1.0 if ok else 0.0, "" if ok else f"누락: {missing}")


@register_grader("regex")
def regex(task: Task, result: AgentResult) -> Grade:
    pattern = task.meta.get("pattern") or str(task.expected)
    ok = re.search(pattern, result.output, re.S) is not None
    return Grade("regex", ok, 1.0 if ok else 0.0, "" if ok else f"패턴 불일치: {pattern}")


@register_grader("json_valid")
def json_valid(task: Task, result: AgentResult) -> Grade:
    # 구조 준수율 측정용. 필요하면 jsonschema로 확장한다.
    try:
        json.loads(result.output)
    except json.JSONDecodeError as e:
        return Grade("json_valid", False, 0.0, f"JSON 아님: {e}")
    return Grade("json_valid", True, 1.0)


@register_grader("cited")
def cited(task: Task, result: AgentResult) -> Grade:
    # 근거 포함률. 03 Agentic RAG의 "문서 위치 포함 100%" 지표에 대응한다.
    pattern = task.meta.get("citation_pattern", r"\[[^\]]+:[^\]]+\]")
    hits = re.findall(pattern, result.output)
    ok = len(hits) > 0
    return Grade("cited", ok, float(len(hits)), "" if ok else "근거 표기 없음")


@register_grader("no_forbidden")
def no_forbidden(task: Task, result: AgentResult) -> Grade:
    ok = result.forbidden_actions == 0
    return Grade("no_forbidden", ok, float(result.forbidden_actions), "" if ok else "금지 행동 발생")


@register_grader("tool_used")
def tool_used(task: Task, result: AgentResult) -> Grade:
    # 기대 도구 호출 검증. meta.expected_tools 에 도구 이름 배열을 둔다.
    expected = task.meta.get("expected_tools", [])
    used = [c.name for c in result.tool_calls]
    missing = [t for t in expected if t not in used]
    ok = not missing
    return Grade("tool_used", ok, 1.0 if ok else 0.0, "" if ok else f"미사용 도구: {missing} (실제 {used})")


@register_grader("llm")
def llm_grader(task: Task, result: AgentResult) -> Grade:
    # 코드 검사로 판정이 어려운 항목 보조용.
    # 단독 판정 금지 — 항상 결정적 grader와 함께 쓰고 불일치는 리포트에 남긴다.
    from .models import make_chat_model

    rubric = task.meta.get("rubric", "질문에 정확하고 근거 있게 답했는가?")
    model = make_chat_model(route="small")
    prompt = (
        "다음 답변을 채점하라. PASS 또는 FAIL 로 시작하고 한 문장으로 이유를 붙여라.\n"
        f"[기준] {rubric}\n[질문] {task.prompt}\n[답변] {result.output}"
    )
    text = model.invoke(prompt).content
    verdict = str(text).strip()
    ok = verdict.upper().startswith("PASS")
    return Grade("llm", ok, 1.0 if ok else 0.0, verdict)
