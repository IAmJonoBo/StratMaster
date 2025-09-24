"""PIE/ICE scoring system with evidence requirements for strategic initiatives."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class EvidenceType(str, Enum):
    """Types of evidence that can support scoring."""
    MARKET_RESEARCH = "market_research"
    CUSTOMER_FEEDBACK = "customer_feedback"
    FINANCIAL_DATA = "financial_data" 
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    STAKEHOLDER_INPUT = "stakeholder_input"
    HISTORICAL_DATA = "historical_data"


class EvidenceRequirement(BaseModel):
    """Evidence requirement for a scoring criterion."""
    criterion: str
    evidence_types: List[EvidenceType]
    minimum_sources: int = 1
    required: bool = True
    description: str
    
    
class Evidence(BaseModel):
    """Piece of evidence supporting a score."""
    evidence_type: EvidenceType
    source: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    date: Optional[str] = None
    url: Optional[str] = None


class ScoredCriterion(BaseModel):
    """A criterion with its score and supporting evidence."""
    name: str
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    weight: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    rationale: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    
    @validator('score')
    def validate_score(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Score must be between 1 and 5')
        return v


class PIEScore(BaseModel):
    """PIE (Potential, Importance, Ease) scoring result."""
    potential: ScoredCriterion
    importance: ScoredCriterion 
    ease: ScoredCriterion
    total_score: float = 0.0
    weighted_score: float = 0.0
    priority_tier: str = ""
    evidence_completeness: float = 0.0
    
    def calculate_scores(self):
        """Calculate total and weighted scores."""
        self.total_score = self.potential.score + self.importance.score + self.ease.score
        
        total_weight = self.potential.weight + self.importance.weight + self.ease.weight
        if total_weight > 0:
            self.weighted_score = (
                (self.potential.score * self.potential.weight + 
                 self.importance.score * self.importance.weight +
                 self.ease.score * self.ease.weight) / total_weight
            )
        
        # Determine priority tier
        if self.weighted_score >= 4.0:
            self.priority_tier = "High"
        elif self.weighted_score >= 3.0:
            self.priority_tier = "Medium" 
        else:
            self.priority_tier = "Low"


class ICEScore(BaseModel):
    """ICE (Impact, Confidence, Ease) scoring result."""
    impact: ScoredCriterion
    confidence: ScoredCriterion
    ease: ScoredCriterion
    total_score: float = 0.0
    ice_score: float = 0.0  # Product of I * C * E
    priority_tier: str = ""
    evidence_completeness: float = 0.0
    
    def calculate_scores(self):
        """Calculate total and ICE scores."""
        self.total_score = self.impact.score + self.confidence.score + self.ease.score
        self.ice_score = (self.impact.score * self.confidence.score * self.ease.score) / 125.0  # Normalize to 0-1
        
        # Determine priority tier
        if self.ice_score >= 0.64:  # (4*4*4)/125
            self.priority_tier = "High"
        elif self.ice_score >= 0.216:  # (3*3*3)/125
            self.priority_tier = "Medium"
        else:
            self.priority_tier = "Low"


class StrategicInitiative(BaseModel):
    """A strategic initiative to be scored."""
    id: str
    title: str
    description: str
    category: str = "general"
    owner: Optional[str] = None
    estimated_effort: Optional[str] = None
    timeline: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    
    pie_score: Optional[PIEScore] = None
    ice_score: Optional[ICEScore] = None
    
    created_date: Optional[str] = None
    last_updated: Optional[str] = None


class PIEScorer:
    """PIE (Potential, Importance, Ease) scoring system with evidence requirements."""
    
    def __init__(self):
        self.evidence_requirements = {
            "potential": EvidenceRequirement(
                criterion="potential",
                evidence_types=[EvidenceType.MARKET_RESEARCH, EvidenceType.FINANCIAL_DATA],
                minimum_sources=2,
                description="Evidence of market size, growth potential, or financial impact"
            ),
            "importance": EvidenceRequirement(
                criterion="importance",
                evidence_types=[EvidenceType.STAKEHOLDER_INPUT, EvidenceType.CUSTOMER_FEEDBACK],
                minimum_sources=1,
                description="Evidence of strategic importance and stakeholder priority"
            ),
            "ease": EvidenceRequirement(
                criterion="ease",
                evidence_types=[EvidenceType.TECHNICAL_FEASIBILITY, EvidenceType.HISTORICAL_DATA],
                minimum_sources=1,
                description="Evidence of implementation complexity and resource requirements"
            )
        }
    
    def score_initiative(
        self,
        initiative: StrategicInitiative,
        evidence_by_criterion: Dict[str, List[Evidence]],
        weights: Optional[Dict[str, float]] = None
    ) -> StrategicInitiative:
        """Score a strategic initiative using PIE framework."""
        
        logger.info(f"Scoring initiative '{initiative.title}' using PIE framework")
        
        # Default weights
        if weights is None:
            weights = {"potential": 1.0, "importance": 1.0, "ease": 1.0}
        
        # Score each criterion
        potential = self._score_criterion(
            "potential", 
            evidence_by_criterion.get("potential", []),
            weights.get("potential", 1.0)
        )
        
        importance = self._score_criterion(
            "importance",
            evidence_by_criterion.get("importance", []),
            weights.get("importance", 1.0)
        )
        
        ease = self._score_criterion(
            "ease",
            evidence_by_criterion.get("ease", []),
            weights.get("ease", 1.0)
        )
        
        # Create PIE score
        pie_score = PIEScore(
            potential=potential,
            importance=importance,
            ease=ease
        )
        
        pie_score.calculate_scores()
        pie_score.evidence_completeness = self._calculate_evidence_completeness(evidence_by_criterion)
        
        initiative.pie_score = pie_score
        
        logger.info(f"PIE score calculated: {pie_score.weighted_score:.2f} ({pie_score.priority_tier} priority)")
        return initiative
    
    def _score_criterion(self, criterion_name: str, evidence_list: List[Evidence], weight: float) -> ScoredCriterion:
        """Score a single criterion based on evidence."""
        
        requirement = self.evidence_requirements.get(criterion_name)
        if not requirement:
            raise ValueError(f"Unknown criterion: {criterion_name}")
        
        # Calculate base score from evidence
        if not evidence_list:
            base_score = 1  # Minimum score if no evidence
            confidence = 0.1
            rationale = f"No evidence provided for {criterion_name}"
        else:
            # Score based on evidence quality and quantity
            evidence_scores = []
            for evidence in evidence_list:
                # Weight evidence by confidence and relevance
                evidence_score = evidence.confidence * self._get_evidence_relevance(evidence.evidence_type, requirement)
                evidence_scores.append(evidence_score)
            
            # Average evidence score converted to 1-5 scale
            avg_evidence_score = sum(evidence_scores) / len(evidence_scores)
            base_score = max(1, min(5, int(avg_evidence_score * 5) + 1))
            confidence = avg_evidence_score
            rationale = f"Based on {len(evidence_list)} pieces of evidence"
        
        # Adjust score based on evidence completeness
        evidence_penalty = self._calculate_evidence_penalty(evidence_list, requirement)
        final_score = max(1, base_score - evidence_penalty)
        
        return ScoredCriterion(
            name=criterion_name,
            score=final_score,
            weight=weight,
            evidence=evidence_list,
            rationale=rationale,
            confidence=confidence
        )
    
    def _get_evidence_relevance(self, evidence_type: EvidenceType, requirement: EvidenceRequirement) -> float:
        """Get relevance score (0-1) of evidence type for a requirement."""
        if evidence_type in requirement.evidence_types:
            return 1.0
        else:
            # Partial credit for related evidence types
            relevance_map = {
                EvidenceType.MARKET_RESEARCH: [EvidenceType.COMPETITIVE_ANALYSIS, EvidenceType.CUSTOMER_FEEDBACK],
                EvidenceType.FINANCIAL_DATA: [EvidenceType.HISTORICAL_DATA],
                EvidenceType.TECHNICAL_FEASIBILITY: [EvidenceType.STAKEHOLDER_INPUT],
            }
            
            for primary_type, related_types in relevance_map.items():
                if primary_type in requirement.evidence_types and evidence_type in related_types:
                    return 0.7
            
            return 0.3  # Minimal credit for any evidence
    
    def _calculate_evidence_penalty(self, evidence_list: List[Evidence], requirement: EvidenceRequirement) -> int:
        """Calculate penalty for insufficient evidence."""
        if not requirement.required:
            return 0
        
        if len(evidence_list) < requirement.minimum_sources:
            return min(2, requirement.minimum_sources - len(evidence_list))
        
        # Check for required evidence types
        provided_types = {evidence.evidence_type for evidence in evidence_list}
        required_types = set(requirement.evidence_types)
        
        if not required_types.intersection(provided_types):
            return 1  # Penalty for missing required evidence types
        
        return 0
    
    def _calculate_evidence_completeness(self, evidence_by_criterion: Dict[str, List[Evidence]]) -> float:
        """Calculate overall evidence completeness score (0-1)."""
        total_requirements = len(self.evidence_requirements)
        completeness_scores = []
        
        for criterion_name, requirement in self.evidence_requirements.items():
            evidence_list = evidence_by_criterion.get(criterion_name, [])
            
            # Score based on minimum sources requirement
            source_completeness = min(1.0, len(evidence_list) / requirement.minimum_sources)
            
            # Score based on evidence type requirements
            provided_types = {evidence.evidence_type for evidence in evidence_list}
            required_types = set(requirement.evidence_types)
            type_completeness = len(required_types.intersection(provided_types)) / len(required_types)
            
            criterion_completeness = (source_completeness + type_completeness) / 2
            completeness_scores.append(criterion_completeness)
        
        return sum(completeness_scores) / total_requirements if completeness_scores else 0.0


class ICEScorer:
    """ICE (Impact, Confidence, Ease) scoring system with evidence requirements."""
    
    def __init__(self):
        self.evidence_requirements = {
            "impact": EvidenceRequirement(
                criterion="impact",
                evidence_types=[EvidenceType.MARKET_RESEARCH, EvidenceType.FINANCIAL_DATA, EvidenceType.CUSTOMER_FEEDBACK],
                minimum_sources=2,
                description="Evidence of potential business impact and value creation"
            ),
            "confidence": EvidenceRequirement(
                criterion="confidence",
                evidence_types=[EvidenceType.HISTORICAL_DATA, EvidenceType.TECHNICAL_FEASIBILITY],
                minimum_sources=1,
                description="Evidence supporting confidence in successful execution"
            ),
            "ease": EvidenceRequirement(
                criterion="ease",
                evidence_types=[EvidenceType.TECHNICAL_FEASIBILITY, EvidenceType.STAKEHOLDER_INPUT],
                minimum_sources=1,
                description="Evidence of implementation simplicity and resource availability"
            )
        }
    
    def score_initiative(
        self,
        initiative: StrategicInitiative,
        evidence_by_criterion: Dict[str, List[Evidence]]
    ) -> StrategicInitiative:
        """Score a strategic initiative using ICE framework."""
        
        logger.info(f"Scoring initiative '{initiative.title}' using ICE framework")
        
        # Score each criterion (reuse PIE scoring logic)
        pie_scorer = PIEScorer()
        pie_scorer.evidence_requirements = self.evidence_requirements
        
        impact = pie_scorer._score_criterion("impact", evidence_by_criterion.get("impact", []), 1.0)
        confidence = pie_scorer._score_criterion("confidence", evidence_by_criterion.get("confidence", []), 1.0)
        ease = pie_scorer._score_criterion("ease", evidence_by_criterion.get("ease", []), 1.0)
        
        # Create ICE score
        ice_score = ICEScore(
            impact=impact,
            confidence=confidence,
            ease=ease
        )
        
        ice_score.calculate_scores()
        ice_score.evidence_completeness = pie_scorer._calculate_evidence_completeness(evidence_by_criterion)
        
        initiative.ice_score = ice_score
        
        logger.info(f"ICE score calculated: {ice_score.ice_score:.3f} ({ice_score.priority_tier} priority)")
        return initiative


class InitiativePortfolio(BaseModel):
    """Portfolio of strategic initiatives with comparative analysis."""
    initiatives: List[StrategicInitiative] = Field(default_factory=list)
    scoring_method: str = "PIE"  # PIE or ICE
    
    def add_initiative(self, initiative: StrategicInitiative):
        """Add initiative to portfolio."""
        self.initiatives.append(initiative)
    
    def get_ranked_initiatives(self, by_score: str = "weighted") -> List[StrategicInitiative]:
        """Get initiatives ranked by score."""
        if self.scoring_method == "PIE":
            if by_score == "weighted":
                return sorted(self.initiatives, key=lambda x: x.pie_score.weighted_score if x.pie_score else 0, reverse=True)
            else:
                return sorted(self.initiatives, key=lambda x: x.pie_score.total_score if x.pie_score else 0, reverse=True)
        else:  # ICE
            if by_score == "ice":
                return sorted(self.initiatives, key=lambda x: x.ice_score.ice_score if x.ice_score else 0, reverse=True)
            else:
                return sorted(self.initiatives, key=lambda x: x.ice_score.total_score if x.ice_score else 0, reverse=True)
    
    def get_high_priority_initiatives(self) -> List[StrategicInitiative]:
        """Get high priority initiatives."""
        return [
            initiative for initiative in self.initiatives
            if (self.scoring_method == "PIE" and initiative.pie_score and initiative.pie_score.priority_tier == "High") or
               (self.scoring_method == "ICE" and initiative.ice_score and initiative.ice_score.priority_tier == "High")
        ]
    
    def generate_portfolio_summary(self) -> Dict[str, Any]:
        """Generate portfolio summary with insights."""
        total_initiatives = len(self.initiatives)
        if total_initiatives == 0:
            return {"error": "No initiatives in portfolio"}
        
        high_priority = len(self.get_high_priority_initiatives())
        
        # Calculate average evidence completeness
        completeness_scores = []
        for initiative in self.initiatives:
            if self.scoring_method == "PIE" and initiative.pie_score:
                completeness_scores.append(initiative.pie_score.evidence_completeness)
            elif self.scoring_method == "ICE" and initiative.ice_score:
                completeness_scores.append(initiative.ice_score.evidence_completeness)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        return {
            "total_initiatives": total_initiatives,
            "high_priority_count": high_priority,
            "high_priority_percentage": (high_priority / total_initiatives) * 100,
            "average_evidence_completeness": avg_completeness,
            "scoring_method": self.scoring_method,
            "recommendations": self._generate_portfolio_recommendations(avg_completeness, high_priority, total_initiatives)
        }
    
    def _generate_portfolio_recommendations(self, avg_completeness: float, high_priority: int, total: int) -> List[str]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        if avg_completeness < 0.5:
            recommendations.append("Gather additional evidence to support initiative scoring")
        
        if high_priority / total > 0.5:
            recommendations.append("High proportion of high-priority initiatives may indicate resource constraints")
        elif high_priority / total < 0.2:
            recommendations.append("Consider reassessing initiative importance or gathering better evidence")
        
        if total > 20:
            recommendations.append("Large portfolio may benefit from consolidation or phased approach")
        
        return recommendations