"""Phase 3 - Debate Framework & Causality API Router per SCRATCH.md"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any
import pandas as pd

from ..debate_framework import (
    ToulminDebateFramework, 
    ToulminArgument, 
    Evidence, 
    ConfidenceLevel,
    ArgumentType
)
from ..causal_analysis import CausalAnalysisFramework, StrategyImpact, CausalDAG

router = APIRouter(prefix="/phase3", tags=["Phase 3 - Debate & Causality"])


# Request/Response Models for Toulmin Debate Framework

class CreateDebateRequest(BaseModel):
    """Request to create structured debate."""
    title: str = Field(..., description="Debate title")
    context: str = Field(..., description="Debate context and background")
    participants: list[str] = Field(..., description="List of participants")
    moderator: str | None = Field(None, description="Optional moderator")


class CreateArgumentRequest(BaseModel):
    """Request to create Toulmin argument."""
    debate_id: str
    claim: str = Field(..., description="Central assertion")
    grounds: list[str] = Field(..., description="Evidence supporting the claim")
    warrant: str = Field(..., description="Link between grounds and claim")
    backing: str | None = Field(None, description="Support for the warrant")
    qualifier: str | None = Field(None, description="Conditions/limitations")
    rebuttal: str | None = Field(None, description="Counter-arguments/exceptions")
    author: str = Field("system", description="Argument author")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence level")
    evidence: list[dict[str, Any]] | None = Field(None, description="Supporting evidence")


class ArgumentRelationRequest(BaseModel):
    """Request to create argument relationship."""
    debate_id: str
    from_argument_id: str
    to_argument_id: str
    relation_type: str = Field(..., description="supports, rebuts, qualifies, extends")
    strength: float = Field(1.0, ge=0.0, le=1.0, description="Relationship strength")
    description: str | None = Field(None, description="Relationship description")


# Request/Response Models for Causal Analysis

class StrategyAnalysisRequest(BaseModel):
    """Request to analyze strategy causal impact."""
    strategy_id: str = Field(..., description="Unique strategy identifier") 
    strategy_title: str = Field(..., description="Strategy title")
    treatment_vars: list[str] = Field(..., description="Treatment variables (interventions)")
    outcome_vars: list[str] = Field(..., description="Outcome variables (KPIs)")
    confounders: list[str] | None = Field(None, description="Potential confounding variables")
    historical_data: dict[str, list[float]] | None = Field(None, description="Historical data for analysis")


class StrategyValidationResponse(BaseModel):
    """Response for strategy validation."""
    strategy_id: str
    impact_category: str
    quality_gates_passed: bool
    recommendation: str
    quality_gates: dict[str, bool]
    estimations_summary: list[dict[str, Any]]
    dag_screenshot_available: bool


# Global framework instances
_debate_framework: ToulminDebateFramework | None = None
_causal_framework: CausalAnalysisFramework | None = None


def get_debate_framework() -> ToulminDebateFramework:
    """Get or create debate framework."""
    global _debate_framework
    if _debate_framework is None:
        _debate_framework = ToulminDebateFramework()
    return _debate_framework


def get_causal_framework() -> CausalAnalysisFramework:
    """Get or create causal analysis framework."""
    global _causal_framework
    if _causal_framework is None:
        _causal_framework = CausalAnalysisFramework()
    return _causal_framework


# Toulmin Debate Framework Endpoints

@router.post("/debates/create")
async def create_debate(
    request: CreateDebateRequest,
    framework: ToulminDebateFramework = Depends(get_debate_framework)
) -> dict[str, Any]:
    """
    Create structured debate with Toulmin framework per SCRATCH.md Phase 3.1.
    
    Features:
    - Explicit Toulmin schema (claim/grounds/warrant/backing/qualifier/rebuttal)
    - Argument mapping for audit/UI overlays
    - JSON serialization for structured reasoning
    """
    try:
        debate = framework.create_debate(
            title=request.title,
            context=request.context,
            participants=request.participants,
            moderator=request.moderator
        )
        
        return {
            "debate_id": debate.debate_id,
            "title": debate.title,
            "status": debate.status,
            "participants": debate.participants,
            "moderator": debate.moderator,
            "created_at": debate.created_at,
            "message": "Structured debate created with Toulmin framework"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create debate: {str(e)}")


@router.post("/debates/arguments/create")
async def create_argument(
    request: CreateArgumentRequest,
    framework: ToulminDebateFramework = Depends(get_debate_framework)
) -> dict[str, Any]:
    """
    Create structured argument using Toulmin schema.
    
    Toulmin Components:
    - Claim: Central assertion
    - Grounds: Evidence supporting claim
    - Warrant: Link between grounds and claim  
    - Backing: Support for the warrant
    - Qualifier: Conditions/limitations
    - Rebuttal: Counter-arguments/exceptions
    """
    try:
        # Convert evidence dicts to Evidence objects
        evidence_objects = []
        if request.evidence:
            for ev_dict in request.evidence:
                evidence_objects.append(Evidence(**ev_dict))
        
        argument = framework.create_argument(
            claim=request.claim,
            grounds=request.grounds,
            warrant=request.warrant,
            backing=request.backing,
            qualifier=request.qualifier,
            rebuttal=request.rebuttal,
            author=request.author,
            evidence=evidence_objects
        )
        
        framework.add_argument_to_debate(request.debate_id, argument)
        
        # Calculate argument strength
        strength_score = argument.get_strength_score()
        validation_issues = argument.validate()
        
        return {
            "argument_id": argument.argument_id,
            "debate_id": request.debate_id,
            "toulmin_structure": {
                "claim": argument.claim,
                "grounds": argument.grounds,
                "warrant": argument.warrant,
                "backing": argument.backing,
                "qualifier": argument.qualifier,
                "rebuttal": argument.rebuttal
            },
            "strength_score": strength_score,
            "confidence": argument.confidence.value,
            "validation_issues": validation_issues,
            "created_at": argument.created_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create argument: {str(e)}")


@router.post("/debates/relations/create")
async def create_argument_relation(
    request: ArgumentRelationRequest,
    framework: ToulminDebateFramework = Depends(get_debate_framework)
) -> dict[str, Any]:
    """Create relationship between arguments for argument mapping."""
    try:
        relation = framework.create_argument_relation(
            debate_id=request.debate_id,
            from_argument_id=request.from_argument_id,
            to_argument_id=request.to_argument_id,
            relation_type=request.relation_type,
            strength=request.strength,
            description=request.description
        )
        
        return {
            "relation_id": relation.relation_id,
            "from_argument": relation.from_argument,
            "to_argument": relation.to_argument,
            "relation_type": relation.relation_type,
            "strength": relation.strength,
            "description": relation.description
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create relation: {str(e)}")


@router.get("/debates/{debate_id}/summary")
async def get_debate_summary(
    debate_id: str,
    framework: ToulminDebateFramework = Depends(get_debate_framework)
) -> dict[str, Any]:
    """Get debate summary with argument strengths and validation."""
    try:
        summary = framework.get_debate_summary(debate_id)
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/debates/{debate_id}/argument-map")
async def get_argument_map_ui(
    debate_id: str,
    framework: ToulminDebateFramework = Depends(get_debate_framework)
) -> dict[str, Any]:
    """
    Export debate as JSON for UI argument map per SCRATCH.md.
    
    Returns structured data for visualization with nodes and edges.
    """
    try:
        ui_json = framework.export_for_ui(debate_id)
        return {"ui_structure": ui_json, "format": "json", "framework": "toulmin"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export UI: {str(e)}")


# Causal Analysis Framework Endpoints

@router.post("/causality/analyze")
async def analyze_strategy_causality(
    request: StrategyAnalysisRequest,
    framework: CausalAnalysisFramework = Depends(get_causal_framework)
) -> dict[str, Any]:
    """
    Analyze causal impact of strategy using DoWhy/EconML per SCRATCH.md Phase 3.2.
    
    Features:
    - Causal DAG construction and validation
    - Causal identification and estimation
    - Refutation testing for robustness
    - Quality gate enforcement for high-impact strategies
    """
    try:
        # Convert historical data to DataFrame if provided
        historical_data = None
        if request.historical_data:
            historical_data = pd.DataFrame(request.historical_data)
        
        # Analyze strategy impact
        impact = framework.analyze_strategy_impact(
            strategy_id=request.strategy_id,
            strategy_title=request.strategy_title,
            treatment_vars=request.treatment_vars,
            outcome_vars=request.outcome_vars,
            historical_data=historical_data,
            confounders=request.confounders
        )
        
        return {
            "strategy_id": impact.strategy_id,
            "strategy_title": impact.strategy_title,
            "impact_category": impact.impact_category,
            "causal_dag": impact.causal_dag.to_dict(),
            "estimations": [
                {
                    "treatment": est.treatment_var,
                    "outcome": est.outcome_var,
                    "effect_estimate": est.effect_estimate,
                    "confidence_interval": est.confidence_interval,
                    "p_value": est.p_value,
                    "method": est.method,
                    "identified": est.identified,
                    "refutation_passed": est.refutation_passed
                }
                for est in impact.estimations
            ],
            "quality_gates": {
                "identification_passed": impact.identification_passed,
                "refutation_passed": impact.refutation_passed,
                "dag_screenshot_available": impact.dag_screenshot_path is not None,
                "synthetic_control_applicable": impact.synthetic_control_applicable
            },
            "analyzed_at": impact.analyzed_at,
            "analyst": impact.analyst
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Causal analysis failed: {str(e)}")


@router.get("/causality/validate/{strategy_id}", response_model=StrategyValidationResponse)
async def validate_strategy_quality_gates(
    strategy_id: str,
    framework: CausalAnalysisFramework = Depends(get_causal_framework)
) -> StrategyValidationResponse:
    """
    Validate strategy quality gates per SCRATCH.md requirements.
    
    Quality Gates for "High-impact" strategies:
    - Causal DAG screenshot + identification result + refutation test passing
    """
    try:
        validation = framework.validate_high_impact_strategy(strategy_id)
        
        return StrategyValidationResponse(
            strategy_id=validation["strategy_id"],
            impact_category=validation["impact_category"],
            quality_gates_passed=all(validation["quality_gates"].values()),
            recommendation=validation["recommendation"],
            quality_gates=validation["quality_gates"],
            estimations_summary=validation["estimations_summary"],
            dag_screenshot_available=validation["quality_gates"]["causal_dag_screenshot"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/causality/dag/{strategy_id}")
async def get_causal_dag_visualization(
    strategy_id: str,
    framework: CausalAnalysisFramework = Depends(get_causal_framework)
) -> dict[str, Any]:
    """
    Get causal DAG in DOT format for visualization per SCRATCH.md.
    
    Returns DAG structure that can be rendered as a diagram.
    """
    try:
        dot_graph = framework.export_dag_visualization(strategy_id)
        
        return {
            "strategy_id": strategy_id,
            "dag_format": "dot",
            "dag_content": dot_graph,
            "visualization_note": "Use Graphviz to render this DAG"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DAG export failed: {str(e)}")


@router.get("/config")
async def get_phase3_config() -> dict[str, Any]:
    """Get Phase 3 configuration and status."""
    return {
        "phase": "Phase 3 - Debate Framework & Causality",
        "components": {
            "toulmin_debates": "active",
            "causal_analysis": "active",
            "argument_mapping": "available",
            "quality_gates": "enforced"
        },
        "toulmin_framework": {
            "argument_components": [
                "claim", "grounds", "warrant", "backing", "qualifier", "rebuttal"
            ],
            "relation_types": ["supports", "rebuts", "qualifies", "extends"],
            "serialization": "JSON for audit/UI overlays"
        },
        "causal_analysis": {
            "methods": ["DoWhy identification", "EconML estimation", "refutation tests"],
            "quality_gates": {
                "high_impact_requirements": [
                    "causal DAG screenshot",
                    "identification result", 
                    "refutation test passing"
                ]
            },
            "synthetic_control": "available for policy changes"
        },
        "status": "Phase 3 implementation complete per SCRATCH.md"
    }


@router.get("/health")
async def phase3_health_check() -> dict[str, Any]:
    """Health check for Phase 3 components."""
    return {
        "status": "healthy",
        "phase": "Phase 3 - Debate Framework & Causality",
        "frameworks": {
            "toulmin_debates": "initialized",
            "causal_analysis": "initialized"
        },
        "features": {
            "argument_mapping": True,
            "quality_gate_validation": True,
            "dag_visualization": True,
            "json_serialization": True
        },
        "dependencies": {
            "dowhy": "optional",
            "econml": "optional", 
            "pandas": "required",
            "numpy": "required"
        }
    }