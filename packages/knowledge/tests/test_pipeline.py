from __future__ import annotations

from datetime import datetime
from pathlib import Path

from knowledge import ArtefactRecord, KnowledgePipeline
from knowledge.storage.repositories import (
    GraphStore,
    KeywordStore,
    ManifestStore,
    VectorStore,
)


def _create_pipeline(tmp_path: Path) -> KnowledgePipeline:
    vector = VectorStore(tmp_path / "vectors")
    keyword = KeywordStore(tmp_path / "keywords")
    graph = GraphStore(tmp_path / "graph")
    manifest = ManifestStore(tmp_path / "manifests")
    return KnowledgePipeline(
        vector_store=vector,
        keyword_store=keyword,
        graph_store=graph,
        manifest_store=manifest,
    )


def test_ingest_materialises_graph(tmp_path: Path) -> None:
    pipeline = _create_pipeline(tmp_path)
    artefacts = [
        ArtefactRecord.from_text(
            tenant_id="tenant-a",
            document_id="doc-1",
            title="Premium tier roadmap",
            summary="Focus on premium positioning for strategic accounts",
            fingerprint="hash-1",
            source="analyst",
            sast=datetime(2024, 1, 1),
            tags=["premium", "roadmap"],
        ),
        ArtefactRecord.from_text(
            tenant_id="tenant-a",
            document_id="doc-2",
            title="Operational excellence playbook",
            summary="Improve retention through journey diagnostics and JTBD mapping",
            fingerprint="hash-2",
            source="ops",
            sast=datetime(2024, 1, 2),
            tags=["retention", "diagnostics"],
        ),
    ]

    result = pipeline.ingest("tenant-a", artefacts, graph_version="v2")

    assert result.tenant_id == "tenant-a"
    assert len(result.nodes) >= 2
    assert len(result.edges) >= 2
    assert result.summaries, "summaries should be materialised"

    manifest = pipeline.manifest_store.get("tenant-a")
    assert manifest is not None
    assert manifest.graph_version == "v2"
    assert set(manifest.artefact_ids) == {"doc-1", "doc-2"}

    persisted_graph = pipeline.graph_store.get("tenant-a")
    assert persisted_graph is not None
    assert len(persisted_graph["nodes"]) == len(result.nodes)


def test_hybrid_query_merges_dense_and_sparse(tmp_path: Path) -> None:
    pipeline = _create_pipeline(tmp_path)
    artefact = ArtefactRecord.from_text(
        tenant_id="tenant-b",
        document_id="doc-3",
        title="Customer journey analysis",
        summary="Detailed journey diagnostics for premium customers",
        fingerprint="hash-3",
        source="research",
        tags=["diagnostics", "premium"],
    )
    pipeline.ingest("tenant-b", [artefact])

    hits = pipeline.query_hybrid("tenant-b", query="premium diagnostics", top_k=5)

    assert hits
    assert hits[0]["document_id"] == "doc-3"
    assert hits[0]["score"] > 0


def test_community_summaries_returns_materialised_items(tmp_path: Path) -> None:
    pipeline = _create_pipeline(tmp_path)
    artefact = ArtefactRecord.from_text(
        tenant_id="tenant-c",
        document_id="doc-4",
        title="Retention programme",
        summary="Increase loyalty with concierge onboarding",
        fingerprint="hash-4",
        source="ops",
        tags=["retention", "loyalty"],
    )
    pipeline.ingest("tenant-c", [artefact])

    summaries = pipeline.community_summaries("tenant-c", limit=1)
    assert len(summaries) == 1
    assert summaries[0].community_id.startswith("comm-")
