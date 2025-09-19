from __future__ import annotations

from fastapi import APIRouter, FastAPI

from .config import load_config
from .models import (
    ColbertSearchRequest,
    HybridQueryRequest,
    HybridQueryResponse,
    InfoResponse,
    RankingRequest,
    RankingResponse,
    ServiceInfo,
)
from .service import KnowledgeService


def create_app() -> FastAPI:
    config = load_config()
    service = KnowledgeService(config)
    app = FastAPI(title="Knowledge MCP", version="0.1.0")

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/info", response_model=InfoResponse)
    async def info():
        connector_status = service.connector_status()
        return InfoResponse(
            name="knowledge-mcp",
            version="0.1.0",
            capabilities=[
                "vector.search",
                "keyword.search",
                "graph.community_summaries",
                "graphrag.run",
                "colbert.search",
                "splade.search",
                "rerank.bge",
            ],
            service=ServiceInfo(
                collections=[config.vector.collection],
                dense_index=config.vector.collection,
                sparse_index=config.keyword.index,
                graph_space=config.graph.space,
                connectors=connector_status,
            ),
        )

    tools = APIRouter(prefix="/tools", tags=["tools"])

    @tools.post("/hybrid_query", response_model=HybridQueryResponse)
    async def hybrid_query(payload: HybridQueryRequest):
        return service.hybrid_query(payload)

    @tools.post("/colbert_search", response_model=HybridQueryResponse)
    async def colbert_search(payload: ColbertSearchRequest):
        req = HybridQueryRequest(**payload.model_dump())
        return service.colbert_search(req)

    @tools.post("/splade_search", response_model=HybridQueryResponse)
    async def splade_search(payload: ColbertSearchRequest):
        req = HybridQueryRequest(**payload.model_dump())
        return service.splade_search(req)

    @tools.post("/rerank_bge", response_model=RankingResponse)
    async def rerank_bge(payload: RankingRequest):
        return service.rerank(payload)

    app.include_router(tools)

    resources = APIRouter(prefix="/resources", tags=["resources"])

    @resources.get("/graph/community_summaries")
    async def community_summaries(tenant_id: str, limit: int = 3):
        return service.community_summaries(tenant_id=tenant_id, limit=limit)

    app.include_router(resources)

    return app
