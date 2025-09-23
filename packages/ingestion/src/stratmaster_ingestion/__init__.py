"""StratMaster ingestion primitives and orchestration utilities."""

from .clarify import (
    ClarificationInput,
    ClarificationPlan,
    ClarificationPrompt,
    ClarificationService,
)
from .confidence import ConfidenceScorer
from .models import (
    ChunkKind,
    ChunkMetadata,
    ChunkStatistics,
    DocumentChunk,
    DocumentMetrics,
    DocumentPayload,
    DocumentProvenance,
    ParseResult,
)
from .parsers import ParserRegistry
from .service import IngestionCoordinator

__all__ = [
    "ClarificationInput",
    "ClarificationPlan",
    "ClarificationPrompt",
    "ClarificationService",
    "ConfidenceScorer",
    "ChunkKind",
    "ChunkMetadata",
    "ChunkStatistics",
    "DocumentChunk",
    "DocumentMetrics",
    "DocumentPayload",
    "DocumentProvenance",
    "ParseResult",
    "ParserRegistry",
    "IngestionCoordinator",
]