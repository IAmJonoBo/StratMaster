from __future__ import annotations

from typing import Any

from stratmaster_api.services import (
    EvalsMCPClient,
    KnowledgeMCPClient,
    OrchestratorService,
    ResearchMCPClient,
    RouterMCPClient,
)


class StubResearch(ResearchMCPClient):
    def metasearch(self, query: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        return {
            "results": [
                {"title": "Insight A", "url": "https://example.com/a", "snippet": "A"},
                {"title": "Insight B", "url": "https://example.com/b", "snippet": "B"},
            ][:limit]
        }

    def crawl(self, url: str) -> dict[str, Any]:  # type: ignore[override]
        return {
            "url": url,
            "content": f"content for {url}",
            "sha256": "hash-abc",
            "cache_key": "cache-abc",
        }


class StubKnowledge(KnowledgeMCPClient):
    def hybrid_query(self, tenant_id: str, query: str, top_k: int = 5) -> dict[str, Any]:  # type: ignore[override]
        return {
            "hits": [
                {
                    "document_id": "dense-1",
                    "score": 0.9,
                    "snippet": "Dense hit",
                    "source_url": "https://example.com/dense",
                }
            ]
        }

    def community_summaries(self, tenant_id: str, limit: int = 3) -> dict[str, Any]:  # type: ignore[override]
        return {
            "summaries": [
                {
                    "community_id": "c1",
                    "title": "Premium Movers",
                    "summary": "Focus on premium positioning.",
                    "representative_nodes": ["brand", "customer"],
                }
            ]
        }


class StubRouter(RouterMCPClient):
    def complete(
        self, tenant_id: str, prompt: str, max_tokens: int = 256, task: str = "reasoning"
    ) -> dict[str, Any]:  # type: ignore[override]
        return {
            "text": "Completed recommendation",
            "provider": "local",
            "model": "mixtral",
        }

    def rerank(  # type: ignore[override]
        self,
        tenant_id: str,
        query: str,
        documents: list[dict[str, str]],
        top_k: int,
        task: str = "rerank",
    ) -> dict[str, Any]:
        # reverse order to confirm orchestrator respects rerank results
        ordered = list(reversed(documents))[:top_k]
        return {
            "results": [
                {"id": doc["id"], "score": 1.0 - i * 0.1, "text": doc["text"]}
                for i, doc in enumerate(ordered)
            ]
        }


class StubEvals(EvalsMCPClient):
    def run(self, tenant_id: str, suite: str, thresholds: dict[str, float] | None = None) -> dict[str, Any]:  # type: ignore[override]
        return {"run_id": "eval-1234", "passed": True, "metrics": {"ragas": 0.9}}


class FailingEvals(EvalsMCPClient):
    def run(self, tenant_id: str, suite: str, thresholds: dict[str, float] | None = None) -> dict[str, Any]:  # type: ignore[override]
        return {"run_id": "eval-9999", "passed": False, "metrics": {"ragas": 0.4}}


def test_run_research_reranks_results():
    orchestrator = OrchestratorService(
        research_client=StubResearch(),
        knowledge_client=StubKnowledge(),
        router_client=StubRouter(),
        evals_client=StubEvals(),
    )

    result = orchestrator.run_research(plan_id="plan-1", tenant_id="tenant-a")
    hits = result["retrieval"]
    assert len(hits) == 2
    # router reverses order so last synthetic doc should appear first
    assert hits[0].document_id != hits[1].document_id


def test_generate_recommendation_uses_router_completion():
    orchestrator = OrchestratorService(
        research_client=StubResearch(),
        knowledge_client=StubKnowledge(),
        router_client=StubRouter(),
        evals_client=StubEvals(),
    )
    outcome = orchestrator.generate_recommendation(
        tenant_id="tenant-a",
        cep_id="cep-1",
        jtbd_ids=["jtbd-1"],
        risk_tolerance="medium",
    )
    assert outcome.decision_brief.recommendation.startswith("Completed recommendation")


def test_run_eval_calls_evals_service():
    orchestrator = OrchestratorService(
        research_client=StubResearch(),
        knowledge_client=StubKnowledge(),
        router_client=StubRouter(),
        evals_client=StubEvals(),
    )
    payload = orchestrator.run_eval(tenant_id="tenant-a", suite="rag")
    assert payload["passed"] is True
    assert payload["metrics"]["ragas"] == 0.9


def test_recommendation_blocked_when_evals_fail():
    orchestrator = OrchestratorService(
        research_client=StubResearch(),
        knowledge_client=StubKnowledge(),
        router_client=StubRouter(),
        evals_client=FailingEvals(),
    )
    outcome = orchestrator.generate_recommendation(
        tenant_id="tenant-a",
        cep_id="cep-1",
        jtbd_ids=["jtbd-1"],
        risk_tolerance="medium",
    )
    assert outcome.metrics["evaluation_passed"] == 0.0
    assert "Additional research" in outcome.decision_brief.recommendation
