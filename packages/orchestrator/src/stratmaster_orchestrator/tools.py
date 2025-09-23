# ruff: noqa: I001
"""Deterministic tool mediation layer for LangGraph agents."""

from __future__ import annotations

import importlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

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
    RetrievalRecord,
    RetrievalScore,
    Source,
    SourceType,
    WorkflowMetadata,
)

from .state import StrategyState, ToolInvocation


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
    """Synthetic MCP-like tool registry used by agent nodes."""

    def __init__(self, tenant_id: str, query: str) -> None:
        self.tenant_id = tenant_id
        self.query = query

    def metasearch(self, limit: int = 3) -> tuple[list[Source], ToolInvocation]:
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
            response={"results": len(sources)},
        )
        return sources, invocation

    def crawl_and_embed(
        self, sources: Iterable[Source]
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
            response={"records": len(records)},
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

    def graph_artifacts(self, claims: Iterable[Claim]) -> GraphArtifacts:
        nodes = [
            GraphNode(id="focus", label=self.query.title(), type="topic", score=0.8),
        ]
        edges: list[GraphEdge] = []
        community_scores: list[CommunityScore] = []
        community_summaries: list[CommunitySummary] = []
        narrative_chunks: list[NarrativeChunk] = []
        for idx, claim in enumerate(claims, start=1):
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

    def run_evaluations(self, suite: str) -> tuple[dict[str, float], ToolInvocation]:
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
            arguments={"suite": suite, "tenant_id": self.tenant_id},
            response={"metrics": base_metrics},
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
        return RecommendationOutcome(
            decision_brief=decision_brief,
            debate=debate,
            retrieval=list(state.retrieval),
            graph=graph,
            metrics=dict(state.metrics),
            workflow=workflow,
            # status and failure_reasons are set by downstream evaluation
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
