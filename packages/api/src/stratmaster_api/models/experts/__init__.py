"""Expert Council models for StratMaster API.

This module provides Pydantic v2 models for the Expert Council system, implementing
domain models for experts, doctrines, memos, votes, and risk assessments as specified
in the Expert Council feature specification.
"""

from .base import Model, WithMeta
from .doctrine import Doctrine, DoctrineRule
from .expert_profile import ExpertProfile
from .memo import DisciplineMemo, Finding
from .message_map import MessageMap
from .persuasion_risk import PersuasionRisk
from .vote import CouncilVote, DisciplineVote

__all__ = [
    "Model",
    "WithMeta",
    "ExpertProfile", 
    "Doctrine",
    "DoctrineRule",
    "Finding",
    "DisciplineMemo",
    "DisciplineVote",
    "CouncilVote",
    "MessageMap",
    "PersuasionRisk",
]