"""Service layer for knowledge MCP.

The implementation currently synthesises responses while maintaining signatures that can be
swapped with real vector/keyword/graph backends (Qdrant, OpenSearch, NebulaGraph) later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .config import AppConfig
from .connectors import ConnectorBundle
from .models import (
    CommunitySummariesResponse,
    GraphSummary,
    HybridQueryRequest,
    HybridQueryResponse,
    RankingRequest,
    RankingResponse,
    RetrievalHit,
)


class KnowledgeService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.connectors = ConnectorBundle.from_config(config)

    # ------------------------------------------------------------------
    # Hybrid retrieval
    # ------------------------------------------------------------------
    def hybrid_query(self, payload: HybridQueryRequest) -> HybridQueryResponse:
        dense_hits = list(self._dense_hits(payload.query, payload.top_k))
        if self.connectors.qdrant.client:
            dense_hits = (
                list(self._qdrant_hits(payload.query, payload.top_k)) or dense_hits
            )

        sparse_hits = list(self._sparse_hits(payload.query, payload.top_k))
        if self.connectors.opensearch.client:
            sparse_hits = (
                list(self._opensearch_hits(payload.query, payload.top_k)) or sparse_hits
            )
        combined = self._blend_hits(
            dense_hits,
            sparse_hits,
            payload.top_k,
            payload.alpha_dense,
            payload.alpha_sparse,
        )
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
        return HybridQueryResponse(
            hits=hits, dense_score_weight=0.0, sparse_score_weight=1.0
        )

    def rerank(self, payload: RankingRequest) -> RankingResponse:
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
        return RankingResponse(reranked=reranked)

    # ------------------------------------------------------------------
    # Graph summaries
    # ------------------------------------------------------------------
    def community_summaries(
        self, tenant_id: str, limit: int = 3
    ) -> CommunitySummariesResponse:
        summaries = list(self.connectors.nebula.community_summaries(limit))
        if not summaries:
            summaries = [
                GraphSummary(
                    community_id=f"comm-{i}",
                    title=f"Community {i}",
                    summary=f"Community {i} focuses on premium positioning and market shifts.",
                    representative_nodes=["brand", "competitor", "customer"],
                )
                for i in range(1, limit + 1)
            ]
        return CommunitySummariesResponse(
            generated_at=datetime.now(tz=timezone.utc),
            summaries=summaries,
        )

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
