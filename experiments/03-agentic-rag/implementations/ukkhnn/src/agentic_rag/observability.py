"""Connect LangChain/LangGraph and explicit tool spans to local Phoenix."""

from __future__ import annotations

from typing import Any

from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from phoenix.otel import register


_instrumentor = LangChainInstrumentor()


def configure_phoenix(endpoint: str, project_name: str) -> TracerProvider:
    provider = register(
        endpoint=endpoint,
        project_name=project_name,
        batch=False,
        verbose=False,
    )
    if not _instrumentor.is_instrumented_by_opentelemetry:
        _instrumentor.instrument(tracer_provider=provider)
    return provider


def shutdown_phoenix(provider: TracerProvider | None) -> None:
    if provider is None:
        return
    if _instrumentor.is_instrumented_by_opentelemetry:
        _instrumentor.uninstrument()
    provider.shutdown()


def tracer():
    return trace.get_tracer("gongchangjin.agentic-rag")


def safe_attributes(**values: Any) -> dict[str, Any]:
    """Keep trace attributes useful without exporting document bodies or secrets."""

    return {key: value for key, value in values.items() if value is not None}
