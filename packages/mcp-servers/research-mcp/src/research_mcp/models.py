"""Structured request/response models for the research MCP server."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: HttpUrl
    snippet: str
    fetched_at: datetime


class MetasearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    query: str = Field(..., min_length=3)
    limit: int = Field(default=5, ge=1, le=20)


class MetasearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    results: list[SearchResult]


class CrawlSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    obey_robots: bool = True
    max_depth: int = Field(default=1, ge=1, le=3)
    render_js: bool = False


class CrawlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    spec: CrawlSpec


class CrawlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    status: Literal["cached", "fetched"]
    content: str
    sha256: str
    fetched_at: datetime
    cache_key: str


class ProvenanceResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    sha256: str
    fetched_at: datetime
    cache_key: str


class CachedPageResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    content: str
    fetched_at: datetime
    sha256: str
