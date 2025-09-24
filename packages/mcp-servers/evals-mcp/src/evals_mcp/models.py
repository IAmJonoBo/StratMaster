"""Schemas for evals MCP."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EvalRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    suite: Literal["rag", "truthfulqa", "factscore", "custom"]
    thresholds: dict[str, float] | None = None


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    passed: bool
    metrics: dict[str, float]


class InfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    suites: list[str]


# Sprint 2 - Learning from Debates Models
class DebateOutcome(BaseModel):
    """Schema for logging debate outcomes to enable policy learning."""
    model_config = ConfigDict(extra="forbid")

    task_id: str
    tenant_id: str
    agents: list[str] = Field(description="List of agent names that participated")
    evidence_count: int = Field(ge=0, description="Number of evidence pieces used")
    citations_ok: bool = Field(description="Whether citations were properly validated")
    critique_count: int = Field(ge=0, description="Number of critique rounds")
    user_acceptance: Literal["accepted", "revised", "rejected"]
    latency_ms: float = Field(ge=0, description="Total debate latency in milliseconds")
    cost_tokens: int = Field(ge=0, description="Total tokens consumed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateOutcomeRequest(BaseModel):
    """Request to log a debate outcome."""
    model_config = ConfigDict(extra="forbid")

    outcome: DebateOutcome


class DebateOutcomeResponse(BaseModel):
    """Response after logging debate outcome."""
    model_config = ConfigDict(extra="forbid")

    logged: bool
    outcome_id: str


class DebatePolicyPrediction(BaseModel):
    """Prediction from the debate policy model."""
    model_config = ConfigDict(extra="forbid")

    should_single_agent: bool = Field(description="Recommend single agent instead of debate")
    should_skip_debate: bool = Field(description="Skip debate entirely")
    recommended_agents: int = Field(ge=1, le=5, description="Recommended number of agents")
    confidence: float = Field(ge=0, le=1, description="Prediction confidence")
    reasoning: str = Field(description="Explanation for the recommendation")


class DebatePolicyRequest(BaseModel):
    """Request for debate policy prediction."""
    model_config = ConfigDict(extra="forbid")

    task_id: str
    tenant_id: str
    query: str
    historical_features: dict[str, float] = Field(
        default_factory=dict,
        description="Historical features for the tenant/task type"
    )


class DebatePolicyResponse(BaseModel):
    """Response with debate policy recommendation."""
    model_config = ConfigDict(extra="forbid")

    prediction: DebatePolicyPrediction
    task_id: str
