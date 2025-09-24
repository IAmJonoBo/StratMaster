from __future__ import annotations

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
