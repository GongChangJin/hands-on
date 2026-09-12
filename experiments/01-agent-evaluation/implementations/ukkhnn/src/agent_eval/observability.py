"""Connect OpenAI Agents SDK traces to a local Phoenix collector."""

from __future__ import annotations

from agents import set_trace_processors
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from phoenix.otel import register


def configure_phoenix(endpoint: str, project_name: str) -> TracerProvider:
    """Route Agents SDK traces only to Phoenix and return the provider for flushing."""

    # The Agents SDK otherwise uploads traces to OpenAI as well. For this hands-on,
    # Phoenix is the single trace destination so the two UIs are not mixed together.
    set_trace_processors([])
    tracer_provider = register(
        endpoint=endpoint,
        project_name=project_name,
        batch=False,
        verbose=False,
    )
    OpenAIAgentsInstrumentor().instrument(tracer_provider=tracer_provider)
    return tracer_provider
