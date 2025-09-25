"""Public exports for the StratMaster orchestrator package with lazy loading."""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "DecisionSupportBundle",
    "build_strategy_graph",
    "OrchestrationResult",
    "run_decision_workflow",
    "StrategyState",
]


def __getattr__(name: str) -> Any:
    if name == "build_strategy_graph":
        module = importlib.import_module(".graph", __name__)
        return getattr(module, name)
    if name in {"OrchestrationResult", "StrategyState"}:
        module = importlib.import_module(".state", __name__)
        return getattr(module, name)
    if name in {"DecisionSupportBundle", "run_decision_workflow"}:
        module = importlib.import_module(".decision_support", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
