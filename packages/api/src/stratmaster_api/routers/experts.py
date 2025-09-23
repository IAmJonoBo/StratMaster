"""FastAPI router for expert evaluation endpoints."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stratmaster_api.models.experts.memo import DisciplineMemo
from stratmaster_api.models.experts.vote import CouncilVote
from stratmaster_api.clients.mcp_client import get_mcp_client
from stratmaster_api.clients.cache_client import get_cache_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experts", tags=["experts"])


class EvaluateBody(BaseModel):
    """Request body for expert evaluation."""
    strategy: dict[str, Any]
    disciplines: list[str] = ["psychology", "design", "communication", "brand_science", "economics", "legal"]


class VoteBody(BaseModel):
    """Request body for expert voting."""
    strategy_id: str
    weights: dict[str, float]
    memos: list[DisciplineMemo]


# Remove the old placeholder - using the imported function instead


@router.post("/evaluate", response_model=list[DisciplineMemo])
async def evaluate(body: EvaluateBody) -> list[DisciplineMemo]:
    """Evaluate a strategy across expert disciplines.
    
    Args:
        body: Evaluation request containing strategy and disciplines
        
    Returns:
        List of discipline memos with findings and scores
    """
    logger.info(f"Evaluating strategy across {len(body.disciplines)} disciplines")
    
    try:
        # Generate cache key based on strategy content and disciplines
        cache_key_data = {
            "strategy": body.strategy,
            "disciplines": sorted(body.disciplines)  # Sort for consistent keys
        }
        cache_key = hashlib.md5(
            json.dumps(cache_key_data, sort_keys=True).encode()
        ).hexdigest()
        cache_key = f"expert_evaluation:{cache_key}"
        
        # Try to get from cache first
        cache = await get_cache_client()
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached evaluation result")
            return [DisciplineMemo(**memo_data) for memo_data in cached_result]
        
        # Get MCP client and call the server
        mcp = await get_mcp_client()
        result = await mcp.call("expert.evaluate", body.model_dump())
        
        # Convert result to DisciplineMemo objects
        memos = [DisciplineMemo(**memo_data) for memo_data in result]
        
        # Cache the result for 10 minutes (600 seconds)
        await cache.set(cache_key, [memo.model_dump() for memo in memos], 600)
        
        logger.info(f"Evaluation complete: {len(memos)} memos generated")
        return memos
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/vote", response_model=CouncilVote)
async def vote(body: VoteBody) -> CouncilVote:
    """Aggregate memos into a weighted council vote.
    
    Args:
        body: Vote request containing strategy ID, weights, and memos
        
    Returns:
        Council vote with weighted score
    """
    logger.info(f"Aggregating vote for strategy {body.strategy_id}")
    
    try:
        # Generate cache key for vote aggregation
        cache_key_data = {
            "strategy_id": body.strategy_id,
            "weights": body.weights,
            "memos": [memo.model_dump() for memo in body.memos]
        }
        cache_key = hashlib.md5(
            json.dumps(cache_key_data, sort_keys=True, default=str).encode()
        ).hexdigest()
        cache_key = f"expert_vote:{cache_key}"
        
        # Try to get from cache first
        cache = await get_cache_client()
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached vote result")
            return CouncilVote(**cached_result)
        
        # Get MCP client and call the server
        mcp = await get_mcp_client()
        result = await mcp.call("expert.vote", body.model_dump())
        
        # Convert result to CouncilVote object
        council_vote = CouncilVote(**result)
        
        # Cache the result for 5 minutes (300 seconds)
        await cache.set(cache_key, council_vote.model_dump(), 300)
        
        logger.info(f"Vote complete: weighted score {council_vote.weighted_score:.2f}")
        return council_vote
        
    except Exception as e:
        logger.error(f"Vote aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vote aggregation failed: {str(e)}")


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for expert services."""
    return {"status": "ok", "service": "experts"}


@router.delete("/cache")
async def clear_cache() -> dict[str, str]:
    """Clear expert evaluation cache."""
    try:
        cache = await get_cache_client()
        await cache.clear_pattern("expert_*")
        logger.info("Expert evaluation cache cleared")
        return {"status": "ok", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")