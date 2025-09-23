"""LangGraph wiring for the strategy orchestration pipeline with Chain-of-Verification."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph
from stratmaster_api.models import DebateTrace, GraphArtifacts, WorkflowMetadata

from .agents import build_nodes
from .checkpoints import InMemoryCheckpointStore
from .prompts import load_prompts
from .state import OrchestrationResult, StrategyState
from .tools import EvaluationGate, ToolRegistry
from .verification import ChainOfVerificationNode

DEFAULT_EVALUATION_MINIMUMS = {
    "cove_verified_fraction": 0.8,
    "ragas_score": 0.75,
    "factscore": 0.7,
    "constitutional_compliance": 1.0,
    "verification_confidence": 0.7,
}


def _coerce_state(
    raw: StrategyState | dict[str, Any], seed: StrategyState
) -> StrategyState:
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
        state.workflow = WorkflowMetadata(
            workflow_id="wf-synthetic", tenant_id=state.tenant_id
        )
    return state


def build_strategy_graph(
    *,
    evaluation_gate: EvaluationGate | None = None,
    minimum_verification_pass_ratio: float = 0.8,
    include_cove: bool = True,
) -> Callable[[StrategyState], OrchestrationResult]:
    """Return a callable that executes the enhanced LangGraph agent pipeline with CoVe."""

    prompts = load_prompts()
    gate = evaluation_gate or EvaluationGate(DEFAULT_EVALUATION_MINIMUMS)

    def _run(initial_state: StrategyState) -> OrchestrationResult:
        checkpoints = InMemoryCheckpointStore()
        graph = StateGraph(StrategyState)
        
        # Build standard agent nodes
        nodes = build_nodes(
            initial_state,
            checkpoints,
            prompts,
            gate,
            minimum_pass_ratio=minimum_verification_pass_ratio,
        )

        # Define node names and structure
        if include_cove:
            node_names = [
                "researcher",
                "synthesiser", 
                "verification",  # CoVe between synthesiser and strategist
                "strategist",
                "adversary",
                "critic",
                "recommender",
            ]
            
            # Add CoVe node
            tool_registry = ToolRegistry(initial_state.tenant_id, initial_state.query)
            cove_node = ChainOfVerificationNode(tool_registry, checkpoints)
            
            # Add all nodes to graph
            for i, (name, node) in enumerate(zip(node_names, nodes, strict=False)):
                if name == "verification":
                    graph.add_node(name, cove_node)
                else:
                    # Adjust index for non-verification nodes
                    actual_index = i if i < 2 else i - 1
                    if actual_index < len(nodes):
                        graph.add_node(name, nodes[actual_index])
        else:
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

        # Connect nodes in sequence
        graph.add_edge(START, node_names[0])
        for current, nxt in zip(node_names, node_names[1:], strict=False):
            graph.add_edge(current, nxt)
        graph.add_edge(node_names[-1], END)

        # Execute the graph
        runnable = graph.compile()
        raw_state = runnable.invoke(initial_state)
        final_state = _coerce_state(raw_state, initial_state)
        final_state = _ensure_defaults(final_state)
        
        # Compose final recommendation
        tool_registry = ToolRegistry(final_state.tenant_id, final_state.query)
        outcome = tool_registry.compose_recommendation(
            final_state, final_state.workflow
        )
        return OrchestrationResult(outcome=outcome, state=final_state)

    return _run


def build_enhanced_strategy_graph_with_dspy(
    initial_query: str,
    tenant_id: str,
    *,
    evaluation_gate: EvaluationGate | None = None,
    enable_dspy_telemetry: bool = True,
) -> Callable[[StrategyState], OrchestrationResult]:
    """Build strategy graph with integrated DSPy telemetry."""
    
    # This would integrate with the DSPy programs created earlier
    # For now, we return the standard graph but with enhanced telemetry hooks
    graph_runner = build_strategy_graph(
        evaluation_gate=evaluation_gate,
        include_cove=True
    )
    
    def _run_with_telemetry(initial_state: StrategyState) -> OrchestrationResult:
        if enable_dspy_telemetry:
            try:
                from stratmaster_dsp import TelemetryRecorder, compile_full_pipeline
                
                # Record the strategy execution in DSPy telemetry
                telemetry = TelemetryRecorder()
                telemetry.start_trace("strategy_orchestration", 
                                    query=initial_query, 
                                    tenant_id=tenant_id)
                
                # Run the standard graph
                result = graph_runner(initial_state)
                
                # Compile DSPy programs based on the results
                try:
                    compile_full_pipeline(initial_query, telemetry=telemetry)
                except Exception as e:
                    telemetry.record("dspy_compilation_error", {"error": str(e)})
                
                telemetry.end_trace(
                    success=True,
                    final_status=result.outcome.status.value,
                    debate_turns=len(result.outcome.debate.turns) if result.outcome.debate else 0
                )
                
                return result
                
            except ImportError:
                # Fall back to standard execution if DSPy not available
                return graph_runner(initial_state)
        else:
            return graph_runner(initial_state)
    
    return _run_with_telemetry
