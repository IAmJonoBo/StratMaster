from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException

from .config import AppConfig, load_config
from .models import (
    CachedPageResource,
    CrawlRequest,
    CrawlResponse,
    MetasearchRequest,
    MetasearchResponse,
    ProvenanceResource,
)
from .service import ResearchService


def _build_service() -> tuple[AppConfig, ResearchService]:
    config = load_config()
    service = ResearchService(config)
    return config, service


def create_app() -> FastAPI:
    config, service = _build_service()
    app = FastAPI(title="Research MCP", version="0.3.0")

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/info")
    async def info():
        return {
            "name": "research-mcp",
            "version": "0.3.0",
            "capabilities": ["health", "info", "metasearch", "crawl", "resources"],
            "allowlist": config.crawler.allowlist,
            "network_enabled": config.crawler.use_network,
        }

    tools_router = APIRouter(prefix="/tools", tags=["tools"])

    @tools_router.post("/metasearch", response_model=MetasearchResponse)
    async def metasearch(payload: MetasearchRequest):
        try:
            return service.metasearch(payload)
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @tools_router.post("/crawl", response_model=CrawlResponse)
    async def crawl(payload: CrawlRequest):
        try:
            return service.crawl(payload)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    app.include_router(tools_router)

    resources_router = APIRouter(prefix="/resources", tags=["resources"])

    @resources_router.get("/cached_page/{cache_key}", response_model=CachedPageResource)
    async def cached_page(cache_key: str):
        try:
            return service.cached_page(cache_key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="cached page not found")

    @resources_router.get("/provenance/{cache_key}", response_model=ProvenanceResource)
    async def provenance(cache_key: str):
        try:
            return service.provenance(cache_key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="provenance not found")

    app.include_router(resources_router)

    return app
