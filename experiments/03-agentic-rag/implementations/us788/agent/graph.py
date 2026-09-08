# LangGraph 파이프라인
#   route -> retrieve -> grade_docs -(부족하면 재검색)-> calculate -> answer
# 각 노드는 tool_calls 와 telemetry 를 state 에 누적해 AgentResult 로 변환된다.
from __future__ import annotations

import re
import time
from typing import Annotated, Any, TypedDict

from .prompts import ANSWER, INJECTION_MARKERS, RELEVANCE, SYSTEM
from .tools import Doc, calculate, retrieve

MAX_RETRIEVALS = 2


class State(TypedDict, total=False):
    question: str
    docs: list[Doc]
    calculations: list[str]
    attempts: int
    answer: str
    tool_calls: list[dict[str, Any]]
    input_tokens: int
    output_tokens: int
    forbidden_actions: int
    route: str


def _record(state: State, name: str, args: dict, t0: float, ok: bool = True, error: str | None = None) -> None:
    state.setdefault("tool_calls", []).append(
        {"name": name, "args": args, "ok": ok, "latency_ms": (time.perf_counter() - t0) * 1000, "error": error}
    )


def node_retrieve(state: State) -> State:
    t0 = time.perf_counter()
    query = state["question"]
    if state.get("attempts", 0) > 0:
        # 재검색: 이미 본 문서를 제외하기 위해 질의를 넓힌다.
        query = f"{query} {' '.join(state['question'].split()[:3])}"
    docs = retrieve(query, k=4)
    _record(state, "retriever", {"query": query, "k": 4}, t0)
    state["docs"] = docs
    state["attempts"] = state.get("attempts", 0) + 1
    state["forbidden_actions"] = state.get("forbidden_actions", 0) + sum(
        1 for d in docs for m in INJECTION_MARKERS if m in d.text.lower()
    )
    return state


def node_grade_docs(state: State) -> State:
    # TODO: LLM 관련성 판정으로 교체. 지금은 토큰 겹침만 확인하는 결정적 판정.
    q = set(re.findall(r"[0-9A-Za-z가-힣]+", state["question"].lower()))
    state["docs"] = [d for d in state.get("docs", []) if q & set(re.findall(r"[0-9A-Za-z가-힣]+", d.text.lower()))]
    return state


def route_after_grade(state: State) -> str:
    if state.get("docs"):
        return "calculate"
    if state.get("attempts", 0) < MAX_RETRIEVALS:
        return "retrieve"
    return "answer"


def node_calculate(state: State) -> State:
    # 질문에서 산술식을 뽑아 결정적으로 계산한다.
    state.setdefault("calculations", [])
    for expr in re.findall(r"[-+]?[\d,]+(?:\.\d+)?(?:\s*[-+*/]\s*[-+]?[\d,]+(?:\.\d+)?)+", state["question"]):
        t0 = time.perf_counter()
        try:
            value = calculate(expr)
            _record(state, "calculator", {"expression": expr}, t0)
            state["calculations"].append(f"{expr} = {value}")
        except Exception as e:
            _record(state, "calculator", {"expression": expr}, t0, ok=False, error=str(e))
    return state


def node_answer(state: State) -> State:
    from evalkit.models import make_chat_model

    docs = state.get("docs", [])
    rendered = "\n".join(f"<document id=\"{d.doc_id}\" page=\"{d.page}\">{d.text}</document>" for d in docs)
    calcs = "\n".join(state.get("calculations", [])) or "없음"
    route = state.get("route", "balanced")
    model = make_chat_model(route=route)
    t0 = time.perf_counter()
    reply = model.invoke(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": ANSWER.format(question=state["question"], documents=rendered or "없음", calculations=calcs)},
        ]
    )
    _record(state, "llm", {"route": route}, t0)
    usage = getattr(reply, "usage_metadata", None) or {}
    state["input_tokens"] = state.get("input_tokens", 0) + int(usage.get("input_tokens", 0))
    state["output_tokens"] = state.get("output_tokens", 0) + int(usage.get("output_tokens", 0))
    state["answer"] = str(reply.content)
    return state


def build_graph():
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(State)
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade_docs", node_grade_docs)
    g.add_node("calculate", node_calculate)
    g.add_node("answer", node_answer)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade_docs")
    g.add_conditional_edges("grade_docs", route_after_grade, {"retrieve": "retrieve", "calculate": "calculate", "answer": "answer"})
    g.add_edge("calculate", "answer")
    g.add_edge("answer", END)
    return g.compile()


def answer_question(question: str, route: str = "balanced") -> State:
    return build_graph().invoke({"question": question, "route": route, "attempts": 0})
