"""Utilities for exporting JSON Schemas for public API models."""

from __future__ import annotations

import json
from pathlib import Path

from .core import (
    Assumption,
    Claim,
    DecisionBrief,
    GraphArtifacts,
    Provenance,
    RecommendationOutcome,
    RetrievalRecord,
    Source,
)

SCHEMA_VERSION = "2024-10-01"
SCHEMA_BASE_URL = "https://schemas.stratmaster.ai"

MODELS = {
    "source": Source,
    "provenance": Provenance,
    "claim": Claim,
    "assumption": Assumption,
    "decision-brief": DecisionBrief,
    "graph-artifacts": GraphArtifacts,
    "retrieval-record": RetrievalRecord,
    "recommendation-outcome": RecommendationOutcome,
}


def export_json_schemas(output_dir: Path) -> list[Path]:
    """Render deterministic JSON Schemas with versioned `$id` fields."""

    output_dir.mkdir(parents=True, exist_ok=True)
    emitted: list[Path] = []
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        schema["$id"] = f"{SCHEMA_BASE_URL}/{name}/{SCHEMA_VERSION}"
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        path = output_dir / f"{name}-{SCHEMA_VERSION}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
        emitted.append(path)
    return emitted
