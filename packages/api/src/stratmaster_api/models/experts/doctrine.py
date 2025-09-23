"""Doctrine models for rubrics and checklists in the Expert Council system."""

from pydantic import Field
from .base import WithMeta


class DoctrineRule(WithMeta):
    """Individual rule within a doctrine rubric or checklist."""
    
    severity: str = Field(..., pattern=r"^(blocker|warn|info)$")
    desc: str


class Doctrine(WithMeta):
    """Collection of rules and references for a specific discipline."""
    
    discipline: str
    type: str = Field(..., pattern=r"^(rubric|checklist)$") 
    rules: list[DoctrineRule] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)