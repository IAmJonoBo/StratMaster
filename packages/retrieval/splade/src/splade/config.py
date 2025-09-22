"""Configuration loader for SPLADE utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CorpusConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path
    text_fields: list[str] = Field(default_factory=lambda: ["summary"])


class IndexConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    shards: int = 1
    replication: int = 1


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    max_document_length: int = Field(default=512, ge=64)


class SearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k: int = 20
    pruning_threshold: float = Field(default=0.001, ge=0.0)


class StorageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: str = "filesystem"
    output_dir: Path = Path("artifacts/splade")


class SpladeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpus: CorpusConfig
    index: IndexConfig
    model: ModelConfig
    search: SearchConfig
    storage: StorageConfig


def load_config(path: str | Path) -> SpladeConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    merged: dict[str, Any] = {
        "corpus": raw.get("corpus", {}),
        "index": raw.get("index", {}),
        "model": raw.get("model", {}),
        "search": raw.get("search", {}),
        "storage": raw.get("storage", {}),
    }
    return SpladeConfig(**merged)
