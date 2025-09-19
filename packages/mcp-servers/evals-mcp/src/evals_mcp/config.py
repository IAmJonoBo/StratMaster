"""Configuration for evals MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _threshold(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass
class Thresholds:
    ragas: float = field(
        default_factory=lambda: _threshold("EVALS_MCP_RAGAS_THRESHOLD", 0.75)
    )
    factscore: float = field(
        default_factory=lambda: _threshold("EVALS_MCP_FACTSCORE_THRESHOLD", 0.7)
    )
    truthfulqa: float = field(
        default_factory=lambda: _threshold("EVALS_MCP_TRUTHFULQA_THRESHOLD", 0.65)
    )


@dataclass
class AppConfig:
    thresholds: Thresholds


def load_config() -> AppConfig:
    return AppConfig(thresholds=Thresholds())
