# ruff: noqa: I001
"""Deterministic tool mediation layer for LangGraph agents."""

from __future__ import annotations

import importlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

from stratmaster_api.models import (
    CEP,
    Assumption,
    Claim,
    CommunityScore,
    CommunitySummary,
    DebateTrace,
    DecisionBrief,
    EvidenceGrade,
    GraphArtifacts,
    GraphEdge,
    GraphNode,
    GroundingSpan,
    NarrativeChunk,
    RecommendationOutcome,
    RecommendationStatus,
    RetrievalRecord,
    RetrievalScore,
    Source,
    SourceType,
    WorkflowMetadata,
)

from .state import StrategyState, ToolInvocation


class ResearchClient(Protocol):
    """Minimal protocol covering the Research MCP client surface we need."""

    def metasearch(self, query: str, limit: int) -> Mapping[str, Any]:
        ...


class KnowledgeClient(Protocol):
    """Minimal protocol covering the Knowledge MCP client surface we need."""

    def hybrid_query(self, tenant_id: str, query: str, top_k: int) -> Mapping[str, Any]:
        ...

    def community_summaries(self, tenant_id: str, limit: int) -> Mapping[str, Any]:
        ...


class EvalsClient(Protocol):
    """Minimal protocol covering the Evals MCP client surface we need."""

    def run(
        self,
        tenant_id: str,
        suite: str,
        thresholds: Mapping[str, float] | None = None,
    ) -> Mapping[str, Any]:
        ...


def run_cove(*args: Any, **kwargs: Any) -> object:
    """Invoke stratmaster_cove.run_cove if available, else return a placeholder.

    This keeps the orchestrator optional. When the verification package is not installed,
    we degrade gracefully without raising import errors.
    """
    try:  # pragma: no cover - optional dependency
        mod = importlib.import_module("stratmaster_cove")
        _run_cove = getattr(mod, "run_cove", None)
        if callable(_run_cove):
            return _run_cove(*args, **kwargs)
        return {"status": "verification_unavailable"}
    except (ImportError, AttributeError):

        class _FallbackVerification:
            status = "skipped"
            verified_fraction = 0.0

        return _FallbackVerification()


@dataclass(frozen=True)
class EvaluationGate:
    """Thresholds for evaluation metrics before recommendations are emitted."""

    minimums: Mapping[str, float]

    def check(self, metrics: Mapping[str, float]) -> tuple[bool, list[str]]:
        failures: list[str] = []
        for name, threshold in self.minimums.items():
            value = metrics.get(name)
            if value is None or value < threshold:
                failures.append(f"{name}<{threshold:.2f}")
        return (not failures, failures)


