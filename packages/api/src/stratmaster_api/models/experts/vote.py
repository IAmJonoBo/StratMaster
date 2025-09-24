"""Voting models for the Expert Council weighted consensus system."""

from pydantic import Field

from .base import WithMeta


class DisciplineVote(WithMeta):
    """Vote from a single discipline expert."""
    
    discipline: str
    score: float = Field(ge=0, le=1)
    justification: str | None = None


class CouncilVote(WithMeta):
    """Aggregated weighted vote from the entire Expert Council."""
    
    strategy_id: str
    votes: list[DisciplineVote] = Field(default_factory=list)
    weighted_score: float = Field(ge=0, le=1)
    weights: dict[str, float] = Field(default_factory=dict)