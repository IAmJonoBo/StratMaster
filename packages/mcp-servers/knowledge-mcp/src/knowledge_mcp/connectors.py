"""Optional connectors to backing stores (Qdrant, OpenSearch, NebulaGraph).

This module keeps network interactions best-effort so the service can degrade gracefully when
optional dependencies or remote services are unavailable. Each connector exposes lightweight
status flags that surface in the `/info` endpoint.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable

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
    enabled: bool
    client: Any | None
    collection: str
    available: bool = False
    last_error: str | None = None
    probe_query: str = "health-check"
    probe_top_k: int = 1
    probe_enabled: bool = False

    @classmethod
    def create(
        cls,
        enabled: bool,
        host: str,
        collection: str,
        probe_enabled: bool,
        probe_query: str,
        probe_top_k: int,
    ) -> "QdrantConnector":
        if not enabled:
            return cls(
                enabled=False,
                client=None,
                collection=collection,
                available=False,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
        if QdrantClient is None:
            message = (
                "qdrant-client is not installed; falling back to synthetic dense hits"
            )
            logger.warning(message)
            return cls(
                enabled=True,
                client=None,
                collection=collection,
                available=False,
                last_error=message,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
        try:  # pragma: no cover - network path
            client = QdrantClient(host=host)
            connector = cls(
                enabled=True,
                client=client,
                collection=collection,
                available=True,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
            connector.run_health_probe()
            return connector
        except Exception as exc:
            logger.warning("Failed to connect to Qdrant", exc_info=exc)
            return cls(
                enabled=True,
                client=None,
                collection=collection,
                available=False,
                last_error=str(exc),
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )

    def search(self, query: str, top_k: int) -> Iterable[dict[str, Any]]:
        if not self.client:
            return []
        try:  # pragma: no cover - network path
            response = self.client.search(
                collection_name=self.collection,
                query_vector=self.client.embeddings(text=query),
                limit=top_k,
            )
            self.available = True
            self.last_error = None
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
            self.available = False
            self.last_error = str(exc)
            return []

    def run_health_probe(self) -> None:
        if not self.client or not self.probe_enabled:
            return
        try:  # pragma: no cover - network path
            response = self.client.search(
                collection_name=self.collection,
                query_vector=self.client.embeddings(text=self.probe_query),
                limit=self.probe_top_k,
            )
            self.available = bool(response)
            if not self.available:
                self.last_error = "Probe returned no hits"
        except Exception as exc:  # pragma: no cover
            self.available = False
            self.last_error = str(exc)


@dataclass
class OpenSearchConnector:
    enabled: bool
    client: Any | None
    index: str
    available: bool = False
    last_error: str | None = None
    probe_enabled: bool = False
    probe_query: str = "health-check"
    probe_top_k: int = 1

    @classmethod
    def create(
        cls,
        enabled: bool,
        host: str,
        index: str,
        probe_enabled: bool,
        probe_query: str,
        probe_top_k: int,
    ) -> "OpenSearchConnector":
        if not enabled:
            return cls(
                enabled=False,
                client=None,
                index=index,
                available=False,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
        if OpenSearch is None:
            message = (
                "opensearch-py is not installed; falling back to synthetic sparse hits"
            )
            logger.warning(message)
            return cls(
                enabled=True,
                client=None,
                index=index,
                available=False,
                last_error=message,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
        try:  # pragma: no cover
            client = OpenSearch(hosts=[host])
            connector = cls(
                enabled=True,
                client=client,
                index=index,
                available=True,
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )
            try:
                if not client.ping():
                    connector.available = False
                    connector.last_error = "OpenSearch ping returned False"
                elif not client.indices.exists(index=index):
                    logger.info(
                        "OpenSearch index %s missing; connector still available", index
                    )
            except Exception as ping_exc:  # pragma: no cover
                logger.warning("OpenSearch availability ping failed", exc_info=ping_exc)
                connector.available = False
                connector.last_error = str(ping_exc)
            connector.run_health_probe()
            return connector
        except Exception as exc:
            logger.warning("Failed to connect to OpenSearch", exc_info=exc)
            return cls(
                enabled=True,
                client=None,
                index=index,
                available=False,
                last_error=str(exc),
                probe_enabled=probe_enabled,
                probe_query=probe_query,
                probe_top_k=probe_top_k,
            )

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
            self.available = True
            self.last_error = None
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
            self.available = False
            self.last_error = str(exc)
            return []

    def run_health_probe(self) -> None:
        if not self.client or not self.probe_enabled:
            return
        try:  # pragma: no cover
            response = self.client.search(
                index=self.index,
                body={
                    "query": {"match": {"content": self.probe_query}},
                    "size": self.probe_top_k,
                },
            )
            hits = response.get("hits", {}).get("hits", [])
            self.available = bool(hits)
            if not self.available:
                self.last_error = "Probe returned no hits"
        except Exception as exc:
            self.available = False
            self.last_error = str(exc)


@dataclass
class NebulaConnector:
    enabled: bool
    pool: Any | None
    space: str
    available: bool = False
    last_error: str | None = None
    probe_enabled: bool = False
    probe_limit: int = 1

    @classmethod
    def create(
        cls,
        enabled: bool,
        host: str,
        space: str,
        probe_enabled: bool,
        probe_limit: int,
    ) -> "NebulaConnector":
        if not enabled:
            return cls(
                enabled=False,
                pool=None,
                space=space,
                available=False,
                probe_enabled=probe_enabled,
                probe_limit=probe_limit,
            )
        if ConnectionPool is None:
            message = "nebula3 is not installed; graph summaries will be synthetic"
            logger.warning(message)
            return cls(
                enabled=True,
                pool=None,
                space=space,
                available=False,
                last_error=message,
                probe_enabled=probe_enabled,
                probe_limit=probe_limit,
            )
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
            connector = cls(
                enabled=True,
                pool=pool,
                space=space,
                available=True,
                probe_enabled=probe_enabled,
                probe_limit=probe_limit,
            )
            try:
                session = pool.get_session("root", "nebula")
                try:
                    session.execute("SHOW SPACES")
                finally:
                    session.release()
            except Exception as ping_exc:
                logger.warning(
                    "NebulaGraph availability ping failed", exc_info=ping_exc
                )
                connector.available = False
                connector.last_error = str(ping_exc)
            connector.run_health_probe()
            return connector
        except Exception as exc:
            logger.warning("Failed to connect to NebulaGraph", exc_info=exc)
            return cls(
                enabled=True,
                pool=None,
                space=space,
                available=False,
                last_error=str(exc),
                probe_enabled=probe_enabled,
                probe_limit=probe_limit,
            )

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
                self.available = True
                self.last_error = None
                return summaries
            finally:
                session.release()
        except Exception as exc:
            logger.warning("NebulaGraph query failed", exc_info=exc)
            self.available = False
            self.last_error = str(exc)
            return []

    def run_health_probe(self) -> None:
        if not self.pool or not self.probe_enabled:
            return
        try:  # pragma: no cover
            session = self.pool.get_session("root", "nebula")
            try:
                session.execute(f"USE {self.space}")
                result = session.execute(
                    "MATCH (c) RETURN c.name AS name LIMIT %d" % self.probe_limit
                )
                self.available = result.is_succeeded() and result.rows()
                if not self.available:
                    self.last_error = "Probe returned no rows"
            finally:
                session.release()
        except Exception as exc:
            self.available = False
            self.last_error = str(exc)


@dataclass
class ConnectorBundle:
    qdrant: QdrantConnector
    opensearch: OpenSearchConnector
    nebula: NebulaConnector

    @classmethod
    def from_config(cls, config: AppConfig) -> "ConnectorBundle":
        return cls(
            qdrant=QdrantConnector.create(
                enabled=config.vector.enable,
                host=config.vector.host,
                collection=config.vector.collection,
                probe_enabled=config.vector.health_probe_enabled,
                probe_query=config.vector.health_probe_query,
                probe_top_k=config.vector.health_probe_top_k,
            ),
            opensearch=OpenSearchConnector.create(
                enabled=config.keyword.enable,
                host=config.keyword.host,
                index=config.keyword.index,
                probe_enabled=config.keyword.health_probe_enabled,
                probe_query=config.keyword.health_probe_query,
                probe_top_k=config.keyword.health_probe_top_k,
            ),
            nebula=NebulaConnector.create(
                enabled=config.graph.enable,
                host=config.graph.host,
                space=config.graph.space,
                probe_enabled=config.graph.health_probe_enabled,
                probe_limit=config.graph.health_probe_limit,
            ),
        )

    def as_statuses(self) -> Dict[str, dict[str, Any]]:
        return {
            "vector": {
                "enabled": self.qdrant.enabled,
                "available": self.qdrant.available,
                "last_error": self.qdrant.last_error,
            },
            "keyword": {
                "enabled": self.opensearch.enabled,
                "available": self.opensearch.available,
                "last_error": self.opensearch.last_error,
            },
            "graph": {
                "enabled": self.nebula.enabled,
                "available": self.nebula.available,
                "last_error": self.nebula.last_error,
            },
        }
