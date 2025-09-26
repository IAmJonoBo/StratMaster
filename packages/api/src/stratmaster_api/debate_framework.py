"""Phase 3 - Toulmin Argument Schema per SCRATCH.md

Implements structured debate framework with:
- Toulmin argument schema (claim/grounds/warrant/backing/qualifier/rebuttal)
- Argument mapping and visualization
- JSON serialization for audit/UI overlays
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ArgumentType(str, Enum):
    """Types of arguments in Toulmin schema."""
    CLAIM = "claim"
    GROUNDS = "grounds"
    WARRANT = "warrant"
    BACKING = "backing"
    QUALIFIER = "qualifier"
    REBUTTAL = "rebuttal"


class ConfidenceLevel(str, Enum):
    """Confidence levels for arguments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Evidence:
    """Evidence supporting an argument component."""
    source: str
    content: str
    credibility: float  # 0.0 to 1.0
    relevance: float   # 0.0 to 1.0
    url: str | None = None
    publication_date: str | None = None


@dataclass
class ToulminArgument:
    """Structured argument following Toulmin model."""
    argument_id: str
    
    # Core Toulmin components
    claim: str  # The central assertion
    grounds: list[str]  # Evidence supporting the claim
    warrant: str  # Link between grounds and claim
    backing: str | None = None  # Support for the warrant
    qualifier: str | None = None  # Conditions/limitations
    rebuttal: str | None = None  # Counter-arguments/exceptions
    
    # Metadata
    author: str = "system"
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    created_at: str | None = None
    evidence: list[Evidence] | None = None
    tags: list[str] | None = None
    
    def __post_init__(self):
        """Initialize derived fields."""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.evidence is None:
            self.evidence = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToulminArgument:
        """Create from dictionary."""
        # Handle evidence objects
        if "evidence" in data and data["evidence"]:
            evidence_list = []
            for ev in data["evidence"]:
                if isinstance(ev, dict):
                    evidence_list.append(Evidence(**ev))
                else:
                    evidence_list.append(ev)
            data["evidence"] = evidence_list
        
        return cls(**data)
    
    def validate(self) -> list[str]:
        """Validate argument structure and return issues."""
        issues = []
        
        if not self.claim.strip():
            issues.append("Claim cannot be empty")
        
        if not self.grounds:
            issues.append("Grounds cannot be empty")
        
        if not self.warrant.strip():
            issues.append("Warrant cannot be empty")
        
        # Check evidence quality
        if self.evidence:
            for i, ev in enumerate(self.evidence):
                if ev.credibility < 0.3:
                    issues.append(f"Evidence {i}: Low credibility ({ev.credibility})")
                if ev.relevance < 0.5:
                    issues.append(f"Evidence {i}: Low relevance ({ev.relevance})")
        
        return issues
    
    def get_strength_score(self) -> float:
        """Calculate argument strength score (0.0 to 1.0)."""
        base_score = 0.6  # Base score for having claim, grounds, warrant
        
        # Bonus for backing
        if self.backing and self.backing.strip():
            base_score += 0.1
        
        # Bonus for qualifier (shows nuance)
        if self.qualifier and self.qualifier.strip():
            base_score += 0.05
        
        # Evidence quality bonus
        if self.evidence:
            avg_credibility = sum(ev.credibility for ev in self.evidence) / len(self.evidence)
            avg_relevance = sum(ev.relevance for ev in self.evidence) / len(self.evidence)
            evidence_score = (avg_credibility + avg_relevance) / 2
            base_score += evidence_score * 0.25
        
        # Confidence adjustment
        confidence_multiplier = {
            ConfidenceLevel.LOW: 0.8,
            ConfidenceLevel.MEDIUM: 1.0,
            ConfidenceLevel.HIGH: 1.1,
            ConfidenceLevel.VERY_HIGH: 1.2
        }
        base_score *= confidence_multiplier.get(self.confidence, 1.0)
        
        return min(1.0, base_score)


