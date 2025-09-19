"""HTTP request payload contracts for StratMaster API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .core import (
    Assumption,
    Claim,
    DebateTrace,
    Forecast,
    GraphArtifacts,
    Hypothesis,
    RetrievalRecord,
    Source,
)


class ResearchPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=3)
    tenant_id: str
    include_sources: bool = True
    max_sources: int = Field(default=10, ge=1, le=50)


class ResearchPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    tasks: list[str]
    sources: list[Source]


class ResearchRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    tenant_id: str
    force_refresh: bool = False


class ResearchRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    claims: list[Claim]
    assumptions: list[Assumption]
    hypotheses: list[Hypothesis]
    retrieval: list[RetrievalRecord]
    artifacts: GraphArtifacts


class GraphSummariseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    focus: Literal["community", "entity", "narrative"] = "community"
    limit: int = Field(default=5, ge=1, le=50)


class GraphSummariseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summaries: list[str]
    artifacts: GraphArtifacts


class DebateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    hypothesis_id: str | None = None
    claim_ids: list[str] | None = None
    max_turns: int = Field(default=6, ge=2, le=20)


class DebateRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debate_id: str
    debate: DebateTrace


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    cep_id: str
    jtbd_ids: list[str]
    risk_tolerance: Literal["low", "medium", "high"] = "medium"


class RetrievalQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict | None = None


class RetrievalQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[RetrievalRecord]


class EvalRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    suite: str
    thresholds: dict | None = None


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    passed: bool
    metrics: dict[str, float]


class ExperimentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    hypothesis_id: str
    variants: list[dict]
    primary_metric: dict


class ExperimentCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str


class ForecastCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    metric_id: str
    horizon_days: int = Field(..., ge=1, le=365)


class ForecastCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forecast: Forecast
