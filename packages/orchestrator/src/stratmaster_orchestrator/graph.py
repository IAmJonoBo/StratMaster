"""LangGraph wiring for the strategy orchestration pipeline."""

from __future__ import annotations

from typing import Callable

from stratmaster_api.models import DebateTrace, GraphArtifacts, RecommendationOutcome

from .agents import ordered_agents
from .state import OrchestrationResult, StrategyState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - fallback when langgraph not installed
    END = "__end__"
    START = "__start__"
    StateGraph = None


def build_strategy_graph() -> Callable[[StrategyState], OrchestrationResult]:
    """Create a LangGraph runnable for the strategy pipeline.

    Returns a callable that accepts a ``StrategyState`` and emits an
    ``OrchestrationResult``. When `langgraph` is unavailable, a fallback sequential
    executor is returned instead so that tests can exercise flow without the heavy
    dependency.
    """

    if StateGraph is None:
        return _sequential_executor

    graph: StateGraph = StateGraph(StrategyState)
    for agent_callable in ordered_agents():
        graph.add_node(agent_callable.__name__, agent_callable)

    graph.add_edge(START, "researcher_node")
    agents = [fn.__name__ for fn in ordered_agents()]
    for current, nxt in zip(agents, agents[1:], strict=False):
        graph.add_edge(current, nxt)
    graph.add_edge(agents[-1], END)

    compiled = graph.compile()

    def _run(initial_state: StrategyState) -> OrchestrationResult:
        final_state = compiled.invoke(initial_state)
        if final_state.debate is None:
            final_state.debate = DebateTrace(turns=[])
        if final_state.artefacts is None:
            final_state.artefacts = GraphArtifacts(
                nodes=[],
                edges=[],
                communities=[],
                community_summaries=[],
                narrative_chunks=[],
            )
        outcome = RecommendationOutcome(
            decision_brief=final_state.decision_brief,
            debate=final_state.debate,
            retrieval=final_state.retrieval,
            graph=final_state.artefacts,
            metrics=final_state.metrics,
            workflow=final_state.workflow,
        )
        return OrchestrationResult(outcome=outcome, state=final_state)

    return _run


def _sequential_executor(initial_state: StrategyState) -> OrchestrationResult:
    state = initial_state
    for agent_callable in ordered_agents():
        state = agent_callable(state)
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
    outcome = RecommendationOutcome(
        decision_brief=state.decision_brief,
        debate=state.debate,
        retrieval=state.retrieval,
        graph=state.artefacts,
        metrics=state.metrics,
        workflow=state.workflow,
    )
    return OrchestrationResult(outcome=outcome, state=state)
