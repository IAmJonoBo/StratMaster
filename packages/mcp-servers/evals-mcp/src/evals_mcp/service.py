"""Evaluation service producing synthetic metrics while honouring thresholds."""

from __future__ import annotations

from uuid import uuid4

from .config import AppConfig
from .models import EvalRunRequest, EvalRunResponse


class EvalsService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def run(self, payload: EvalRunRequest) -> EvalRunResponse:
        metrics = self._generate_metrics(payload.suite)
        thresholds = payload.thresholds or self._default_thresholds_for_suite(
            payload.suite
        )
        passed = all(
            metrics.get(name, 0.0) >= value for name, value in thresholds.items()
        )
        return EvalRunResponse(
            run_id=f"eval-{uuid4().hex[:8]}",
            passed=passed,
            metrics=metrics,
        )

    def _generate_metrics(self, suite: str) -> dict[str, float]:
        if suite == "rag":
            return {"ragas": 0.82, "grounding": 0.85}
        if suite == "truthfulqa":
            return {"truthfulqa": 0.68, "hallucination_rate": 0.02}
        if suite == "factscore":
            return {"factscore": 0.78}
        return {"custom_metric": 0.5}

    def _default_thresholds_for_suite(self, suite: str) -> dict[str, float]:
        thresholds = self.config.thresholds
        if suite == "rag":
            return {"ragas": thresholds.ragas}
        if suite == "truthfulqa":
            return {"truthfulqa": thresholds.truthfulqa}
        if suite == "factscore":
            return {"factscore": thresholds.factscore}
        return {}
