"""LangGraph wiring for the strategy orchestration pipeline."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from stratmaster_api.models import DebateTrace, GraphArtifacts, RecommendationOutcome, WorkflowMetadata

from .agents import build_nodes
from .checkpoints import InMemoryCheckpointStore
from .prompts import load_prompts
from .state import OrchestrationResult, StrategyState
from .tools import EvaluationGate, ToolRegistry

from langgraph.graph import END, START, StateGraph


DEFAULT_EVALUATION_MINIMUMS = {
    "cove_verified_fraction": 0.8,
    "ragas_score": 0.75,
    "factscore": 0.7,
}


def _coerce_state(raw: StrategyState | dict[str, Any], seed: StrategyState) -> StrategyState:
    if isinstance(raw, StrategyState):
        return raw
    if isinstance(raw, dict):
        base = vars(seed).copy()
        base.update(raw)
        return StrategyState(**base)
    return seed


def _ensure_defaults(state: StrategyState) -> StrategyState:
    if state.debate is None:
        state.debate = DebateTrace(turns=[])
    if state.artefacts is None:
        state.artefacts = GraphArtifacts(
            nodes=[],
            edges=[],
            communities=[],
            community_summaries=[],
            narrative_chunks=[],
        )
    if state.workflow is None:
        state.workflow = WorkflowMetadata(workflow_id="wf-synthetic", tenant_id=state.tenant_id)
    return state


def build_strategy_graph(
    *,
    evaluation_gate: EvaluationGate | None = None,
    minimum_verification_pass_ratio: float = 0.8,
) -> Callable[[StrategyState], OrchestrationResult]:
    """Return a callable that executes the LangGraph agent pipeline."""

    prompts = load_prompts()
    gate = evaluation_gate or EvaluationGate(DEFAULT_EVALUATION_MINIMUMS)

    def _run(initial_state: StrategyState) -> OrchestrationResult:
        checkpoints = InMemoryCheckpointStore()
        graph = StateGraph(StrategyState)
        nodes = build_nodes(
            initial_state,
            checkpoints,
            prompts,
            gate,
            minimum_pass_ratio=minimum_verification_pass_ratio,
        )

        node_names = [
            "researcher",
            "synthesiser",
            "strategist",
            "adversary",
            "critic",
            "recommender",
        ]
        for name, node in zip(node_names, nodes, strict=True):
            graph.add_node(name, node)

        graph.add_edge(START, node_names[0])
        for current, nxt in zip(node_names, node_names[1:], strict=False):
            graph.add_edge(current, nxt)
        graph.add_edge(node_names[-1], END)

        runnable = graph.compile()
        raw_state = runnable.invoke(initial_state)
        final_state = _coerce_state(raw_state, initial_state)
        final_state = _ensure_defaults(final_state)
        tool_registry = ToolRegistry(final_state.tenant_id, final_state.query)
        outcome = tool_registry.compose_recommendation(final_state, final_state.workflow)
        return OrchestrationResult(outcome=outcome, state=final_state)

    return _run
