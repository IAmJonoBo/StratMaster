"""Agent node implementations backed by deterministic tool stubs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from stratmaster_api.models import DebateTrace, DebateTurn, WorkflowMetadata

from .checkpoints import InMemoryCheckpointStore
from .prompts import DebatePrompts
from .state import StrategyState, ToolInvocation, ensure_agent_scratchpad
from .tools import EvaluationGate, ToolRegistry


@dataclass
class ResearcherNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "researcher")
        sources, metasearch_call = self.tools.metasearch()
        pad.notes.append("Collected metasearch results and prioritised sources")
        pad.tool_calls.append(metasearch_call)
        retrieval, retrieval_call = self.tools.crawl_and_embed(sources)
        pad.tool_calls.append(retrieval_call)
        working.claims = self.tools.synthesise_claims(sources)
        working.assumptions = self.tools.synthesise_assumptions(working.claims)
        working.retrieval = retrieval
        working.artefacts = self.tools.graph_artifacts(working.claims)
        working.completed_tasks.append("research")
        working.pending_tasks.extend(
            [
                task
                for task in ("synthesis", "debate")
                if task not in working.pending_tasks
            ]
        )
        self.checkpoints.save("researcher", working)
        return working


@dataclass
class SynthesiserNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore
    minimum_pass_ratio: float

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "synthesiser")
        verification: Any = self.tools.run_verification(
            working.claims,
            working.retrieval,
            minimum_pass_ratio=self.minimum_pass_ratio,
        )
        pad.notes.append("Ran CoVe verification across claims")
        pad.tool_calls.append(
            ToolInvocation(
                name="assurance.cove.verify",
                arguments={"claims": len(working.claims)},
                response={
                    "verified_fraction": getattr(
                        verification, "verified_fraction", 0.0
                    ),
                    "status": getattr(verification, "status", "skipped"),
                },
            )
        )
        # attach for downstream visibility in case the type is not from stratmaster_cove
        working.scratchpad.setdefault("synthesiser", pad)
        vf = cast(float, getattr(verification, "verified_fraction", 0.0))
        status = cast(str, getattr(verification, "status", "skipped"))
        working.record_metric("cove_verified_fraction", vf)
        if status != "verified":
            working.mark_failure("verification_below_threshold")
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        working.debate.turns.append(
            DebateTurn(
                agent="synthesiser",
                role="Synthesiser",
                content="Summarised evidence and verification results",
                grounding=[],
            )
        )
        working.completed_tasks.append("synthesis")
        self.checkpoints.save("synthesiser", working)
        return working


@dataclass
class StrategistNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore
    evaluation_gate: EvaluationGate

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "strategist")
        metrics, invocation = self.tools.run_evaluations("rag-safety")
        pad.notes.append("Evaluated retrieval and reasoning metrics")
        pad.tool_calls.append(invocation)
        for name, value in metrics.items():
            working.record_metric(name, value)
        working.completed_tasks.append("strategy")
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        working.debate.turns.append(
            DebateTurn(
                agent="strategist",
                role="Strategist",
                content="Prepared recommendation draft with evaluation metrics",
                grounding=[],
            )
        )
        self.checkpoints.save("strategist", working)
        return working


@dataclass
class AdversaryNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore
    prompts: DebatePrompts

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "adversary")
        guidance = self.prompts.adversary.get("principles", [])
        pad.notes.append("Stress-tested assumptions using adversary prompt")
        pad.tool_calls.append(
            ToolInvocation(
                name="debate.adversary.review",
                arguments={
                    "principles": [
                        rule["id"]
                        for rule in guidance
                        if isinstance(rule, dict) and "id" in rule
                    ]
                },
            )
        )
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        working.debate.turns.append(
            DebateTurn(
                agent="adversary",
                role="Adversary",
                content="Raised counterfactual risks based on constitutional rules",
                grounding=[],
            )
        )
        self.checkpoints.save("adversary", working)
        return working


@dataclass
class ConstitutionalCriticNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore
    prompts: DebatePrompts
    evaluation_gate: EvaluationGate

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "critic")
        pad.notes.append("Applied constitutional critic to evaluation metrics")
        passed, failures = self.evaluation_gate.check(working.metrics)
        pad.tool_calls.append(
            ToolInvocation(
                name="assurance.evals.gate",
                arguments={"metrics": list(self.evaluation_gate.minimums.keys())},
                response={"passed": passed, "failures": failures},
            )
        )
        working.record_metric("evaluation_passed", 1.0 if passed else 0.0)
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        verdict = (
            "Approved under constitution" if passed else "Requires operator review"
        )
        working.debate.turns.append(
            DebateTurn(
                agent="critic",
                role="ConstitutionalCritic",
                content=verdict,
                grounding=[],
            )
        )
        working.debate.verdict = verdict
        if not passed:
            for failure in failures:
                working.mark_failed(failure)
        self.checkpoints.save("critic", working)
        return working


@dataclass
class RecommenderNode:
    tools: ToolRegistry
    checkpoints: InMemoryCheckpointStore

    def __call__(self, state: StrategyState) -> StrategyState:
        working = state.copy()
        pad = ensure_agent_scratchpad(working, "recommender")
        if not working.failure_reasons:
            working.mark_complete()
        pad.notes.append("Composed decision brief and final recommendation")
        outcome = self.tools.compose_recommendation(
            working,
            workflow=(
                working.workflow
                if working.workflow
                else WorkflowMetadata(
                    workflow_id="wf-synthetic", tenant_id=working.tenant_id
                )
            ),
        )
        pad.tool_calls.append(
            ToolInvocation(
                name="decision.compose", arguments={"status": outcome.status.value}
            )
        )
        working.decision_brief = outcome.decision_brief
        working.metrics = dict(outcome.metrics)
        working.artefacts = outcome.graph
        working.workflow = outcome.workflow
        working.completed_tasks.append("recommendation")
        self.checkpoints.save("recommender", working)
        return working


def build_nodes(
    state: StrategyState,
    checkpoints: InMemoryCheckpointStore,
    prompts: DebatePrompts,
    evaluation_gate: EvaluationGate,
    minimum_pass_ratio: float,
) -> list:
    tools = ToolRegistry(state.tenant_id, state.query)
    return [
        ResearcherNode(tools, checkpoints),
        SynthesiserNode(tools, checkpoints, minimum_pass_ratio),
        StrategistNode(tools, checkpoints, evaluation_gate),
        AdversaryNode(tools, checkpoints, prompts),
        ConstitutionalCriticNode(tools, checkpoints, prompts, evaluation_gate),
        RecommenderNode(tools, checkpoints),
    ]
