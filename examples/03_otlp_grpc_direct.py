#!/usr/bin/env python3
"""
Example 03 — Direct OTLP/gRPC export (no lmnr SDK).

Shows how to send traces to Laminar using the standard OpenTelemetry
SDK with the gRPC exporter. Use this when you want full control over
the OTEL pipeline or can't use the lmnr SDK.

IMPORTANT: gRPC uses port 443 (standard HTTPS), NOT 8443.

Usage:
    export LAMINAR_API_KEY="<your-key>"
    uv run python examples/03_otlp_grpc_direct.py
"""

from __future__ import annotations

import time

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from examples.config import OTLP_GRPC_URL, get_api_key


def setup_tracer(api_key: str, service_name: str) -> trace.Tracer:
    """Configure OpenTelemetry with gRPC exporter targeting Laminar.

    Args:
        api_key: Laminar project API key.
        service_name: Name that identifies your service in traces.

    Returns:
        A configured OpenTelemetry Tracer.
    """
    resource = Resource.create({"service.name": service_name})

    # gRPC exporter — sends to otlp-grpc.laminar.orbitronai.com:443
    exporter = OTLPSpanExporter(
        endpoint=OTLP_GRPC_URL,
        headers=(("authorization", f"Bearer {api_key}"),),
    )

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


def main() -> None:
    """Send a sample trace via OTLP/gRPC to Laminar."""
    api_key = get_api_key()
    tracer = setup_tracer(api_key, "laminar-grpc-example")

    print(f"OTLP/gRPC endpoint → {OTLP_GRPC_URL}")
    print("Sending traced operations...")

    # Create a parent span with children
    with tracer.start_as_current_span("agent-workflow") as parent:
        parent.set_attribute("agent.name", "compliance-checker")
        parent.set_attribute("agent.version", "1.0.0")

        with tracer.start_as_current_span("retrieve-documents") as child:
            child.set_attribute("query", "regulation updates 2026")
            child.set_attribute("doc.count", 5)
            time.sleep(0.1)

        with tracer.start_as_current_span("analyze-compliance") as child:
            child.set_attribute("model", "gpt-4o")
            child.set_attribute("tokens.input", 1500)
            child.set_attribute("tokens.output", 320)
            time.sleep(0.05)

        parent.set_attribute("result.status", "compliant")

    # Force flush all spans
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.force_flush()

    print("Done! Check your traces at: https://laminar.orbitronai.com")


if __name__ == "__main__":
    main()
