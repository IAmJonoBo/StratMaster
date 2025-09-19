from __future__ import annotations

from fastapi import APIRouter, FastAPI

from .config import load_config
from .models import EvalRunRequest, EvalRunResponse, InfoResponse
from .service import EvalsService


def create_app() -> FastAPI:
    config = load_config()
    service = EvalsService(config)

    app = FastAPI(title="Evals MCP", version="0.1.0")

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/info", response_model=InfoResponse)
    async def info():
        return InfoResponse(
            name="evals-mcp",
            version="0.1.0",
            suites=["rag", "truthfulqa", "factscore"],
        )

    router = APIRouter(prefix="/tools", tags=["tools"])

    @router.post("/run", response_model=EvalRunResponse)
    async def run_eval(payload: EvalRunRequest):
        return service.run(payload)

    app.include_router(router)

    return app
