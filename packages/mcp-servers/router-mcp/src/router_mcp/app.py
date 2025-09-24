from __future__ import annotations

from fastapi import APIRouter, FastAPI

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

    app.include_router(tools)

    return app
