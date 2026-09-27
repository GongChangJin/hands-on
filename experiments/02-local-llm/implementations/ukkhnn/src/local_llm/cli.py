"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .adapters import OllamaAdapter, OpenAICompatibleAdapter
from .report import comparison_markdown
from .runner import run_benchmark


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="local-llm")
    commands = root.add_subparsers(dest="command", required=True)

    evaluate = commands.add_parser("evaluate", help="고정 데이터셋으로 모델을 평가합니다.")
    evaluate.add_argument("--adapter", choices=("ollama", "api"), required=True)
    evaluate.add_argument("--model", required=True)
    evaluate.add_argument("--repetitions", type=int, default=1)
    evaluate.add_argument("--context-window", type=int, default=4096)
    evaluate.add_argument("--base-url")
    evaluate.add_argument("--api-key-env", default="UPSTAGE_API_KEY")
    evaluate.add_argument("--dataset", type=Path)
    evaluate.add_argument("--output", type=Path, required=True)

    inspect = commands.add_parser("inspect", help="Ollama 모델 설정을 확인합니다.")
    inspect.add_argument("--model", required=True)
    inspect.add_argument("--context-window", type=int, default=4096)
    inspect.add_argument("--base-url", default="http://127.0.0.1:11434")

    compare = commands.add_parser("compare", help="여러 summary.json을 비교합니다.")
    compare.add_argument("summaries", type=Path, nargs="+")
    compare.add_argument("--output", type=Path, required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "inspect":
        adapter = OllamaAdapter(model=args.model, base_url=args.base_url, context_window=args.context_window)
        adapter.warmup()
        print(json.dumps(adapter.inspect(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "compare":
        summaries = [json.loads(path.read_text(encoding="utf-8")) for path in args.summaries]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(comparison_markdown(summaries), encoding="utf-8")
        print(args.output)
        return 0
    if args.adapter == "ollama":
        adapter = OllamaAdapter(
            model=args.model,
            base_url=args.base_url or "http://127.0.0.1:11434",
            context_window=args.context_window,
        )
    else:
        adapter = OpenAICompatibleAdapter(
            model=args.model,
            base_url=args.base_url or "https://api.upstage.ai/v1",
            api_key_env=args.api_key_env,
        )
    summary, report_path = run_benchmark(
        adapter,
        repetitions=args.repetitions,
        output_dir=args.output,
        dataset_path=args.dataset,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
