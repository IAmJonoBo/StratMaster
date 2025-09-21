"""Agent node implementations for the LangGraph strategy pipeline.

All functions currently provide deterministic placeholder behaviour. They should be
replaced with calls into MCP servers (research, knowledge, router, evals) once those
services are wired in. Keeping the interface stable now ensures downstream integrations
(e.g., API handlers, tests) can start exercising the orchestration flow.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from stratmaster_api.models import (
    CEP,
    JTBD,
    Assumption,
    Claim,
    DecisionBrief,
    EvidenceGrade,
    RetrievalRecord,
    RetrievalScore,
)

from .state import StrategyState, ensure_agent_scratchpad


def researcher_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "researcher")
    pad.notes.append("Gathered baseline insights")

    if not state.claims:
        state.claims.append(
            Claim(
                id="claim-seed",
                statement="Synthetic claim seeded by Researcher",
                evidence_grade=EvidenceGrade.MODERATE,
                provenance_ids=["prov-seed"],
            )
        )
    return state


def synthesiser_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "synthesiser")
    pad.notes.append("Clustered research claims")
    if not state.assumptions:
        state.assumptions.append(
            Assumption(
                id="assumption-synth",
                statement="Market growth continues",
                confidence=0.55,
                provenance_ids=["prov-seed"],
            )
        )
    return state


def strategist_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "strategist")
    pad.notes.append("Drafted recommendation outline")
    return state


def adversary_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "adversary")
    pad.notes.append("Challenged assumptions")
    return state


def constitutional_critic_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "critic")
    pad.notes.append("Verified compliance with constitution")
    return state


def recommender_node(state: StrategyState) -> StrategyState:
    pad = ensure_agent_scratchpad(state, "recommender")
    pad.notes.append("Finalised decision brief")

    if state.decision_brief is None:
        state.decision_brief = DecisionBrief(
            id="brief-graph",
            cep=CEP(
                id="cep-seed",
                title="Customer expansion programme",
                narrative="Outline of customer journey",
                jobs_to_be_done=["Understand the market"],
            ),
            jtbd=[JTBD(id="jtbd-1", actor="Customer", motivation="", outcome="")],
            dbas=[],
            assumptions=list(state.assumptions),
            claims=list(state.claims),
            experiments=[],
            forecasts=[],
            recommendation="Invest in premium positioning",
            safer_alternative="Run limited pilot",
            evidence_grade=EvidenceGrade.MODERATE,
            provenance_ids=["prov-seed"],
            confidence=0.6,
        )
    if not state.retrieval:
        state.retrieval.append(
            RetrievalRecord(
                document_id="doc-graph",
                scores=RetrievalScore(hybrid_score=0.8),
                grounding_spans=[],
                chunk_hash="hash-graph",
                provenance_id="prov-seed",
            )
        )
    return state


def ordered_agents() -> Iterable[Callable[[StrategyState], StrategyState]]:
    return (
        researcher_node,
        synthesiser_node,
        strategist_node,
        adversary_node,
        constitutional_critic_node,
        recommender_node,
    )