@dataclass 
class ArgumentRelation:
    """Relationship between two arguments."""
    relation_id: str
    from_argument: str  # argument_id
    to_argument: str    # argument_id
    relation_type: str  # "supports", "rebuts", "qualifies", "extends"
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    description: str | None = None


@dataclass
class DebateStructure:
    """Complete debate structure with Toulmin arguments."""
    debate_id: str
    title: str
    context: str
    arguments: list[ToulminArgument]
    relations: list[ArgumentRelation]
    
    # Metadata
    participants: list[str]
    moderator: str | None = None
    created_at: str | None = None
    status: str = "active"  # "active", "paused", "completed"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
    
    def add_argument(self, argument: ToulminArgument) -> None:
        """Add argument to debate."""
        self.arguments.append(argument)
    
    def add_relation(self, relation: ArgumentRelation) -> None:
        """Add relationship between arguments."""
        self.relations.append(relation)
    
    def get_argument_by_id(self, argument_id: str) -> ToulminArgument | None:
        """Retrieve argument by ID."""
        for arg in self.arguments:
            if arg.argument_id == argument_id:
                return arg
        return None
    
    def get_supporting_arguments(self, argument_id: str) -> list[ToulminArgument]:
        """Get all arguments supporting the given argument."""
        supporting_ids = [
            rel.from_argument for rel in self.relations 
            if rel.to_argument == argument_id and rel.relation_type == "supports"
        ]
        return [self.get_argument_by_id(arg_id) for arg_id in supporting_ids if self.get_argument_by_id(arg_id)]
    
    def get_rebuttals(self, argument_id: str) -> list[ToulminArgument]:
        """Get all rebuttals to the given argument."""
        rebuttal_ids = [
            rel.from_argument for rel in self.relations 
            if rel.to_argument == argument_id and rel.relation_type == "rebuts"
        ]
        return [self.get_argument_by_id(arg_id) for arg_id in rebuttal_ids if self.get_argument_by_id(arg_id)]
    
    def validate_structure(self) -> list[str]:
        """Validate entire debate structure."""
        issues = []
        
        # Validate individual arguments
        for arg in self.arguments:
            arg_issues = arg.validate()
            if arg_issues:
                issues.extend([f"Argument {arg.argument_id}: {issue}" for issue in arg_issues])
        
        # Validate relations
        arg_ids = {arg.argument_id for arg in self.arguments}
        for rel in self.relations:
            if rel.from_argument not in arg_ids:
                issues.append(f"Relation {rel.relation_id}: from_argument {rel.from_argument} not found")
            if rel.to_argument not in arg_ids:
                issues.append(f"Relation {rel.relation_id}: to_argument {rel.to_argument} not found")
        
        return issues
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "debate_id": self.debate_id,
            "title": self.title,
            "context": self.context,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "relations": [asdict(rel) for rel in self.relations],
            "participants": self.participants,
            "moderator": self.moderator,
            "created_at": self.created_at,
            "status": self.status
        }
    
    def to_json(self) -> str:
        """Convert to JSON for audit/UI overlays per SCRATCH.md."""
        return json.dumps(self.to_dict(), indent=2)


