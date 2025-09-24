"""Schema registry for Expert Council models."""

from .doctrine import Doctrine
from .expert_profile import ExpertProfile
from .memo import DisciplineMemo
from .message_map import MessageMap
from .persuasion_risk import PersuasionRisk
from .vote import CouncilVote

REGISTRY = [ExpertProfile, Doctrine, DisciplineMemo, CouncilVote, MessageMap, PersuasionRisk]