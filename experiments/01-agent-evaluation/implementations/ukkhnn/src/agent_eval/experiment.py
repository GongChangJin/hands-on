"""Run Agent architectures over a Phoenix dataset and export evaluation reports."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import Runner, trace
from agents.items import HandoffOutputItem, ToolCallItem, ToolCallOutputItem
from openai import APIError, AsyncOpenAI
from phoenix.client import AsyncClient
from phoenix.client.experiments import create_evaluator

from .agent import ARCHITECTURES, PROMPT_VERSION, Architecture, build_agent
from .contracts import validate_contract
from .dataset import DATASET_NAME
from .observability import configure_phoenix
from .providers import (
    PROVIDERS,
    build_client,
    build_model,
    estimate_cost_usd,
    provider_error_message,
    provider_spec,
)
from .report import build_records, default_report_root, export_report, summarize_records


def _answer_contains_required_text(
    output: dict[str, Any] | None,
    expected: dict[str, Any],
) -> bool:
    if output is None or output.get("error"):
        return False
    answer = str(output["answer"]).casefold()
    return all(str(text).casefold() in answer for text in expected["required_texts"])


def _tool_accuracy(output: dict[str, Any] | None, expected: dict[str, Any]) -> float:
    if output is None:
        return 0.0
    actual = Counter(output.get("tools", []))
    required = Counter(expected["required_tools"])
    matches = sum((actual & required).values())
    denominator = max(sum(actual.values()), sum(required.values()))
    return matches / denominator if denominator else 1.0


def _required_tools_used(output: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
    """Backward-compatible helper retained for the first learning checkpoint."""

    if output is None:
        return False
    return set(expected["required_tools"]).issubset(output.get("tools", []))


def _safe_tool_use(output: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
    if output is None or output.get("error"):
        return False
    return set(output.get("tools", [])).issubset(expected["required_tools"])


def _tool_execution_success(output: dict[str, Any] | None) -> bool:
    if output is None or output.get("error"):
        return False
    return all(trace_item.get("error") is None for trace_item in output.get("tool_traces", []))


def _handoff_route_correct(output: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
    if output is None or output.get("error"):
        return False
    return output.get("agent") == expected["expected_agent"]


answer_contains_required_text = create_evaluator(
    kind="CODE",
    name="answer-contains-required-text",
)(_answer_contains_required_text)

tool_accuracy = create_evaluator(kind="CODE", name="tool-accuracy")(_tool_accuracy)

safe_tool_use = create_evaluator(kind="CODE", name="safe-tool-use")(_safe_tool_use)

tool_execution_success = create_evaluator(
    kind="CODE",
    name="tool-execution-success",
)(_tool_execution_success)

handoff_route_correct = create_evaluator(
    kind="CODE",
    name="handoff-route-correct",
)(_handoff_route_correct)


def build_llm_judge(api_client: AsyncOpenAI, model_name: str) -> Any:
    """Create an optional diagnostic evaluator that never controls task_success."""

    @create_evaluator(kind="LLM", name="semantic-quality-llm")
    async def semantic_quality_llm(
        input: dict[str, Any],
        output: dict[str, Any] | None,
        expected: dict[str, Any],
    ) -> tuple[float, str, str]:
        if output is None or output.get("error"):
            return (0.0, "FAIL", "Agent 실행 결과가 없습니다.")
        response = await api_client.chat.completions.create(
            model=model_name,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 Agent 답변 품질 평가자입니다. 답변이 질문에 직접 답하고 기대 사실과 "
                        "모순되지 않으면 PASS, 아니면 FAIL로 판정하세요. 첫 단어는 반드시 PASS 또는 "
                        "FAIL이고 이어서 한 문장 이유를 쓰세요."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": input["prompt"],
                            "expected_facts": expected["required_texts"],
                            "answer": output["answer"],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        explanation = (response.choices[0].message.content or "").strip()
        passed = explanation.upper().startswith("PASS")
        return (float(passed), "PASS" if passed else "FAIL", explanation)

    return semantic_quality_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Phoenix Agent experiment.")
    parser.add_argument(
        "--provider",
        choices=tuple(PROVIDERS),
        default=os.getenv("AGENT_PROVIDER", "upstage"),
    )
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL"))
    parser.add_argument("--architecture", choices=ARCHITECTURES, default="single")
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="별도 LLM 진단 평가를 추가합니다. 결정적 성공 판정에는 사용하지 않습니다.",
    )
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument(
        "--phoenix-url",
        default=os.getenv("PHOENIX_BASE_URL", "http://localhost:6006"),
    )
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    return parser.parse_args()


def _item_value(raw_item: Any, name: str) -> Any:
    if isinstance(raw_item, dict):
        return raw_item.get(name)
    return getattr(raw_item, name, None)


def _summarize_items(result: Any, task_id: str) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    tool_calls: dict[str, ToolCallItem] = {}
    tool_outputs: dict[str, ToolCallOutputItem] = {}
    handoffs: list[str] = []
    tools: list[str] = []
    for item in result.new_items:
        if isinstance(item, ToolCallItem) and item.tool_name:
            tools.append(item.tool_name)
            if item.call_id:
                tool_calls[item.call_id] = item
        elif isinstance(item, ToolCallOutputItem) and item.call_id:
            tool_outputs[item.call_id] = item
        elif isinstance(item, HandoffOutputItem):
            handoffs.append(item.target_agent.name)

    traces: list[dict[str, Any]] = []
    for call_id, call in tool_calls.items():
        output_item = tool_outputs.get(call_id)
        result_summary = str(output_item.output if output_item else "")
        tool_error = (
            result_summary if "An error occurred while running the tool" in result_summary else None
        )
        trace_record = {
            "task_id": task_id,
            "tool_name": call.tool_name or "unknown",
            "input_summary": str(_item_value(call.raw_item, "arguments") or ""),
            "result_summary": result_summary,
            "duration_ms": 0.0,
            "error": tool_error,
            "metadata": {"timing_source": "phoenix_span", "call_id": call_id},
        }
        validate_contract("tool-trace", trace_record)
        traces.append(trace_record)
    return tools, handoffs, traces


def _failure_output(task_id: str, architecture: str, message: str) -> dict[str, Any]:
    agent_result = {
        "task_id": task_id,
        "status": "failed",
        "output": None,
        "evidence": [],
        "actions": [],
        "limitations": [message],
        "metadata": {"architecture": architecture},
    }
    validate_contract("agent-result", agent_result)
    return {
        "task_id": task_id,
        "answer": "",
        "tools": [],
        "handoffs": [],
        "agent": None,
        "usage": {},
        "estimated_cost_usd": None,
        "agent_result": agent_result,
        "tool_traces": [],
        "error": message,
    }


def _report_directory(args: argparse.Namespace, model_name: str) -> Path:
    if args.report_dir:
        return args.report_dir
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return default_report_root() / f"{timestamp}-{args.provider}-{model_name}-{args.architecture}"


async def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.repetitions < 1:
        raise SystemExit("--repetitions는 1 이상이어야 합니다.")
    architecture: Architecture = args.architecture
    spec = provider_spec(args.provider)
    model_name = args.model or spec.default_model
    try:
        api_client = build_client(args.provider)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        if spec.check_models_before_experiment:
            print(f"🔌 {args.provider} API 연결 확인 중...")
            await api_client.models.list()
            print(f"✅ {args.provider} API 연결 확인 완료.")
    except APIError as exc:
        await api_client.close()
        raise SystemExit(provider_error_message(args.provider, exc)) from None

    model = build_model(args.provider, model_name, client=api_client)
    client = AsyncClient(base_url=args.phoenix_url)
    dataset = await client.datasets.get_dataset(dataset=args.dataset)
    agent = build_agent(model, architecture)
    tracer_provider = configure_phoenix(
        endpoint=args.phoenix_endpoint,
        project_name="01-agent-evaluation",
    )

    async def run_agent(
        input: dict[str, Any], metadata: dict[str, Any], expected: dict[str, Any]
    ) -> dict[str, Any]:
        task_id = str(metadata["case_id"])
        with trace(
            workflow_name="01-agent-evaluation-experiment",
            metadata={
                "provider": args.provider,
                "model": model_name,
                "architecture": architecture,
                "task_id": task_id,
            },
        ):
            try:
                result = await Runner.run(agent, input["prompt"], max_turns=8)
            except APIError as exc:
                return _failure_output(
                    task_id, architecture, provider_error_message(args.provider, exc)
                )
            except Exception as exc:
                return _failure_output(task_id, architecture, f"{type(exc).__name__}: {exc}")

        tools, handoffs, tool_traces = _summarize_items(result, task_id)
        usage = result.context_wrapper.usage
        cached_tokens = int(getattr(usage.input_tokens_details, "cached_tokens", 0) or 0)
        usage_payload = {
            "requests": usage.requests,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "cached_input_tokens": cached_tokens,
        }
        cost = estimate_cost_usd(
            args.provider,
            model_name,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cached_input_tokens=cached_tokens,
            at=datetime.now(timezone.utc),
        )
        answer = str(result.final_output)
        evidence = [
            {
                "source": trace_item["tool_name"],
                "location": trace_item["metadata"]["call_id"],
                "claim": trace_item["result_summary"],
            }
            for trace_item in tool_traces
        ]
        agent_result = {
            "task_id": task_id,
            "status": "success",
            "output": answer,
            "evidence": evidence,
            "actions": [*handoffs, *tools],
            "limitations": [],
            "metadata": {"architecture": architecture, "agent": result.last_agent.name},
        }
        validate_contract("agent-result", agent_result)
        return {
            "task_id": task_id,
            "answer": answer,
            "tools": tools,
            "handoffs": handoffs,
            "agent": result.last_agent.name,
            "usage": usage_payload,
            "estimated_cost_usd": cost,
            "agent_result": agent_result,
            "tool_traces": tool_traces,
        }

    evaluators: list[Any] = [
        answer_contains_required_text,
        tool_accuracy,
        safe_tool_use,
        tool_execution_success,
    ]
    if architecture == "handoff":
        evaluators.append(handoff_route_correct)
    if args.llm_judge:
        evaluators.append(build_llm_judge(api_client, model_name))

    try:
        ran_experiment = await client.experiments.run_experiment(
            dataset=dataset,
            task=run_agent,
            evaluators=evaluators,
            experiment_name=f"{args.provider}-{model_name}-{architecture}-{PROMPT_VERSION}",
            experiment_description=(
                "Compare answer correctness, exact tool use, safety, and Agent architecture."
            ),
            experiment_metadata={
                "provider": args.provider,
                "model": model_name,
                "architecture": architecture,
                "prompt_version": PROMPT_VERSION,
                "llm_judge": args.llm_judge,
            },
            concurrency=spec.experiment_concurrency,
            repetitions=args.repetitions,
            retries=0,
        )
        records = build_records(
            ran_experiment,
            dataset,
            provider=args.provider,
            model_name=model_name,
            architecture=architecture,
        )
        summary = summarize_records(
            records,
            experiment_id=str(ran_experiment["experiment_id"]),
            provider=args.provider,
            model_name=model_name,
            architecture=architecture,
        )
        report_path = export_report(records, summary, _report_directory(args, model_name))
        print(f"📄 Report: {report_path}")
        return summary
    finally:
        tracer_provider.shutdown()
        await api_client.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
