# mypy: ignore-errors
"""Pydantic schemas for router MCP."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    prompt: str
    max_tokens: int = Field(default=256, ge=16, le=4096)
    temperature: float = Field(default=0.2, ge=0, le=2)
    task: str = Field(default="reasoning")


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
    task: str = Field(default="embedding")


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
    task: str = Field(default="rerank")


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


# Sprint 1 - Dynamic Agent Selection Models
class AgentRouteRequest(BaseModel):
    """Request for agent routing - Sprint 1 implementation."""
    model_config = ConfigDict(extra="forbid")

    query: str
    tenant_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    policy_flags: dict[str, bool] = Field(default_factory=dict)


class AgentRouteResponse(BaseModel):
    """Response from agent routing - Sprint 1 implementation."""
    model_config = ConfigDict(extra="forbid")

    selected_agents: list[str]
    rationale: str
    confidence: float
    routing_metadata: dict[str, Any]
    tenant_id: str
