from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FallbackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    when_no_results: str


class PipelinesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dense_config: str
    sparse_config: str
    reranker_config: str


class RetrievalHybridConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str
    alpha_dense: float
    alpha_sparse: float
    limit: int
    fallback: FallbackConfig
    pipelines: PipelinesConfig


class CompressionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    target_token_ratio: float
    safety_keywords: list[str]
    domains_exempt: list[str] = Field(default_factory=list)


class RedactionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    pattern: str
    replacement: str


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    otlp_endpoint: str


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[RedactionRule]
    telemetry: TelemetryConfig | None = None


class EvalsThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingestion: dict[str, str | float | int | bool]
    retrieval: dict[str, str | float | int | bool]
    reasoning: dict[str, str | float | int | bool]
    recommendations: dict[str, str | float | int | bool]
    egress: dict[str, str | float | int | bool]
