"""Patch providers for deterministic replay and optional live evaluation."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .io import implementation_dir
from .models import CodingIssue, PatchProposal, ProviderResult


class ProviderFailure(RuntimeError):
    pass


class PatchProvider(Protocol):
    def propose(
        self,
        issue: CodingIssue,
        files: dict[str, str],
        feedback: list[str],
        attempt: int,
    ) -> ProviderResult: ...


@dataclass
class ReplayPatchProvider:
    """Load a frozen reference patch without network or arbitrary command access."""

    replay_root: Path | None = None
    model: str = "reference-replay-v1"

    def propose(
        self,
        issue: CodingIssue,
        files: dict[str, str],
        feedback: list[str],
        attempt: int,
    ) -> ProviderResult:
        del files, feedback, attempt
        started = time.perf_counter()
        root = self.replay_root or implementation_dir() / "replay"
        task_root = root / issue.task_id
        edits = []
        for relative in issue.allowed_paths:
            source = task_root / relative
            if not source.is_file():
                raise ProviderFailure(f"missing replay file: {issue.task_id}/{relative}")
            edits.append({"path": relative, "content": source.read_text(encoding="utf-8")})
        proposal = PatchProposal.model_validate(
            {
                "summary": f"Apply the frozen reference patch for {issue.task_id}",
                "plan": [
                    "Replace the issue implementation within its allowlist.",
                    "Add a focused regression test for the reported behavior.",
                ],
                "edits": edits,
                "risks": ["This replay validates the harness, not live model generation quality."],
            }
        )
        return ProviderResult(
            proposal=proposal,
            model=self.model,
            latency_ms=(time.perf_counter() - started) * 1000,
            input_tokens=0,
            cached_input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            request_id=f"replay:{issue.task_id}",
        )


def estimate_solar_pro4_cost(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
) -> float:
    """Use the same 2026-09-24 pricing snapshot as Hands-on 02 and 03."""

    uncached = max(0, input_tokens - cached_input_tokens)
    return (uncached * 0.30 + cached_input_tokens * 0.06 + output_tokens * 1.20) / 1_000_000


@dataclass
class SolarPatchProvider:
    model: str = "solar-pro4"
    base_url: str = "https://api.upstage.ai/v1"
    api_key_env: str = "UPSTAGE_API_KEY"
    timeout_seconds: float = 90.0

    def _api_key(self) -> str:
        value = os.getenv(self.api_key_env)
        if not value:
            raise ProviderFailure(f"{self.api_key_env} is not configured")
        return value

    def propose(
        self,
        issue: CodingIssue,
        files: dict[str, str],
        feedback: list[str],
        attempt: int,
    ) -> ProviderResult:
        output_shape = {
            "summary": "short change summary",
            "plan": ["ordered implementation and verification steps"],
            "edits": [
                {
                    "path": "one of allowed_paths",
                    "content": "complete replacement file content",
                }
            ],
            "risks": ["remaining risk, if any"],
        }
        prompt = {
            "issue": {
                "id": issue.task_id,
                "title": issue.title,
                "description": issue.description,
                "acceptance_criteria": issue.acceptance_criteria,
            },
            "attempt": attempt,
            "allowed_paths": issue.allowed_paths,
            "required_regression_test": issue.regression_test_path,
            "repository_files": files,
            "previous_feedback": feedback[-2:],
            "output_shape": output_shape,
        }
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a bounded Python coding agent. Return only one JSON object. "
                        "Make the smallest complete fix for the issue. Replace only allowed_paths and include "
                        "complete content for both the implementation file and the required regression test. "
                        "Do not use Git, network access, hidden tests, placeholders, markdown fences, or ellipses. "
                        "The regression test must fail on the original bug and pass after the fix."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": 3200,
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except (TimeoutError, urllib.error.URLError) as error:
            raise ProviderFailure(f"provider request failed: {type(error).__name__}: {error}") from error
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            content = json.loads(payload["choices"][0]["message"]["content"])
            proposal = PatchProposal.model_validate(content)
            usage = payload.get("usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0) or 0)
            cached_tokens = int(usage.get("prompt_tokens_details", {}).get("cached_tokens", 0) or 0)
            output_tokens = int(usage.get("completion_tokens", 0) or 0)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ProviderFailure(f"invalid provider response: {type(error).__name__}: {error}") from error
        return ProviderResult(
            proposal=proposal,
            model=str(payload.get("model", self.model)),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=output_tokens,
            cost_usd=estimate_solar_pro4_cost(input_tokens, cached_tokens, output_tokens),
            request_id=payload.get("id"),
        )
