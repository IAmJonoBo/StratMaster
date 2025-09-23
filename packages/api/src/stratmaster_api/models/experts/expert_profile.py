"""Expert profile model for the Expert Council system."""

from pydantic import Field
from .base import WithMeta


class ExpertProfile(WithMeta):
    """Profile for a domain expert in the Expert Council system."""
    
    discipline: str = Field(..., description="e.g., psychology, design, communication")
    doctrine_ids: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    weight_prior: float = Field(ge=0.0, le=1.0, default=0.5)
    calibration: dict = Field(default_factory=dict)