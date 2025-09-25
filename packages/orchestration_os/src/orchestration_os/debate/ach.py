"""ACH matrix modelling, critique, and serialization utilities."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(slots=True)
class Hypothesis:
    """Represents a single hypothesis under consideration."""

    id: str
    statement: str


@dataclass(slots=True)
class EvidenceAssessment:
    """Evaluation of how a single evidence item maps to hypotheses."""

    evidence_id: str
    description: str
    assessments: dict[str, str]
    weight: float = 1.0

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "EvidenceAssessment":
        return cls(
            evidence_id=str(payload["id"]),
            description=str(payload.get("description", "")),
            assessments={k: str(v) for k, v in dict(payload.get("assessments", {})).items()},
            weight=float(payload.get("weight", 1.0)),
        )


@dataclass(slots=True)
class Decision:
    verdict: str
    rationale: str
    confidence: float | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Decision":
        return cls(
            verdict=str(payload.get("verdict", "undecided")),
            rationale=str(payload.get("rationale", "")),
            confidence=(float(payload["confidence"]) if "confidence" in payload else None),
        )


@dataclass(slots=True)
class ACHMatrix:
    """In-memory representation of an ACH matrix and associated critiques."""

    title: str
    context: str
    hypotheses: list[Hypothesis]
    evidence: list[EvidenceAssessment]
    decision: Decision
    actions: list[dict[str, str]] = field(default_factory=list)
    critiques: list[str] = field(default_factory=list)
    consistency_warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ACHMatrix":
        hypotheses = [
            Hypothesis(id=str(item["id"]), statement=str(item.get("statement", "")))
            for item in payload.get("hypotheses", [])
        ]
        evidence = [EvidenceAssessment.from_dict(item) for item in payload.get("evidence", [])]
        decision = Decision.from_dict(dict(payload.get("decision", {})))
        actions = [dict(action) for action in payload.get("actions", [])]
        return cls(
            title=str(payload.get("title", "Untitled ACH")),
            context=str(payload.get("context", "")),
            hypotheses=hypotheses,
            evidence=evidence,
            decision=decision,
            actions=actions,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "context": self.context,
            "hypotheses": [asdict(hyp) for hyp in self.hypotheses],
            "evidence": [
                {
                    "id": item.evidence_id,
                    "description": item.description,
                    "assessments": item.assessments,
                    "weight": item.weight,
                }
                for item in self.evidence
            ],
            "decision": {
                "verdict": self.decision.verdict,
                "rationale": self.decision.rationale,
                "confidence": self.decision.confidence,
            },
            "actions": self.actions,
            "critiques": self.critiques,
            "consistency_warnings": self.consistency_warnings,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    # --- Evaluation helpers -------------------------------------------------
    def evaluate(self, critique_level: str = "standard") -> None:
        """Perform self-consistency and constitutional critiques."""

        self.consistency_warnings = list(self._self_consistency_warnings())
        self.critiques = list(self._constitutional_critiques(level=critique_level))
        if self.decision.confidence is None:
            self.decision.confidence = self._estimate_confidence()

    def _self_consistency_warnings(self) -> Iterable[str]:
        hypothesis_ids = {hyp.id for hyp in self.hypotheses}
        if not hypothesis_ids:
            yield "No hypotheses defined."
            return
        evidence_seen = set()
        for item in self.evidence:
            evidence_seen.add(item.evidence_id)
            missing = hypothesis_ids - set(item.assessments)
            if missing:
                yield f"Evidence {item.evidence_id} missing assessments for {', '.join(sorted(missing))}."
            if item.weight <= 0:
                yield f"Evidence {item.evidence_id} has non-positive weight."
        if not evidence_seen:
            yield "No evidence captured."
        for hyp in self.hypotheses:
            if all(
                item.assessments.get(hyp.id, "unknown").lower() == "unknown" for item in self.evidence
            ):
                yield f"Hypothesis {hyp.id} is never evaluated by evidence."

    def _constitutional_critiques(self, level: str) -> Iterable[str]:
        level = level.lower()
        if not self.context:
            yield "Context is empty; articulate mission/user need before proceeding."
        if level in {"standard", "strict"}:
            if not self.actions:
                yield "No follow-up actions defined for decision implementation."
            if "rollback" not in " ".join(action.get("description", "").lower() for action in self.actions):
                yield "Fallback/rollback criteria missing from actions."
        if level == "strict":
            if not self.decision.rationale:
                yield "Decision rationale missing under strict critique."
            if self.decision.verdict.lower() == "proceed" and self.consistency_warnings:
                yield "Cannot proceed while self-consistency warnings remain."
        guardrail_mentions = [
            "slo" in self.decision.rationale.lower(),
            "dora" in self.decision.rationale.lower(),
            "risk" in self.decision.rationale.lower(),
        ]
        if guardrail_mentions.count(True) < 2:
            yield "Decision rationale should mention SLO/DORA impact explicitly."

    def _estimate_confidence(self) -> float:
        if not self.evidence:
            return 0.0
        support_weight = 0.0
        total_weight = 0.0
        verdict = self.decision.verdict.lower()
        verdict_id = None
        for hyp in self.hypotheses:
            if hyp.statement.lower() in verdict or hyp.id.lower() in verdict:
                verdict_id = hyp.id
                break
        for item in self.evidence:
            decision = item.assessments.get(verdict_id or "", "unknown").lower()
            if decision == "support":
                support_weight += item.weight
            if decision in {"support", "contradict", "unknown"}:
                total_weight += item.weight
        return round((support_weight / total_weight) if total_weight else 0.0, 2)


# --- Persistence helpers ----------------------------------------------------

def update_board(board_path: Path, matrix: ACHMatrix) -> None:
    """Update the ACH board markdown table with the latest verdict."""

    row = _board_row(matrix)
    board_path.parent.mkdir(parents=True, exist_ok=True)
    if not board_path.exists():
        board_path.write_text("# ACH Decision Board\n\n| Title | Verdict | Confidence | Last Updated | Critique Issues |\n| --- | --- | --- | --- | --- |\n", encoding="utf-8")
    lines = board_path.read_text(encoding="utf-8").splitlines()
    header_end = 0
    for idx, line in enumerate(lines):
        header_end = idx
        if line.strip().startswith("| ---"):
            break
    entries = lines[header_end + 1 :]
    header = lines[: header_end + 1]
    updated = False
    for index, entry in enumerate(entries):
        if entry.startswith(f"| {matrix.title} |"):
            entries[index] = row
            updated = True
            break
    if not updated:
        entries = [line for line in entries if line.strip()] + [row]
    board_path.write_text("\n".join(header + entries) + "\n", encoding="utf-8")


def save_result(path: Path, matrix: ACHMatrix) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(matrix.to_dict(), indent=2), encoding="utf-8")


def export_yaml(path: Path, matrix: ACHMatrix) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(matrix.to_dict(), sort_keys=False), encoding="utf-8")


def _board_row(matrix: ACHMatrix) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    confidence = matrix.decision.confidence if matrix.decision.confidence is not None else 0.0
    issues = ", ".join(matrix.critiques or matrix.consistency_warnings) or "None"
    if len(issues) > 80:
        issues = issues[:77] + "..."
    return f"| {matrix.title} | {matrix.decision.verdict} | {confidence:.2f} | {timestamp} | {issues} |"


def load_matrix(path: Path) -> ACHMatrix:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ACHMatrix.from_dict(payload)
