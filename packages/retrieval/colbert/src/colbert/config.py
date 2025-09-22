"""Configuration loader for the ColBERT tooling."""

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


class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    dim: int = Field(default=128, ge=32)
    max_document_length: int = Field(default=512, ge=64)


class SearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k: int = 20
    max_passages: int = 4
    alpha_dense_sparse_mix: float = Field(default=0.7, ge=0.0, le=1.0)


class StorageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: str = "filesystem"
    output_dir: Path = Path("artifacts/colbert")


class ColbertConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpus: CorpusConfig
    index: IndexConfig
    embedding: EmbeddingConfig
    search: SearchConfig
    storage: StorageConfig


def load_config(path: str | Path) -> ColbertConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if "corpus" not in raw:
        raise ValueError("Config must include corpus settings")
    merged: dict[str, Any] = {
        "corpus": raw.get("corpus", {}),
        "index": raw.get("index", {}),
        "embedding": raw.get("embedding", {}),
        "search": raw.get("search", {}),
        "storage": raw.get("storage", {}),
    }
    return ColbertConfig(**merged)

