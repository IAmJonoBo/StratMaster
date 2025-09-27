"""TruLens evaluation helpers for StratMaster RAG pipelines.

The true TruLens dependency is optional – when it is not available we fall back
on deterministic lexical heuristics that approximate the groundedness and
relevance checks described in SCRATCH.md. The heuristics are designed to be
stable and fast so that they can run in CI without external services while still
highlighting quality regressions.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .models import EvaluationRequest, TruLensMetrics

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import trulens_eval  # type: ignore

    TRULENS_AVAILABLE = True
except Exception:  # pragma: no cover - import failure is expected in CI
    TRULENS_AVAILABLE = False

_WORD_RE = re.compile(r"[\w']+")
_STOP_WORDS = {
    "the",
    "and",
    "in",
    "on",
    "with",
    "for",
    "by",
    "to",
    "of",
    "a",
    "an",
    "as",
    "at",
    "from",
    "this",
    "that",
    "it",
    "is",
    "was",
    "were",
    "are",
    "which",
    "what",
    "did",
    "team",
}


@dataclass
class TruLensEvaluation:
    """Aggregated TruLens evaluation output for a request."""

    metrics: TruLensMetrics
    passes_quality_gates: bool
    failures: list[str]
    sample_scores: list[dict[str, float]]
    backend: str
    analysis_ms: float

    def to_metadata(self) -> dict[str, Any]:
        """Convert the evaluation into metadata for Langfuse/telemetry payloads."""
        return {
            "backend": self.backend,
            "analysis_ms": self.analysis_ms,
            "passes_quality_gates": self.passes_quality_gates,
            "failures": self.failures,
            "sample_scores": self.sample_scores,
            "metrics": self.metrics.as_dict(),
        }


class TruLensRAGEvaluator:
    """Evaluate RAG answers using TruLens metrics with graceful fallback."""

    def __init__(self) -> None:
        self.backend = "trulens" if TRULENS_AVAILABLE else "heuristic"
        if TRULENS_AVAILABLE:
            logger.info("TruLens library detected – will attempt native evaluation")
        else:
            logger.info("TruLens not installed – using heuristic scoring backend")

    def evaluate(self, request: EvaluationRequest) -> TruLensEvaluation:
        """Evaluate the supplied samples and return aggregated metrics."""

        started = time.perf_counter()

        evaluation = None
        if TRULENS_AVAILABLE:
            try:  # pragma: no cover - depends on optional lib
                evaluation = self._evaluate_with_trulens(request)
            except Exception as exc:  # pragma: no cover - fallback path
                logger.warning(
                    "TruLens evaluation failed (%s) – falling back to heuristics",
                    exc,
                )

        if evaluation is None:
            evaluation = self._evaluate_with_heuristics(request)

        analysis_ms = (time.perf_counter() - started) * 1_000
        evaluation.metrics.analysis_latency_ms = analysis_ms
        evaluation.analysis_ms = analysis_ms
        return evaluation

    # ------------------------------------------------------------------
    # TruLens native integration (best effort)
    # ------------------------------------------------------------------
    def _evaluate_with_trulens(
        self, request: EvaluationRequest
    ) -> TruLensEvaluation | None:
        """Attempt to run TruLens if the dependency is installed."""

        # The OSS environment in this repository does not bundle a full TruLens
        # pipeline; native execution requires an LLM provider and configured
        # instrumentation. We therefore return ``None`` so the caller can fall
        # back to heuristics while still logging the attempted backend.
        logger.debug(
            "Native TruLens backend is not configured – skipping to heuristics"
        )
        return None

    # ------------------------------------------------------------------
    # Heuristic implementation – deterministic and fast
    # ------------------------------------------------------------------
    def _evaluate_with_heuristics(self, request: EvaluationRequest) -> TruLensEvaluation:
        sample_scores: list[dict[str, float]] = []
        groundedness_values: list[float] = []
        answer_relevance_values: list[float] = []
        context_relevance_values: list[float] = []
        support_coverage_values: list[float] = []

        for idx, (question, contexts, answer, truth) in enumerate(
            zip(
                request.questions,
                request.contexts,
                request.answers,
                request.ground_truths,
            )
        ):
            score = self._score_sample(question, contexts, answer, truth, idx)
            sample_scores.append(score)
            groundedness_values.append(score["groundedness"])
            answer_relevance_values.append(score["answer_relevance"])
            context_relevance_values.append(score["context_relevance"])
            support_coverage_values.append(score["support_coverage"])

        metrics = TruLensMetrics(
            groundedness=_mean(groundedness_values),
            answer_relevance=_mean(answer_relevance_values),
            context_relevance=_mean(context_relevance_values),
            support_coverage=_mean(support_coverage_values),
            analysis_latency_ms=0.0,
        )

        failures: list[str] = []
        if metrics.groundedness < metrics.GROUNDEDNESS_THRESHOLD:
            failures.append(
                f"Groundedness {metrics.groundedness:.2f} < {metrics.GROUNDEDNESS_THRESHOLD:.2f}"
            )
        if metrics.answer_relevance < metrics.ANSWER_THRESHOLD:
            failures.append(
                f"Answer relevance {metrics.answer_relevance:.2f} < {metrics.ANSWER_THRESHOLD:.2f}"
            )
        if metrics.context_relevance < metrics.CONTEXT_THRESHOLD:
            failures.append(
                f"Context relevance {metrics.context_relevance:.2f} < {metrics.CONTEXT_THRESHOLD:.2f}"
            )
        if metrics.support_coverage < metrics.SUPPORT_THRESHOLD:
            failures.append(
                f"Support coverage {metrics.support_coverage:.2f} < {metrics.SUPPORT_THRESHOLD:.2f}"
            )

        passes = not failures
        backend = "heuristic"

        return TruLensEvaluation(
            metrics=metrics,
            passes_quality_gates=passes,
            failures=failures,
            sample_scores=sample_scores,
            backend=backend,
            analysis_ms=0.0,
        )

    def _score_sample(
        self,
        question: str,
        contexts: Sequence[str],
        answer: str,
        ground_truth: str,
        index: int,
    ) -> dict[str, float]:
        question_tokens = _tokenise(question)
        answer_tokens = _tokenise(answer)
        context_tokens = [_tokenise(ctx) for ctx in contexts]
        truth_tokens = _tokenise(ground_truth) if ground_truth else set()

        combined_context = set().union(*context_tokens) if context_tokens else set()
        groundedness = _overlap_ratio(answer_tokens, combined_context)

        reference_tokens = truth_tokens or question_tokens
        answer_relevance = _f1_overlap(answer_tokens, reference_tokens)

        context_relevance = _overlap_ratio(question_tokens, combined_context)

        if answer_tokens and context_tokens:
            supporting = [
                _overlap_ratio(answer_tokens, tokens) for tokens in context_tokens
            ]
            support_coverage = sum(1 for value in supporting if value >= 0.2) / len(
                supporting
            )
        else:
            support_coverage = 0.0

        score = {
            "index": float(index),
            "groundedness": groundedness,
            "answer_relevance": answer_relevance,
            "context_relevance": context_relevance,
            "support_coverage": support_coverage,
        }

        return score


def _tokenise(text: str) -> set[str]:
    if not text:
        return set()
    tokens = set()
    for match in _WORD_RE.finditer(text):
        token = match.group(0).lower()
        if len(token) <= 2:
            continue
        if token in _STOP_WORDS:
            continue
        tokens.add(token)
    return tokens


def _overlap_ratio(source: Iterable[str], reference: Iterable[str]) -> float:
    source_set = set(source)
    reference_set = set(reference)
    if not source_set:
        return 0.0
    if not reference_set:
        return 0.0
    overlap = len(source_set & reference_set)
    return overlap / len(source_set)


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _f1_overlap(source: Iterable[str], reference: Iterable[str]) -> float:
    source_set = set(source)
    reference_set = set(reference)
    if not source_set or not reference_set:
        return 0.0
    overlap = len(source_set & reference_set)
    if overlap == 0:
        return 0.0
    precision = overlap / len(source_set)
    recall = overlap / len(reference_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


__all__ = ["TruLensRAGEvaluator", "TruLensEvaluation", "TRULENS_AVAILABLE"]
