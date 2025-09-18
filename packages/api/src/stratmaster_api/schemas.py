from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DenseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    k: int


class SparseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    k: int


class RerankerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    topk_in: int
    topk_out: int


class RetrievalHybridConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dense: DenseConfig
    sparse: SparseConfig
    alpha: float
    reranker: RerankerConfig


# Compression (LLMLingua) schema
class CompressionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    target_token_ratio: float
    safety_keywords: list[str]


# Privacy/Redaction schema
class PrivacyPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redact_pii: bool
    annotate_only: bool
    replacement: str


class PrivacyPatterns(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pii: list[str]


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patterns: PrivacyPatterns
    policy: PrivacyPolicy


class EvalsThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingestion: dict[str, str | float | int | bool]
    retrieval: dict[str, str | float | int | bool]
    reasoning: dict[str, str | float | int | bool]
    recommendations: dict[str, str | float | int | bool]
    egress: dict[str, str | float | int | bool]
