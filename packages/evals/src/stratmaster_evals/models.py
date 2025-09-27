"""RAGAS-powered evaluation models for StratMaster."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class RAGASMetrics:
    """RAGAS evaluation metrics with quality gates from Scratch.md."""

    faithfulness: float
    context_precision: float
    context_recall: float
    answer_relevancy: float

    # Quality gate thresholds from Scratch.md
    FAITHFULNESS_THRESHOLD = 0.8
    PRECISION_THRESHOLD = 0.7
    RECALL_THRESHOLD = 0.7

    def passes_quality_gates(self) -> bool:
        """Check if metrics meet quality gate requirements."""
        return (
            self.faithfulness >= self.FAITHFULNESS_THRESHOLD
            and self.context_precision >= self.PRECISION_THRESHOLD
            and self.context_recall >= self.RECALL_THRESHOLD
        )

    def quality_score(self) -> float:
        """Overall quality score (0-1)."""
        return (
            self.faithfulness * 0.4
            + self.context_precision * 0.3
            + self.context_recall * 0.3
        )


@dataclass
class TruLensMetrics:
    """TruLens-inspired metrics for grounding and relevance checks."""

    groundedness: float
    answer_relevance: float
    context_relevance: float
    support_coverage: float
    analysis_latency_ms: float

    GROUNDEDNESS_THRESHOLD = 0.75
    ANSWER_THRESHOLD = 0.70
    CONTEXT_THRESHOLD = 0.60
    SUPPORT_THRESHOLD = 0.60

    def passes_quality_gates(self) -> bool:
        """Return True when all TruLens quality thresholds are satisfied."""
        return (
            self.groundedness >= self.GROUNDEDNESS_THRESHOLD
            and self.answer_relevance >= self.ANSWER_THRESHOLD
            and self.context_relevance >= self.CONTEXT_THRESHOLD
            and self.support_coverage >= self.SUPPORT_THRESHOLD
        )

    def quality_score(self) -> float:
        """Combine metrics into a single score mirroring TruLens dashboards."""
        return (
            self.groundedness * 0.4
            + self.answer_relevance * 0.3
            + self.context_relevance * 0.2
            + self.support_coverage * 0.1
        )

    def as_dict(self) -> dict[str, float]:
        """Serialise metrics for metadata payloads."""
        return {
            "groundedness": self.groundedness,
            "answer_relevance": self.answer_relevance,
            "context_relevance": self.context_relevance,
            "support_coverage": self.support_coverage,
            "analysis_latency_ms": self.analysis_latency_ms,
            "quality_score": self.quality_score(),
        }


class EvaluationRequest(BaseModel):
    """Request for RAGAS evaluation."""
    
    questions: list[str] = Field(..., description="List of questions to evaluate")
    contexts: list[list[str]] = Field(..., description="Retrieved contexts for each question")
    answers: list[str] = Field(..., description="Generated answers")
    ground_truths: list[str] = Field(..., description="Expected ground truth answers")
    experiment_name: str = Field(..., description="Langfuse experiment name")
    model_name: str = Field(default="unknown", description="Model used for generation")


class EvaluationResult(BaseModel):
    """Results from RAG evaluation with RAGAS + TruLens quality gates."""

    experiment_id: str = Field(..., description="Langfuse experiment ID")
    experiment_name: str = Field(..., description="Experiment name")
    model_name: str = Field(..., description="Model evaluated")
    metrics: RAGASMetrics = Field(..., description="RAGAS evaluation metrics")
    passes_quality_gates: bool = Field(..., description="Whether quality gates are met")
    quality_score: float = Field(..., description="Overall quality score")
    evaluation_time: datetime = Field(default_factory=datetime.now, description="When evaluation was performed")
    sample_count: int = Field(..., description="Number of samples evaluated")

    # TruLens supplementary metrics
    trulens_metrics: TruLensMetrics | None = Field(
        default=None,
        description="TruLens-inspired metrics for groundedness and context checks",
    )
    trulens_passes_quality_gates: bool | None = Field(
        default=None,
        description="Whether TruLens quality gates were satisfied",
    )
    trulens_failures: list[str] = Field(
        default_factory=list,
        description="TruLens-specific quality gate failures",
    )

    # Detailed results for debugging
    individual_scores: dict[str, list[float]] = Field(default_factory=dict, description="Per-sample scores")
    failures: list[str] = Field(default_factory=list, description="Quality gate failures")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ModelPerformance(BaseModel):
    """Model performance tracking for the recommender system."""
    
    model_name: str = Field(..., description="Model identifier")
    task_type: str = Field(..., description="Task type (chat, embedding, etc)")
    
    # Performance metrics
    avg_latency: float = Field(..., description="Average latency in ms")
    p95_latency: float = Field(..., description="95th percentile latency")
    cost_per_token: float = Field(..., description="Cost per token in USD")
    quality_score: float = Field(..., description="Quality score from RAGAS")
    
    # Utilization metrics
    request_count: int = Field(default=0, description="Total requests processed")
    success_rate: float = Field(default=1.0, description="Success rate")
    
    # Model selection utility score from Scratch.md
    utility_score: float = Field(..., description="Utility = quality_z - λ·cost - μ·latency")
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.now, description="Last metrics update")
    evaluation_period: str = Field(default="24h", description="Evaluation period")


class CascadeRoutingDecision(BaseModel):
    """Decision from cascade routing system (cheap → strong)."""
    
    initial_model: str = Field(..., description="Initial cheap model tried")
    final_model: str = Field(..., description="Final model used")
    escalated: bool = Field(..., description="Whether escalation occurred")
    
    # Confidence and trigger reasons
    confidence_score: float = Field(..., description="Initial model confidence")
    escalation_reasons: list[str] = Field(default_factory=list, description="Why escalation happened")
    
    # Performance metrics
    total_latency: float = Field(..., description="Total latency including escalation")
    total_cost: float = Field(..., description="Total cost")
    
    # Quality assessment
    retrieval_coverage: float = Field(..., description="RAGAS context recall")
    self_consistency: float = Field(..., description="Vote agreement among cheap models")
    task_complexity: str = Field(..., description="Detected task complexity")
    
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional routing metadata")