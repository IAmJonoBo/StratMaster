from __future__ import annotations

from fastapi import APIRouter, FastAPI

from .config import load_config
from .models import CompressRequest, CompressResponse
from .service import CompressionService


def create_app() -> FastAPI:
    config = load_config()
    service = CompressionService(config)

    app = FastAPI(title="Compression MCP", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    tools = APIRouter(prefix="/tools", tags=["tools"])

    @tools.post("/compress", response_model=CompressResponse)
    async def compress(payload: CompressRequest) -> CompressResponse:
        return service.compress(payload)

    app.include_router(tools)

    return app
