"""Compression MCP models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    text: str
    target_tokens: int = Field(default=128, ge=16, le=2048)
    mode: str = Field(default="summary")


class CompressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compressed: str
    original_tokens: int
    compressed_tokens: int
    provider: str