class ToulminDebateFramework:
    """Framework for managing Toulmin-structured debates per SCRATCH.md Phase 3."""
    
    def __init__(self):
        self.debates: dict[str, DebateStructure] = {}
    
    def create_debate(
        self, 
        title: str, 
        context: str, 
        participants: list[str],
        moderator: str | None = None
    ) -> DebateStructure:
        """Create new structured debate."""
        debate = DebateStructure(
            debate_id=str(uuid4()),
            title=title,
            context=context,
            arguments=[],
            relations=[],
            participants=participants,
            moderator=moderator
        )
        
        self.debates[debate.debate_id] = debate
        logger.info(f"Created debate: {debate.debate_id} - {title}")
        
        return debate
    
    def create_argument(
        self,
        claim: str,
        grounds: list[str],
        warrant: str,
        backing: str | None = None,
        qualifier: str | None = None,
        rebuttal: str | None = None,
        author: str = "system",
        evidence: list[Evidence] | None = None
    ) -> ToulminArgument:
        """Create structured Toulmin argument."""
        argument = ToulminArgument(
            argument_id=str(uuid4()),
            claim=claim,
            grounds=grounds,
            warrant=warrant,
            backing=backing,
            qualifier=qualifier,
            rebuttal=rebuttal,
            author=author,
            evidence=evidence or []
        )
        
        # Validate argument
        issues = argument.validate()
        if issues:
            logger.warning(f"Argument validation issues: {issues}")
        
        return argument
    
    def add_argument_to_debate(
        self, 
        debate_id: str, 
        argument: ToulminArgument
    ) -> None:
        """Add argument to existing debate."""
        if debate_id not in self.debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        self.debates[debate_id].add_argument(argument)
        logger.info(f"Added argument {argument.argument_id} to debate {debate_id}")
    
    def create_argument_relation(
        self,
        debate_id: str,
        from_argument_id: str,
        to_argument_id: str,
        relation_type: str,
        strength: float = 1.0,
        description: str | None = None
    ) -> ArgumentRelation:
        """Create relationship between arguments."""
        if debate_id not in self.debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        relation = ArgumentRelation(
            relation_id=str(uuid4()),
            from_argument=from_argument_id,
            to_argument=to_argument_id,
            relation_type=relation_type,
            strength=strength,
            description=description
        )
        
        self.debates[debate_id].add_relation(relation)
        logger.info(f"Created relation: {from_argument_id} {relation_type} {to_argument_id}")
        
        return relation
    
    def get_debate_summary(self, debate_id: str) -> dict[str, Any]:
        """Generate debate summary with argument strengths."""
        if debate_id not in self.debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        debate = self.debates[debate_id]
        
        # Calculate argument strengths
        argument_strengths = []
        for arg in debate.arguments:
            strength = arg.get_strength_score()
            supporting_count = len(debate.get_supporting_arguments(arg.argument_id))
            rebuttal_count = len(debate.get_rebuttals(arg.argument_id))
            
            argument_strengths.append({
                "argument_id": arg.argument_id,
                "claim": arg.claim,
                "author": arg.author,
                "strength_score": strength,
                "confidence": arg.confidence.value,
                "supporting_arguments": supporting_count,
                "rebuttals": rebuttal_count,
                "evidence_count": len(arg.evidence)
            })
        
        # Sort by strength
        argument_strengths.sort(key=lambda x: x["strength_score"], reverse=True)
        
        return {
            "debate_id": debate_id,
            "title": debate.title,
            "status": debate.status,
            "participants": debate.participants,
            "argument_count": len(debate.arguments),
            "relation_count": len(debate.relations),
            "strongest_arguments": argument_strengths[:5],  # Top 5
            "validation_issues": debate.validate_structure(),
            "created_at": debate.created_at
        }
    
    def export_for_ui(self, debate_id: str) -> str:
        """Export debate as JSON for UI argument map per SCRATCH.md."""
        if debate_id not in self.debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        debate = self.debates[debate_id]
        
        # Create UI-friendly structure
        ui_structure = {
            "debate": debate.to_dict(),
            "visualization": {
                "nodes": [
                    {
                        "id": arg.argument_id,
                        "label": arg.claim[:100] + "..." if len(arg.claim) > 100 else arg.claim,
                        "type": "argument",
                        "author": arg.author,
                        "strength": arg.get_strength_score(),
                        "confidence": arg.confidence.value,
                        "components": {
                            "claim": arg.claim,
                            "grounds": arg.grounds,
                            "warrant": arg.warrant,
                            "backing": arg.backing,
                            "qualifier": arg.qualifier,
                            "rebuttal": arg.rebuttal
                        }
                    }
                    for arg in debate.arguments
                ],
                "edges": [
                    {
                        "from": rel.from_argument,
                        "to": rel.to_argument,
                        "type": rel.relation_type,
                        "strength": rel.strength,
                        "description": rel.description
                    }
                    for rel in debate.relations
                ]
            },
            "metadata": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "framework": "toulmin",
                "version": "1.0"
            }
        }
        
        return json.dumps(ui_structure, indent=2)