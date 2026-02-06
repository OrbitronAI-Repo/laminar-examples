#!/usr/bin/env python3
"""
Example 02 — Laminar SDK: Async tracing.

Demonstrates how @observe works seamlessly with async functions.
The decorator auto-detects sync vs async and handles both.

Usage:
    export LAMINAR_API_KEY="<your-key>"
    uv run python examples/02_lmnr_sdk_async.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from lmnr import Laminar, observe

from examples.config import BASE_URL, get_api_key


@observe(name="async-fetch-documents")
async def fetch_documents(query: str) -> list[dict[str, Any]]:
    """Simulate async document retrieval."""
    await asyncio.sleep(0.1)
    return [
        {"id": "doc-1", "title": "AI Safety Guidelines", "relevance": 0.95},
        {"id": "doc-2", "title": "Agent Architecture", "relevance": 0.87},
    ]


@observe(name="async-rank-results")
async def rank_results(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simulate async ranking."""
    await asyncio.sleep(0.05)
    return sorted(docs, key=lambda d: d["relevance"], reverse=True)


@observe(name="async-search-pipeline")
async def search_pipeline(query: str) -> list[dict[str, Any]]:
    """Full async search pipeline — parent span with async children."""
    docs = await fetch_documents(query)
    ranked = await rank_results(docs)
    return ranked


async def main() -> None:
    """Initialize Laminar and run async traced operations."""
    api_key = get_api_key()

    Laminar.initialize(
        project_api_key=api_key,
        base_url=BASE_URL,
    )

    print(f"Laminar initialized → {BASE_URL}")
    print("Running async search pipeline...")

    results = await search_pipeline("AI agent best practices")

    print(f"Found {len(results)} results:")
    for doc in results:
        print(f"  - {doc['title']} (relevance: {doc['relevance']})")

    Laminar.flush()
    print("\nDone! Check your traces at: https://laminar.orbitronai.com")


if __name__ == "__main__":
    asyncio.run(main())
