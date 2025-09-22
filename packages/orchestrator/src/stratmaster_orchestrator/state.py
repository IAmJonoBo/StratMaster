"""Shared orchestration state definitions used by LangGraph agents.

The structures mirror the data contracts defined in ``stratmaster_api.models`` so that
agents, evaluators, and downstream surfaces operate over the same schema regardless of
transport (HTTP, MCP, LangGraph shared memory).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stratmaster_cove import VerificationResult

from stratmaster_api.models import (
    Assumption,
    Claim,
    DebateTrace,
    DecisionBrief,
    GraphArtifacts,
    RecommendationOutcome,
    RecommendationStatus,
    RetrievalRecord,
    WorkflowMetadata,
)


@dataclass
class ToolInvocation:
    """Record of a single MCP tool invocation."""

    name: str
    arguments: dict[str, Any]
    response: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class AgentScratchpad:
    """Temporary agent-level working memory."""

    notes: list[str] = field(default_factory=list)
    tool_calls: list[ToolInvocation] = field(default_factory=list)

    def copy(self) -> "AgentScratchpad":
        return AgentScratchpad(
            notes=list(self.notes),
            tool_calls=list(self.tool_calls),
        )


@dataclass
class StrategyState:
    """Cross-agent state container persisted across LangGraph steps."""

    tenant_id: str
    query: str
    claims: list[Claim] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)
    retrieval: list[RetrievalRecord] = field(default_factory=list)
    artefacts: GraphArtifacts | None = None
    debate: DebateTrace | None = None
    decision_brief: DecisionBrief | None = None
    workflow: WorkflowMetadata | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    scratchpad: dict[str, AgentScratchpad] = field(default_factory=dict)
    pending_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    verification: VerificationResult | None = None
    status: RecommendationStatus = RecommendationStatus.NEEDS_REVIEW
    failure_reasons: list[str] = field(default_factory=list)

    def copy(self) -> "StrategyState":
        return StrategyState(
            tenant_id=self.tenant_id,
            query=self.query,
            claims=list(self.claims),
            assumptions=list(self.assumptions),
            retrieval=list(self.retrieval),
            artefacts=self.artefacts,
            debate=self.debate,
            decision_brief=self.decision_brief,
            workflow=self.workflow,
            metrics=dict(self.metrics),
            scratchpad={name: pad.copy() for name, pad in self.scratchpad.items()},
            pending_tasks=list(self.pending_tasks),
            completed_tasks=list(self.completed_tasks),
            verification=self.verification,
            status=self.status,
            failure_reasons=list(self.failure_reasons),
        )

    def with_updates(self, **updates: Any) -> "StrategyState":
        clone = self.copy()
        for key, value in updates.items():
            setattr(clone, key, value)
        return clone

    def record_metric(self, name: str, value: float) -> None:
        self.metrics[name] = value

    def mark_failure(self, reason: str) -> None:
        if reason not in self.failure_reasons:
            self.failure_reasons.append(reason)
        self.status = RecommendationStatus.NEEDS_REVIEW

    def mark_failed(self, reason: str) -> None:
        self.mark_failure(reason)
        self.status = RecommendationStatus.FAILED

    def mark_complete(self) -> None:
        self.status = RecommendationStatus.COMPLETE


@dataclass
class OrchestrationResult:
    """Final output returned by the LangGraph run."""

    outcome: RecommendationOutcome
    state: StrategyState


def ensure_agent_scratchpad(state: StrategyState, agent_name: str) -> AgentScratchpad:
    """Get or create the scratchpad for a named agent."""

    if agent_name not in state.scratchpad:
        state.scratchpad[agent_name] = AgentScratchpad()
    return state.scratchpad[agent_name]
