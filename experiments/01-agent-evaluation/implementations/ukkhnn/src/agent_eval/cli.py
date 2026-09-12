"""Run one real tool-calling agent and export its trace to Phoenix."""

from __future__ import annotations

import argparse
import asyncio
import os

from agents import Runner, trace
from openai import APIError

from .agent import build_agent
from .observability import configure_phoenix
from .providers import PROVIDERS, build_model, provider_error_message, provider_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a traced tool-calling agent.")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="6과 7을 곱한 값과 01-agent-evaluation 프로젝트 상태를 알려줘.",
    )
    parser.add_argument(
        "--provider",
        choices=tuple(PROVIDERS),
        default=os.getenv("AGENT_PROVIDER", "upstage"),
    )
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL"))
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    parser.add_argument("--project", default="01-agent-evaluation")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    spec = provider_spec(args.provider)
    model_name = args.model or spec.default_model
    try:
        model = build_model(args.provider, model_name)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    tracer_provider = configure_phoenix(
        endpoint=args.phoenix_endpoint,
        project_name=args.project,
    )
    try:
        with trace(
            workflow_name="01-agent-evaluation",
            metadata={"provider": args.provider, "model": model_name},
        ):
            try:
                result = await Runner.run(build_agent(model), args.prompt)
            except APIError as exc:
                raise SystemExit(provider_error_message(args.provider, exc)) from None
        print(result.final_output)
    finally:
        tracer_provider.shutdown()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
