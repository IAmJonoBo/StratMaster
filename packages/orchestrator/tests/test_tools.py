from datetime import UTC, datetime

from stratmaster_api.models import (
    Claim,
    EvidenceGrade,
    Source,
    SourceType,
)

from stratmaster_orchestrator.tools import ToolRegistry


class StubResearchClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def metasearch(self, query: str, limit: int) -> dict:
        self.calls.append((query, limit))
        return {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/one",
                    "language": "en",
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/two",
                    "language": "en",
                },
            ]
        }


class StubKnowledgeClient:
    def __init__(self) -> None:
        self.hybrid_invocations: list[tuple[str, str, int]] = []
        self.summary_invocations: list[tuple[str, int]] = []

    def hybrid_query(self, tenant_id: str, query: str, top_k: int) -> dict:
        self.hybrid_invocations.append((tenant_id, query, top_k))
        return {
            "hits": [
                {
                    "document_id": "doc-1",
                    "score": 0.91,
                    "metadata": {
                        "chunk_hash": "chunk-doc-1",
                        "provenance_id": "prov-doc-1",
                        "dense_score": 0.9,
                        "sparse_score": 0.88,
                        "hybrid_score": 0.93,
                        "reranker_score": 0.87,
                    },
                }
            ],
            "dense_score_weight": 0.6,
            "sparse_score_weight": 0.4,
        }

    def community_summaries(self, tenant_id: str, limit: int) -> dict:
        self.summary_invocations.append((tenant_id, limit))
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "summaries": [
                {
                    "community_id": "c1",
                    "title": "Key Cluster",
                    "summary": "Cluster narrative",
                    "representative_nodes": ["alpha", "beta"],
                }
            ],
        }


class StubEvalsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, float] | None]] = []

    def run(
        self,
        tenant_id: str,
        suite: str,
        thresholds: dict[str, float] | None = None,
    ) -> dict:
        self.calls.append((tenant_id, suite, thresholds))
        return {
            "run_id": "eval-1234",
            "passed": True,
            "metrics": {"ragas_score": 0.92, "factscore": 0.81},
        }


def _make_source(source_id: str = "src-1") -> Source:
    return Source(
        id=source_id,
        type=SourceType.WEB,
        title="Example Source",
        url="https://example.com",
        language="en",
    )


def _make_claim(claim_id: str = "claim-1") -> Claim:
    return Claim(
        id=claim_id,
        statement="Insight grounded in customer data",
        evidence_grade=EvidenceGrade.HIGH,
        provenance_ids=["prov-doc-1"],
    )


def test_tool_registry_metasearch_prefers_mcp_results() -> None:
    research = StubResearchClient()
    registry = ToolRegistry(
        "tenant-1", "market expansion", research_client=research
    )

    sources, invocation = registry.metasearch(limit=2)

    assert research.calls == [("market expansion", 2)]
    assert len(sources) == 2
    assert invocation.response["source"] == "research-mcp"
    assert sources[0].title == "Result 1"


def test_tool_registry_crawl_and_embed_uses_knowledge_hits() -> None:
    knowledge = StubKnowledgeClient()
    registry = ToolRegistry(
        "tenant-9", "pricing strategy", knowledge_client=knowledge
    )

    records, invocation = registry.crawl_and_embed([_make_source()])

    assert knowledge.hybrid_invocations == [("tenant-9", "pricing strategy", 1)]
    assert len(records) == 1
    record = records[0]
    assert record.document_id == "doc-1"
    assert record.chunk_hash == "chunk-doc-1"
    assert record.scores.hybrid_score == 0.93
    assert invocation.response["source"] == "knowledge-mcp"


def test_tool_registry_graph_artifacts_from_community_summaries() -> None:
    knowledge = StubKnowledgeClient()
    registry = ToolRegistry(
        "tenant-2", "brand moat", knowledge_client=knowledge
    )

    artifacts = registry.graph_artifacts([_make_claim()])

    assert knowledge.summary_invocations == [("tenant-2", 1)]
    assert any(node.id.startswith("community-") for node in artifacts.nodes)
    assert artifacts.community_summaries[0].summary == "Cluster narrative"


def test_tool_registry_run_evaluations_via_evals_client() -> None:
    evals = StubEvalsClient()
    registry = ToolRegistry(
        "tenant-7", "expansion plan", evals_client=evals
    )

    metrics, invocation = registry.run_evaluations(
        "rag-safety", thresholds={"ragas_score": 0.8}
    )

    assert evals.calls == [("tenant-7", "rag-safety", {"ragas_score": 0.8})]
    assert metrics == {"ragas_score": 0.92, "factscore": 0.81}
    assert invocation.response["source"] == "evals-mcp"
    assert invocation.response["run_id"] == "eval-1234"
