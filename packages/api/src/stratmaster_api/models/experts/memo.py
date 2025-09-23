"""Discipline memo models for Expert Council assessments."""

from pydantic import Field
from .base import WithMeta


class Finding(WithMeta):
    """Individual finding within a discipline memo."""
    
    issue: str
    severity: str = Field(..., pattern=r"^(high|medium|low)$")
    evidence: list[str] = Field(default_factory=list)
    fix: str | None = None


class DisciplineMemo(WithMeta):
    """Comprehensive memo output from a discipline expert."""
    
    discipline: str
    applies_to: str
    findings: list[Finding] = Field(default_factory=list)
    scores: dict = Field(default_factory=dict)
    recommendations: list[dict] = Field(default_factory=list)