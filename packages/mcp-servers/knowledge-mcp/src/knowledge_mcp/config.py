"""Configuration loader for knowledge MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class VectorStoreConfig:
    host: str = "http://localhost:6333"
    collection: str = "default"
    enable: bool = False
    health_probe_enabled: bool = False
    health_probe_query: str = "health-check"
    health_probe_top_k: int = 1


@dataclass
class KeywordStoreConfig:
    host: str = "http://localhost:9200"
    index: str = "documents"
    enable: bool = False
    health_probe_enabled: bool = False
    health_probe_query: str = "health-check"
    health_probe_top_k: int = 1


@dataclass
class GraphStoreConfig:
    host: str = "nebula://localhost:9669"
    space: str = "knowledge"
    enable: bool = False
    health_probe_enabled: bool = False
    health_probe_limit: int = 1


@dataclass
class AppConfig:
    vector: VectorStoreConfig
    keyword: KeywordStoreConfig
    graph: GraphStoreConfig


def load_config() -> AppConfig:
    vector = VectorStoreConfig(
        host=os.getenv("KNOWLEDGE_MCP_VECTOR_HOST", "http://localhost:6333"),
        collection=os.getenv("KNOWLEDGE_MCP_VECTOR_COLLECTION", "default"),
        enable=os.getenv("KNOWLEDGE_MCP_VECTOR_ENABLE", "0") in {"1", "true", "True"},
        health_probe_enabled=os.getenv("KNOWLEDGE_MCP_VECTOR_PROBE_ENABLE", "0")
        in {"1", "true", "True"},
        health_probe_query=os.getenv(
            "KNOWLEDGE_MCP_VECTOR_PROBE_QUERY", "health-check"
        ),
        health_probe_top_k=int(os.getenv("KNOWLEDGE_MCP_VECTOR_PROBE_TOP_K", "1")),
    )
    keyword = KeywordStoreConfig(
        host=os.getenv("KNOWLEDGE_MCP_KEYWORD_HOST", "http://localhost:9200"),
        index=os.getenv("KNOWLEDGE_MCP_KEYWORD_INDEX", "documents"),
        enable=os.getenv("KNOWLEDGE_MCP_KEYWORD_ENABLE", "0") in {"1", "true", "True"},
        health_probe_enabled=os.getenv("KNOWLEDGE_MCP_KEYWORD_PROBE_ENABLE", "0")
        in {"1", "true", "True"},
        health_probe_query=os.getenv(
            "KNOWLEDGE_MCP_KEYWORD_PROBE_QUERY", "health-check"
        ),
        health_probe_top_k=int(os.getenv("KNOWLEDGE_MCP_KEYWORD_PROBE_TOP_K", "1")),
    )
    graph = GraphStoreConfig(
        host=os.getenv("KNOWLEDGE_MCP_GRAPH_HOST", "nebula://localhost:9669"),
        space=os.getenv("KNOWLEDGE_MCP_GRAPH_SPACE", "knowledge"),
        enable=os.getenv("KNOWLEDGE_MCP_GRAPH_ENABLE", "0") in {"1", "true", "True"},
        health_probe_enabled=os.getenv("KNOWLEDGE_MCP_GRAPH_PROBE_ENABLE", "0")
        in {"1", "true", "True"},
        health_probe_limit=int(os.getenv("KNOWLEDGE_MCP_GRAPH_PROBE_LIMIT", "1")),
    )
    return AppConfig(vector=vector, keyword=keyword, graph=graph)
