"""Service layer for router MCP."""

from __future__ import annotations

import json
from typing import Iterable

from fastapi import HTTPException

from .config import AppConfig
from .models import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingVector,
    RerankRequest,
    RerankResponse,
    RerankResult,
)
from .providers import ProviderAdapter


class RouterService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider = ProviderAdapter(config.default_provider)
        self.decoding_cfg = config.structured_decoding

    def complete(self, payload: CompletionRequest) -> CompletionResponse:
        result = self.provider.complete(payload.prompt, payload.max_tokens)
        text = self._ensure_structured(result["text"])
        return CompletionResponse(
            text=text,
            tokens=int(result["tokens"]),
            provider=result.get("provider", self.config.default_provider.name),
            model=result.get("model", self.config.default_provider.completion_model),
        )

    def embed(self, payload: EmbeddingRequest) -> EmbeddingResponse:
        result = self.provider.embed(payload.input, payload.model)
        vectors = [
            EmbeddingVector(index=idx, vector=vec)
            for idx, vec in enumerate(result["embeddings"])
        ]
        return EmbeddingResponse(
            embeddings=vectors,
            provider=result.get("provider", self.config.default_provider.name),
            model=result.get(
                "model", payload.model or self.config.default_provider.embedding_model
            ),
        )

    def rerank(self, payload: RerankRequest) -> RerankResponse:
        docs = [{"id": item.id, "text": item.text} for item in payload.documents]
        result = self.provider.rerank(payload.query, docs, payload.top_k)
        ranked = [
            RerankResult(id=item["id"], score=float(item["score"]), text=item["text"])
            for item in result["results"]
        ]
        return RerankResponse(
            results=ranked[: payload.top_k],
            provider=result.get("provider", self.config.default_provider.name),
            model=result.get("model", self.config.default_provider.rerank_model),
        )

    def _ensure_structured(self, text: str) -> str:
        cfg = self.decoding_cfg.get("llm", {})
        if not cfg.get("json_mode"):
            return text
        try:
            json.loads(text)
            return text
        except Exception:
            strict = self.decoding_cfg.get("schema_validation", {}).get("strict", False)
            fallback_obj = {
                "summary": text,
                "provider": self.config.default_provider.name,
            }
            fallback = json.dumps(fallback_obj)
            try:
                json.loads(fallback)
            except Exception as exc:  # pragma: no cover
                if strict:
                    raise HTTPException(
                        status_code=500, detail="structured decoding failed"
                    ) from exc
                return text
            if strict:
                # emit structured fallback instead of raising
                return fallback
            return fallback

    # synthetic helpers now live in ProviderAdapter fallback
