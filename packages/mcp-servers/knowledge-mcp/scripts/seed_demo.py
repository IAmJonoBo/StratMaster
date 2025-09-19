"""Seed demo documents into Qdrant and OpenSearch when available."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from knowledge_mcp.config import load_config

logger = logging.getLogger(__name__)

try:  # pragma: no cover
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover
    QdrantClient = None

try:  # pragma: no cover
    from opensearchpy import OpenSearch
except ImportError:  # pragma: no cover
    OpenSearch = None

DEMO_DOCS = [
    {
        "id": "doc-1",
        "content": "Premium positioning drives conversion uplift",
        "source_url": "https://example.com/premium",
    },
    {
        "id": "doc-2",
        "content": "Competitors pivot to value offers",
        "source_url": "https://example.com/value",
    },
]


def seed_qdrant(host: str, collection: str) -> None:
    if QdrantClient is None:
        logger.warning("qdrant-client missing; skipping Qdrant seeding")
        return
    client = QdrantClient(host=host)
    client.recreate_collection(
        collection, vectors_config={"size": 8, "distance": "Cosine"}
    )
    points = []
    for doc in DEMO_DOCS:
        vector = [float(ord(ch) % 13) / 10.0 for ch in doc["content"][:8]]
        points.append(
            (
                doc["id"],
                vector,
                {"snippet": doc["content"], "source_url": doc["source_url"]},
            )
        )
    client.upsert(collection_name=collection, points=points)


def seed_opensearch(host: str, index: str) -> None:
    if OpenSearch is None:
        logger.warning("opensearch-py missing; skipping OpenSearch seeding")
        return
    client = OpenSearch(hosts=[host])
    if not client.indices.exists(index=index):  # pragma: no cover
        client.indices.create(index=index)
    for doc in DEMO_DOCS:
        client.index(index=index, id=doc["id"], body={"content": doc["content"]})


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    seed_qdrant(cfg.vector.host, cfg.vector.collection)
    seed_opensearch(cfg.keyword.host, cfg.keyword.index)
    logger.info("Demo documents seeded (where connectors available)")


if __name__ == "__main__":
    main()
