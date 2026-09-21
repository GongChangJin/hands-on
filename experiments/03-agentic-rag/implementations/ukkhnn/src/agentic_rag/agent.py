"""Bounded LangGraph workflow for retrieval, grading, retry, calculation, and answer."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .calculator import evaluate_arithmetic, format_number
from .contracts import validate_contract
from .observability import safe_attributes, tracer
from .pricing import estimate_cost
from .prompts import (
    ANSWER_PROMPT,
    FORMULA_PROMPT,
    GRADE_PROMPT,
    PLAN_PROMPT,
    PROMPT_VERSION,
    REWRITE_PROMPT,
)
from .types import Chunk, Gateway, Retriever


PlanAction = Literal["search", "calculate", "search_then_calculate", "direct"]


class GraphState(TypedDict, total=False):
    task: dict[str, Any]
    question: str
    plan_action: PlanAction
    query: str
    expression: str
    retrieved_chunks: list[Chunk]
    relevant_chunks: list[Chunk]
    calculation: str
    tool_traces: list[dict[str, Any]]
    retry_count: int
    step_count: int
    route: str
    output: str
    status: str
    evidence: list[dict[str, str]]
    limitations: list[str]


@dataclass(frozen=True)
class AgentConfig:
    top_k: int = 4
    score_threshold: float = 0.45
    max_retries: int = 1
    max_graph_steps: int = 12


def _chunk_context(chunks: list[Chunk]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "location": chunk.location,
            "score": round(chunk.score, 4) if chunk.score is not None else None,
            "content": chunk.text,
        }
        for chunk in chunks
    ]


def _expression_is_grounded(expression: str, question: str) -> bool:
    """Return whether every numeric literal in an expression appears in the question."""

    expression_numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?", expression)
    question_numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?", question)
    remaining = list(question_numbers)
    for number in expression_numbers:
        if number not in remaining:
            return False
        remaining.remove(number)
    return bool(expression_numbers)


class AgenticRAG:
    def __init__(self, gateway: Gateway, retriever: Retriever, config: AgentConfig | None = None) -> None:
        self.gateway = gateway
        self.retriever = retriever
        self.config = config or AgentConfig()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(GraphState)
        builder.add_node("plan", self._plan)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("grade", self._grade)
        builder.add_node("rewrite", self._rewrite)
        builder.add_node("formulate", self._formulate)
        builder.add_node("calculate", self._calculate)
        builder.add_node("answer", self._answer)
        builder.add_node("no_answer", self._no_answer)
        builder.add_edge(START, "plan")
        builder.add_conditional_edges(
            "plan",
            lambda state: state["route"],
            {
                "retrieve": "retrieve",
                "calculate": "calculate",
                "answer": "answer",
            },
        )
        builder.add_edge("retrieve", "grade")
        builder.add_conditional_edges(
            "grade",
            lambda state: state["route"],
            {
                "rewrite": "rewrite",
                "formulate": "formulate",
                "answer": "answer",
                "no_answer": "no_answer",
            },
        )
        builder.add_edge("rewrite", "retrieve")
        builder.add_edge("formulate", "calculate")
        builder.add_edge("calculate", "answer")
        builder.add_edge("answer", END)
        builder.add_edge("no_answer", END)
        return builder.compile()

    @staticmethod
    def _next_step(state: GraphState) -> int:
        return int(state.get("step_count", 0)) + 1

    @staticmethod
    def _tool_allowed(state: GraphState, tool_name: str) -> tuple[bool, str | None]:
        constraints = state["task"]["constraints"]
        if tool_name not in constraints["allowed_tools"]:
            return False, f"TaskRequest가 {tool_name} 호출을 허용하지 않습니다."
        if len(state.get("tool_traces", [])) >= int(constraints.get("max_tool_calls", 0)):
            return False, "TaskRequest의 max_tool_calls에 도달했습니다."
        return True, None

    async def _plan(self, state: GraphState) -> dict[str, Any]:
        plan = await self.gateway.complete_json(
            operation="plan",
            system=PLAN_PROMPT,
            payload={
                "question": state["question"],
                "allowed_tools": state["task"]["constraints"]["allowed_tools"],
            },
        )
        action = str(plan.get("action", "search"))
        if action not in {"search", "calculate", "search_then_calculate", "direct"}:
            action = "search"
        expression = str(plan.get("expression") or "")
        allowed_tools = set(state["task"]["constraints"]["allowed_tools"])
        if (
            action == "calculate"
            and "retriever" in allowed_tools
            and not _expression_is_grounded(expression, state["question"])
        ):
            action = "search_then_calculate"
            expression = ""
        route = {
            "search": "retrieve",
            "search_then_calculate": "retrieve",
            "calculate": "calculate",
            "direct": "answer",
        }[action]
        return {
            "plan_action": action,
            "query": str(plan.get("search_query") or state["question"]),
            "expression": expression,
            "route": route,
            "step_count": self._next_step(state),
        }

    async def _retrieve(self, state: GraphState) -> dict[str, Any]:
        allowed, reason = self._tool_allowed(state, "retriever")
        if not allowed:
            return {
                "retrieved_chunks": [],
                "relevant_chunks": [],
                "route": "no_answer",
                "limitations": [*state.get("limitations", []), str(reason)],
                "step_count": self._next_step(state),
            }
        started = time.perf_counter()
        error: str | None = None
        chunks: list[Chunk] = []
        with tracer().start_as_current_span("retriever.search") as span:
            span.set_attributes(
                safe_attributes(
                    **{
                        "openinference.span.kind": "RETRIEVER",
                        "task.id": state["task"]["task_id"],
                        "retrieval.query": state["query"],
                        "retrieval.top_k": self.config.top_k,
                    }
                )
            )
            try:
                chunks = self.retriever.search(
                    state["query"],
                    limit=self.config.top_k,
                    score_threshold=self.config.score_threshold,
                )
                span.set_attribute("retrieval.document_ids", [chunk.document_id for chunk in chunks])
                span.set_attribute("retrieval.chunk_ids", [chunk.chunk_id for chunk in chunks])
                span.set_attribute(
                    "retrieval.scores",
                    [round(chunk.score or 0.0, 5) for chunk in chunks],
                )
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                span.record_exception(exc)
        trace = {
            "task_id": state["task"]["task_id"],
            "tool_name": "retriever",
            "input_summary": state["query"][:240],
            "result_summary": (
                f"{len(chunks)} chunks: {', '.join(chunk.chunk_id for chunk in chunks)}"
                if not error
                else "검색 실패"
            ),
            "duration_ms": (time.perf_counter() - started) * 1000,
            "error": error,
            "metadata": {
                "query": state["query"],
                "attempt": int(state.get("retry_count", 0)) + 1,
                "chunk_ids": [chunk.chunk_id for chunk in chunks],
                "scores": [chunk.score for chunk in chunks],
            },
        }
        validate_contract("tool-trace", trace)
        limitations = list(state.get("limitations", []))
        if error:
            limitations.append(error)
        return {
            "retrieved_chunks": chunks,
            "tool_traces": [*state.get("tool_traces", []), trace],
            "limitations": limitations,
            "step_count": self._next_step(state),
        }

    async def _grade(self, state: GraphState) -> dict[str, Any]:
        chunks = state.get("retrieved_chunks", [])
        if chunks:
            grade = await self.gateway.complete_json(
                operation="grade",
                system=GRADE_PROMPT,
                payload={"question": state["question"], "chunks": _chunk_context(chunks)},
            )
        else:
            grade = {
                "relevant": False,
                "relevant_chunk_ids": [],
                "improved_query": state["question"],
            }
        valid_ids = {chunk.chunk_id for chunk in chunks}
        selected_ids = {
            str(chunk_id)
            for chunk_id in grade.get("relevant_chunk_ids", [])
            if str(chunk_id) in valid_ids
        }
        relevant = bool(grade.get("relevant")) and bool(selected_ids)
        selected = [chunk for chunk in chunks if chunk.chunk_id in selected_ids] if relevant else []
        if relevant:
            route = "formulate" if state["plan_action"] == "search_then_calculate" else "answer"
        elif int(state.get("retry_count", 0)) < self.config.max_retries:
            route = "rewrite"
        else:
            route = "no_answer"
        return {
            "relevant_chunks": selected,
            "query": str(grade.get("improved_query") or state["query"]),
            "route": route,
            "step_count": self._next_step(state),
        }

    async def _rewrite(self, state: GraphState) -> dict[str, Any]:
        rewritten = await self.gateway.complete_json(
            operation="rewrite",
            system=REWRITE_PROMPT,
            payload={"question": state["question"], "failed_query": state["query"]},
        )
        return {
            "query": str(rewritten.get("query") or state["question"]),
            "retry_count": int(state.get("retry_count", 0)) + 1,
            "route": "retrieve",
            "step_count": self._next_step(state),
        }

    async def _formulate(self, state: GraphState) -> dict[str, Any]:
        formula = await self.gateway.complete_json(
            operation="formulate",
            system=FORMULA_PROMPT,
            payload={
                "question": state["question"],
                "chunks": _chunk_context(state.get("relevant_chunks", [])),
            },
        )
        return {
            "expression": str(formula.get("expression") or ""),
            "step_count": self._next_step(state),
        }

    async def _calculate(self, state: GraphState) -> dict[str, Any]:
        allowed, reason = self._tool_allowed(state, "calculator")
        expression = state.get("expression", "")
        if not allowed:
            return {
                "calculation": "",
                "limitations": [*state.get("limitations", []), str(reason)],
                "step_count": self._next_step(state),
            }
        started = time.perf_counter()
        error: str | None = None
        result = ""
        with tracer().start_as_current_span("tool.calculator") as span:
            span.set_attributes(
                safe_attributes(
                    **{
                        "openinference.span.kind": "TOOL",
                        "task.id": state["task"]["task_id"],
                        "tool.name": "calculator",
                        "calculator.expression": expression,
                    }
                )
            )
            try:
                result = format_number(evaluate_arithmetic(expression))
                span.set_attribute("calculator.result", result)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                span.record_exception(exc)
        trace = {
            "task_id": state["task"]["task_id"],
            "tool_name": "calculator",
            "input_summary": expression[:120],
            "result_summary": result if not error else "계 실패",
            "duration_ms": (time.perf_counter() - started) * 1000,
            "error": error,
            "metadata": {"expression": expression, "result": result},
        }
        validate_contract("tool-trace", trace)
        limitations = list(state.get("limitations", []))
        if error:
            limitations.append(error)
        return {
            "calculation": result,
            "tool_traces": [*state.get("tool_traces", []), trace],
            "limitations": limitations,
            "step_count": self._next_step(state),
        }

    async def _answer(self, state: GraphState) -> dict[str, Any]:
        chunks = state.get("relevant_chunks", [])
        answer = await self.gateway.complete_json(
            operation="answer",
            system=ANSWER_PROMPT,
            payload={
                "question": state["question"],
                "evidence_chunks": _chunk_context(chunks),
                "calculation": {
                    "expression": state.get("expression", ""),
                    "result": state.get("calculation", ""),
                },
            },
        )
        valid_chunks = {chunk.chunk_id: chunk for chunk in chunks}
        cited_ids = [
            str(chunk_id)
            for chunk_id in answer.get("citation_chunk_ids", [])
            if str(chunk_id) in valid_chunks
        ]
        evidence = [
            {
                "source": valid_chunks[chunk_id].document_id,
                "location": valid_chunks[chunk_id].location,
                "claim": f"{valid_chunks[chunk_id].title}의 검색 근거",
            }
            for chunk_id in dict.fromkeys(cited_ids)
        ]
        if state.get("calculation"):
            evidence.append(
                {
                    "source": "calculator",
                    "location": f"expression:{state.get('expression', '')}",
                    "claim": f"계산 결과 {state['calculation']}",
                }
            )
        limitations = list(state.get("limitations", []))
        status = "success"
        if chunks and not cited_ids:
            status = "partial"
            limitations.append("답변 모델이 검색 chunk ID를 인용하지 않았습니다.")
        if state.get("expression") and not state.get("calculation"):
            status = "failed"
            limitations.append("결정적 계산 결과를 만들지 못했습니다.")
        return {
            "output": str(answer.get("answer") or "답변을 생성하지 못했습니다."),
            "evidence": evidence,
            "status": status,
            "limitations": limitations,
            "step_count": self._next_step(state),
        }

    async def _no_answer(self, state: GraphState) -> dict[str, Any]:
        return {
            "output": "공통 문서에서 질문에 대한 근거를 확인할 수 없습니다.",
            "evidence": [],
            "status": "partial",
            "limitations": [*state.get("limitations", []), "검색 및 제한된 재검색에서 직접 근거가 없었습니다."],
            "step_count": self._next_step(state),
        }

    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        validate_contract("task-request", task)
        if task["task_type"] != "rag":
            raise ValueError("Agentic RAG는 task_type=rag 요청만 처리합니다.")
        question = task["input"] if isinstance(task["input"], str) else json.dumps(task["input"], ensure_ascii=False)
        self.gateway.reset_usage()
        started = time.perf_counter()
        initial: GraphState = {
            "task": task,
            "question": question,
            "query": question,
            "expression": "",
            "retrieved_chunks": [],
            "relevant_chunks": [],
            "calculation": "",
            "tool_traces": [],
            "retry_count": 0,
            "step_count": 0,
            "evidence": [],
            "limitations": [],
        }
        final: GraphState = initial
        workflow_tracer = tracer()
        try:
            with workflow_tracer.start_as_current_span("03-agentic-rag.workflow") as span:
                span.set_attributes(
                    safe_attributes(
                        **{
                            "openinference.span.kind": "AGENT",
                            "task.id": task["task_id"],
                            "agent.provider": self.gateway.provider,
                            "agent.model": self.gateway.model_name,
                            "agent.prompt_version": PROMPT_VERSION,
                        }
                    )
                )
                final = await self.graph.ainvoke(
                    initial,
                    config={
                        "recursion_limit": min(
                            self.config.max_graph_steps,
                            int(task["constraints"].get("max_steps", self.config.max_graph_steps)),
                        )
                        + 3
                    },
                )
                if int(final.get("step_count", 0)) > int(task["constraints"]["max_steps"]):
                    final["status"] = "failed"
                    final["limitations"] = [
                        *final.get("limitations", []),
                        "TaskRequest의 max_steps를 초과했습니다.",
                    ]
                span.set_attribute("agent.status", final.get("status", "failed"))
                span.set_attribute("agent.tool_calls", len(final.get("tool_traces", [])))
        except Exception as exc:
            final = {
                **initial,
                "status": "failed",
                "output": "Agentic RAG 실행 중 오류가 발생했습니다.",
                "limitations": [f"{type(exc).__name__}: {exc}"],
            }
        latency_ms = (time.perf_counter() - started) * 1000
        usage = self.gateway.usage.as_dict()
        cost = estimate_cost(
            self.gateway.provider,
            self.gateway.model_name,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        )
        tool_traces = final.get("tool_traces", [])
        safety_violations: list[str] = []
        output = str(final.get("output", ""))
        if "UPSTAGE_API_KEY=" in output or "DEEPSEEK_API_KEY=" in output or "sk-" in output:
            safety_violations.append("비밀로 보이는 문자열이 답변에 포함됨")
        result = {
            "task_id": task["task_id"],
            "status": final.get("status", "failed"),
            "output": output,
            "evidence": final.get("evidence", []),
            "actions": [trace["tool_name"] for trace in tool_traces],
            "limitations": final.get("limitations", []),
            "metadata": {
                "implementation_id": "ukkhnn-langgraph-qdrant-v1",
                "provider": self.gateway.provider,
                "model": self.gateway.model_name,
                "prompt_version": PROMPT_VERSION,
                "latency_ms": latency_ms,
                "usage": usage,
                "estimated_cost_usd": cost,
                "tool_traces": tool_traces,
                "retrieval_attempts": sum(1 for item in tool_traces if item["tool_name"] == "retriever"),
                "graph_steps": final.get("step_count", 0),
                "safety_violations": safety_violations,
            },
        }
        validate_contract("agent-result", result)
        return result
