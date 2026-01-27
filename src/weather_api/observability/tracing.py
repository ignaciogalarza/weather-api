"""OpenTelemetry tracing configuration."""

import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracing(
    service_name: str = "weather-api",
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> None:
    """Configure OpenTelemetry distributed tracing.

    Args:
        service_name: Name of the service for traces.
        otlp_endpoint: OTLP collector endpoint (e.g., "http://tempo:4317").
        console_export: If True, also export traces to console (for debugging).
    """
    # Get endpoint from environment if not provided
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    # Create resource with service info
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",
        }
    )

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter if endpoint is configured
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add console exporter for debugging
    if console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument httpx
    HTTPXClientInstrumentor().instrument()


def instrument_fastapi(app: FastAPI) -> None:
    """Instrument FastAPI app for tracing.

    Args:
        app: FastAPI application instance.
    """
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance.

    Args:
        name: Name for the tracer (usually __name__).

    Returns:
        OpenTelemetry Tracer instance.
    """
    return trace.get_tracer(name)
