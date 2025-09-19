"""Pydantic data models for knowledge MCP responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    score: float = Field(..., ge=0)
    method: Literal["dense", "sparse", "hybrid", "colbert", "splade", "rerank"]
    snippet: str
    source_url: HttpUrl
    metadata: dict[str, str] = Field(default_factory=dict)


class HybridQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    alpha_dense: float = Field(default=0.6, ge=0, le=1)
    alpha_sparse: float = Field(default=0.4, ge=0, le=1)


class HybridQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: list[RetrievalHit]
    dense_score_weight: float
    sparse_score_weight: float


class ColbertSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class RankingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str
    documents: list[str]


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reranked: list[RetrievalHit]


class GraphSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    community_id: str
    title: str
    summary: str
    representative_nodes: list[str]


class CommunitySummariesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summaries: list[GraphSummary]


class ConnectorStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    available: bool
    last_error: str | None = None


class ServiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collections: list[str]
    dense_index: str
    sparse_index: str
    graph_space: str
    connectors: dict[str, ConnectorStatus] = Field(default_factory=dict)


class InfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    capabilities: list[str]
    service: ServiceInfo
