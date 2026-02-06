"""
Shared configuration for Laminar examples.

All examples read from environment variables so secrets never leak into code.
Set these before running any example:

    export LAMINAR_API_KEY="your-project-api-key"

Optional overrides (defaults point to OrbitronAI production):

    export LAMINAR_BASE_URL="https://laminar.orbitronai.com"
    export LAMINAR_OTLP_GRPC_URL="https://otlp-grpc.laminar.orbitronai.com:443"
    export LAMINAR_OTLP_HTTP_URL="https://otlp-http.laminar.orbitronai.com"
"""

import os
import sys


def get_api_key() -> str:
    """Retrieve the Laminar project API key from the environment.

    Returns:
        The API key string.

    Raises:
        SystemExit: If the key is not set.
    """
    key = os.environ.get("LAMINAR_API_KEY", "").strip()
    if not key:
        print(
            "ERROR: LAMINAR_API_KEY is not set.\n"
            "  1. Go to https://laminar.orbitronai.com\n"
            "  2. Open your project → Settings → API Keys\n"
            "  3. export LAMINAR_API_KEY='<your-key>'",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


# Endpoint defaults (OrbitronAI production)
BASE_URL: str = os.environ.get("LAMINAR_BASE_URL", "https://laminar.orbitronai.com")
OTLP_GRPC_URL: str = os.environ.get("LAMINAR_OTLP_GRPC_URL", "https://otlp-grpc.laminar.orbitronai.com:443")
OTLP_HTTP_URL: str = os.environ.get("LAMINAR_OTLP_HTTP_URL", "https://otlp-http.laminar.orbitronai.com")
