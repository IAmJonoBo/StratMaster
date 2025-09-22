"""Deterministic cosine-style scoring emulating BGE reranking."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .models import RerankRequest, RerankResult

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _tokenise(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _vectorise(text: str) -> dict[str, float]:
    tokens = _tokenise(text)
    weights: dict[str, float] = {}
    for token in tokens:
        weights[token] = weights.get(token, 0.0) + 1.0
    norm = math.sqrt(sum(val * val for val in weights.values())) or 1.0
    return {token: weight / norm for token, weight in weights.items()}


def _similarity(query_vec: dict[str, float], doc_vec: dict[str, float]) -> float:
    overlap = set(query_vec) & set(doc_vec)
    return sum(query_vec[token] * doc_vec[token] for token in overlap)


@dataclass(slots=True)
class BGEReranker:
    model_name: str = "BAAI/bge-reranker-base"

    def rerank(
        self, request: RerankRequest | None = None, **kwargs: object
    ) -> list[RerankResult]:
        if request is None:
            request = RerankRequest(**kwargs)  # type: ignore[arg-type]
        query_vec = _vectorise(request.query)
        results: list[RerankResult] = []
        for doc in request.documents:
            doc_vec = _vectorise(doc.text)
            score = _similarity(query_vec, doc_vec)
            results.append(RerankResult(id=doc.id, text=doc.text, score=score, rank=0))
        results.sort(key=lambda item: item.score, reverse=True)
        for idx, item in enumerate(results[: request.top_k], start=1):
            item.rank = idx
        return results[: request.top_k]
