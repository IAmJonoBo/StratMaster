"""Industry-specific templates router for StratMaster API."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..templates import (
    get_available_industries,
    get_industry_template,
    get_industry_kpis,
    render_industry_strategy,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["industry-templates"])


class IndustryTemplateResponse(BaseModel):
    """Response model for industry template data."""
    template_id: str
    industry: str
    name: str
    description: str
    recommended_kpis: List[str]
    success_metrics: List[str]
    common_challenges: List[str]
    strategic_focus_areas: List[str]
    enabled: bool


class IndustryListResponse(BaseModel):
    """Response model for available industries."""
    industries: List[str]
    enabled: bool


class StrategyRenderRequest(BaseModel):
    """Request model for rendering industry-specific strategy."""
    industry: str
    title: str = "Strategic Analysis Brief"
    executive_summary: str = ""
    key_findings: List[str] = []
    strategic_recommendations: List[str] = []
    market_analysis: str = ""
    situation_analysis: str = ""
    competitive_landscape: str = ""
    internal_capabilities: str = ""
    implementation_roadmap: str = ""
    evidence_sources: List[str] = []
    assumptions: List[str] = []
    evidence_strength: str = "Medium"
    confidence_level: str = "High"
    completeness_score: float = 0.8
    version: str = "1.0"
    authors: List[str] = []


@router.get("/industries", response_model=IndustryListResponse)
async def get_industries() -> IndustryListResponse:
    """Get list of available industry templates."""
    try:
        industries = get_available_industries()
        return IndustryListResponse(
            industries=industries,
            enabled=True
        )
    except Exception as e:
        logger.error(f"Error getting industries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available industries")


@router.get("/industry/{industry}", response_model=IndustryTemplateResponse)
async def get_template_for_industry(industry: str) -> IndustryTemplateResponse:
    """Get template metadata for specific industry."""
    try:
        template_data = get_industry_template(industry)
        return IndustryTemplateResponse(**template_data)
    except Exception as e:
        logger.error(f"Error getting template for industry {industry}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template for industry {industry}")


@router.get("/industry/{industry}/kpis")
async def get_kpis_for_industry(industry: str) -> Dict[str, Any]:
    """Get recommended KPIs for specific industry."""
    try:
        kpis = get_industry_kpis(industry)
        return {
            "industry": industry,
            "recommended_kpis": kpis,
            "count": len(kpis)
        }
    except Exception as e:
        logger.error(f"Error getting KPIs for industry {industry}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get KPIs for industry {industry}")


@router.post("/render")
async def render_strategy_template(request: StrategyRenderRequest) -> Dict[str, Any]:
    """Render strategy using industry-specific template."""
    try:
        # Convert request to dict for template rendering
        strategy_data = request.model_dump()
        
        # Render strategy using industry template
        rendered_strategy = render_industry_strategy(
            industry=request.industry,
            strategy_data=strategy_data
        )
        
        return {
            "industry": request.industry,
            "rendered_strategy": rendered_strategy,
            "title": request.title,
            "generated_at": "2024-09-24T20:55:00Z"  # Would be dynamic in real implementation
        }
        
    except Exception as e:
        logger.error(f"Error rendering strategy template: {e}")
        raise HTTPException(status_code=500, detail="Failed to render strategy template")


@router.get("/catalog")
async def get_template_catalog() -> Dict[str, Any]:
    """Get complete catalog of available templates."""
    try:
        industries = get_available_industries()
        catalog = {}
        
        for industry in industries:
            template_data = get_industry_template(industry)
            catalog[industry] = {
                "name": template_data["name"],
                "description": template_data["description"],
                "kpi_count": len(template_data["recommended_kpis"]),
                "focus_areas": template_data["strategic_focus_areas"]
            }
        
        return {
            "catalog": catalog,
            "total_templates": len(catalog),
            "enabled": True
        }
        
    except Exception as e:
        logger.error(f"Error getting template catalog: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template catalog")