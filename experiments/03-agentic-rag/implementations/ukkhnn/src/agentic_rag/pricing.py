"""Documented estimates for the two allowed providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone


@dataclass(frozen=True)
class Price:
    input_per_million: float
    cached_input_per_million: float
    output_per_million: float
    peak_multiplier: float = 1.0


PRICES = {
    ("upstage", "solar-pro4"): Price(0.30, 0.06, 1.20),
    ("deepseek", "deepseek-v4-flash"): Price(0.22, 0.007, 0.66, peak_multiplier=2.0),
}


def _deepseek_peak(at: datetime) -> bool:
    utc = at.astimezone(timezone.utc)
    if utc.weekday() >= 5:
        return False
    current = utc.time()
    return time(1) <= current < time(4) or time(6) <= current < time(10)


def estimate_cost(
    provider: str,
    model_name: str,
    *,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    at: datetime | None = None,
) -> float | None:
    price = PRICES.get((provider, model_name))
    if price is None:
        return None
    uncached = max(0, input_tokens - cached_input_tokens)
    multiplier = (
        price.peak_multiplier
        if provider == "deepseek" and _deepseek_peak(at or datetime.now(timezone.utc))
        else 1.0
    )
    return multiplier * (
        uncached * price.input_per_million
        + cached_input_tokens * price.cached_input_per_million
        + output_tokens * price.output_per_million
    ) / 1_000_000