class ToolRegistry:
    """Tool mediation layer that prefers MCP clients and falls back to stubs."""

    def __init__(
        self,
        tenant_id: str,
        query: str,
        *,
        research_client: ResearchClient | None = None,
        knowledge_client: KnowledgeClient | None = None,
        evals_client: EvalsClient | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.query = query
        self._research_client = research_client or self._load_default_client(
            "ResearchMCPClient"
        )
        self._knowledge_client = knowledge_client or self._load_default_client(
            "KnowledgeMCPClient"
        )
        self._evals_client = evals_client or self._load_default_client(
            "EvalsMCPClient"
        )

    @staticmethod
    def _load_default_client(name: str) -> Any | None:
        """Best-effort factory that instantiates API MCP clients when available."""

        try:
            services = importlib.import_module("stratmaster_api.services")
        except Exception:  # pragma: no cover - optional dependency
            return None
        client_cls = getattr(services, name, None)
        if client_cls is None:
            return None
        try:
            return client_cls()
        except Exception:  # pragma: no cover - constructor guards
            return None

    @staticmethod
    def _coerce_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _synthetic_metasearch(
        self, limit: int
    ) -> tuple[list[Source], ToolInvocation]:
        sources = [
            Source(
                id=f"src-{idx}",
                type=SourceType.WEB,
                title=f"{self.query.title()} insight {idx}",
                url=f"https://example.com/{self.query.replace(' ', '-')}/{idx}",
                language="en",
                tags=["metasearch", self.query.split()[0]],
            )
            for idx in range(1, limit + 1)
        ]
        invocation = ToolInvocation(
            name="research.metasearch",
            arguments={"query": self.query, "limit": limit},
            response={"results": len(sources), "source": "synthetic"},
        )
        return sources, invocation

    def metasearch(self, limit: int = 3) -> tuple[list[Source], ToolInvocation]:
        if self._research_client is None:
            return self._synthetic_metasearch(limit)

        try:
            response = self._research_client.metasearch(self.query, limit)
            raw_results = response.get("results", [])
        except Exception:
            return self._synthetic_metasearch(limit)

        sources: list[Source] = []
        for idx, payload in enumerate(raw_results, start=1):
            title = payload.get("title")
            url = payload.get("url")
            if not title or not url:
                continue
            language_raw = payload.get("language")
            sources.append(
                Source(
                    id=f"mcp-src-{idx}",
                    type=SourceType.WEB,
                    title=title,
                    url=str(url),
                    language=(str(language_raw) if language_raw is not None else None),
                    tags=["metasearch", self.query.split()[0]],
                )
            )

        if not sources:
            return self._synthetic_metasearch(limit)

        invocation = ToolInvocation(
            name="research.metasearch",
            arguments={"query": self.query, "limit": limit},
            response={
                "results": len(sources),
                "source": "research-mcp",
                "raw_count": len(raw_results),
            },
        )
        return sources, invocation

    def _synthetic_crawl_and_embed(
        self, sources: list[Source]
    ) -> tuple[list[RetrievalRecord], ToolInvocation]:
        records: list[RetrievalRecord] = []
        for idx, source in enumerate(sources, start=1):
            chunk_hash = f"hash-{source.id}-{idx}"
            records.append(
                RetrievalRecord(
                    document_id=source.id,
                    scores=RetrievalScore(
                        dense_score=0.72 + idx * 0.03,
                        sparse_score=0.68 + idx * 0.02,
                        hybrid_score=0.75 + idx * 0.025,
                        reranker_score=0.7 + idx * 0.01,
                    ),
                    grounding_spans=[
                        GroundingSpan(
                            source_id=source.id,
                            chunk_hash=chunk_hash,
                            start_char=0,
                            end_char=160,
                        )
                    ],
                    chunk_hash=chunk_hash,
                    provenance_id=f"prov-{source.id}",
                )
            )
        invocation = ToolInvocation(
            name="knowledge.hybrid_query",
            arguments={"query": self.query, "top_k": len(records)},
            response={"records": len(records), "source": "synthetic"},
        )
        return records, invocation

    def synthesise_claims(self, sources: Iterable[Source]) -> list[Claim]:
        claims: list[Claim] = []
        for idx, source in enumerate(sources, start=1):
            grade = EvidenceGrade.HIGH if idx == 1 else EvidenceGrade.MODERATE
            claims.append(
                Claim(
                    id=f"claim-{idx}",
                    statement=f"{self.query.title()} insight confirmed by {source.title}",
                    evidence_grade=grade,
                    provenance_ids=[f"prov-{source.id}"],
                )
            )
        return claims

    def synthesise_assumptions(self, claims: Iterable[Claim]) -> list[Assumption]:
        assumptions: list[Assumption] = []
        for idx, claim in enumerate(claims, start=1):
            assumptions.append(
                Assumption(
                    id=f"assumption-{idx}",
                    statement=f"If {claim.statement.lower()}, market share grows",
                    confidence=0.55 + idx * 0.1,
                    provenance_ids=list(claim.provenance_ids),
                )
            )
        return assumptions

    def crawl_and_embed(
        self, sources: Iterable[Source]
    ) -> tuple[list[RetrievalRecord], ToolInvocation]:
        materialised_sources = list(sources)
        if self._knowledge_client is not None:
            try:
                top_k = max(len(materialised_sources), 1)
                response = self._knowledge_client.hybrid_query(
                    self.tenant_id, self.query, top_k=top_k
                )
                raw_hits = response.get("hits", [])
                hits: Iterable[Mapping[str, Any]]
                if isinstance(raw_hits, list):
                    hits = cast(Iterable[Mapping[str, Any]], raw_hits)
                else:
                    hits = []
            except Exception:
                hits = []
                response = {}
                top_k = max(len(materialised_sources), 1)
            records: list[RetrievalRecord] = []
            for hit in hits:
                document_id = str(hit.get("document_id"))
                if not document_id:
                    continue
                metadata_raw = hit.get("metadata", {})
                metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
                chunk_hash = str(
                    metadata.get("chunk_hash", f"chunk-{document_id}")
                )
                provenance_id = str(
                    metadata.get("provenance_id", f"prov-{document_id}")
                )
                dense = self._coerce_float(
                    metadata.get("dense_score"), self._coerce_float(hit.get("score"))
                )
                sparse = self._coerce_float(
                    metadata.get("sparse_score"), self._coerce_float(hit.get("score"))
                )
                hybrid = self._coerce_float(
                    metadata.get("hybrid_score"), self._coerce_float(hit.get("score"))
                )
                reranker = self._coerce_float(
                    metadata.get("reranker_score"), self._coerce_float(hit.get("score"))
                )
                records.append(
                    RetrievalRecord(
                        document_id=document_id,
                        scores=RetrievalScore(
                            dense_score=dense,
                            sparse_score=sparse,
                            hybrid_score=hybrid,
                            reranker_score=reranker,
                        ),
                        grounding_spans=[
                            GroundingSpan(
                                source_id=document_id,
                                chunk_hash=chunk_hash,
                                start_char=0,
                                end_char=160,
                            )
                        ],
                        chunk_hash=chunk_hash,
                        provenance_id=provenance_id,
                    )
                )
            if records:
                invocation = ToolInvocation(
                    name="knowledge.hybrid_query",
                    arguments={
                        "query": self.query,
                        "tenant_id": self.tenant_id,
                        "top_k": top_k,
                    },
                    response={
                        "records": len(records),
                        "source": "knowledge-mcp",
                        "dense_weight": response.get("dense_score_weight"),
                        "sparse_weight": response.get("sparse_score_weight"),
                    },
                )
                return records, invocation
        return self._synthetic_crawl_and_embed(materialised_sources)

    def graph_artifacts(self, claims: Iterable[Claim]) -> GraphArtifacts:
        claim_list = list(claims)
        if self._knowledge_client is not None:
            try:
                response = self._knowledge_client.community_summaries(
                    self.tenant_id, limit=max(len(claim_list), 1)
                )
                raw_summaries = response.get("summaries", [])
                if isinstance(raw_summaries, list):
                    summaries = cast(Iterable[Mapping[str, Any]], raw_summaries)
                else:
                    summaries = []
            except Exception:
                summaries = []
            nodes: list[GraphNode] = [
                GraphNode(id="focus", label=self.query.title(), type="topic", score=0.8)
            ]
            edges: list[GraphEdge] = []
            community_scores: list[CommunityScore] = []
            community_summaries: list[CommunitySummary] = []
            narrative_chunks: list[NarrativeChunk] = []
            for summary in summaries:
                community_id = str(summary.get("community_id"))
                if not community_id:
                    continue
                title = str(summary.get("title", community_id))
                summary_text = str(summary.get("summary", ""))
                representative_nodes = [
                    str(node) for node in summary.get("representative_nodes", [])
                ]
                node_id = f"community-{community_id}"
                nodes.append(
                    GraphNode(id=node_id, label=title, type="community", score=0.75)
                )
                edges.append(
                    GraphEdge(
                        source="focus",
                        target=node_id,
                        relation="related_to",
                        weight=0.8,
                    )
                )
                community_scores.append(
                    CommunityScore(community_id=community_id, score=0.75)
                )
                community_summaries.append(
                    CommunitySummary(
                        community_id=community_id,
                        summary=summary_text,
                        key_entities=representative_nodes or [self.query.title()],
                    )
                )
                narrative_chunks.append(
                    NarrativeChunk(
                        id=f"chunk-{community_id}",
                        text=summary_text or title,
                        supporting_claims=[claim.id for claim in claim_list],
                    )
                )
            if len(nodes) > 1:
                return GraphArtifacts(
                    nodes=nodes,
                    edges=edges,
                    communities=community_scores,
                    community_summaries=community_summaries,
                    narrative_chunks=narrative_chunks,
                )

        nodes = [
            GraphNode(id="focus", label=self.query.title(), type="topic", score=0.8),
        ]
        edges: list[GraphEdge] = []
        community_scores: list[CommunityScore] = []
        community_summaries: list[CommunitySummary] = []
        narrative_chunks: list[NarrativeChunk] = []
        for idx, claim in enumerate(claim_list, start=1):
            node_id = f"claim-node-{idx}"
            nodes.append(
                GraphNode(
                    id=node_id, label=claim.statement[:32], type="claim", score=0.7
                )
            )
            edges.append(
                GraphEdge(
                    source="focus",
                    target=node_id,
                    relation="supports",
                    weight=0.8,
                )
            )
            community_id = f"community-{idx}"
            community_scores.append(
                CommunityScore(community_id=community_id, score=0.76)
            )
            community_summaries.append(
                CommunitySummary(
                    community_id=community_id,
                    summary=f"Evidence cluster for {claim.statement[:24]}",
                    key_entities=[self.query.title(), claim.statement.split()[0]],
                )
            )
            narrative_chunks.append(
                NarrativeChunk(
                    id=f"chunk-{idx}",
                    text=f"{claim.statement} grounded in customer interviews.",
                    supporting_claims=[claim.id],
                )
            )
        return GraphArtifacts(
            nodes=nodes,
            edges=edges,
            communities=community_scores,
            community_summaries=community_summaries,
            narrative_chunks=narrative_chunks,
        )

    def run_evaluations(
        self, suite: str, thresholds: Mapping[str, float] | None = None
    ) -> tuple[dict[str, float], ToolInvocation]:
        serialised_thresholds = dict(thresholds) if thresholds else None
        response_payload: Mapping[str, Any] | None = None
        if self._evals_client is not None:
            try:
                response_payload = self._evals_client.run(
                    self.tenant_id, suite, thresholds=serialised_thresholds
                )
            except Exception:
                response_payload = None
            else:
                metrics_payload = response_payload.get("metrics", {})
                if isinstance(metrics_payload, Mapping):
                    metrics = {
                        name: self._coerce_float(value)
                        for name, value in metrics_payload.items()
                    }
                    invocation = ToolInvocation(
                        name="evals.run",
                        arguments={
                            "suite": suite,
                            "tenant_id": self.tenant_id,
                            **(
                                {"thresholds": serialised_thresholds}
                                if serialised_thresholds
                                else {}
                            ),
                        },
                        response={
                            "metrics": metrics,
                            "run_id": response_payload.get("run_id"),
                            "source": "evals-mcp",
                            "passed": response_payload.get("passed"),
                        },
                    )
                    return metrics, invocation

        base_metrics = {
            "ragas_score": 0.82,
            "factscore": 0.78,
            "truthfulqa": 0.76,
        }
        lowered_query = self.query.lower()
        if "fail" in lowered_query or "red" in lowered_query:
            base_metrics["factscore"] = 0.62
        invocation = ToolInvocation(
            name="evals.run",
            arguments={
                "suite": suite,
                "tenant_id": self.tenant_id,
                **({"thresholds": serialised_thresholds} if serialised_thresholds else {}),
            },
            response={"metrics": base_metrics, "source": "synthetic"},
        )
        return base_metrics, invocation

    def run_verification(
        self,
        claims: Iterable[Claim],
        retrieval: Iterable[RetrievalRecord],
        minimum_pass_ratio: float,
    ) -> object:
        return run_cove(
            list(claims), list(retrieval), minimum_pass_ratio=minimum_pass_ratio
        )

    def compose_recommendation(
        self,
        state: StrategyState,
        workflow: WorkflowMetadata,
    ) -> RecommendationOutcome:
        debate = state.debate or DebateTrace(turns=[])
        graph = state.artefacts or self.graph_artifacts(state.claims)
        decision_brief = state.decision_brief or self._build_decision_brief(state)
        failure_reasons = list(state.failure_reasons)
        status = (
            RecommendationStatus.COMPLETE
            if not failure_reasons
            else RecommendationStatus.FAILED
        )
        return RecommendationOutcome(
            decision_brief=decision_brief,
            debate=debate,
            retrieval=list(state.retrieval),
            graph=graph,
            metrics=dict(state.metrics),
            workflow=workflow,
            status=status,
            failure_reasons=failure_reasons,
        )

    def _build_decision_brief(self, state: StrategyState) -> DecisionBrief:
        provenance = [prov for claim in state.claims for prov in claim.provenance_ids]
        cep = CEP(
            id="cep-1",
            title=f"{self.query.title()} Growth Initiative",
            narrative=f"Strategy focus for {self.query}",
            jobs_to_be_done=["Understand the market", "Differentiate offering"],
        )
        return DecisionBrief(
            id="brief-1",
            cep=cep,
            jtbd=[],
            dbas=[],
            assumptions=list(state.assumptions),
            claims=list(state.claims),
            experiments=[],
            forecasts=[],
            recommendation="Invest in premium positioning",
            safer_alternative="Pilot limited rollout",
            evidence_grade=EvidenceGrade.MODERATE,
            provenance_ids=provenance or ["prov-synthetic"],
            confidence=0.64,
        )
