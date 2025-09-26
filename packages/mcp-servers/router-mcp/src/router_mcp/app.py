from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from .config import load_config
from .models import (
    AgentRouteRequest,
    AgentRouteResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    InfoResponse,
    RerankRequest,
    RerankResponse,
)
from .service import RouterService
from .model_recommender import is_model_recommender_v2_enabled


def create_app() -> FastAPI:
    config = load_config()
    service = RouterService(config)

    app = FastAPI(title="Router MCP", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/info", response_model=InfoResponse)
    async def info() -> InfoResponse:
        provider = config.default_provider
        return InfoResponse(
            name="router-mcp",
            version="0.1.0",
            capabilities=["complete", "embed", "rerank"],
            service={
                "default_completion_model": provider.completion_model,
                "default_embedding_model": provider.embedding_model,
                "default_rerank_model": provider.rerank_model,
                "providers": [provider.name],
            },
        )

    tools = APIRouter(prefix="/tools", tags=["tools"])

    @tools.post("/complete", response_model=CompletionResponse)
    async def complete(payload: CompletionRequest) -> CompletionResponse:
        return service.complete(payload)

    @tools.post("/embed", response_model=EmbeddingResponse)
    async def embed(payload: EmbeddingRequest) -> EmbeddingResponse:
        return service.embed(payload)

    @tools.post("/rerank", response_model=RerankResponse)
    async def rerank(payload: RerankRequest) -> RerankResponse:
        return service.rerank(payload)

    @tools.post("/route", response_model=AgentRouteResponse)
    async def route_agents(payload: AgentRouteRequest) -> AgentRouteResponse:
        """Route query to appropriate specialist agents - Sprint 1."""
        return service.route_agents(payload)

    # Model recommendation with bandit selection per SCRATCH.md Phase 1
    @tools.post("/models/recommend")
    async def recommend_model(request: dict) -> JSONResponse:
        """Recommend model using UCB1 bandit selection."""
        if not is_model_recommender_v2_enabled():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "disabled",
                    "message": "Model Recommender V2 is disabled. Using default routing.",
                    "model": config.default_provider.completion_model,
                    "fallbacks": []
                }
            )
        
        try:
            # Extract context from request
            task_type = request.get("task_type", "reasoning")
            tenant_id = request.get("tenant_id", "default")
            complexity = request.get("complexity", "medium")
            latency_critical = request.get("latency_critical", False)
            cost_sensitive = request.get("cost_sensitive", False)
            
            # Create task context
            from .model_recommender import TaskContext
            context = TaskContext(
                task_type=task_type,
                tenant_id=tenant_id,
                complexity=complexity,
                latency_critical=latency_critical,
                cost_sensitive=cost_sensitive
            )
            
            # Get recommendation using bandit
            recommender = service.get_model_recommender()
            if not recommender:
                raise RuntimeError("Model recommender not initialized")
                
            primary, fallbacks = await recommender.recommend_model_with_bandit(context)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "primary_model": primary,
                    "fallback_models": fallbacks,
                    "task_type": task_type,
                    "tenant_id": tenant_id,
                    "routing_strategy": "ucb1_bandit",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Model recommendation failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": str(e),
                    "fallback_model": config.default_provider.completion_model
                }
            )
    
    @tools.post("/models/feedback")
    async def record_model_feedback(request: dict) -> JSONResponse:
        """Record model performance feedback for bandit learning."""
        if not is_model_recommender_v2_enabled():
            return JSONResponse(
                status_code=200,
                content={"status": "disabled", "message": "Model Recommender V2 is disabled"}
            )
        
        try:
            # Extract feedback data
            model_name = request.get("model_name")
            task_type = request.get("task_type", "reasoning")
            success = request.get("success", True)
            latency_ms = request.get("latency_ms", 0.0)
            cost_usd = request.get("cost_usd", 0.0)
            quality_score = request.get("quality_score", 0.0)
            
            if not model_name:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "model_name is required"}
                )
            
            # Record outcome for bandit learning
            recommender = service.get_model_recommender()
            if not recommender:
                raise RuntimeError("Model recommender not initialized")
                
            await recommender.record_outcome(
                model_name=model_name,
                task_type=task_type,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                quality_score=quality_score
            )
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Feedback recorded successfully",
                    "model_name": model_name,
                    "task_type": task_type
                }
            )
            
        except Exception as e:
            logger.error(f"Recording feedback failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    # Debug endpoint for Model Recommender V2
    @tools.get("/models/recommendation")
    async def get_model_recommendation_debug() -> JSONResponse:
        """Debug endpoint for model recommendation system.
        
        Returns current performance cache, model scores, and recommendation status.
        Only available when ENABLE_MODEL_RECOMMENDER_V2 is enabled.
        """
        if not is_model_recommender_v2_enabled():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "disabled",
                    "message": "Model Recommender V2 is disabled. Set ENABLE_MODEL_RECOMMENDER_V2=true to enable.",
                    "feature_flag": "ENABLE_MODEL_RECOMMENDER_V2",
                    "current_value": "false"
                }
            )
        
        try:
            recommender = service.get_model_recommender()
            if not recommender:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "error",
                        "message": "Model recommender not initialized"
                    }
                )
            
            # Get performance cache data
            cache_data = {}
            for model_name, performance in recommender.performance_cache.items():
                cache_data[model_name] = {
                    "arena_elo": performance.arena_elo,
                    "mteb_score": performance.mteb_score,
                    "internal_score": performance.internal_score,
                    "avg_latency_ms": performance.avg_latency_ms,
                    "cost_per_1k_tokens": performance.cost_per_1k_tokens,
                    "success_rate": performance.success_rate,
                    "last_updated": performance.last_updated.isoformat() if performance.last_updated else None
                }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "enabled",
                    "version": "v2",
                    "last_cache_update": recommender.last_cache_update.isoformat() if recommender.last_cache_update else None,
                    "cached_models": len(cache_data),
                    "performance_cache": cache_data,
                    "feature_flags": {
                        "ENABLE_MODEL_RECOMMENDER_V2": "true"
                    }
                }
            )
        
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Failed to get recommendation debug info: {str(e)}"
                }
            )

    app.include_router(tools)

    return app
