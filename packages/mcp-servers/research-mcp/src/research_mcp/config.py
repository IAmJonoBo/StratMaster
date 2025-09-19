"""Configuration helpers for the Research MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _list_env(name: str, default: Optional[List[str]] = None) -> List[str]:
    value = os.getenv(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class MetasearchSettings:
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout: float = 10.0
    use_network: bool = False


@dataclass
class CrawlerSettings:
    user_agent: str = "StratMaster-ResearchBot/0.1"
    allowlist: List[str] = field(default_factory=lambda: ["example.com"])
    blocklist: List[str] = field(default_factory=list)
    use_network: bool = False
    use_playwright: bool = False


@dataclass
class StorageSettings:
    base_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("RESEARCH_MCP_CACHE_DIR", ".cache/research_mcp")
        )
    )


@dataclass
class ProvenanceSettings:
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    enable_openlineage: bool = False


@dataclass
class AppConfig:
    metasearch: MetasearchSettings
    crawler: CrawlerSettings
    storage: StorageSettings
    provenance: ProvenanceSettings


def load_config() -> AppConfig:
    allowlist = _list_env("RESEARCH_MCP_ALLOWLIST", ["example.com"])
    blocklist = _list_env("RESEARCH_MCP_BLOCKLIST", [])

    metasearch = MetasearchSettings(
        endpoint=os.getenv("SEARXNG_ENDPOINT"),
        api_key=os.getenv("SEARXNG_API_KEY"),
        timeout=float(os.getenv("RESEARCH_MCP_METASEARCH_TIMEOUT", "10")),
        use_network=_bool_env("RESEARCH_MCP_ENABLE_NETWORK", False),
    )
    crawler = CrawlerSettings(
        user_agent=os.getenv("RESEARCH_MCP_USER_AGENT", "StratMaster-ResearchBot/0.1"),
        allowlist=allowlist,
        blocklist=blocklist,
        use_network=_bool_env("RESEARCH_MCP_ENABLE_NETWORK", False),
        use_playwright=_bool_env("RESEARCH_MCP_USE_PLAYWRIGHT", False),
    )
    storage = StorageSettings()
    storage.base_path.mkdir(parents=True, exist_ok=True)
    provenance = ProvenanceSettings(
        minio_endpoint=os.getenv("RESEARCH_MCP_MINIO_ENDPOINT"),
        minio_access_key=os.getenv("RESEARCH_MCP_MINIO_ACCESS_KEY"),
        minio_secret_key=os.getenv("RESEARCH_MCP_MINIO_SECRET_KEY"),
        minio_bucket=os.getenv("RESEARCH_MCP_MINIO_BUCKET"),
        enable_openlineage=_bool_env("RESEARCH_MCP_ENABLE_OPENLINEAGE", False),
    )
    return AppConfig(
        metasearch=metasearch,
        crawler=crawler,
        storage=storage,
        provenance=provenance,
    )
