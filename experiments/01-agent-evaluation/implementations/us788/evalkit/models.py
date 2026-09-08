# provider 비종속 모델 팩토리.
# 모델 ID를 코드에 고정하지 않고 models.yaml + 환경변수에서 읽는다 (02 실험 규칙).
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "models.yaml"


@lru_cache(maxsize=1)
def load_model_config(path: str | Path | None = None) -> dict[str, Any]:
    import yaml

    cfg_path = Path(path or os.getenv("MODELS_CONFIG", DEFAULT_CONFIG))
    if not cfg_path.exists():
        raise FileNotFoundError(f"모델 설정이 없습니다: {cfg_path} (models.example.yaml 복사)")
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve(route: str) -> dict[str, Any]:
    # 논리 라우트 이름 -> {provider, model, params, pricing}
    cfg = load_model_config()
    routes = cfg.get("routes", {})
    if route not in routes:
        raise KeyError(f"정의되지 않은 라우트: {route} (사용 가능: {sorted(routes)})")
    return routes[route]


def make_chat_model(route: str = "balanced", **overrides: Any):
    # langchain init_chat_model 은 provider 문자열만 바꾸면
    # anthropic / openai / google / ollama 등으로 그대로 옮겨간다.
    from langchain.chat_models import init_chat_model

    spec = resolve(route)
    params = {**spec.get("params", {}), **overrides}
    return init_chat_model(model=spec["model"], model_provider=spec["provider"], **params)


def price_of(route: str) -> tuple[float, float]:
    # (input 100만토큰당 USD, output 100만토큰당 USD)
    pricing = resolve(route).get("pricing", {})
    return float(pricing.get("input_per_mtok", 0.0)), float(pricing.get("output_per_mtok", 0.0))


def estimate_cost(route: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = price_of(route)
    return (input_tokens / 1_000_000) * pin + (output_tokens / 1_000_000) * pout
