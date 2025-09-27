from __future__ import annotations

import json
from pathlib import Path

import pytest

from stratmaster_evals.models import EvaluationRequest
from stratmaster_evals.trulens import TruLensRAGEvaluator


@pytest.fixture(scope="module")
def golden_request() -> EvaluationRequest:
    dataset_path = Path("data/evals/golden_rag_samples.json")
    payload = json.loads(dataset_path.read_text())
    return EvaluationRequest(
        **payload,
        experiment_name="golden-rag",
        model_name="router/test-model",
    )


def test_trulens_heuristic_passes_quality_gates(golden_request: EvaluationRequest) -> None:
    evaluator = TruLensRAGEvaluator()
    result = evaluator.evaluate(golden_request)

    assert result.metrics.groundedness > 0.75
    assert result.metrics.answer_relevance > 0.7
    assert result.metrics.support_coverage > 0.6
    assert result.passes_quality_gates is True
    assert result.failures == []
    assert result.metrics.analysis_latency_ms >= 0


def test_trulens_detects_low_grounding() -> None:
    evaluator = TruLensRAGEvaluator()
    request = EvaluationRequest(
        questions=["Summarise the quarterly revenue results."],
        contexts=[["The roadmap emphasises employee wellbeing programmes and hiring plans."]],
        answers=["Revenue climbed by 40 percent, which is unrelated to the contexts provided."],
        ground_truths=["The contexts do not mention revenue figures."],
        experiment_name="fail-case",
        model_name="router/test-model",
    )

    result = evaluator.evaluate(request)

    assert result.passes_quality_gates is False
    assert any("Groundedness" in failure for failure in result.failures)
    assert result.metrics.groundedness < result.metrics.GROUNDEDNESS_THRESHOLD
