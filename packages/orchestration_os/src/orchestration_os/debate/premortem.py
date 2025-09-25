"""Pre-mortem scenario modelling utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _default_risk_triggers() -> list[str]:
    return [
        "Latency above target for sustained period",
        "Error budget burn-rate exceeds threshold",
    ]


@dataclass(slots=True)
class Mitigation:
    risk: str
    action: str
    owner: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Mitigation":
        return cls(
            risk=str(payload.get("risk", "")),
            action=str(payload.get("action", "")),
            owner=str(payload.get("owner", "")),
        )


@dataclass(slots=True)
class PreMortemScenario:
    initiative: str
    time_horizon: str
    success_definition: str
    catastrophe: str
    risk_triggers: list[str] = field(default_factory=_default_risk_triggers)
    mitigations: list[Mitigation] = field(default_factory=list)
    confidence_score: float = 0.5

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "PreMortemScenario":
        mitigations = [Mitigation.from_dict(item) for item in payload.get("mitigations", [])]
        return cls(
            initiative=str(payload.get("initiative", "Unnamed initiative")),
            time_horizon=str(payload.get("time_horizon", "")),
            success_definition=str(payload.get("success_definition", "")),
            catastrophe=str(payload.get("catastrophe", "")),
            risk_triggers=[str(item) for item in payload.get("risk_triggers", _default_risk_triggers())],
            mitigations=mitigations,
            confidence_score=float(payload.get("confidence_score", 0.5)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "initiative": self.initiative,
            "time_horizon": self.time_horizon,
            "success_definition": self.success_definition,
            "catastrophe": self.catastrophe,
            "risk_triggers": self.risk_triggers,
            "mitigations": [mit.__dict__ for mit in self.mitigations],
            "confidence_score": self.confidence_score,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def render_markdown(self) -> str:
        lines = [
            f"# Pre-Mortem: {self.initiative}",
            "",
            f"**Time Horizon:** {self.time_horizon}",
            f"**Success Definition:** {self.success_definition}",
            f"**Catastrophe:** {self.catastrophe}",
            "",
            "## Risk Triggers",
        ]
        lines.extend(f"- {trigger}" for trigger in self.risk_triggers)
        lines.append("")
        lines.append("## Mitigations")
        if self.mitigations:
            for mitigation in self.mitigations:
                lines.append(f"- **{mitigation.risk}**: {mitigation.action} _(owner: {mitigation.owner})_")
        else:
            lines.append("- _No mitigations defined_")
        lines.append("")
        lines.append(f"**Confidence Score:** {self.confidence_score:.2f}")
        return "\n".join(lines)


def save_json(path: Path, scenario: PreMortemScenario) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario.to_dict(), indent=2), encoding="utf-8")


def save_markdown(path: Path, scenario: PreMortemScenario) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(scenario.render_markdown(), encoding="utf-8")


def load_scenario(path: Path) -> PreMortemScenario:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PreMortemScenario.from_dict(payload)
