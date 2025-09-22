"""Service layer for knowledge MCP.

The implementation currently synthesises responses while maintaining signatures that can be
swapped with real vector/keyword/graph backends (Qdrant, OpenSearch, NebulaGraph) later.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from .config import AppConfig
from .connectors import ConnectorBundle
from .models import (
    CommunitySummariesResponse,
    ConnectorStatus,
    GraphSummary,
    HybridQueryRequest,
    HybridQueryResponse,
    RankingRequest,
    RankingResponse,
    RetrievalHit,
)

try:  # pragma: no cover - optional dependency
    from bge_reranker import BGEReranker, RerankDocument
except ImportError:  # pragma: no cover
    BGEReranker = None  # type: ignore[assignment]
    RerankDocument = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from opentelemetry import metrics
except ImportError:  # pragma: no cover
    metrics = None


if metrics is not None:  # pragma: no cover - requires OTEL SDK
    _METER = metrics.get_meter(__name__)
    _DEGRADED_COUNTER = _METER.create_counter(
        "knowledge_mcp.connector.degraded",
        unit="1",
        description="Count of connector degradations falling back to synthetic responses",
    )
    _SUCCESS_COUNTER = _METER.create_counter(
        "knowledge_mcp.connector.success",
        unit="1",
        description="Count of successful connector round-trips",
    )
else:
    _DEGRADED_COUNTER = None
    _SUCCESS_COUNTER = None


class KnowledgeService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.connectors = ConnectorBundle.from_config(config)
        self._connector_status_cache = self.connectors.as_statuses()
        self._logger = logging.getLogger(__name__)
        self._reranker = BGEReranker() if BGEReranker is not None else None

    # ------------------------------------------------------------------
    # Hybrid retrieval
    # ------------------------------------------------------------------
    def hybrid_query(self, payload: HybridQueryRequest) -> HybridQueryResponse:
        dense_hits = list(self._dense_hits(payload.query, payload.top_k))
        if self.connectors.qdrant.enabled:
            dense_results = list(self._qdrant_hits(payload.query, payload.top_k))
            if dense_results:
                dense_hits = dense_results
                self._record_success("vector")
            elif not self.connectors.qdrant.available:
                self._logger.warning(
                    "Qdrant connector unavailable; using synthetic dense hits",
                    extra={
                        "event": "connector.degraded",
                        "connector": "vector",
                        "tenant_id": payload.tenant_id,
                        "query": payload.query,
                    },
                )
                self._record_degraded("vector")

        sparse_hits = list(self._sparse_hits(payload.query, payload.top_k))
        if self.connectors.opensearch.enabled:
            sparse_results = list(self._opensearch_hits(payload.query, payload.top_k))
            if sparse_results:
                sparse_hits = sparse_results
                self._record_success("keyword")
            elif not self.connectors.opensearch.available:
                self._logger.warning(
                    "OpenSearch connector unavailable; using synthetic sparse hits",
                    extra={
                        "event": "connector.degraded",
                        "connector": "keyword",
                        "tenant_id": payload.tenant_id,
                        "query": payload.query,
                    },
                )
                self._record_degraded("keyword")
        combined = self._blend_hits(
            dense_hits,
            sparse_hits,
            payload.top_k,
            payload.alpha_dense,
            payload.alpha_sparse,
        )
        self._refresh_connector_status()
        return HybridQueryResponse(
            hits=combined,
            dense_score_weight=payload.alpha_dense,
            sparse_score_weight=payload.alpha_sparse,
        )

    def colbert_search(self, payload: HybridQueryRequest) -> HybridQueryResponse:
        hits = [
            RetrievalHit(
                document_id=f"colbert-{i}",
                score=0.9 - i * 0.05,
                method="colbert",
                snippet=f"ColBERT passage {i} for {payload.query}",
                source_url="https://example.com/colbert",
                metadata={"collection": self.config.vector.collection},
            )
            for i in range(1, min(payload.top_k, 5) + 1)
        ]
        self._refresh_connector_status()
        return HybridQueryResponse(
            hits=hits, dense_score_weight=1.0, sparse_score_weight=0.0
        )

    def splade_search(self, payload: HybridQueryRequest) -> HybridQueryResponse:
        hits = [
            RetrievalHit(
                document_id=f"splade-{i}",
                score=0.85 - i * 0.04,
                method="splade",
                snippet=f"SPLADE expansion {i} for {payload.query}",
                source_url="https://example.com/splade",
                metadata={"index": self.config.keyword.index},
            )
            for i in range(1, min(payload.top_k, 5) + 1)
        ]
        self._refresh_connector_status()
        return HybridQueryResponse(
            hits=hits, dense_score_weight=0.0, sparse_score_weight=1.0
        )

    def rerank(self, payload: RankingRequest) -> RankingResponse:
        if self._reranker is not None and RerankDocument is not None:
            request_documents = [
                RerankDocument(id=f"doc-{idx}", text=text)
                for idx, text in enumerate(payload.documents, start=1)
            ]
            results = self._reranker.rerank(
                query=payload.query, documents=request_documents, top_k=len(request_documents)
            )
            reranked = [
                RetrievalHit(
                    document_id=item.id,
                    score=float(item.score),
                    method="rerank",
                    snippet=item.text[:160],
                    source_url="https://example.com/rerank",
                    metadata={"rank": str(item.rank)},
                )
                for item in results
            ]
        else:
            reranked = [
                RetrievalHit(
                    document_id=f"rerank-{idx}",
                    score=1.0 - idx * 0.05,
                    method="rerank",
                    snippet=doc[:160],
                    source_url="https://example.com/rerank",
                    metadata={"position": str(idx)},
                )
                for idx, doc in enumerate(payload.documents, start=1)
            ]
        self._refresh_connector_status()
        return RankingResponse(reranked=reranked)

    # ------------------------------------------------------------------
    # Graph summaries
    # ------------------------------------------------------------------
    def community_summaries(
        self, tenant_id: str, limit: int = 3
    ) -> CommunitySummariesResponse:
        summaries = list(self.connectors.nebula.community_summaries(limit))
        if not summaries:
            if self.connectors.nebula.enabled and not self.connectors.nebula.available:
                self._logger.warning(
                    "NebulaGraph connector unavailable; using synthetic graph summaries",
                    extra={
                        "event": "connector.degraded",
                        "connector": "graph",
                        "tenant_id": tenant_id,
                        "limit": limit,
                    },
                )
                self._record_degraded("graph")
            summaries = [
                GraphSummary(
                    community_id=f"comm-{i}",
                    title=f"Community {i}",
                    summary=f"Community {i} focuses on premium positioning and market shifts.",
                    representative_nodes=["brand", "competitor", "customer"],
                )
                for i in range(1, limit + 1)
            ]
        else:
            self._record_success("graph")
        self._refresh_connector_status()
        return CommunitySummariesResponse(
            generated_at=datetime.now(tz=timezone.utc),
            summaries=summaries,
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def connector_status(self) -> dict[str, ConnectorStatus]:
        """Return connector status map as Pydantic models for the /info endpoint."""
        # refresh cached status for any runtime degradations
        self._connector_status_cache = self.connectors.as_statuses()
        return {
            name: ConnectorStatus(**payload)
            for name, payload in self._connector_status_cache.items()
        }

    def _refresh_connector_status(self) -> None:
        """Update cached connector status after tool execution."""
        self._connector_status_cache = self.connectors.as_statuses()

    @staticmethod
    def _record_success(connector: str) -> None:
        if _SUCCESS_COUNTER is not None:  # pragma: no cover - metrics optional
            _SUCCESS_COUNTER.add(1, attributes={"connector": connector})

    @staticmethod
    def _record_degraded(connector: str) -> None:
        if _DEGRADED_COUNTER is not None:  # pragma: no cover - metrics optional
            _DEGRADED_COUNTER.add(1, attributes={"connector": connector})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _dense_hits(query: str, top_k: int) -> Iterable[RetrievalHit]:
        for i in range(1, min(top_k, 5) + 1):
            yield RetrievalHit(
                document_id=f"dense-{i}",
                score=0.8 - i * 0.03,
                method="dense",
                snippet=f"Dense embedding match {i} for {query}",
                source_url="https://example.com/dense",
                metadata={"collection": "demo-dense"},
            )

    @staticmethod
    def _sparse_hits(query: str, top_k: int) -> Iterable[RetrievalHit]:
        for i in range(1, min(top_k, 5) + 1):
            yield RetrievalHit(
                document_id=f"sparse-{i}",
                score=0.75 - i * 0.02,
                method="sparse",
                snippet=f"Sparse keyword match {i} for {query}",
                source_url="https://example.com/sparse",
                metadata={"index": "demo-sparse"},
            )

    @staticmethod
    def _blend_hits(
        dense_hits: list[RetrievalHit],
        sparse_hits: list[RetrievalHit],
        top_k: int,
        alpha_dense: float,
        alpha_sparse: float,
    ) -> list[RetrievalHit]:
        if not dense_hits and not sparse_hits:
            return []
        blended: list[RetrievalHit] = []
        max_length = max(len(dense_hits), len(sparse_hits), 1)
        for idx in range(max_length):
            dense = dense_hits[idx] if idx < len(dense_hits) else None
            sparse = sparse_hits[idx] if idx < len(sparse_hits) else None
            blended.append(
                KnowledgeService._compose_hybrid_hit(
                    dense,
                    sparse,
                    alpha_dense,
                    alpha_sparse,
                    rank_hint=idx,
                )
            )

        # trim to requested top_k while keeping highest scores first
        blended.sort(key=lambda hit: hit.score, reverse=True)
        trimmed = blended[:top_k]
        for rank, hit in enumerate(trimmed, start=1):
            hit.metadata["hybrid_rank"] = str(rank)
        return trimmed

    @staticmethod
    def _compose_hybrid_hit(
        dense: RetrievalHit | None,
        sparse: RetrievalHit | None,
        alpha_dense: float,
        alpha_sparse: float,
        *,
        rank_hint: int,
    ) -> RetrievalHit:
        dense_score = dense.score if dense else 0.0
        sparse_score = sparse.score if sparse else 0.0
        weight = 0.0
        snippet_parts: list[str] = []
        metadata: dict[str, str] = {"hybrid_rank_hint": str(rank_hint + 1)}

        if dense is not None:
            weight += alpha_dense
            snippet_parts.append(dense.snippet)
            metadata["dense_id"] = dense.document_id
            metadata["dense_score"] = f"{dense.score:.4f}"
            for key, value in dense.metadata.items():
                metadata[f"dense_{key}"] = value

        if sparse is not None:
            weight += alpha_sparse
            snippet_parts.append(sparse.snippet)
            metadata["sparse_id"] = sparse.document_id
            metadata["sparse_score"] = f"{sparse.score:.4f}"
            for key, value in sparse.metadata.items():
                metadata[f"sparse_{key}"] = value

        score = dense_score * alpha_dense + sparse_score * alpha_sparse
        if weight > 0:
            score /= weight

        snippet = " | ".join(snippet_parts) if snippet_parts else ""
        source_url = str(
            dense.source_url
            if dense is not None
            else (
                sparse.source_url
                if sparse is not None
                else "https://example.com/hybrid"
            )
        )

        doc_id_parts = ["hybrid", str(rank_hint)]
        if dense is not None:
            doc_id_parts.append(dense.document_id)
        if sparse is not None:
            doc_id_parts.append(sparse.document_id)
        document_id = "-".join(doc_id_parts)

        return RetrievalHit(
            document_id=document_id,
            score=score,
            method="hybrid",
            snippet=snippet,
            source_url=source_url,
            metadata=metadata,
        )

    def _qdrant_hits(self, query: str, top_k: int) -> Iterable[RetrievalHit]:
        hits = self.connectors.qdrant.search(query, top_k)
        for hit in hits:
            payload = hit.get("payload", {})
            yield RetrievalHit(
                document_id=hit.get("document_id", ""),
                score=float(hit.get("score", 0.0)),
                method="dense",
                snippet=payload.get("snippet", ""),
                source_url=payload.get("source_url", "https://example.com/dense"),
                metadata=payload,
            )

    def _opensearch_hits(self, query: str, top_k: int) -> Iterable[RetrievalHit]:
        hits = self.connectors.opensearch.bm25(query, top_k)
        for hit in hits:
            yield RetrievalHit(
                document_id=hit.get("document_id", ""),
                score=float(hit.get("score", 0.0)),
                method="sparse",
                snippet=hit.get("snippet", ""),
                source_url="https://example.com/sparse",
                metadata={"index": self.config.keyword.index},
            )
