"""Explicit Phoenix spans with a strict metadata allow-list."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from phoenix.otel import register


PROJECT_NAME = "04-multimodal-agent"


def configure_phoenix(endpoint: str) -> TracerProvider:
    return register(endpoint=endpoint, project_name=PROJECT_NAME, batch=False, verbose=False)


def shutdown_phoenix(provider: TracerProvider | None) -> None:
    if provider is not None:
        provider.shutdown()


def tracer():
    return trace.get_tracer("gongchangjin.multimodal-agent")


def safe_attributes(**values: Any) -> dict[str, str | int | float | bool]:
    """Serialize only primitive, pre-approved summaries—not image/context bodies."""

    allowed: dict[str, str | int | float | bool] = {}
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            allowed[key] = value
    return allowed


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    with tracer().start_as_current_span(name) as current:
        current.set_attributes(safe_attributes(**attributes))
        yield current
