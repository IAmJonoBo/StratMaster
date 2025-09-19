"""Pydantic schemas for router MCP."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    prompt: str
    max_tokens: int = Field(default=256, ge=16, le=4096)
    temperature: float = Field(default=0.2, ge=0, le=2)


class CompletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    tokens: int
    provider: str
    model: str


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    input: list[str]
    model: str = "bge-small"


class EmbeddingVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    vector: list[float]


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embeddings: list[EmbeddingVector]
    provider: str
    model: str


class RerankItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str


class RerankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str
    documents: list[RerankItem]
    top_k: int = Field(default=5, ge=1, le=50)


class RerankResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    score: float
    text: str


class RerankResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[RerankResult]
    provider: str
    model: str


class ServiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_completion_model: str
    default_embedding_model: str
    default_rerank_model: str
    providers: list[str]


class InfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    capabilities: list[str]
    service: ServiceInfo
