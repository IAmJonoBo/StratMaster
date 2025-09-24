"""Pydantic models shared across ingestion services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ChunkKind(str, Enum):
    """Supported chunk categories."""

    TEXT = "text"
    TABLE = "table"
    STRUCTURED = "structured"
    BINARY = "binary"


class ChunkStatistics(BaseModel):
    """Aggregate statistics for a parsed chunk."""

    model_config = ConfigDict(extra="forbid")

    char_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    whitespace_ratio: float = Field(ge=0.0, le=1.0)


class ChunkMetadata(BaseModel):
    """Metadata describing the origin of a chunk."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    parser: str
    kind: ChunkKind = ChunkKind.TEXT
    source_page: int | None = Field(default=None, ge=1)
    source_path: str | None = None
    mimetype: str | None = None


class DocumentChunk(BaseModel):
    """Parsed chunk payload with metadata and confidence."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: ChunkMetadata
    statistics: ChunkStatistics


class DocumentProvenance(BaseModel):
    """Provenance fields for the ingested document."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    tenant_id: str
    filename: str
    mimetype: str
    sha256: str
    size_bytes: int = Field(ge=0)
    parser: str
    ingested_at: datetime


class DocumentMetrics(BaseModel):
    """Summary metrics derived from parsed chunks."""

    model_config = ConfigDict(extra="forbid")

    overall_confidence: float = Field(ge=0.0, le=1.0)
    avg_chunk_confidence: float = Field(ge=0.0, le=1.0)
    low_confidence_chunks: int = Field(ge=0)
    threshold: float = Field(ge=0.0, le=1.0)


class ParseResult(BaseModel):
    """Top-level ingestion response."""

    model_config = ConfigDict(extra="forbid")

    provenance: DocumentProvenance
    metrics: DocumentMetrics
    chunks: list[DocumentChunk]

    @property
    def needs_clarification(self) -> bool:
        return self.metrics.low_confidence_chunks > 0

    def low_confidence(self) -> list[DocumentChunk]:
        """Return chunks that are currently below the configured threshold."""

        threshold = self.metrics.threshold
        return [chunk for chunk in self.chunks if chunk.confidence < threshold]


@dataclass(slots=True)
class DocumentPayload:
    """Raw document payload passed to the ingestion coordinator."""

    filename: str
    content: bytes
    tenant_id: str
    mimetype: str | None = None

    def size(self) -> int:
        return len(self.content)

    def timestamp(self) -> datetime:
        return datetime.now(tz=UTC)