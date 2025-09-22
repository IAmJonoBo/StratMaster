"""Pydantic models for BGE reranker requests/responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RerankDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str


class RerankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    documents: list[RerankDocument]
    top_k: int = Field(default=5, ge=1, le=50)
    device: str = "cpu"


class RerankResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    score: float
    text: str
    rank: int
