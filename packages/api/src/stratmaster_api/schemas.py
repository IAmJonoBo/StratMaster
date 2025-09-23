from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field


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


class CompressionProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_token_ratio: float
    max_tokens: int
    preserve_headings: bool | None = None
    ensure_bullets: bool | None = None
    highlight_citations: bool | None = None
    allow_structured_tables: bool | None = None
    redact_pii: bool | None = None
    collapse_reasoning: bool | None = None


class CompressionGuardrails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refuse_on_keywords: bool = False
    preserve_sections: list[str] = Field(default_factory=list)
    min_ratio: float | None = None
    max_ratio: float | None = None


class CompressionMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    threshold: float


class CompressionRegressionSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str


class CompressionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: str
    metrics: list[CompressionMetric]
    regression_suite: CompressionRegressionSuite | None = None


class CompressionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    default_profile: str
    profiles: dict[str, CompressionProfile]
    safety_keywords: list[str]
    domains_exempt: list[str] = Field(default_factory=list)
    guardrails: CompressionGuardrails | None = None
    evaluation: CompressionEvaluation | None = None

    @computed_field(return_type=float)
    def target_token_ratio(self) -> float:
        profile = self.profiles.get(self.default_profile)
        if profile is None:
            raise ValueError(
                f"default_profile '{self.default_profile}' missing from profiles"
            )
        return profile.target_token_ratio

    @computed_field(return_type=int)
    def max_tokens(self) -> int:
        profile = self.profiles.get(self.default_profile)
        if profile is None:
            raise ValueError(
                f"default_profile '{self.default_profile}' missing from profiles"
            )
        return profile.max_tokens


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
    # Allow extra sections so config files can include additional domain-specific thresholds
    model_config = ConfigDict(extra="ignore")

    ingestion: dict[str, str | float | int | bool]
    retrieval: dict[str, str | float | int | bool]
    reasoning: dict[str, str | float | int | bool]
    recommendations: dict[str, str | float | int | bool]
    egress: dict[str, str | float | int | bool]
