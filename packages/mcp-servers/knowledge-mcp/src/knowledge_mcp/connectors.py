"""Optional connectors to backing stores (Qdrant, OpenSearch, NebulaGraph)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable

from .config import AppConfig

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover
    QdrantClient = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from opensearchpy import OpenSearch
except ImportError:  # pragma: no cover
    OpenSearch = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from nebula3.Config import Config as NebulaConfig
    from nebula3.gclient.net import ConnectionPool
except ImportError:  # pragma: no cover
    ConnectionPool = None  # type: ignore[misc]


@dataclass
class QdrantConnector:
    client: Any | None
    collection: str

    @classmethod
    def create(cls, host: str, collection: str) -> "QdrantConnector":
        if QdrantClient is None:
            logger.warning(
                "qdrant-client is not installed; falling back to synthetic dense hits"
            )
            return cls(None, collection)
        try:  # pragma: no cover - network path
            client = QdrantClient(host=host)
            return cls(client, collection)
        except Exception as exc:
            logger.warning("Failed to connect to Qdrant", exc_info=exc)
            return cls(None, collection)

    def search(self, query: str, top_k: int) -> Iterable[dict[str, Any]]:
        if not self.client:
            return []
        try:  # pragma: no cover - network path
            response = self.client.search(
                collection_name=self.collection,
                query_vector=self.client.embeddings(text=query),
                limit=top_k,
            )
            return [
                {
                    "document_id": str(point.id),
                    "score": float(point.score or 0.0),
                    "payload": point.payload or {},
                }
                for point in response
            ]
        except Exception as exc:
            logger.warning("Qdrant search failed", exc_info=exc)
            return []


@dataclass
class OpenSearchConnector:
    client: Any | None
    index: str

    @classmethod
    def create(cls, host: str, index: str) -> "OpenSearchConnector":
        if OpenSearch is None:
            logger.warning(
                "opensearch-py is not installed; falling back to synthetic sparse hits"
            )
            return cls(None, index)
        try:  # pragma: no cover
            client = OpenSearch(hosts=[host])
            return cls(client, index)
        except Exception as exc:
            logger.warning("Failed to connect to OpenSearch", exc_info=exc)
            return cls(None, index)

    def bm25(self, query: str, top_k: int) -> Iterable[dict[str, Any]]:
        if not self.client:
            return []
        try:  # pragma: no cover
            response = self.client.search(
                index=self.index,
                body={
                    "query": {"match": {"content": query}},
                    "size": top_k,
                },
            )
            hits = response.get("hits", {}).get("hits", [])
            return [
                {
                    "document_id": hit.get("_id"),
                    "score": hit.get("_score", 0.0),
                    "snippet": hit.get("_source", {}).get("content", ""),
                }
                for hit in hits
            ]
        except Exception as exc:
            logger.warning("OpenSearch query failed", exc_info=exc)
            return []


@dataclass
class NebulaConnector:
    pool: Any | None
    space: str

    @classmethod
    def create(cls, host: str, space: str) -> "NebulaConnector":
        if ConnectionPool is None:
            logger.warning(
                "nebula3 is not installed; graph summaries will be synthetic"
            )
            return cls(None, space)
        try:  # pragma: no cover
            host_parts = host.replace("nebula://", "").split(":")
            address = (
                host_parts[0],
                int(host_parts[1]) if len(host_parts) > 1 else 9669,
            )
            config = NebulaConfig()
            pool = ConnectionPool()
            if not pool.init([address], config):
                raise RuntimeError("Failed to init nebula connection pool")
            return cls(pool, space)
        except Exception as exc:
            logger.warning("Failed to connect to NebulaGraph", exc_info=exc)
            return cls(None, space)

    def community_summaries(self, limit: int) -> Iterable[dict[str, Any]]:
        if not self.pool:
            return []
        try:  # pragma: no cover
            session = self.pool.get_session("root", "nebula")
            try:
                session.execute(f"USE {self.space}")
                result = session.execute(
                    "MATCH (c) RETURN c.name AS name LIMIT %d" % limit
                )
                summaries = []
                for row in result.rows():
                    name = row.values[0].as_string()
                    summaries.append(
                        {
                            "community_id": name,
                            "title": name,
                            "summary": f"Community {name}",
                            "representative_nodes": [],
                        }
                    )
                return summaries
            finally:
                session.release()
        except Exception as exc:
            logger.warning("NebulaGraph query failed", exc_info=exc)
            return []


@dataclass
class ConnectorBundle:
    qdrant: QdrantConnector
    opensearch: OpenSearchConnector
    nebula: NebulaConnector

    @classmethod
    def from_config(cls, config: AppConfig) -> "ConnectorBundle":
        return cls(
            qdrant=(
                QdrantConnector.create(config.vector.host, config.vector.collection)
                if config.vector.enable
                else QdrantConnector(None, config.vector.collection)
            ),
            opensearch=(
                OpenSearchConnector.create(config.keyword.host, config.keyword.index)
                if config.keyword.enable
                else OpenSearchConnector(None, config.keyword.index)
            ),
            nebula=(
                NebulaConnector.create(config.graph.host, config.graph.space)
                if config.graph.enable
                else NebulaConnector(None, config.graph.space)
            ),
        )
