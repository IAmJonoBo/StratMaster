"""Deterministic DSPy program stubs with simple telemetry hooks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class DSPyArtifact(BaseModel):
    """Serializable artifact persisted after compilation."""

    model_config = ConfigDict(extra="forbid")

    program_name: str
    version: str
    created_at: datetime
    prompt: str
    steps: list[str]


@dataclass
class TelemetryRecorder:
    """Trivial telemetry recorder used in tests to capture events."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        enriched = payload | {
            "event_type": event_type,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
        self.events.append(enriched)


@dataclass
class ResearchPlanner:
    """DSPy-style planner that emits deterministic task lists."""

    program_name: str = "research_planner"
    version: str = "2024.10.01"
    prompt: str = (
        "Generate research tasks covering market sizing, competition, and risks."
    )

    def plan(self, query: str) -> list[str]:
        base = query.strip().title() or "Strategy"
        return [
            f"Quantify demand signals for {base}",
            f"Map competitive landscape impacting {base}",
            f"Identify regulatory or ethical risks for {base}",
        ]

    def compile(self, query: str) -> DSPyArtifact:
        steps = self.plan(query)
        return DSPyArtifact(
            program_name=self.program_name,
            version=self.version,
            created_at=datetime.now(tz=UTC),
            prompt=self.prompt,
            steps=steps,
        )

    def save(self, artifact: DSPyArtifact, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = artifact.model_dump(mode="json")
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load(self, path: Path) -> DSPyArtifact:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DSPyArtifact.model_validate(data)


def compile_research_planner(
    query: str,
    output_dir: Path | None = None,
    telemetry: TelemetryRecorder | None = None,
) -> Path:
    """Compile the research planner and persist its artifact."""

    planner = ResearchPlanner()
    artifact = planner.compile(query)
    target_dir = output_dir or Path("packages/dsp/dspy_programs")
    artifact_path = target_dir / f"{planner.program_name}-{planner.version}.json"
    planner.save(artifact, artifact_path)
    if telemetry is not None:
        telemetry.record(
            "dspy.compile",
            {
                "program": planner.program_name,
                "version": planner.version,
                "artifact_path": str(artifact_path),
            },
        )
    return artifact_path
