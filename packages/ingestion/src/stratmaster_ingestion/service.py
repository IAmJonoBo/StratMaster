"""High level ingestion coordinator wiring parsers, scoring, and provenance."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

import base64

from .clarify import ClarificationService
from .confidence import ConfidenceScorer
from .models import (
    ChunkKind,
    DocumentChunk,
    DocumentMetrics,
    DocumentPayload,
    DocumentProvenance,
    ParseResult,
)
from .parsers import ParserOutput, ParserRegistry, guess_mimetype


@dataclass(slots=True)
class IngestionConfig:
    threshold: float = 0.7
    min_tokens: int = 8


class IngestionCoordinator:
    """Coordinate parsing, scoring, and clarification planning."""

    def __init__(
        self,
        *,
        registry: ParserRegistry | None = None,
        config: IngestionConfig | None = None,
    ) -> None:
        self.config = config or IngestionConfig()
        self.registry = registry or ParserRegistry()
        self.scorer = ConfidenceScorer(min_tokens=self.config.min_tokens)
        self.clarifier = ClarificationService(threshold=self.config.threshold)

    def ingest(self, payload: DocumentPayload) -> ParseResult:
        parser = self.registry.select(payload)
        outputs = list(parser.parse(payload))
        if not outputs:
            outputs = [ParserOutput(text="", kind=ChunkKind.TEXT)]

        chunks: list[DocumentChunk] = []
        scores: list[float] = []
        for idx, output in enumerate(outputs):
            confidence = self.scorer.score(output.text)
            scores.append(confidence)
            metadata = self.registry.build_metadata(
                index=idx,
                parser=parser,
                kind=output.kind,
                payload=payload,
                source_page=output.source_page,
            )
            statistics = self.registry.build_statistics(output.text)
            chunk_id = f"chunk-{uuid.uuid4().hex[:12]}"
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=output.text,
                    confidence=confidence,
                    metadata=metadata,
                    statistics=statistics,
                )
            )

        overall_confidence = self.scorer.aggregate(scores)
        low_confidence = sum(1 for score in scores if score < self.config.threshold)

        mimetype = payload.mimetype or guess_mimetype(payload.filename) or "application/octet-stream"

        provenance = DocumentProvenance(
            document_id=f"doc-{uuid.uuid4().hex[:10]}",
            tenant_id=payload.tenant_id,
            filename=payload.filename,
            mimetype=mimetype,
            sha256=_sha256(payload.content),
            size_bytes=payload.size(),
            parser=parser.name,
            ingested_at=payload.timestamp(),
        )
        metrics = DocumentMetrics(
            overall_confidence=overall_confidence,
            avg_chunk_confidence=overall_confidence,
            low_confidence_chunks=low_confidence,
            threshold=self.config.threshold,
        )
        return ParseResult(provenance=provenance, metrics=metrics, chunks=chunks)

    def clarification_plan(self, result: ParseResult) -> list[dict[str, str | float]]:
        plan = self.clarifier.for_result(result)
        return [prompt.model_dump() for prompt in plan.prompts]


def _sha256(content: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(content)
    return digest.hexdigest()


def decode_base64(data: str) -> bytes:
    """Utility decoding with helpful error surface for API usage."""

    try:
        return base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 payload") from exc