"""Base models for Expert Council system."""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Model(BaseModel):
    """Base model with standard configuration for Expert Council models."""
    
    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
        strict=True,
    )


class WithMeta(Model):
    """Base model with metadata fields for Expert Council entities."""
    
    id: str = Field(..., pattern=r"^[a-z0-9\:\.\-]+$")
    version: int = 1
    created_at: AwareDatetime | None = None
    source_strategy_id: str | None = None