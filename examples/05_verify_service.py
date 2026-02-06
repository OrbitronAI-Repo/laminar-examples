#!/usr/bin/env python3
"""
Example 05 — Laminar Service Verification Script.

Validates that the Laminar deployment is fully operational by testing:
  1. UI reachability (HTTPS)
  2. OTLP/HTTP ingestion endpoint
  3. OTLP/gRPC ingestion endpoint (HTTP/2 on port 443)
  4. Trace export via lmnr SDK
  5. Trace export via OTLP/gRPC direct
  6. Trace export via OTLP/HTTP direct

Usage:
    export LAMINAR_API_KEY="<your-key>"
    uv run python examples/05_verify_service.py
"""

from __future__ import annotations

import sys
import time
from typing import Any

import httpx
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from examples.config import BASE_URL, OTLP_GRPC_URL, OTLP_HTTP_URL, get_api_key

# ─── Helpers ────────────────────────────────────────────────────────


def _check(label: str, ok: bool, detail: str = "") -> bool:
    """Print a status line and return the result."""
    status = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    return ok


# ─── Individual checks ──────────────────────────────────────────────


def check_ui_reachable() -> bool:
    """Verify the Laminar UI responds on HTTPS."""
    try:
        resp = httpx.get(f"{BASE_URL}/sign-in", timeout=15, follow_redirects=True)
        return _check("UI reachable", resp.status_code == 200, f"HTTP {resp.status_code}")
    except Exception as exc:
        return _check("UI reachable", False, str(exc))


def check_otlp_http_reachable() -> bool:
    """Verify the OTLP/HTTP endpoint responds (even with an empty body)."""
    try:
        resp = httpx.post(
            f"{OTLP_HTTP_URL}/v1/traces",
            headers={"Content-Type": "application/x-protobuf"},
            content=b"",
            timeout=15,
        )
        # 400/401/415 = endpoint is alive (body invalid or auth required)
        ok = resp.status_code in (200, 400, 401, 415)
        return _check("OTLP/HTTP endpoint", ok, f"HTTP {resp.status_code}")
    except Exception as exc:
        return _check("OTLP/HTTP endpoint", False, str(exc))


def check_otlp_grpc_reachable() -> bool:
    """Verify gRPC endpoint accepts HTTP/2 on port 443."""
    try:
        # Use httpx HTTP/2 to check ALPN negotiation
        with httpx.Client(http2=True, timeout=15) as client:
            resp = client.post(
                f"{OTLP_GRPC_URL}/opentelemetry.proto.collector.trace.v1.TraceService/Export",
                headers={"Content-Type": "application/grpc", "TE": "trailers"},
                content=b"",
            )
        # gRPC returns various codes; connection success = endpoint alive
        return _check("OTLP/gRPC endpoint (HTTP/2 :443)", True, f"HTTP {resp.status_code}")
    except Exception as exc:
        return _check("OTLP/gRPC endpoint (HTTP/2 :443)", False, str(exc))


def check_sdk_export(api_key: str) -> bool:
    """Export a trace via the lmnr SDK and verify no errors."""
    try:
        from lmnr import Laminar, observe

        Laminar.initialize(project_api_key=api_key, base_url=BASE_URL)

        @observe(name="verify-sdk-trace")
        def _dummy_op() -> str:
            time.sleep(0.01)
            return "ok"

        _dummy_op()
        Laminar.flush()
        return _check("lmnr SDK trace export", True)
    except Exception as exc:
        return _check("lmnr SDK trace export", False, str(exc))


def _export_and_check(label: str, exporter: Any) -> bool:
    """Create a single span, export, and verify the result."""
    try:
        resource = Resource.create({"service.name": f"verify-{label}"})
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        tracer = provider.get_tracer("verify")

        with tracer.start_as_current_span(f"verify-{label}") as span:
            span.set_attribute("test", True)
            time.sleep(0.01)

        # force_flush returns True if all spans exported successfully
        flushed = provider.force_flush(timeout_millis=10000)
        provider.shutdown()
        return _check(label, flushed)
    except Exception as exc:
        return _check(label, False, str(exc))


def check_grpc_export(api_key: str) -> bool:
    """Export a trace via OTLP/gRPC directly."""
    exporter = GrpcExporter(
        endpoint=OTLP_GRPC_URL,
        headers=(("authorization", f"Bearer {api_key}"),),
    )
    return _export_and_check("OTLP/gRPC trace export", exporter)


def check_http_export(api_key: str) -> bool:
    """Export a trace via OTLP/HTTP directly."""
    exporter = HttpExporter(
        endpoint=f"{OTLP_HTTP_URL}/v1/traces",
        headers={"authorization": f"Bearer {api_key}"},
    )
    return _export_and_check("OTLP/HTTP trace export", exporter)


# ─── Main ───────────────────────────────────────────────────────────


def main() -> None:
    """Run all verification checks."""
    api_key = get_api_key()

    print("\nLaminar Service Verification")
    print(f"{'=' * 50}")
    print(f"  UI:        {BASE_URL}")
    print(f"  OTLP HTTP: {OTLP_HTTP_URL}")
    print(f"  OTLP gRPC: {OTLP_GRPC_URL}")
    print(f"{'=' * 50}\n")

    results: list[bool] = []

    # Connectivity checks
    print("Connectivity:")
    results.append(check_ui_reachable())
    results.append(check_otlp_http_reachable())
    results.append(check_otlp_grpc_reachable())

    # Export checks
    print("\nTrace Export:")
    results.append(check_sdk_export(api_key))
    results.append(check_grpc_export(api_key))
    results.append(check_http_export(api_key))

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed")

    if all(results):
        print("Laminar is fully operational!")
    else:
        print("Some checks failed — see details above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
