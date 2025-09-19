"""Placeholder orchestration services used by the public API.

These implementations do not attempt to reach external systems. They instead fabricate
plausible responses so that the FastAPI surface remains testable and aligns with the
engineering blueprint. Real integrations should replace this module once LangGraph and MCP
pipelines are wired in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

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
    RetrievalRecord,
    RetrievalScore,
    Source,
    SourceType,
    WorkflowMetadata,
)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class OrchestratorStub:
    """In-memory stub for all major flows described in PROJECT.md."""

    def generate_source(self, idx: int) -> Source:
        return Source(
            id=f"src-{idx}",
            type=SourceType.WEB,
            title=f"Synthetic Source {idx}",
            url=f"https://example.com/article/{idx}",
            tags=["synthetic", "demo"],
        )

    def plan_research(
        self, query: str, tenant_id: str, max_sources: int
    ) -> dict[str, Any]:
        sources = [self.generate_source(i) for i in range(1, max_sources + 1)]
        tasks = [f"Investigate angle {i}" for i in range(1, 4)]
        return {
            "plan_id": f"plan-{uuid4().hex[:8]}",
            "tasks": tasks,
            "sources": sources,
        }

    def run_research(self, plan_id: str, tenant_id: str) -> dict[str, Any]:
        claims = [
            Claim(
                id="claim-1",
                statement="Our synthetic claim",
                evidence_grade=EvidenceGrade.MODERATE,
                provenance_ids=["prov-1"],
            )
        ]
        assumptions = [
            Assumption(
                id="assumption-1",
                statement="We assume continued demand",
                confidence=0.7,
                provenance_ids=["prov-1"],
            )
        ]
        hypotheses = [
            Hypothesis(
                id="hyp-1",
                description="If we expand marketing, demand grows",
                supporting_claims=["claim-1"],
                contradicting_claims=[],
            )
        ]
        retrieval = [
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
        graph = GraphArtifacts(
            nodes=[GraphNode(id="n1", label="Brand", type="entity")],
            edges=[],
            communities=[CommunityScore(community_id="c1", score=0.9)],
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
                    supporting_claims=["claim-1"],
                )
            ],
        )
        return {
            "run_id": f"run-{uuid4().hex[:8]}",
            "claims": claims,
            "assumptions": assumptions,
            "hypotheses": hypotheses,
            "retrieval": retrieval,
            "artifacts": graph,
        }

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

    def generate_recommendation(
        self, tenant_id: str, cep_id: str, jtbd_ids: list[str], risk_tolerance: str
    ) -> RecommendationOutcome:
        cep = CEP(
            id=cep_id,
            title="Customer expansion programme",
            narrative="Outline of customer journey",
            jobs_to_be_done=["Understand the market", "Prioritise bets"],
        )
        assumptions = [
            Assumption(
                id="assumption-1",
                statement="Market remains stable",
                confidence=0.6,
                provenance_ids=["prov-1"],
            )
        ]
        claims = [
            Claim(
                id="claim-1",
                statement="Customers prefer premium positioning",
                evidence_grade=EvidenceGrade.HIGH,
                provenance_ids=["prov-1"],
            )
        ]
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
        decision = DecisionBrief(
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
        retrieval = [
            RetrievalRecord(
                document_id="doc-1",
                scores=RetrievalScore(hybrid_score=0.9, reranker_score=0.86),
                grounding_spans=[],
                chunk_hash="hash-rec",
                provenance_id="prov-1",
            )
        ]
        graph = GraphArtifacts(
            nodes=[GraphNode(id="brand", label="Brand", type="entity")],
            edges=[],
            communities=[CommunityScore(community_id="c1", score=0.8)],
            community_summaries=[],
            narrative_chunks=[],
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
            retrieval=retrieval,
            graph=graph,
            metrics={
                "risk_tolerance": {"low": 0.4, "medium": 0.6, "high": 0.2}[
                    risk_tolerance
                ]
            },
            workflow=workflow,
        )

    def query_retrieval(
        self, tenant_id: str, query: str, top_k: int
    ) -> list[RetrievalRecord]:
        return [
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

    def run_eval(self, tenant_id: str, suite: str) -> dict[str, Any]:
        metrics = {"ragas_score": 0.82, "factscore": 0.78}
        passed = all(value >= 0.7 for value in metrics.values())
        return {
            "run_id": f"eval-{uuid4().hex[:8]}",
            "passed": passed,
            "metrics": metrics,
        }

    def create_experiment(self, tenant_id: str, payload: dict[str, Any]) -> str:
        return f"exp-{uuid4().hex[:8]}"

    def create_forecast(
        self, tenant_id: str, metric_id: str, horizon_days: int
    ) -> Forecast:
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


orchestrator_stub = OrchestratorStub()
"""Default orchestrator used by dependency injection."""
