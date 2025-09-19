"""Configuration for compression MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class ProviderConfig:
    name: str
    enable_llmlingua: bool


@dataclass
class AppConfig:
    provider: ProviderConfig


def load_config() -> AppConfig:
    provider = ProviderConfig(
        name=_env("COMPRESSION_MCP_PROVIDER", "llmlingua"),
        enable_llmlingua=_bool("COMPRESSION_MCP_ENABLE_LLMLINGUA", False),
    )
    return AppConfig(provider=provider)
