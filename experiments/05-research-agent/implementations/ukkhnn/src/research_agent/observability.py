"""Explicit Phoenix spans with an allow-list that excludes content and secrets."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from phoenix.otel import register

from .paths import PHOENIX_PROJECT_NAME


ALLOWED_ATTRIBUTES = {
    "task_id",
    "query_hash",
    "query_version",
    "search_source",
    "search_condition",
    "paper_identifier",
    "content_hash",
    "content_type",
    "content_size",
    "validation_status",
    "model",
    "request_model",
    "response_model",
    "protocol_provider",
    "actual_endpoint_provider",
    "actual_hostname",
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "total_tokens",
    "cost_usd",
    "latency_ms",
    "failure_type",
    "result_count",
    "request_count",
    "project",
    "offline",
}


def configure_phoenix(endpoint: str) -> TracerProvider:
    return register(endpoint=endpoint, project_name=PHOENIX_PROJECT_NAME, batch=False, verbose=False)


def shutdown_phoenix(provider: TracerProvider | None) -> None:
    if provider is not None:
        provider.shutdown()


def tracer():
    return trace.get_tracer("gongchangjin.research-agent")


def safe_attributes(values: dict[str, Any]) -> dict[str, str | int | float | bool]:
    return {
        key: value
        for key, value in values.items()
        if key in ALLOWED_ATTRIBUTES and isinstance(value, (str, int, float, bool))
    }


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    with tracer().start_as_current_span(name, record_exception=False, set_status_on_exception=False) as current:
        current.set_attributes(safe_attributes(attributes))
        try:
            yield current
        except Exception as exc:
            failure_type = getattr(exc, "kind", type(exc).__name__)
            current.set_attribute("failure_type", str(failure_type))
            raise
