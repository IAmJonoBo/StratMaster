"""Knowledge fabric package exposing storage and graph materialisation utilities."""

from .pipeline import KnowledgePipeline, MaterialisationResult
from .storage.contracts import (
    ArtefactRecord,
    CommunitySummary,
    GraphEdge,
    GraphNode,
    TenantManifest,
)

__all__ = [
    "ArtefactRecord",
    "CommunitySummary",
    "GraphEdge",
    "GraphNode",
    "KnowledgePipeline",
    "MaterialisationResult",
    "TenantManifest",
]
