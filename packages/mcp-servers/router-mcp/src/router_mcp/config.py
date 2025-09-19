"""Configuration loader for router MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass
class ProviderConfig:
    name: str
    completion_model: str
    embedding_model: str
    rerank_model: str
    temperature: float
    base_url: str | None
    api_key: str | None


@dataclass
class AppConfig:
    default_provider: ProviderConfig
    structured_decoding: dict[str, Any]


def load_config() -> AppConfig:
    provider = ProviderConfig(
        name=_env("ROUTER_MCP_PROVIDER", "local"),
        completion_model=_env("ROUTER_MCP_COMPLETION_MODEL", "mixtral-8x7b"),
        embedding_model=_env("ROUTER_MCP_EMBEDDING_MODEL", "bge-small"),
        rerank_model=_env("ROUTER_MCP_RERANK_MODEL", "bge-reranker-large"),
        temperature=_float_env("ROUTER_MCP_TEMPERATURE", 0.2),
        base_url=os.getenv("ROUTER_MCP_PROVIDER_BASE_URL"),
        api_key=os.getenv("ROUTER_MCP_PROVIDER_API_KEY"),
    )
    structured = _load_structured_decoding()
    return AppConfig(default_provider=provider, structured_decoding=structured)


def _load_structured_decoding() -> dict[str, Any]:
    cfg_path = (
        Path(__file__).resolve().parents[5]
        / "configs"
        / "router"
        / "structured_decoding.yaml"
    )
    if not cfg_path.is_file():
        return {}
    try:
        with cfg_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}
