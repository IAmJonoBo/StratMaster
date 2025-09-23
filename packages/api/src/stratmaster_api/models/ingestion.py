from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IngestionDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    filename: str
    content_base64: str = Field(..., alias="content")
    mimetype: str | None = None


class IngestionChunkPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    index: int = Field(ge=0)
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    kind: Literal["text", "table", "structured", "binary"] = "text"


class ClarificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    chunks: list[IngestionChunkPayload]
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class IngestionChunkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    confidence: float
    parser: str
    kind: str
    statistics: dict[str, float | int]


class IngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    tenant_id: str
    filename: str
    mimetype: str
    sha256: str
    size_bytes: int
    parser: str
    ingested_at: datetime
    metrics: dict[str, float | int]
    chunks: list[IngestionChunkResponse]
    needs_clarification: bool


class ClarificationPromptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    question: str
    rationale: str
    suggested_action: str
    confidence: float
    threshold: float


class ClarificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    prompts: list[ClarificationPromptResponse]

