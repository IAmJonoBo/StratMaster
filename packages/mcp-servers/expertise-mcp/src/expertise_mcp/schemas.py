"""JSON schemas for MCP tool input/output validation."""

from __future__ import annotations

# Import from the shared API models
from packages.api.src.stratmaster_api.models.experts.memo import DisciplineMemo
from packages.api.src.stratmaster_api.models.experts.vote import CouncilVote

# Expose pydantic JSON schemas for tool I/O
MEMO_SCHEMA = DisciplineMemo.model_json_schema()
VOTE_SCHEMA = CouncilVote.model_json_schema()

__all__ = ["MEMO_SCHEMA", "VOTE_SCHEMA"]