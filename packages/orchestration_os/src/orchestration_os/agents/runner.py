"""Minimal multi-agent runner with governance checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


Tool = Callable[[str], str]


@dataclass(slots=True)
class Agent:
    name: str
    tool: Tool
    description: str

    def act(self, task: str) -> str:
        return self.tool(task)


@dataclass(slots=True)
class SafetyState:
    human_approved: bool = False
    guardrails_ok: bool = False
    eval_scores: dict[str, float] = field(default_factory=dict)

    def ready_to_deploy(self, min_eval_score: float = 0.8) -> bool:
        if not self.human_approved or not self.guardrails_ok:
            return False
        return all(score >= min_eval_score for score in self.eval_scores.values())


@dataclass(slots=True)
class SafeOrchestrator:
    agents: list[Agent]
    reviewers: list[str]
    safety_state: SafetyState = field(default_factory=SafetyState)

    def register_eval_score(self, name: str, score: float) -> None:
        self.safety_state.eval_scores[name] = score

    def mark_guardrails(self, passed: bool) -> None:
        self.safety_state.guardrails_ok = passed

    def approve(self, reviewer: str) -> None:
        if reviewer not in self.reviewers:
            raise PermissionError(f"Reviewer {reviewer} is not authorised")
        self.safety_state.human_approved = True

    def run(self, task: str, rounds: int = 2) -> list[str]:
        """Execute collaborative rounds between agents."""

        transcripts: list[str] = []
        for _ in range(rounds):
            for agent in self.agents:
                response = agent.act(task)
                transcripts.append(f"{agent.name}: {response}")
        return transcripts

    def safe_to_merge(self, min_eval_score: float = 0.8) -> bool:
        return self.safety_state.ready_to_deploy(min_eval_score=min_eval_score)
