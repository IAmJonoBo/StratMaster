"""Shared orchestration state definitions used by LangGraph agents.

The structures mirror the data contracts defined in ``stratmaster_api.models`` so that
agents, evaluators, and downstream surfaces operate over the same schema regardless of
transport (HTTP, MCP, LangGraph shared memory).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
    arguments: Dict[str, Any]
    response: Dict[str, Any] | None = None
    error: str | None = None


@dataclass
class AgentScratchpad:
    """Temporary agent-level working memory."""

    notes: List[str] = field(default_factory=list)
    tool_calls: List[ToolInvocation] = field(default_factory=list)


@dataclass
class StrategyState:
    """Cross-agent state container persisted across LangGraph steps."""

    tenant_id: str
    query: str
    claims: List[Claim] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    retrieval: List[RetrievalRecord] = field(default_factory=list)
    artefacts: Optional[GraphArtifacts] = None
    debate: Optional[DebateTrace] = None
    decision_brief: Optional[DecisionBrief] = None
    workflow: WorkflowMetadata | None = None
    metrics: Dict[str, float] = field(default_factory=dict)
    scratchpad: Dict[str, AgentScratchpad] = field(default_factory=dict)
    pending_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)


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
