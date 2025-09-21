"""Provider adapters for router MCP."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable

from .config import ProviderConfig

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import litellm
except ImportError:  # pragma: no cover
    litellm = None

try:  # pragma: no cover - optional dependency
    from rerankers.bge import BGEReranker
except ImportError:  # pragma: no cover
    BGEReranker = None  # type: ignore[assignment]


@dataclass
class ProviderAdapter:
    config: ProviderConfig
    _reranker: "BGEReranker | None" = field(init=False, default=None, repr=False)

    def complete(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
            try:  # pragma: no cover - network path
                response = litellm.completion(
                    model=self.config.completion_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=self.config.temperature,
                    api_base=self.config.base_url,
                    api_key=self.config.api_key,
                )
                text = response.choices[0].message["content"]  # type: ignore[attr-defined]
                tokens = response.usage["total_tokens"]  # type: ignore[index]
                provider = response.model  # type: ignore[attr-defined]
                return {
                    "text": text,
                    "tokens": tokens,
                    "provider": provider,
                    "model": self.config.completion_model,
                }
            except Exception as exc:
                logger.warning(
                    "Provider completion failed; falling back to synthetic",
                    exc_info=exc,
                )
        return {
            "text": prompt
            + "\nRecommended: consolidate premium positioning with phased rollout.",
            "tokens": min(len(prompt.split()) + 12, max_tokens),
            "provider": self.config.name,
            "model": self.config.completion_model,
        }

    def embed(self, inputs: Iterable[str], model: str) -> dict[str, Any]:
        vectors = []
        if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
            try:  # pragma: no cover
                response = litellm.embedding(
                    model=model or self.config.embedding_model,
                    input=list(inputs),
                    api_base=self.config.base_url,
                    api_key=self.config.api_key,
                )
                vectors = [item.embedding for item in response.data]  # type: ignore[attr-defined]
            except Exception as exc:
                logger.warning("Provider embedding failed; falling back", exc_info=exc)
        if not vectors:
            for text in inputs:
                vectors.append([float(ord(ch) % 17) / 16.0 for ch in text[:32]])
        return {
            "embeddings": vectors,
            "provider": self.config.name,
            "model": model or self.config.embedding_model,
        }

    def rerank(
        self, query: str, documents: list[dict[str, str]], top_k: int
    ) -> dict[str, Any]:
        if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
            try:  # pragma: no cover
                response = litellm.rerank(
                    model=self.config.rerank_model,
                    query=query,
                    documents=[doc["text"] for doc in documents],
                    api_base=self.config.base_url,
                    api_key=self.config.api_key,
                )
                results = [
                    {
                        "id": documents[idx]["id"],
                        "score": item.score,
                        "text": documents[idx]["text"],
                    }
                    for idx, item in enumerate(response.data)
                ]
                return {
                    "results": results[:top_k],
                    "provider": self.config.name,
                    "model": self.config.rerank_model,
                }
            except Exception as exc:
                logger.warning("Provider rerank failed; falling back", exc_info=exc)
        local_reranker = self._get_local_reranker()
        if local_reranker is not None:
            try:
                ranked = local_reranker.rerank(
                    query,
                    [
                        {
                            "id": doc.get("id"),
                            "text": doc.get("text", ""),
                        }
                        for doc in documents
                    ],
                    top_k=top_k,
                )
                results = [
                    {
                        "id": documents[item.index].get("id"),
                        "score": float(item.score),
                        "text": documents[item.index].get("text", ""),
                    }
                    for item in ranked
                    if isinstance(item.index, int) and 0 <= item.index < len(documents)
                ]
                return {
                    "results": results,
                    "provider": self.config.name,
                    "model": self.config.rerank_model,
                }
            except Exception as exc:
                logger.warning(
                    "Local BGE reranker failed; using heuristic fallback", exc_info=exc
                )
        scored = [
            {"id": doc["id"], "score": max(0.1, 1.0 - idx * 0.05), "text": doc["text"]}
            for idx, doc in enumerate(documents)
        ]
        return {
            "results": scored[:top_k],
            "provider": self.config.name,
            "model": self.config.rerank_model,
        }

    def _get_local_reranker(self) -> "BGEReranker | None":
        if self.config.name != "local" or BGEReranker is None:
            return None
        if self._reranker is None:
            try:
                self._reranker = BGEReranker(
                    model_name=self.config.rerank_model,
                    force_fallback=True,
                )
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("Unable to initialise BGE reranker", exc_info=exc)
                self._reranker = None
        return self._reranker
