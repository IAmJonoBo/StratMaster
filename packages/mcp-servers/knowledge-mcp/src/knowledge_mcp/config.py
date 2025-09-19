"""Configuration loader for knowledge MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class VectorStoreConfig:
    host: str = "http://localhost:6333"
    collection: str = "default"
    enable: bool = False


@dataclass
class KeywordStoreConfig:
    host: str = "http://localhost:9200"
    index: str = "documents"
    enable: bool = False


@dataclass
class GraphStoreConfig:
    host: str = "nebula://localhost:9669"
    space: str = "knowledge"
    enable: bool = False


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
    )
    keyword = KeywordStoreConfig(
        host=os.getenv("KNOWLEDGE_MCP_KEYWORD_HOST", "http://localhost:9200"),
        index=os.getenv("KNOWLEDGE_MCP_KEYWORD_INDEX", "documents"),
        enable=os.getenv("KNOWLEDGE_MCP_KEYWORD_ENABLE", "0") in {"1", "true", "True"},
    )
    graph = GraphStoreConfig(
        host=os.getenv("KNOWLEDGE_MCP_GRAPH_HOST", "nebula://localhost:9669"),
        space=os.getenv("KNOWLEDGE_MCP_GRAPH_SPACE", "knowledge"),
        enable=os.getenv("KNOWLEDGE_MCP_GRAPH_ENABLE", "0") in {"1", "true", "True"},
    )
    return AppConfig(vector=vector, keyword=keyword, graph=graph)
