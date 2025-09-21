"""FastAPI service exposing the BGE reranker."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .reranker import BGEReranker

logger = logging.getLogger(__name__)


class RerankRequest(BaseModel):
    query: str = Field(..., description="Query text")
    candidates: list[str] = Field(..., description="Candidate strings to rerank")
    top_k: int | None = Field(None, description="Optional number of results to return")


class RerankResponse(BaseModel):
    results: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str


def _build_reranker() -> BGEReranker:
    return BGEReranker(
        model_name=os.getenv("RERANKERS_BGE_MODEL", "BAAI/bge-reranker-base"),
        device=os.getenv("RERANKERS_BGE_DEVICE", "auto"),
        batch_size=int(os.getenv("RERANKERS_BGE_BATCH_SIZE", "16")),
        force_fallback=os.getenv("RERANKERS_BGE_FORCE_FALLBACK", "0").lower()
        in {"1", "true", "yes", "on"},
    )


@lru_cache(maxsize=1)
def _cached_reranker() -> BGEReranker:
    return _build_reranker()


def create_app(reranker: BGEReranker | None = None) -> FastAPI:
    app = FastAPI(title="BGE Reranker Service", version="0.1.0")
    service_reranker = reranker or _cached_reranker()

    @app.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:  # pragma: no cover - trivial
        return HealthResponse(status="ok")

    @app.post("/rerank", response_model=RerankResponse)
    def rerank(payload: RerankRequest) -> RerankResponse:
        try:
            results = service_reranker.rerank(
                payload.query, payload.candidates, top_k=payload.top_k
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("Rerank request failed")
            raise HTTPException(status_code=500, detail="rerank_failed") from exc
        serialised = [
            {
                "text": item.text,
                "score": item.score,
                "index": item.index,
                **({"id": item.id} if item.id is not None else {}),
            }
            for item in results
        ]
        return RerankResponse(results=serialised)

    return app


def main() -> None:  # pragma: no cover - CLI entrypoint
    import uvicorn

    uvicorn.run(
        "rerankers.bge.service:create_app",
        host=os.getenv("RERANKERS_BGE_HOST", "0.0.0.0"),
        port=int(os.getenv("RERANKERS_BGE_PORT", "8090")),
        factory=True,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
