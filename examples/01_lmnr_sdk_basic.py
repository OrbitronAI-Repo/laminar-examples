#!/usr/bin/env python3
"""
Example 01 — Laminar SDK: Basic tracing with @observe decorator.

This is the simplest way to get traces into Laminar. The lmnr SDK
wraps OpenTelemetry under the hood and sends spans to our self-hosted
Laminar instance.

Usage:
    export LAMINAR_API_KEY="<your-key>"
    uv run python examples/01_lmnr_sdk_basic.py
"""

from __future__ import annotations

import time
from typing import Any

from lmnr import Laminar, observe

from examples.config import BASE_URL, get_api_key


@observe(name="fetch-user-data")
def fetch_user_data(user_id: str) -> dict[str, Any]:
    """Simulate fetching user data from a database."""
    time.sleep(0.1)  # simulate I/O
    return {
        "id": user_id,
        "name": "Alice",
        "email": "alice@orbitronai.com",
        "plan": "enterprise",
    }


@observe(name="enrich-profile")
def enrich_profile(user: dict[str, Any]) -> dict[str, Any]:
    """Simulate enriching a user profile with external data."""
    time.sleep(0.05)
    user["enriched"] = True
    user["risk_score"] = 0.12
    return user


@observe(name="process-user-request")
def process_user_request(user_id: str) -> dict[str, Any]:
    """Top-level operation that creates a parent span with child spans."""
    user = fetch_user_data(user_id)
    enriched = enrich_profile(user)
    return enriched


def main() -> None:
    """Initialize Laminar and run a traced operation."""
    api_key = get_api_key()

    # Initialize the SDK — this sets up the OpenTelemetry pipeline
    Laminar.initialize(
        project_api_key=api_key,
        base_url=BASE_URL,
    )

    print(f"Laminar initialized → {BASE_URL}")
    print("Sending traced request...")

    result = process_user_request("user-42")

    print(f"Result: {result}")
    print("Flushing traces...")

    # Ensure all spans are exported before exit
    Laminar.flush()
    print("Done! Check your traces at: https://laminar.orbitronai.com")


if __name__ == "__main__":
    main()
