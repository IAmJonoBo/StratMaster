"""BGE reranker utilities with optional transformer-backed scoring."""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass
from typing import Iterator, List, Sequence

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional heavy dependency
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:  # pragma: no cover - fallback path
    torch = None  # type: ignore[assignment]
    AutoModelForSequenceClassification = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]

_FORCE_FALLBACK = os.getenv("RERANKERS_BGE_FORCE_FALLBACK", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@dataclass(slots=True)
class RerankedDocument:
    """Simple data container representing a reranked candidate."""

    text: str
    score: float
    index: int
    id: str | None = None
    metadata: dict[str, str] | None = None


class BGEReranker:
    """Compute similarity scores using BGE cross-encoder models.

    The implementation loads HuggingFace transformers when available and falls
    back to a deterministic lexical scoring heuristic otherwise. This makes the
    reranker usable in CI environments without GPU access or large downloads.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        *,
        device: str = "auto",
        batch_size: int = 16,
        force_fallback: bool | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = max(1, batch_size)
        self.requested_device = device
        self.device = "cpu"
        self._model = None
        self._tokenizer = None
        self._force_fallback = _FORCE_FALLBACK if force_fallback is None else force_fallback
        if not self._force_fallback:
            self._initialise_transformer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def score(self, query: str, candidates: Sequence[str]) -> List[float]:
        """Return relevance scores aligned with *candidates* order."""

        records = self._prepare_candidates(candidates)
        scored = self._score(query, records)
        return [item.score for item in scored]

    def rerank(
        self,
        query: str,
        candidates: Sequence[str | dict[str, str]],
        *,
        top_k: int | None = None,
    ) -> List[RerankedDocument]:
        """Return candidates sorted by descending score.

        Items may be passed as plain strings or dictionaries containing `text`
        alongside identifiers/metadata. Metadata is preserved in the returned
        :class:`RerankedDocument` instances.
        """

        prepared = self._prepare_candidates(candidates)
        scored = self._score(query, prepared)
        scored.sort(key=lambda item: item.score, reverse=True)
        if top_k is not None:
            scored = scored[: max(0, top_k)]
        return scored

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _initialise_transformer(self) -> None:
        if AutoTokenizer is None or AutoModelForSequenceClassification is None or torch is None:
            logger.info("Transformers not available; using lexical fallback for BGE reranker")
            self._force_fallback = True
            return
        self.device = self._resolve_device(self.requested_device)
        try:  # pragma: no cover - network initialisation requires real model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            if self.device != "cpu":
                self._model.to(self.device)  # type: ignore[call-arg]
            self._model.eval()
        except Exception as exc:  # pragma: no cover - avoid hard failure offline
            logger.warning(
                "Failed to initialise transformers model %s; falling back to lexical scoring",
                self.model_name,
                exc_info=exc,
            )
            self._model = None
            self._tokenizer = None
            self.device = "cpu"
            self._force_fallback = True

    def _resolve_device(self, requested: str) -> str:
        if requested == "auto":
            if torch is not None and getattr(torch.cuda, "is_available", lambda: False)():
                return "cuda"
            return "cpu"
        if requested.startswith("cuda") and torch is not None:
            if getattr(torch.cuda, "is_available", lambda: False)():
                return requested
            logger.warning("CUDA requested but unavailable; using CPU instead")
            return "cpu"
        return requested

    def _prepare_candidates(
        self, candidates: Sequence[str | dict[str, str]]
    ) -> List[RerankedDocument]:
        prepared: List[RerankedDocument] = []
        for idx, candidate in enumerate(candidates):
            if isinstance(candidate, dict):
                text = candidate.get("text", "")
                cid = candidate.get("id")
                metadata = {
                    key: value
                    for key, value in candidate.items()
                    if key not in {"text", "id"}
                }
            else:
                text = str(candidate)
                cid = None
                metadata = {}
            prepared.append(
                RerankedDocument(text=text, score=0.0, index=idx, id=cid, metadata=metadata)
            )
        return prepared

    def _score(
        self, query: str, candidates: Sequence[RerankedDocument]
    ) -> List[RerankedDocument]:
        if not candidates:
            return []
        if self._force_fallback or self._model is None or self._tokenizer is None:
            return self._lexical_scores(query, candidates)
        try:
            return self._transformer_scores(query, candidates)
        except Exception as exc:  # pragma: no cover - GPU or runtime failure
            logger.warning("Transformer rerank failed; falling back", exc_info=exc)
            return self._lexical_scores(query, candidates)

    def _transformer_scores(
        self, query: str, candidates: Sequence[RerankedDocument]
    ) -> List[RerankedDocument]:
        assert self._model is not None and self._tokenizer is not None  # for type checkers
        results: List[RerankedDocument] = []
        texts = [item.text for item in candidates]
        for chunk in _chunk(texts, self.batch_size):
            encoded = self._tokenizer(
                [query] * len(chunk),
                list(chunk),
                truncation=True,
                padding=True,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            logits = self._model(**encoded).logits.squeeze(-1)
            scores = logits.detach().cpu().tolist()
            if not isinstance(scores, list):
                scores = [float(scores)]
            for score in scores:
                doc = candidates[len(results)]
                results.append(
                    RerankedDocument(
                        text=doc.text,
                        score=float(score),
                        index=doc.index,
                        id=doc.id,
                        metadata=doc.metadata,
                    )
                )
        return results

    def _lexical_scores(
        self, query: str, candidates: Sequence[RerankedDocument]
    ) -> List[RerankedDocument]:
        query_tokens = _tokenise(query)
        query_counts = _term_counts(query_tokens)
        query_weights = _weights(query_counts)
        query_bigrams = set(_bigrams(query_tokens))
        scored: List[RerankedDocument] = []
        for doc in candidates:
            tokens = _tokenise(doc.text)
            counts = _term_counts(tokens)
            weights = _weights(counts)
            score = _cosine_similarity(query_weights, weights)
            overlap = set(query_weights).intersection(weights)
            match_count = sum(min(query_counts[token], counts[token]) for token in overlap)
            length_penalty = 1.0 / (1 + len(tokens))
            doc_bigrams = set(_bigrams(tokens))
            bigram_matches = len(query_bigrams.intersection(doc_bigrams))
            score += 0.05 * match_count + 0.02 * length_penalty + 0.2 * bigram_matches
            scored.append(
                RerankedDocument(
                    text=doc.text,
                    score=score,
                    index=doc.index,
                    id=doc.id,
                    metadata=doc.metadata,
                )
            )
        return scored


def _tokenise(text: str) -> List[str]:
    return [part for part in text.lower().split() if part]


def _term_counts(tokens: Sequence[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _weights(counts: dict[str, int]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {token: value / norm for token, value in counts.items()}


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    shared = set(vec_a).intersection(vec_b)
    score = sum(vec_a[token] * vec_b[token] for token in shared)
    return float(score)


def _chunk(items: Sequence[str], size: int) -> Iterator[Sequence[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _bigrams(tokens: Sequence[str]) -> Sequence[str]:
    return [" ".join(tokens[idx : idx + 2]) for idx in range(len(tokens) - 1)]


__all__ = ["BGEReranker", "RerankedDocument"]
