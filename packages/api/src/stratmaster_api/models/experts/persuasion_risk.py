"""Persuasion risk assessment model for psychological reactance detection."""

from pydantic import Field

from .base import WithMeta


class PersuasionRisk(WithMeta):
    """Assessment of psychological reactance risk in messaging."""
    
    reactance_risk: float = Field(ge=0, le=1)  # 0=none, 1=extreme
    notes: list[str] = Field(default_factory=list)