"""Knowledge fabric materialisation pipeline."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .graph.materialise import GraphMaterialiser
from .storage.contracts import ArtefactRecord, CommunitySummary, GraphEdge, GraphNode
from .storage.repositories import GraphStore, KeywordStore, ManifestStore, VectorStore


@dataclass(slots=True)
class MaterialisationResult:
    tenant_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summaries: list[CommunitySummary]


class KnowledgePipeline:
    """Coordinates ingestion of artefacts across storage backends."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        keyword_store: KeywordStore | None = None,
        graph_store: GraphStore | None = None,
        manifest_store: ManifestStore | None = None,
        materialiser: GraphMaterialiser | None = None,
    ) -> None:
        self.vector_store = vector_store or VectorStore()
        self.keyword_store = keyword_store or KeywordStore()
        self.graph_store = graph_store or GraphStore()
        self.manifest_store = manifest_store or ManifestStore()
        self.materialiser = materialiser or GraphMaterialiser()

    def ingest(
        self,
        tenant_id: str,
        artefacts: Iterable[ArtefactRecord],
        graph_version: str = "v1",
    ) -> MaterialisationResult:
        artefact_list = list(artefacts)
        if not artefact_list:
            raise ValueError("At least one artefact required for materialisation")
        self.vector_store.upsert(artefact_list)
        self.keyword_store.upsert(artefact_list)
        graph = self.materialiser.build(artefact_list)
        self.graph_store.write(
            tenant_id,
            nodes=[node.model_dump() for node in graph.nodes],
            edges=[edge.model_dump() for edge in graph.edges],
            communities=[summary.model_dump() for summary in graph.summaries],
        )
        self.manifest_store.write(
            tenant_id=tenant_id,
            artefact_ids=[item.document_id for item in artefact_list],
            graph_version=graph_version,
        )
        return MaterialisationResult(
            tenant_id=tenant_id,
            nodes=graph.nodes,
            edges=graph.edges,
            summaries=graph.summaries,
        )

    def query_hybrid(
        self, tenant_id: str, query: str, top_k: int = 5
    ) -> list[dict[str, str | float]]:
        dense_hits = self.vector_store.query(tenant_id, query, limit=top_k)
        sparse_hits = self.keyword_store.query(tenant_id, query, limit=top_k)
        combined: dict[str, dict[str, str | float]] = {}
        for rank, store_hits in enumerate((dense_hits, sparse_hits)):
            weight = 0.6 if rank == 0 else 0.4
            for item in store_hits:
                payload = combined.setdefault(
                    item.artefact.document_id,
                    {
                        "document_id": item.artefact.document_id,
                        "title": item.artefact.title,
                        "summary": item.artefact.summary,
                        "score": 0.0,
                    },
                )
                payload["score"] = (
                    float(payload.get("score", 0.0)) + item.score * weight
                )
        return sorted(combined.values(), key=lambda item: item["score"], reverse=True)[
            :top_k
        ]

    def community_summaries(
        self, tenant_id: str, limit: int = 3
    ) -> list[CommunitySummary]:
        graph = self.graph_store.get(tenant_id)
        if not graph:
            return []
        summaries = graph.get("communities", [])[:limit]
        return [CommunitySummary(**summary) for summary in summaries]
