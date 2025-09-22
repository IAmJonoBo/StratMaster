"""In-memory checkpoint store for LangGraph state snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .state import StrategyState


@dataclass
class CheckpointRecord:
    node: str
    state: StrategyState


@dataclass
class InMemoryCheckpointStore:
    """Minimal checkpoint store used by tests and deterministic runs."""

    records: list[CheckpointRecord] = field(default_factory=list)

    def save(self, node: str, state: StrategyState) -> None:
        self.records.append(CheckpointRecord(node=node, state=state.copy()))

    def latest(self) -> CheckpointRecord | None:
        return self.records[-1] if self.records else None

    def history(self) -> Iterable[CheckpointRecord]:
        return list(self.records)

    def clear(self) -> None:
        self.records.clear()
