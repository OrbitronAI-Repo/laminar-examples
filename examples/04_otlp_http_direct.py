#!/usr/bin/env python3
"""
Example 04 — Direct OTLP/HTTP export (no lmnr SDK).

Sends traces via OTLP/HTTP (protobuf) to Laminar. This is useful when
gRPC is blocked by firewalls or you prefer HTTP transport.

Usage:
    export LAMINAR_API_KEY="<your-key>"
    uv run python examples/04_otlp_http_direct.py
"""

from __future__ import annotations

import time

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from examples.config import OTLP_HTTP_URL, get_api_key


def setup_tracer(api_key: str, service_name: str) -> trace.Tracer:
    """Configure OpenTelemetry with HTTP exporter targeting Laminar.

    Args:
        api_key: Laminar project API key.
        service_name: Name that identifies your service in traces.

    Returns:
        A configured OpenTelemetry Tracer.
    """
    resource = Resource.create({"service.name": service_name})

    # HTTP exporter — sends to otlp-http.laminar.orbitronai.com/v1/traces
    exporter = OTLPSpanExporter(
        endpoint=f"{OTLP_HTTP_URL}/v1/traces",
        headers={"authorization": f"Bearer {api_key}"},
    )

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


def main() -> None:
    """Send a sample trace via OTLP/HTTP to Laminar."""
    api_key = get_api_key()
    tracer = setup_tracer(api_key, "laminar-http-example")

    print(f"OTLP/HTTP endpoint → {OTLP_HTTP_URL}/v1/traces")
    print("Sending traced operations...")

    with tracer.start_as_current_span("data-pipeline") as parent:
        parent.set_attribute("pipeline.name", "lead-enrichment")

        with tracer.start_as_current_span("extract") as span:
            span.set_attribute("source", "crm-api")
            span.set_attribute("records", 150)
            time.sleep(0.08)

        with tracer.start_as_current_span("transform") as span:
            span.set_attribute("transformations", ["normalize", "deduplicate"])
            time.sleep(0.05)

        with tracer.start_as_current_span("load") as span:
            span.set_attribute("destination", "postgres")
            span.set_attribute("records.written", 142)
            time.sleep(0.03)

    # Force flush
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.force_flush()

    print("Done! Check your traces at: https://laminar.orbitronai.com")


if __name__ == "__main__":
    main()
