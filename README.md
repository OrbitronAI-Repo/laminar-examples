# Laminar Examples

Proven Python examples for integrating with [Laminar](https://github.com/lmnr-ai/lmnr), OrbitronAI's self-hosted AI agent observability platform.

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/OrbitronAI-Repo/laminar-examples.git
cd laminar-examples

# 2. Install dependencies (requires uv — https://docs.astral.sh/uv/)
uv sync

# 3. Configure your API key
cp .env.example .env
# Edit .env and set LAMINAR_API_KEY (get it from https://laminar.orbitronai.com → Project → Settings → API Keys)

# 4. Run an example
uv run python -m examples.01_lmnr_sdk_basic
```

## Examples

| # | File | Description | Method |
|---|------|-------------|--------|
| 01 | `01_lmnr_sdk_basic.py` | Basic tracing with the `@observe` decorator | lmnr SDK |
| 02 | `02_lmnr_sdk_async.py` | Async tracing with the `@observe` decorator | lmnr SDK |
| 03 | `03_otlp_grpc_direct.py` | Direct OTLP/gRPC export (no lmnr SDK) | OpenTelemetry gRPC |
| 04 | `04_otlp_http_direct.py` | Direct OTLP/HTTP export (no lmnr SDK) | OpenTelemetry HTTP |
| 05 | `05_verify_service.py` | Comprehensive service verification (6 checks) | All methods |

## Configuration

All examples read from environment variables. Copy `.env.example` to `.env` and set:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LAMINAR_API_KEY` | Yes | — | Project API key from Laminar UI |
| `LAMINAR_BASE_URL` | No | `https://laminar.orbitronai.com` | Laminar UI base URL |
| `LAMINAR_OTLP_GRPC_URL` | No | `https://otlp-grpc.laminar.orbitronai.com:443` | OTLP/gRPC endpoint |
| `LAMINAR_OTLP_HTTP_URL` | No | `https://otlp-http.laminar.orbitronai.com` | OTLP/HTTP endpoint |

### Internal GCP Services (PSC)

For services running inside GCP that use Private Service Connect, override the endpoints with the PSC IP addresses:

```bash
LAMINAR_BASE_URL=http://<psc-http-endpoint-ip>
LAMINAR_OTLP_GRPC_URL=http://<psc-grpc-endpoint-ip>
LAMINAR_OTLP_HTTP_URL=http://<psc-http-endpoint-ip>
```

Contact DevOps for the PSC endpoint IPs.

## Verify the Deployment

Run the verification script to confirm all endpoints are healthy:

```bash
uv run python -m examples.05_verify_service
```

Expected output:

```
Laminar Service Verification
==================================================
Connectivity:
  [PASS] UI reachable — HTTP 200
  [PASS] OTLP/HTTP endpoint — HTTP 401
  [PASS] OTLP/gRPC endpoint (HTTP/2 :443) — HTTP 200

Trace Export:
  [PASS] lmnr SDK trace export
  [PASS] OTLP/gRPC trace export
  [PASS] OTLP/HTTP trace export

==================================================
Results: 6/6 passed
Laminar is fully operational!
```

## Integration Guide

### Option 1: lmnr SDK (Recommended)

The simplest way. Two lines at the top of your app:

```python
from lmnr import Laminar, observe

Laminar.initialize(
    project_api_key="<your-key>",
    base_url="https://laminar.orbitronai.com",
)

@observe(name="my-operation")
def do_work():
    # Your code here — automatically traced
    return result
```

### Option 2: OpenTelemetry Direct (gRPC)

Full control over the OTEL pipeline:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="https://otlp-grpc.laminar.orbitronai.com:443",
    headers=(("authorization", f"Bearer {api_key}"),),
)
```

### Option 3: OpenTelemetry Direct (HTTP)

When gRPC is blocked:

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="https://otlp-http.laminar.orbitronai.com/v1/traces",
    headers={"authorization": f"Bearer {api_key}"},
)
```

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
