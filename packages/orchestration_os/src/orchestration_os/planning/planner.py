"""Planning backlog helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(slots=True)
class PlanSlice:
    strategy_id: str
    epic: str
    slice: str
    lead_time_days: int
    status: str
    dependencies: list[str]


@dataclass(slots=True)
class PlanBacklog:
    items: list[PlanSlice]

    @classmethod
    def load(cls, path: Path) -> "PlanBacklog":
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        items = [
            PlanSlice(
                strategy_id=str(item.get("strategy_id")),
                epic=str(item.get("epic")),
                slice=str(item.get("slice")),
                lead_time_days=int(item.get("lead_time_days", 0)),
                status=str(item.get("status", "unknown")),
                dependencies=[str(dep) for dep in item.get("dependencies", [])],
            )
            for item in payload
        ]
        return cls(items=items)

    def lead_time_by_epic(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in self.items:
            result.setdefault(item.epic, 0)
            result[item.epic] += item.lead_time_days
        return result


def generate_epic_breakdown(backlog: PlanBacklog) -> str:
    """Render a markdown table summarising epics and slices."""

    lines = ["| Epic | Slice | Lead Time (days) | Status | Dependencies |", "| --- | --- | --- | --- | --- |"]
    for item in backlog.items:
        deps = "<br/>".join(item.dependencies) if item.dependencies else "-"
        lines.append(
            f"| {item.epic} | {item.slice} | {item.lead_time_days} | {item.status} | {deps} |"
        )
    return "\n".join(lines)
