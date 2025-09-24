"""FastAPI router for Model Recommender V2 debugging and admin endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from .model_recommender import ModelRecommender, TaskContext, is_model_recommender_v2_enabled
from .model_persistence import ModelPerformanceStore  
from .model_scheduler import ModelDataScheduler

logger = logging.getLogger(__name__)

# Global instances (would be dependency injected in real app)
_model_recommender: ModelRecommender | None = None
_performance_store: ModelPerformanceStore | None = None
_data_scheduler: ModelDataScheduler | None = None


def get_model_recommender() -> ModelRecommender:
    """Dependency to get model recommender instance."""
    global _model_recommender, _performance_store
    
    if _model_recommender is None:
        if is_model_recommender_v2_enabled():
            _performance_store = ModelPerformanceStore()
            _model_recommender = ModelRecommender(persistence_store=_performance_store)
        else:
            _model_recommender = ModelRecommender()
    
    return _model_recommender


def get_data_scheduler() -> ModelDataScheduler | None:
    """Dependency to get data scheduler instance."""
    global _data_scheduler, _model_recommender, _performance_store
    
    if _data_scheduler is None and is_model_recommender_v2_enabled():
        recommender = get_model_recommender()
        if _performance_store is None:
            _performance_store = ModelPerformanceStore()
        _data_scheduler = ModelDataScheduler(recommender, _performance_store)
    
    return _data_scheduler


class ModelRecommendationRequest(BaseModel):
    """Request for model recommendation."""
    task_type: str
    tenant_id: str
    complexity: str = "medium"
    latency_critical: bool = False
    cost_sensitive: bool = False
    quality_threshold: float = 0.7
    available_models: list[str] | None = None


class ModelRecommendationResponse(BaseModel):
    """Response with model recommendations."""
    primary_model: str
    fallback_models: list[str]
    task_context: dict[str, Any]
    recommendation_reason: str
    model_scores: dict[str, float] | None = None


class PerformanceUpdateRequest(BaseModel):
    """Request to update model performance metrics."""
    model_name: str
    latency_ms: float
    success: bool
    cost_per_token: float | None = None


# Create router
router = APIRouter(prefix="/router", tags=["Model Router"])


@router.get("/models/status")
async def get_router_status(
    recommender: ModelRecommender = Depends(get_model_recommender)
) -> dict[str, Any]:
    """Get model router status and feature flag state."""
    return {
        "model_recommender_v2_enabled": is_model_recommender_v2_enabled(),
        "cache_status": {
            "models_cached": len(recommender.performance_cache),
            "last_updated": (
                recommender.last_cache_update.isoformat() 
                if recommender.last_cache_update else None
            )
        },
        "features": {
            "external_data_integration": is_model_recommender_v2_enabled(),
            "persistent_storage": recommender.store is not None,
            "telemetry_tracking": is_model_recommender_v2_enabled()
        }
    }


@router.post("/models/recommendation", response_model=ModelRecommendationResponse)
async def get_model_recommendation(
    request: ModelRecommendationRequest,
    recommender: ModelRecommender = Depends(get_model_recommender)
) -> ModelRecommendationResponse:
    """Get model recommendation for given task context."""
    try:
        context = TaskContext(
            task_type=request.task_type,
            tenant_id=request.tenant_id,
            complexity=request.complexity,
            latency_critical=request.latency_critical,
            cost_sensitive=request.cost_sensitive,
            quality_threshold=request.quality_threshold
        )
        
        primary_model, fallback_models = await recommender.recommend_model(
            context, request.available_models
        )
        
        # Calculate model scores for debugging
        model_scores = {}
        candidates = request.available_models or recommender._get_available_models(context)
        for model in candidates:
            score = await recommender._score_model(model, context)
            model_scores[model] = score
        
        recommendation_reason = _build_recommendation_reason(
            primary_model, context, recommender.performance_cache.get(primary_model)
        )
        
        return ModelRecommendationResponse(
            primary_model=primary_model,
            fallback_models=fallback_models,
            task_context=context.__dict__,
            recommendation_reason=recommendation_reason,
            model_scores=model_scores
        )
        
    except Exception as e:
        logger.error(f"Model recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/debug")
async def get_debug_info(
    recommender: ModelRecommender = Depends(get_model_recommender)
) -> dict[str, Any]:
    """Get detailed debugging information about model recommender."""
    debug_info = recommender.get_debug_info()
    
    # Add scheduler status if available
    scheduler = get_data_scheduler()
    if scheduler:
        debug_info["scheduler"] = scheduler.get_scheduler_status()
    
    return debug_info


@router.post("/models/performance/update")
async def update_model_performance(
    request: PerformanceUpdateRequest,
    recommender: ModelRecommender = Depends(get_model_recommender)
) -> dict[str, str]:
    """Update model performance based on actual usage."""
    try:
        await recommender.update_model_performance(
            model=request.model_name,
            latency_ms=request.latency_ms,
            success=request.success,
            cost_per_token=request.cost_per_token
        )
        
        return {
            "status": "success",
            "message": f"Updated performance for {request.model_name}"
        }
        
    except Exception as e:
        logger.error(f"Performance update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/refresh")
async def trigger_data_refresh(
    background_tasks: BackgroundTasks,
    scheduler: ModelDataScheduler | None = Depends(get_data_scheduler)
) -> dict[str, Any]:
    """Manually trigger external data refresh."""
    if not is_model_recommender_v2_enabled():
        raise HTTPException(
            status_code=404, 
            detail="Model Recommender V2 is not enabled"
        )
    
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Data scheduler not available"
        )
    
    # Run refresh in background
    background_tasks.add_task(_run_manual_refresh, scheduler)
    
    return {
        "status": "started", 
        "message": "Data refresh triggered in background"
    }


@router.get("/models/refresh/status")
async def get_refresh_status(
    scheduler: ModelDataScheduler | None = Depends(get_data_scheduler)
) -> dict[str, Any]:
    """Get status of data refresh jobs."""
    if not is_model_recommender_v2_enabled():
        return {
            "model_recommender_v2_enabled": False,
            "message": "Model Recommender V2 is not enabled"
        }
    
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Data scheduler not available"
        )
    
    return scheduler.get_scheduler_status()


@router.get("/models/{model_name}/performance")
async def get_model_performance(
    model_name: str,
    recommender: ModelRecommender = Depends(get_model_recommender)
) -> dict[str, Any]:
    """Get detailed performance data for a specific model."""
    performance = recommender.performance_cache.get(model_name)
    
    if not performance:
        raise HTTPException(
            status_code=404,
            detail=f"Performance data not found for model: {model_name}"
        )
    
    result = {
        "model_name": performance.model_name,
        "arena_elo": performance.arena_elo,
        "mteb_score": performance.mteb_score,
        "internal_score": performance.internal_score,
        "avg_latency_ms": performance.avg_latency_ms,
        "cost_per_1k_tokens": performance.cost_per_1k_tokens,
        "success_rate": performance.success_rate,
        "last_updated": performance.last_updated.isoformat() if performance.last_updated else None
    }
    
    # Add telemetry stats if available
    if recommender.store and is_model_recommender_v2_enabled():
        try:
            telemetry_stats = await recommender.store.get_model_telemetry_stats(model_name)
            result["recent_telemetry"] = telemetry_stats
        except Exception as e:
            logger.warning(f"Failed to get telemetry stats: {e}")
    
    return result


async def _run_manual_refresh(scheduler: ModelDataScheduler) -> None:
    """Run manual refresh in background."""
    try:
        result = await scheduler.trigger_manual_refresh()
        logger.info(f"Manual refresh completed: {result}")
    except Exception as e:
        logger.error(f"Manual refresh failed: {e}")


def _build_recommendation_reason(
    model: str, 
    context: TaskContext, 
    performance: Any | None
) -> str:
    """Build human-readable explanation for model recommendation."""
    reasons = [f"Recommended {model}"]
    
    if performance:
        if context.task_type == "embed" and performance.mteb_score:
            reasons.append(f"MTEB score: {performance.mteb_score:.1f}")
        elif context.task_type in ["chat", "reasoning"] and performance.arena_elo:
            reasons.append(f"Arena ELO: {performance.arena_elo:.0f}")
        
        if context.cost_sensitive and performance.cost_per_1k_tokens:
            reasons.append(f"Cost: ${performance.cost_per_1k_tokens:.4f}/1k tokens")
        
        if context.latency_critical and performance.avg_latency_ms:
            reasons.append(f"Latency: {performance.avg_latency_ms:.0f}ms")
    
    reasons.append(f"Complexity: {context.complexity}")
    
    return "; ".join(reasons)