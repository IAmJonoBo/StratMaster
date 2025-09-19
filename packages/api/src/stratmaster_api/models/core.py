"""Core data contracts for StratMaster API.

These models translate section 4 of PROJECT.md into Pydantic v2 schemas that can be reused
by HTTP handlers, orchestrator pipelines, and MCP tool schemas. They intentionally favour
explicit typing over convenience so that downstream schema generation remains deterministic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceType(str, Enum):
    WEB = "web"
    DOCUMENT = "document"
    DATASET = "dataset"
    USER_PROVIDED = "user_provided"


class EvidenceGrade(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class CommunityScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    community_id: str = Field(..., description="Identifier for the detected community")
    score: float = Field(..., ge=0, le=1)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: SourceType
    title: str
    url: HttpUrl
    language: str | None = Field(default=None, description="BCP-47 language tag")
    tags: list[str] = Field(default_factory=list)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Source
    fetch_time_utc: datetime = Field(
        ..., description="UTC timestamp the document was fetched"
    )
    original_timezone: str = Field(
        "UTC+02:00",
        description="Timezone offset preserved for SAST-aligned logging",
    )
    sha256: str
    parser_version: str
    crawl_policy_snapshot: str | None = None


class GroundingSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    chunk_hash: str
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    statement: str
    evidence_grade: EvidenceGrade
    provenance_ids: list[str]


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    statement: str
    confidence: float = Field(..., ge=0, le=1)
    provenance_ids: list[str]


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    supporting_claims: list[str]
    contradicting_claims: list[str]


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    definition: str
    unit: str | None = None
    current_value: float | None = None


class ExperimentVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    prior_probability: float | None = Field(default=None, ge=0, le=1)


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    hypothesis_id: str
    variants: list[ExperimentVariant]
    primary_metric: Metric
    minimum_detectable_effect: float
    launch_conditions: list[str] = Field(default_factory=list)


class ForecastInterval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confidence: Literal[50, 90]
    lower: float
    upper: float


class Forecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    metric: Metric
    point_estimate: float
    intervals: list[ForecastInterval]
    horizon_days: int


class CEP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    narrative: str
    jobs_to_be_done: list[str]


class JTBD(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    actor: str
    motivation: str
    outcome: str


class DBA(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    decision: str
    bet: str
    assumption_ids: list[str]


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    type: str
    score: float | None = Field(default=None, ge=0)


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    relation: str
    weight: float | None = Field(default=None, ge=0)


class CommunitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    community_id: str
    summary: str
    key_entities: list[str]


class NarrativeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    supporting_claims: list[str]


class GraphArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    communities: list[CommunityScore]
    community_summaries: list[CommunitySummary]
    narrative_chunks: list[NarrativeChunk]


class RetrievalScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dense_score: float | None = None
    sparse_score: float | None = None
    hybrid_score: float | None = None
    reranker_score: float | None = None


class RetrievalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    scores: RetrievalScore
    grounding_spans: list[GroundingSpan]
    chunk_hash: str
    provenance_id: str


class DecisionBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    cep: CEP
    jtbd: list[JTBD]
    dbas: list[DBA]
    assumptions: list[Assumption]
    claims: list[Claim]
    experiments: list[Experiment]
    forecasts: list[Forecast]
    recommendation: str
    safer_alternative: str
    evidence_grade: EvidenceGrade
    provenance_ids: list[str]
    confidence: float = Field(..., ge=0, le=1)


class DebateTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    role: Literal[
        "Researcher",
        "Synthesiser",
        "Strategist",
        "Adversary",
        "ConstitutionalCritic",
        "Recommender",
    ]
    content: str
    grounding: list[GroundingSpan] = Field(default_factory=list)


class DebateTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turns: list[DebateTurn]
    verdict: Optional[str] = None


class WorkflowMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    tenant_id: str
    trace_id: str | None = None
    langfuse_span_id: str | None = None


class RecommendationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_brief: DecisionBrief
    debate: DebateTrace
    retrieval: list[RetrievalRecord]
    graph: GraphArtifacts
    metrics: dict[str, float]
    workflow: WorkflowMetadata
