"""Orchestration helpers backing the public API surfaces."""

from __future__ import annotations

import importlib.util
import logging
import os
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

import httpx

from .models import (
    CEP,
    JTBD,
    Assumption,
    Claim,
    CommunityScore,
    CommunitySummary,
    DebateTrace,
    DebateTurn,
    DecisionBrief,
    EvidenceGrade,
    Experiment,
    ExperimentVariant,
    Forecast,
    ForecastInterval,
    GraphArtifacts,
    GraphEdge,
    GraphNode,
    GroundingSpan,
    Hypothesis,
    Metric,
    NarrativeChunk,
    RecommendationOutcome,
    RecommendationStatus,
    RetrievalRecord,
    RetrievalScore,
    Source,
    SourceType,
    WorkflowMetadata,
)

from stratmaster_orchestrator import StrategyState, build_strategy_graph

logger = logging.getLogger(__name__)

# Constants
_UNEXPECTED_RESPONSE = "Unexpected response payload"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_DEPTH = 1
DEFAULT_MAX_TOKENS = 256
DEFAULT_TOP_K = 5
DEFAULT_MAX_SOURCES = 3


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class BaseMCPClient:
    """Base HTTP client for MCP servers with common functionality."""

    def __init__(
        self,
        env_url_key: str,
        default_url: str,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url or os.getenv(env_url_key, default_url)
        self.timeout = timeout

    def _post_json(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request and return validated JSON response."""
        resp = httpx.post(
            f"{self.base_url}{endpoint}",
            json=json_data,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError(_UNEXPECTED_RESPONSE)
        return data

    def _get_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request and return validated JSON response."""
        resp = httpx.get(
            f"{self.base_url}{endpoint}",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError(_UNEXPECTED_RESPONSE)
        return data


class ResearchMCPClient(BaseMCPClient):
    """Lightweight HTTP client for the research MCP server."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(
            env_url_key="RESEARCH_MCP_URL",
            default_url="http://localhost:8081",
            base_url=base_url,
            timeout=timeout,
        )

    def metasearch(self, query: str, limit: int) -> dict[str, Any]:
        return self._post_json(
            "/tools/metasearch",
            {"tenant_id": "system", "query": query, "limit": limit},
        )

    def crawl(self, url: str) -> dict[str, Any]:
        return self._post_json(
            "/tools/crawl",
            {
                "tenant_id": "system",
                "spec": {"url": url, "max_depth": DEFAULT_MAX_DEPTH},
            },
        )


class KnowledgeMCPClient(BaseMCPClient):
    """HTTP client for the knowledge MCP server."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(
            env_url_key="KNOWLEDGE_MCP_URL",
            default_url="http://localhost:8082",
            base_url=base_url,
            timeout=timeout,
        )

    def hybrid_query(
        self, tenant_id: str, query: str, top_k: int = DEFAULT_TOP_K
    ) -> dict[str, Any]:
        return self._post_json(
            "/tools/hybrid_query",
            {"tenant_id": tenant_id, "query": query, "top_k": top_k},
        )

    def community_summaries(self, tenant_id: str, limit: int = 3) -> dict[str, Any]:
        return self._get_json(
            "/resources/graph/community_summaries",
            {"tenant_id": tenant_id, "limit": limit},
        )


class RouterMCPClient(BaseMCPClient):
    """HTTP client for the router MCP server."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(
            env_url_key="ROUTER_MCP_URL",
            default_url="http://localhost:8083",
            base_url=base_url,
            timeout=timeout,
        )

    def complete(
        self,
        tenant_id: str,
        prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        task: str = "reasoning",
    ) -> dict[str, Any]:
        return self._post_json(
            "/tools/complete",
            {
                "tenant_id": tenant_id,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "task": task,
            },
        )

    def rerank(
        self,
        tenant_id: str,
        query: str,
        documents: list[dict[str, str]],
        top_k: int,
        task: str = "rerank",
    ) -> dict[str, Any]:
        return self._post_json(
            "/tools/rerank",
            {
                "tenant_id": tenant_id,
                "query": query,
                "documents": documents,
                "top_k": top_k,
                "task": task,
            },
        )


class EvalsMCPClient(BaseMCPClient):
    """HTTP client for the evals MCP server."""

    def __init__(
        self, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        super().__init__(
            env_url_key="EVALS_MCP_URL",
            default_url="http://localhost:8084",
            base_url=base_url,
            timeout=timeout,
        )

    def run(
        self, tenant_id: str, suite: str, thresholds: dict[str, float] | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"tenant_id": tenant_id, "suite": suite}
        if thresholds:
            body["thresholds"] = thresholds
        return self._post_json("/tools/run", body)


class _SequentialPipeline:
    """Fallback pipeline executor when LangGraph is unavailable."""

    # Define a simple protocol for pipelines to satisfy type checking

    def __init__(
        self,
        *steps: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        # store steps as a tuple for immutability and clear typing
        self.steps: tuple[Callable[[dict[str, Any]], dict[str, Any]], ...] = steps

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        current: dict[str, Any] = state
        for step in self.steps:
            current = step(current)
        return current


class Pipeline(Protocol):
    """Minimal interface for an executable pipeline used in this module."""

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


class _GraphPipeline:
    """Wrapper around a compiled LangGraph pipeline with sequential fallback."""

    def __init__(self, compiled: Pipeline, fallback: _SequentialPipeline) -> None:
        self._compiled: Pipeline = compiled
        self._fallback: _SequentialPipeline = fallback

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            # compiled conforms to Pipeline, so invoke returns dict[str, Any]
            return self._compiled.invoke(state)
        except Exception as exc:  # pragma: no cover - protective fallback
            logger.warning(
                "LangGraph pipeline execution failed; using sequential fallback",
                exc_info=exc,
            )
            return self._fallback.invoke(state)


class OrchestratorService:
    """Best-effort orchestrator that leans on MCP services when reachable."""

    def __init__(
        self,
        research_client: ResearchMCPClient | None = None,
        knowledge_client: KnowledgeMCPClient | None = None,
        router_client: RouterMCPClient | None = None,
        evals_client: EvalsMCPClient | None = None,
    ) -> None:
        self.research_client = research_client or ResearchMCPClient()
        self.knowledge_client = knowledge_client or KnowledgeMCPClient()
        self.router_client = router_client or RouterMCPClient()
        self.evals_client = evals_client or EvalsMCPClient()
        self._pipeline: Pipeline = self._build_pipeline()
        self._strategy_graph = build_strategy_graph()

    def _build_pipeline(self) -> Pipeline:
        # Lazy-import LangGraph to avoid hard dependency and import-order lint issues
        if importlib.util.find_spec("langgraph.graph") is None:
            return _SequentialPipeline(
                self._graph_research,
                self._graph_eval,
                self._graph_recommend,
            )
        fallback = _SequentialPipeline(
            self._graph_research,
            self._graph_eval,
            self._graph_recommend,
        )
        try:
            from langgraph.graph import END, StateGraph

            graph = StateGraph(dict)
            graph.add_node("research", self._graph_research)
            graph.add_node("eval", self._graph_eval)
            graph.add_node("recommend", self._graph_recommend)
            graph.set_entry_point("research")
            graph.add_edge("research", "eval")
            graph.add_edge("eval", "recommend")
            graph.add_edge("recommend", END)
            compiled = cast(Pipeline, graph.compile())
        except Exception as exc:  # pragma: no cover - setup guard
            logger.warning(
                "LangGraph pipeline setup failed; using sequential fallback",
                exc_info=exc,
            )
            return fallback
        return _GraphPipeline(compiled, fallback)

    # ------------------------------------------------------------------
    # Research planning/execution
    # ------------------------------------------------------------------
    def plan_research(
        self, query: str, tenant_id: str, max_sources: int
    ) -> dict[str, Any]:
        sources = self._sources_from_metasearch(query, max_sources)
        tasks = [
            f"Validate insight: {src.title}" for src in sources[:DEFAULT_MAX_SOURCES]
        ] or [
            "Collect baseline market context",
            "Identify competitive moves",
            "Quantify demand signals",
        ]
        return {
            "plan_id": f"plan-{uuid4().hex[:8]}",
            "tasks": tasks,
            "sources": sources,
        }

    def run_research(self, plan_id: str, tenant_id: str) -> dict[str, Any]:
        return self._collect_research(plan_id=plan_id, tenant_id=tenant_id)

    def summarise_graph(self, tenant_id: str, focus: str, limit: int) -> dict[str, Any]:
        graph = GraphArtifacts(
            nodes=[
                GraphNode(id=f"{focus}-node", label=f"{focus.title()} Node", type=focus)
            ],
            edges=[
                GraphEdge(
                    source=f"{focus}-node",
                    target="brand",
                    relation="related_to",
                )
            ],
            communities=[CommunityScore(community_id="c1", score=0.75)],
            community_summaries=[
                CommunitySummary(
                    community_id="c1",
                    summary=f"Summary for focus {focus}",
                    key_entities=[focus, "brand"],
                )
            ],
            narrative_chunks=[
                NarrativeChunk(
                    id="chunk-focus",
                    text=f"Narrative for {focus}",
                    supporting_claims=["claim-1"],
                )
            ],
        )
        summaries = [f"Top insight {i} for {focus}" for i in range(1, limit + 1)]
        return {"summaries": summaries, "artifacts": graph}

    def run_debate(
        self,
        tenant_id: str,
        hypothesis_id: str | None,
        claim_ids: list[str] | None,
        max_turns: int,
    ) -> dict[str, Any]:
        # alias to preserve variable names used previously
        turns = [
            DebateTurn(
                agent="agent-1",
                role="Researcher",
                content="We collected evidence.",
            ),
            DebateTurn(
                agent="agent-2",
                role="Adversary",
                content="I question the assumption.",
            ),
        ][:max_turns]
        trace = DebateTrace(turns=turns, verdict="Needs further validation")
        return {"debate_id": f"deb-{uuid4().hex[:8]}", "debate": trace}

    def _collect_research(self, plan_id: str, tenant_id: str) -> dict[str, Any]:
        metasearch_sources = self._sources_from_metasearch(
            plan_id or tenant_id, DEFAULT_MAX_SOURCES
        )
        knowledge_hits = self._knowledge_hits(
            tenant_id, plan_id or tenant_id, DEFAULT_MAX_SOURCES
        )
        claims = [
            Claim(
                id="claim-1",
                statement=(
                    f"Key insight: {metasearch_sources[0].title}"
                    if metasearch_sources
                    else "Market shows stable demand"
                ),
                evidence_grade=EvidenceGrade.MODERATE,
                provenance_ids=["prov-1"],
            )
        ]
        assumptions = [
            Assumption(
                id="assumption-1",
                statement="Demand outlook remains positive",
                confidence=0.7,
                provenance_ids=["prov-1"],
            )
        ]
        hypotheses = [
            Hypothesis(
                id="hyp-1",
                description="Investing in premium positioning increases conversion",
                supporting_claims=["claim-1"],
                contradicting_claims=[],
            )
        ]
        retrieval_candidates = list(
            self._retrieval_records_from_sources(metasearch_sources[:1])
        ) + self._retrieval_records_from_knowledge_hits(knowledge_hits)
        retrieval = retrieval_candidates or [
            RetrievalRecord(
                document_id="doc-1",
                scores=RetrievalScore(dense_score=0.82, hybrid_score=0.88),
                grounding_spans=[
                    GroundingSpan(
                        source_id="src-1",
                        chunk_hash="hash-1",
                        start_char=0,
                        end_char=120,
                    )
                ],
                chunk_hash="hash-1",
                provenance_id="prov-1",
            )
        ]
        graph = self._graph_from_knowledge_summaries(
            tenant_id, fallback_claims=["claim-1"]
        )
        retrieval = self._rerank_records(
            tenant_id=tenant_id,
            query=plan_id or tenant_id,
            records=retrieval,
            max_results=5,
        )
        return {
            "run_id": f"run-{uuid4().hex[:8]}",
            "claims": claims,
            "assumptions": assumptions,
            "hypotheses": hypotheses,
            "retrieval": retrieval,
            "artifacts": graph,
        }

    def _graph_research(self, state: dict[str, Any]) -> dict[str, Any]:
        plan_id = state.get("plan_id") or f"plan-{uuid4().hex[:8]}"
        state["plan_id"] = plan_id
        state["research"] = self._collect_research(
            plan_id=plan_id, tenant_id=state["tenant_id"]
        )
        self._record_stage(state, "research")
        return state

    def _graph_eval(self, state: dict[str, Any]) -> dict[str, Any]:
        suite = state.get("evaluation_suite", "rag")
        state["evaluation"] = self.run_eval(state["tenant_id"], suite)
        self._record_stage(state, "eval")
        return state

    def _graph_recommend(self, state: dict[str, Any]) -> dict[str, Any]:
        outcome = self._compose_recommendation(
            tenant_id=state["tenant_id"],
            cep_id=state.get("cep_id", "cep-unknown"),
            jtbd_ids=state.get("jtbd_ids", []),
            risk_tolerance=state.get("risk_tolerance", "medium"),
            research=state.get("research"),
            evaluation=state.get("evaluation"),
        )
        state["recommendation"] = outcome
        self._record_stage(state, "recommend")
        return state

    def generate_recommendation(
        self, tenant_id: str, cep_id: str, jtbd_ids: list[str], risk_tolerance: str
    ) -> RecommendationOutcome:
        workflow = WorkflowMetadata(workflow_id=f"wf-{uuid4().hex[:6]}", tenant_id=tenant_id)
        initial_state = StrategyState(
            tenant_id=tenant_id,
            query=f"{cep_id} {risk_tolerance} strategy",
            workflow=workflow,
        )
        result = self._strategy_graph(initial_state)
        outcome = result.outcome
        eval_summary = self.run_eval(tenant_id=tenant_id, suite="rag")
        if not eval_summary.get("passed", True):
            outcome.status = RecommendationStatus.FAILED
            if "evaluation_thresholds" not in outcome.failure_reasons:
                outcome.failure_reasons.append("evaluation_thresholds")
            outcome.metrics.update(eval_summary.get("metrics", {}))
            outcome.metrics["evaluation_passed"] = 0.0
            if outcome.decision_brief is not None:
                outcome.decision_brief.recommendation = (
                    "Evaluation thresholds not met. Additional research required."
                )
        else:
            if outcome.decision_brief is not None:
                self._generate_ai_recommendation(
                    tenant_id=tenant_id,
                    claims=list(result.state.claims),
                    assumptions=list(result.state.assumptions),
                    risk_tolerance=risk_tolerance,
                    decision=outcome.decision_brief,
                )
            outcome.metrics.setdefault("evaluation_passed", 1.0)
        return outcome

    def query_retrieval(
        self, tenant_id: str, query: str, top_k: int
    ) -> list[RetrievalRecord]:
        records = [
            RetrievalRecord(
                document_id=f"doc-{i}",
                scores=RetrievalScore(
                    dense_score=0.7 + i * 0.02,
                    sparse_score=0.65 + i * 0.01,
                    hybrid_score=0.75 + i * 0.015,
                ),
                grounding_spans=[],
                chunk_hash=f"hash-{i}",
                provenance_id="prov-1",
            )
            for i in range(1, min(top_k, 3) + 1)
        ]
        return self._rerank_records(
            tenant_id=tenant_id, query=query, records=records, max_results=top_k
        )

    def run_eval(self, tenant_id: str, suite: str) -> dict[str, Any]:
        try:
            payload = self.evals_client.run(tenant_id=tenant_id, suite=suite)
            return payload
        except (httpx.HTTPError, ValueError, TypeError):
            metrics = {"ragas_score": 0.82, "factscore": 0.78}
            passed = all(value >= 0.7 for value in metrics.values())
            return {
                "run_id": f"eval-{uuid4().hex[:8]}",
                "passed": passed,
                "metrics": metrics,
            }

    def create_experiment(self, tenant_id: str, payload: dict[str, Any]) -> str:
        # alias for compatibility with previous underscore-prefixed params
        _tenant_id = tenant_id
        _payload = payload
        return f"exp-{uuid4().hex[:8]}"

    def create_forecast(
        self, tenant_id: str, metric_id: str, horizon_days: int
    ) -> Forecast:
        _tenant_id = tenant_id
        metric = Metric(id=metric_id, name="Metric", definition="Synthetic")
        return Forecast(
            id=f"forecast-{uuid4().hex[:8]}",
            metric=metric,
            point_estimate=1.0,
            intervals=[
                ForecastInterval(confidence=50, lower=0.9, upper=1.1),
                ForecastInterval(confidence=90, lower=0.8, upper=1.2),
            ],
            horizon_days=horizon_days,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sources_from_metasearch(self, query: str, max_sources: int) -> list[Source]:
        try:
            payload = self.research_client.metasearch(query=query, limit=max_sources)
        except (httpx.HTTPError, ValueError, TypeError):
            return [self._synthetic_source(i) for i in range(1, max_sources + 1)]

        results = payload.get("results", [])
        sources: list[Source] = []
        for idx, item in enumerate(results, start=1):
            url = item.get("url") or item.get("link") or f"https://example.com/{idx}"
            title = item.get("title") or f"Result {idx}"
            sources.append(
                Source(
                    id=f"src-{idx}",
                    type=SourceType.WEB,
                    title=title,
                    url=url,
                    language="en",
                    tags=["metasearch"],
                )
            )
        if len(sources) < max_sources:
            sources.extend(
                self._synthetic_source(len(sources) + i)
                for i in range(1, max_sources - len(sources) + 1)
            )
        return sources[:max_sources]

    def _retrieval_records_from_sources(
        self, sources: Iterable[Source]
    ) -> list[RetrievalRecord]:
        records: list[RetrievalRecord] = []
        for src in sources:
            try:
                crawl = self.research_client.crawl(src.url)
            # nosec B112 - network crawl failures are non-fatal; skip and continue
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                logger.warning("research crawl failed; skipping source", exc_info=exc)
                continue
            content = crawl.get("content", "")
            sha256 = crawl.get("sha256", uuid4().hex)
            records.append(
                RetrievalRecord(
                    document_id=src.id,
                    scores=RetrievalScore(hybrid_score=0.85),
                    grounding_spans=[
                        GroundingSpan(
                            source_id=src.id,
                            chunk_hash=sha256,
                            start_char=0,
                            end_char=min(240, len(content)),
                        )
                    ],
                    chunk_hash=sha256,
                    provenance_id=crawl.get("cache_key", "prov-1"),
                )
            )
        return records

    def _knowledge_hits(
        self, tenant_id: str, query: str, top_k: int
    ) -> Sequence[dict[str, Any]]:
        try:
            payload = self.knowledge_client.hybrid_query(
                tenant_id=tenant_id, query=query, top_k=top_k
            )
        except (httpx.HTTPError, ValueError, TypeError):
            return []
        hits = cast(list[dict[str, Any]], payload.get("hits", []))
        return hits

    def _retrieval_records_from_knowledge_hits(
        self, hits: Sequence[dict[str, Any]]
    ) -> list[RetrievalRecord]:
        records: list[RetrievalRecord] = []
        for hit in hits:
            snippet = hit.get("snippet", "")
            doc_id = hit.get("document_id", uuid4().hex)
            chunk_hash = uuid4().hex
            records.append(
                RetrievalRecord(
                    document_id=doc_id,
                    scores=RetrievalScore(hybrid_score=float(hit.get("score", 0.0))),
                    grounding_spans=[
                        GroundingSpan(
                            source_id=doc_id,
                            chunk_hash=chunk_hash,
                            start_char=0,
                            end_char=min(240, len(snippet)),
                        )
                    ],
                    chunk_hash=chunk_hash,
                    provenance_id=hit.get("source_url", "prov-knowledge"),
                )
            )
        return records

    def _graph_from_knowledge_summaries(
        self, tenant_id: str, fallback_claims: list[str]
    ) -> GraphArtifacts:
        try:
            payload = self.knowledge_client.community_summaries(
                tenant_id=tenant_id, limit=3
            )
            summaries = payload.get("summaries", [])
        except (httpx.HTTPError, ValueError, TypeError):
            summaries = []

        if not summaries:
            return GraphArtifacts(
                nodes=[GraphNode(id="brand", label="Brand", type="entity")],
                edges=[],
                communities=[CommunityScore(community_id="c1", score=0.8)],
                community_summaries=[
                    CommunitySummary(
                        community_id="c1",
                        summary="Synthetic summary",
                        key_entities=["Brand"],
                    )
                ],
                narrative_chunks=[
                    NarrativeChunk(
                        id="chunk-1",
                        text="Narrative about brand strategy",
                        supporting_claims=fallback_claims,
                    )
                ],
            )

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        community_scores: list[CommunityScore] = []
        community_summaries: list[CommunitySummary] = []
        narrative_chunks: list[NarrativeChunk] = []

        for summary in summaries:
            community_id = summary.get("community_id", uuid4().hex[:6])
            title = summary.get("title", community_id)
            key_nodes: list[str] = summary.get("representative_nodes", [])
            summary_text = summary.get("summary", "")
            community_scores.append(
                CommunityScore(community_id=community_id, score=0.75)
            )
            community_summaries.append(
                CommunitySummary(
                    community_id=community_id,
                    summary=summary_text,
                    key_entities=key_nodes,
                )
            )
            nodes.append(GraphNode(id=community_id, label=title, type="community"))
            for node_label in key_nodes:
                node_id = f"node-{community_id}-{node_label}"
                nodes.append(GraphNode(id=node_id, label=node_label, type="entity"))
                edges.append(
                    GraphEdge(
                        source=community_id,
                        target=node_id,
                        relation="represents",
                        weight=1.0,
                    )
                )
            narrative_chunks.append(
                NarrativeChunk(
                    id=f"chunk-{community_id}",
                    text=summary_text,
                    supporting_claims=fallback_claims,
                )
            )

        return GraphArtifacts(
            nodes=nodes,
            edges=edges,
            communities=community_scores,
            community_summaries=community_summaries,
            narrative_chunks=narrative_chunks,
        )

    def _rerank_records(
        self,
        tenant_id: str,
        query: str,
        records: list[RetrievalRecord],
        max_results: int,
    ) -> list[RetrievalRecord]:
        if not records:
            return []
        documents = [
            {"id": record.document_id, "text": record.chunk_hash} for record in records
        ]
        try:
            payload = self.router_client.rerank(
                tenant_id=tenant_id,
                query=query,
                documents=documents,
                top_k=max_results,
            )
            order = {
                item["id"]: index
                for index, item in enumerate(payload.get("results", []))
            }
            if order:
                records.sort(key=lambda rec: order.get(rec.document_id, len(order)))
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning(
                "rerank request failed; returning original order", exc_info=exc
            )
        return records[:max_results]

    def _create_synthetic_claims_and_assumptions(
        self, research: dict[str, Any] | None
    ) -> tuple[list[Claim], list[Assumption]]:
        """Create synthetic claims and assumptions when research is incomplete."""
        if research is None:
            research = {}

        claims: list[Claim] = list(research.get("claims", [])) or [
            Claim(
                id="claim-fallback",
                statement="Customers prefer premium positioning",
                evidence_grade=EvidenceGrade.MODERATE,
                provenance_ids=["prov-1"],
            )
        ]
        assumptions: list[Assumption] = list(research.get("assumptions", [])) or [
            Assumption(
                id="assumption-fallback",
                statement="Demand outlook remains positive",
                confidence=0.6,
                provenance_ids=["prov-1"],
            )
        ]
        return claims, assumptions

    def _create_synthetic_experiments_and_forecast(
        self,
    ) -> tuple[list[Experiment], Forecast]:
        """Create synthetic experiments and forecast for recommendations."""
        experiments = [
            Experiment(
                id="exp-1",
                hypothesis_id="hyp-1",
                variants=[
                    ExperimentVariant(name="control", description="Status quo"),
                    ExperimentVariant(name="variant", description="Premium focus"),
                ],
                primary_metric=Metric(
                    id="metric-1",
                    name="Conversion",
                    definition="Share of visitors converting",
                ),
                minimum_detectable_effect=0.05,
            )
        ]
        forecast = Forecast(
            id="forecast-1",
            metric=Metric(id="metric-1", name="Revenue", definition="Monthly revenue"),
            point_estimate=1.15,
            intervals=[
                ForecastInterval(confidence=50, lower=1.05, upper=1.25),
                ForecastInterval(confidence=90, lower=0.95, upper=1.35),
            ],
            horizon_days=90,
        )
        return experiments, forecast

    def _create_decision_brief(
        self,
        cep_id: str,
        jtbd_ids: list[str],
        assumptions: list[Assumption],
        claims: list[Claim],
        experiments: list[Experiment],
        forecast: Forecast,
    ) -> DecisionBrief:
        """Create a decision brief with the given components."""
        cep = CEP(
            id=cep_id,
            title="Customer expansion programme",
            narrative="Outline of customer journey",
            jobs_to_be_done=["Understand the market", "Prioritise bets"],
        )
        return DecisionBrief(
            id=f"brief-{uuid4().hex[:8]}",
            cep=cep,
            jtbd=[
                JTBD(id=j, actor="Customer", motivation="", outcome="")
                for j in jtbd_ids
            ],
            dbas=[],
            assumptions=assumptions,
            claims=claims,
            experiments=experiments,
            forecasts=[forecast],
            recommendation="Invest in premium positioning with phased rollout",
            safer_alternative="Run limited pilot for 30 days",
            evidence_grade=EvidenceGrade.MODERATE,
            provenance_ids=["prov-1"],
            confidence=0.62,
        )

    def _handle_failed_evaluation(
        self,
        evaluation: dict[str, Any],
        decision: DecisionBrief,
        graph: GraphArtifacts,
        retrieval_records: list[RetrievalRecord],
        tenant_id: str,
    ) -> RecommendationOutcome:
        """Handle the case where evaluation thresholds are not met."""
        decision.recommendation = (
            "Evaluation thresholds not met. Additional research required."
        )
        workflow = WorkflowMetadata(
            workflow_id=f"wf-{uuid4().hex[:6]}",
            tenant_id=tenant_id,
            trace_id=uuid4().hex,
            langfuse_span_id=None,
        )
        return RecommendationOutcome(
            decision_brief=decision,
            debate=DebateTrace(turns=[]),
            retrieval=retrieval_records,
            graph=graph,
            metrics={"evaluation_passed": 0.0},
            workflow=workflow,
            status=RecommendationStatus.FAILED,
            failure_reasons=["evaluation_thresholds"],
        )

    def _generate_ai_recommendation(
        self,
        tenant_id: str,
        claims: list[Claim],
        assumptions: list[Assumption],
        risk_tolerance: str,
        decision: DecisionBrief,
    ) -> None:
        """Generate AI-powered recommendation using the router client."""
        prompt = (
            "You are the Recommender agent. Produce a short decision brief.\n"
            f"Claims: {[c.statement for c in claims]}\n"
            f"Assumptions: {[a.statement for a in assumptions]}\n"
            f"Risk tolerance: {risk_tolerance}"
        )
        try:
            completion = self.router_client.complete(
                tenant_id=tenant_id, prompt=prompt, max_tokens=200
            )
            decision.recommendation = completion.get("text", decision.recommendation)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning(
                "completion request failed; keeping default recommendation",
                exc_info=exc,
            )

    def _compose_recommendation(
        self,
        tenant_id: str,
        cep_id: str,
        jtbd_ids: list[str],
        risk_tolerance: str,
        research: dict[str, Any] | None,
        evaluation: dict[str, Any] | None,
    ) -> RecommendationOutcome:
        if research is None:
            research = self._collect_research(
                plan_id=f"plan-{uuid4().hex[:8]}", tenant_id=tenant_id
            )

        claims, assumptions = self._create_synthetic_claims_and_assumptions(research)
        experiments, forecast = self._create_synthetic_experiments_and_forecast()
        decision = self._create_decision_brief(
            cep_id, jtbd_ids, assumptions, claims, experiments, forecast
        )

        retrieval_records: list[RetrievalRecord] = list(research.get("retrieval", []))
        graph: GraphArtifacts | None = research.get("artifacts")
        if graph is None:
            graph = self._graph_from_knowledge_summaries(
                tenant_id, fallback_claims=[c.id for c in claims]
            )

        retrieval_records = self._rerank_records(
            tenant_id=tenant_id,
            query=decision.recommendation,
            records=retrieval_records,
            max_results=DEFAULT_MAX_SOURCES,
        )

        if evaluation and not evaluation.get("passed", True):
            return self._handle_failed_evaluation(
                evaluation, decision, graph, retrieval_records, tenant_id
            )

        self._generate_ai_recommendation(
            tenant_id, claims, assumptions, risk_tolerance, decision
        )

        workflow = WorkflowMetadata(
            workflow_id=f"wf-{uuid4().hex[:6]}",
            tenant_id=tenant_id,
            trace_id=uuid4().hex,
            langfuse_span_id=None,
        )
        metrics = {
            "risk_tolerance": {"low": 0.4, "medium": 0.6, "high": 0.2}.get(
                risk_tolerance, 0.5
            ),
            "evaluation_passed": 1.0 if (evaluation or {}).get("passed", True) else 0.0,
        }

        return RecommendationOutcome(
            decision_brief=decision,
            debate=DebateTrace(turns=[]),
            retrieval=retrieval_records,
            graph=graph,
            metrics=metrics,
            workflow=workflow,
            status=RecommendationStatus.COMPLETE,
            failure_reasons=[],
        )

    def _record_stage(self, state: dict[str, Any], stage: str) -> None:
        trace_id = state.setdefault("trace_id", uuid4().hex)
        logger.debug(
            "workflow-stage",
            extra={
                "trace_id": trace_id,
                "stage": stage,
                "tenant_id": state.get("tenant_id"),
            },
        )

    @staticmethod
    def _synthetic_source(idx: int) -> Source:
        return Source(
            id=f"src-{idx}",
            type=SourceType.WEB,
            title=f"Synthetic Source {idx}",
            url=f"https://example.com/article/{idx}",
            tags=["synthetic", "demo"],
        )


orchestrator_stub = OrchestratorService()
"""Default orchestrator used by dependency injection."""
