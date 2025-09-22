"""Pydantic contracts describing knowledge fabric storage artefacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _tokenise(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


class ArtefactRecord(BaseModel):
    """Canonical record persisted to the knowledge fabric stores."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    source: str = Field(min_length=1)
    sast: datetime
    tags: list[str] = Field(default_factory=list)
    dense_vector: list[float] = Field(default_factory=list)
    sparse_terms: dict[str, float] = Field(default_factory=dict)

    @classmethod
    def from_text(
        cls,
        tenant_id: str,
        document_id: str,
        title: str,
        summary: str,
        fingerprint: str,
        source: str,
        sast: datetime | str | None = None,
        tags: Iterable[str] | None = None,
        embedding_dim: int = 128,
    ) -> "ArtefactRecord":
        if sast is None:
            sast = datetime.now(timezone.utc)
        if isinstance(sast, str):
            try:
                sast = datetime.fromisoformat(sast.replace("Z", "+00:00"))
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValidationError.from_exception_data(  # type: ignore[attr-defined]
                    "ArtefactRecord", [], str(exc)
                ) from exc
        tokens = _tokenise(f"{title} {summary}")
        token_counts = Counter(tokens)
        dense = [0.0] * embedding_dim
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        for token, count in token_counts.items():
            bucket = hash(token) % embedding_dim
            dense[bucket] += float(count)
        magnitude = math.sqrt(sum(val * val for val in dense)) or 1.0
        dense = [val / magnitude for val in dense]
        sparse = {token: float(count) for token, count in token_counts.items()}
        return cls(
            tenant_id=tenant_id,
            document_id=document_id,
            title=title,
            summary=summary,
            fingerprint=fingerprint,
            source=source,
            sast=sast,
            tags=list(tags or []),
            dense_vector=dense,
            sparse_terms=sparse,
        )

    def similarity(self, query: str, alpha_dense: float = 0.6, alpha_sparse: float = 0.4) -> float:
        tokens = _tokenise(query)
        if not tokens:
            return 0.0
        sparse_query = Counter(tokens)
        dense_query = [0.0] * len(self.dense_vector)
        for token, count in sparse_query.items():
            bucket = hash(token) % len(dense_query)
            dense_query[bucket] += float(count)
        magnitude = math.sqrt(sum(val * val for val in dense_query)) or 1.0
        dense_query = [val / magnitude for val in dense_query]
        dense_score = sum(a * b for a, b in zip(self.dense_vector, dense_query))
        sparse_score = 0.0
        for token, weight in sparse_query.items():
            sparse_score += weight * self.sparse_terms.get(token, 0.0)
        sparse_norm = sum(val * val for val in sparse_query.values()) or 1.0
        sparse_score = sparse_score / sparse_norm
        return alpha_dense * dense_score + alpha_sparse * sparse_score


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    relation: str
    weight: float = Field(ge=0, le=1)


class CommunitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    community_id: str
    title: str
    summary: str
    representative_nodes: list[str]
    score: float = Field(ge=0.0, le=1.0)


class TenantManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    artefact_ids: list[str]
    graph_version: str
    stored_at: datetime


@dataclass(slots=True)
class RankedArtefact:
    score: float
    artefact: ArtefactRecord

