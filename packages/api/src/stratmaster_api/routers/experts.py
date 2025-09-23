"""FastAPI router for expert evaluation endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stratmaster_api.models.experts.memo import DisciplineMemo
from stratmaster_api.models.experts.vote import CouncilVote

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experts", tags=["experts"])


class EvaluateBody(BaseModel):
    """Request body for expert evaluation."""
    strategy: dict[str, Any]
    disciplines: list[str] = ["psychology", "design", "communication", "brand_science", "economics"]


class VoteBody(BaseModel):
    """Request body for expert voting."""
    strategy_id: str
    weights: dict[str, float]
    memos: list[DisciplineMemo]


async def get_mcp_client():
    """Get MCP client for expertise server.
    
    TODO: Implement actual MCP client connection.
    For now, this is a placeholder that would connect to the expertise-mcp server.
    """
    # This would normally return an MCP client instance
    # that can communicate with the expertise-mcp server via stdio or HTTP
    raise HTTPException(
        status_code=501, 
        detail="MCP client not yet implemented - connect to expertise-mcp server"
    )


@router.post("/evaluate", response_model=list[DisciplineMemo])
async def evaluate(body: EvaluateBody, mcp=Depends(get_mcp_client)) -> list[DisciplineMemo]:
    """Evaluate a strategy across expert disciplines.
    
    Args:
        body: Evaluation request containing strategy and disciplines
        mcp: MCP client dependency
        
    Returns:
        List of discipline memos with findings and scores
    """
    logger.info(f"Evaluating strategy across {len(body.disciplines)} disciplines")
    
    try:
        # Call the MCP server
        result = await mcp.call("expert.evaluate", body.model_dump())
        
        # Convert result to DisciplineMemo objects
        memos = [DisciplineMemo(**memo_data) for memo_data in result]
        
        logger.info(f"Evaluation complete: {len(memos)} memos generated")
        return memos
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/vote", response_model=CouncilVote)
async def vote(body: VoteBody, mcp=Depends(get_mcp_client)) -> CouncilVote:
    """Aggregate memos into a weighted council vote.
    
    Args:
        body: Vote request containing strategy ID, weights, and memos
        mcp: MCP client dependency
        
    Returns:
        Council vote with weighted score
    """
    logger.info(f"Aggregating vote for strategy {body.strategy_id}")
    
    try:
        # Call the MCP server
        result = await mcp.call("expert.vote", body.model_dump())
        
        # Convert result to CouncilVote object
        council_vote = CouncilVote(**result)
        
        logger.info(f"Vote complete: weighted score {council_vote.weighted_score:.2f}")
        return council_vote
        
    except Exception as e:
        logger.error(f"Vote aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vote aggregation failed: {str(e)}")


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for expert services."""
    return {"status": "ok", "service": "experts"}