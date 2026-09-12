"""Run the real Agent over a Phoenix dataset with two code evaluators."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from agents import Runner, trace
from agents.items import ToolCallItem
from openai import APIError
from phoenix.client import AsyncClient
from phoenix.client.experiments import create_evaluator

from .agent import build_agent
from .dataset import DATASET_NAME
from .observability import configure_phoenix
from .providers import (
    PROVIDERS,
    build_client,
    build_model,
    provider_error_message,
    provider_spec,
)


def _answer_contains_required_text(
    output: dict[str, Any] | None,
    expected: dict[str, Any],
) -> bool:
    if output is None:
        return False
    answer = str(output["answer"]).casefold()
    return all(str(text).casefold() in answer for text in expected["required_texts"])


def _required_tools_used(output: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
    if output is None:
        return False
    return set(expected["required_tools"]).issubset(output["tools"])


answer_contains_required_text = create_evaluator(
    kind="CODE",
    name="answer-contains-required-text",
)(_answer_contains_required_text)

required_tools_used = create_evaluator(
    kind="CODE",
    name="required-tools-used",
)(_required_tools_used)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Phoenix Agent experiment.")
    parser.add_argument(
        "--provider",
        choices=tuple(PROVIDERS),
        default=os.getenv("AGENT_PROVIDER", "upstage"),
    )
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL"))
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument(
        "--phoenix-url",
        default=os.getenv("PHOENIX_BASE_URL", "http://localhost:6006"),
    )
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
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
    agent = build_agent(model)
    tracer_provider = configure_phoenix(
        endpoint=args.phoenix_endpoint,
        project_name="01-agent-evaluation",
    )

    async def run_agent(input: dict[str, Any]) -> dict[str, Any]:
        with trace(
            workflow_name="01-agent-evaluation-experiment",
            metadata={"provider": args.provider, "model": model_name},
        ):
            try:
                result = await Runner.run(agent, input["prompt"])
            except APIError as exc:
                return {
                    "answer": "",
                    "tools": [],
                    "error": provider_error_message(args.provider, exc),
                }
        tools = [
            item.tool_name
            for item in result.new_items
            if isinstance(item, ToolCallItem) and item.tool_name is not None
        ]
        return {"answer": result.final_output, "tools": tools}

    try:
        await client.experiments.run_experiment(
            dataset=dataset,
            task=run_agent,
            evaluators=[answer_contains_required_text, required_tools_used],
            experiment_name=f"{args.provider}-{model_name}",
            experiment_description="Compare answer correctness and required tool use.",
            experiment_metadata={"provider": args.provider, "model": model_name},
            concurrency=spec.experiment_concurrency,
            retries=0,
        )
    finally:
        tracer_provider.shutdown()
        await api_client.close()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
