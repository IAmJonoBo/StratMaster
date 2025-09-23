"""Shared orchestration state definitions used by LangGraph agents.

The structures mirror the data contracts defined in ``stratmaster_api.models`` so that
agents, evaluators, and downstream surfaces operate over the same schema regardless of
transport (HTTP, MCP, LangGraph shared memory).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stratmaster_api.models import (
    Assumption,
    Claim,
    DebateTrace,
    DecisionBrief,
    GraphArtifacts,
    RecommendationOutcome,
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
    # Optional failure tracking used by RecommenderNode
    failure_reasons: list[str] = field(default_factory=list)

    # Utility helpers used by agent nodes
    def copy(self) -> StrategyState:
        """Shallow copy suitable for step-wise mutation.

        Collections are shallow-copied to avoid accidental shared references across nodes.
        """
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
            scratchpad=dict(self.scratchpad),
            pending_tasks=list(self.pending_tasks),
            completed_tasks=list(self.completed_tasks),
            failure_reasons=list(self.failure_reasons),
        )

    def record_metric(self, name: str, value: float) -> None:
        self.metrics[name] = value

    def mark_failure(self, reason: str) -> None:
        if reason not in self.failure_reasons:
            self.failure_reasons.append(reason)

    # Back-compat alias used by some nodes/tests
    def mark_failed(self, reason: str) -> None:
        self.mark_failure(reason)

    def mark_complete(self) -> None:
        # Marker method used by RecommenderNode; no-op for now but kept for compatibility
        pass


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
