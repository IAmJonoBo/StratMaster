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
        status = getattr(verification, "status", "skipped")
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
        metrics, invocation = self.tools.run_evaluations(
            "rag-safety", thresholds=self.evaluation_gate.minimums
        )
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
        
        # Apply constitutional review
        constitutional_violations = self._check_constitutional_compliance(working)
        
        # Apply evaluation gate
        passed, failures = self.evaluation_gate.check(working.metrics)
        
        # Enhanced critique based on constitutional principles
        critique_content = self._generate_constitutional_critique(
            working, constitutional_violations, passed, failures
        )
        
        pad.notes.append("Applied constitutional critic with comprehensive rule checking")
        pad.tool_calls.append(
            ToolInvocation(
                name="assurance.constitutional.review",
                arguments={
                    "metrics": list(self.evaluation_gate.minimums.keys()),
                    "constitutional_principles": list(self.prompts.critic.get("principles", {}).keys()),
                },
                response={
                    "passed": passed and len(constitutional_violations) == 0,
                    "failures": failures,
                    "constitutional_violations": constitutional_violations,
                },
            )
        )
        
        # Record comprehensive metrics
        working.record_metric("evaluation_passed", 1.0 if passed else 0.0)
        working.record_metric("constitutional_compliance", 1.0 if len(constitutional_violations) == 0 else 0.0)
        working.record_metric("total_critique_score", 1.0 if passed and len(constitutional_violations) == 0 else 0.0)
        
        if working.debate is None:
            working.debate = DebateTrace(turns=[])
        
        working.debate.turns.append(
            DebateTurn(
                agent="critic",
                role="ConstitutionalCritic",
                content=critique_content,
                grounding=[],
            )
        )
        
        # Set verdict based on comprehensive review
        overall_passed = passed and len(constitutional_violations) == 0
        working.debate.verdict = (
            "Approved under constitution and evaluation criteria"
            if overall_passed
            else "Requires review for constitutional and evaluation concerns"
        )
        
        # Mark failures comprehensively
        if not overall_passed:
            for failure in failures:
                working.mark_failed(f"Evaluation failure: {failure}")
            for violation in constitutional_violations:
                working.mark_failed(f"Constitutional violation: {violation}")
        
        self.checkpoints.save("critic", working)
        return working

    def _check_constitutional_compliance(self, state: StrategyState) -> list[str]:
        """Check state against constitutional principles."""
        violations = []
        
        critic_principles = self.prompts.critic.get("principles", [])
        
        for principle in critic_principles:
            principle_id = principle.get("id", "unknown")
            principle_rule = principle.get("rule", "")
            
            # Check sourcing compliance
            if principle_id == "factual_accuracy":
                if not state.claims or len(state.claims) == 0:
                    violations.append("No factual claims provided for accuracy review")
                else:
                    for claim in state.claims:
                        if not claim.provenance_ids or len(claim.provenance_ids) == 0:
                            violations.append(f"Claim '{claim.statement}' lacks required provenance")
            
            # Check proportionality/confidence calibration
            elif principle_id == "proportionality":
                if state.decision_brief and state.decision_brief.confidence > 0.9:
                    if not state.claims or all(claim.evidence_grade.value != "high" for claim in state.claims):
                        violations.append("High confidence not justified by evidence grade")
        
        # Check house rules
        house_principles = self.prompts.house.get("principles", [])
        for principle in house_principles:
            principle_id = principle.get("id", "unknown")
            
            if principle_id == "sourcing":
                # Check minimum two sources requirement
                all_provenance = set()
                for claim in state.claims:
                    all_provenance.update(claim.provenance_ids)
                if len(all_provenance) < 2:
                    violations.append("Insufficient sources: minimum two unique sources required")
        
        return violations

    def _generate_constitutional_critique(
        self, state: StrategyState, violations: list[str], eval_passed: bool, eval_failures: list[str]
    ) -> str:
        """Generate comprehensive constitutional critique."""
        critique_parts = []
        
        # Constitutional assessment
        if violations:
            critique_parts.append("CONSTITUTIONAL CONCERNS:")
            for violation in violations:
                critique_parts.append(f"- {violation}")
        else:
            critique_parts.append("✓ Constitutional principles satisfied")
        
        # Evaluation assessment
        if eval_failures:
            critique_parts.append("EVALUATION CONCERNS:")
            for failure in eval_failures:
                critique_parts.append(f"- {failure}")
        else:
            critique_parts.append("✓ Evaluation thresholds met")
        
        # Overall recommendation
        if not violations and eval_passed:
            critique_parts.append("\nRECOMMENDATION: Strategy meets constitutional and evaluation standards")
        else:
            critique_parts.append("\nRECOMMENDATION: Strategy requires revision before approval")
        
        return "\n".join(critique_parts)


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
