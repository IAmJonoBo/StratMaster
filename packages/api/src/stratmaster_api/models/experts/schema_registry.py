"""Schema registry for Expert Council models."""

from .expert_profile import ExpertProfile
from .doctrine import Doctrine
from .memo import DisciplineMemo  
from .vote import CouncilVote
from .message_map import MessageMap
from .persuasion_risk import PersuasionRisk

REGISTRY = [ExpertProfile, Doctrine, DisciplineMemo, CouncilVote, MessageMap, PersuasionRisk]