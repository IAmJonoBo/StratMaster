from __future__ import annotations

import json
import logging
import os
import re
import uuid
from collections.abc import Callable
from json import JSONDecodeError
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from opentelemetry import trace
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from .dependencies import require_idempotency_key
from .models import RecommendationOutcome
from .models.requests import (
    DebateRunRequest,
    DebateRunResponse,
    EvalRunRequest,
    EvalRunResponse,
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ForecastCreateRequest,
    ForecastCreateResponse,
    GraphSummariseRequest,
    GraphSummariseResponse,
    RecommendationRequest,
    ResearchPlanRequest,
    ResearchPlanResponse,
    ResearchRunRequest,
    ResearchRunResponse,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
)
from .models.schema_export import SCHEMA_VERSION
from .routers import debate as debate_hitl_router
from .routers import export as export_router
from .routers import ingestion as ingestion_router
from .routers import performance as performance_router
from .routers import security as security_router
from .routers import strategy as strategy_router
from .routers import ui as ui_router
from .schemas import (
    CompressionConfig,
    EvalsThresholds,
    PrivacyConfig,
    RetrievalHybridConfig,
)
from .services import orchestrator_stub
from .tracing import tracing_manager

# Optional mobile router (heavy optional deps: asyncpg, firebase_admin) placed AFTER all imports
try:  # pragma: no cover - optional dependency block
    from .mobile.router import mobile_router  # type: ignore
    _MOBILE_AVAILABLE = True
except Exception:  # noqa: BLE001
    mobile_router = None  # type: ignore
    _MOBILE_AVAILABLE = False

# Logger and optional instrumentation flags (defined after optional imports)
logger = logging.getLogger(__name__)

# Optional OTEL FastAPI instrumentation - fallback gracefully if not available
try:  # pragma: no cover - optional
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OTEL_FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - instrumentation optional
    FastAPIInstrumentor = None  # type: ignore
    OTEL_FASTAPI_AVAILABLE = False

ALLOWED_SECTIONS = {"router", "retrieval", "evals", "privacy", "compression"}

# Broad YAML data shape for config endpoints
YAMLData = dict[str, Any] | list[Any] | str | int | float | bool | None


def _safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise HTTPException(status_code=400, detail="invalid name")
    return name


def _load_yaml_file(section: str, name: str) -> YAMLData:
    root = Path(__file__).resolve().parents[4]
    cfg_path = root / "configs" / section / f"{name}.yaml"
    if not cfg_path.is_file():
        raise HTTPException(status_code=404, detail="config not found")
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"yaml parse error: {e}") from e
    return data


def _validate_retrieval_config(data: Any) -> dict[str, Any]:
    try:
        validated = RetrievalHybridConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    payload = cast(dict[str, Any], validated.model_dump())
    payload["dense"] = {"model": validated.pipelines.dense_config}
    payload["sparse"] = {"model": validated.pipelines.sparse_config}
    payload["reranker"] = {"model": validated.pipelines.reranker_config}
    return payload


def _validate_compression_config(data: Any) -> dict[str, Any]:
    try:
        validated = CompressionConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    result = cast(dict[str, Any], validated.model_dump())
    return result


def _validate_privacy_config(data: Any) -> dict[str, Any]:
    try:
        validated = PrivacyConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    payload = cast(dict[str, Any], validated.model_dump())
    payload["patterns"] = {rule.name: rule.pattern for rule in validated.rules}
    payload["policy"] = {
        "redact_pii": True,
        "replacement": {rule.name: rule.replacement for rule in validated.rules},
    }
    return payload


def _validate_evals_thresholds(data: Any) -> dict[str, Any]:
    try:
        validated = EvalsThresholds.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    result = cast(dict[str, Any], validated.model_dump())
    return result


VALIDATORS: dict[str, Callable[[Any], dict[str, Any]]] = {
    "retrieval": _validate_retrieval_config,
    "compression": _validate_compression_config,
    "privacy": _validate_privacy_config,
    "evals": _validate_evals_thresholds,
}


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace ID headers and OTEL spans."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())

        # Get the current span from OTEL
        current_span = trace.get_current_span()
        if current_span:
            # Set trace ID as span attribute
            current_span.set_attribute("http.request.trace_id", trace_id)
            current_span.set_attribute("http.method", request.method)
            current_span.set_attribute("http.url", str(request.url))

        # Process the request
        response = await call_next(request)

        # Add trace ID to response headers
        response.headers["X-Trace-Id"] = trace_id

        # Add span attributes for response
        if current_span:
            current_span.set_attribute("http.status_code", response.status_code)

        return response


def create_app() -> FastAPI:
    app = FastAPI(title="StratMaster API", version="0.2.0")

    # Add tracing middleware
    app.add_middleware(TracingMiddleware)

    # Initialize OTEL instrumentation for FastAPI if available
    if OTEL_FASTAPI_AVAILABLE:
        FastAPIInstrumentor.instrument_app(app)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    register_debug_config_endpoint(app)
    register_model_schema_endpoints(app)

    app.include_router(ingestion_router.router)
    app.include_router(debate_hitl_router.router)
    app.include_router(export_router.export_router)
    app.include_router(performance_router.performance_router)
    app.include_router(ui_router.router)
    app.include_router(strategy_router.router)
    app.include_router(security_router.router)
<<<<<<< HEAD
=======
    if _MOBILE_AVAILABLE:
        app.include_router(mobile_router)  # Sprint 1: Consolidated mobile API
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))

    research_router = APIRouter(prefix="/research", tags=["research"])

    @research_router.post("/plan", response_model=ResearchPlanResponse)
    async def plan_research(
        payload: ResearchPlanRequest,
        _: str = Depends(require_idempotency_key),
    ) -> ResearchPlanResponse:
        with tracing_manager.trace_operation("research:plan", {
            "tenant_id": payload.tenant_id,
            "query": payload.query[:100],  # Truncate for tracing
            "max_sources": payload.max_sources
        }):
            result = orchestrator_stub.plan_research(
                query=payload.query,
                tenant_id=payload.tenant_id,
                max_sources=payload.max_sources,
            )
            return ResearchPlanResponse(**result)

    @research_router.post("/run", response_model=ResearchRunResponse)
    async def run_research(
        payload: ResearchRunRequest,
        _: str = Depends(require_idempotency_key),
    ) -> ResearchRunResponse:
        with tracing_manager.trace_operation("research:run", {
            "tenant_id": payload.tenant_id,
            "plan_id": payload.plan_id
        }):
            result = orchestrator_stub.run_research(
                plan_id=payload.plan_id,
                tenant_id=payload.tenant_id,
            )
            return ResearchRunResponse(**result)

    app.include_router(research_router)

    graph_router = APIRouter(prefix="/graph", tags=["graph"])

    @graph_router.post("/summarise", response_model=GraphSummariseResponse)
    async def summarise_graph(
        payload: GraphSummariseRequest,
        _: str = Depends(require_idempotency_key),
    ) -> GraphSummariseResponse:
        result = orchestrator_stub.summarise_graph(
            _tenant_id=payload.tenant_id,
            focus=payload.focus,
            limit=payload.limit,
        )
        return GraphSummariseResponse(**result)

    app.include_router(graph_router)

    debate_router = APIRouter(prefix="/debate", tags=["debate"])

    @debate_router.post("/run", response_model=DebateRunResponse)
    async def run_debate(
        payload: DebateRunRequest,
        _: str = Depends(require_idempotency_key),
    ) -> DebateRunResponse:
        with tracing_manager.trace_operation("debate:start", {
            "tenant_id": payload.tenant_id,
            "hypothesis_id": payload.hypothesis_id,
            "claim_count": len(payload.claim_ids),
            "max_turns": payload.max_turns
        }):
            result = orchestrator_stub.run_debate(
                _tenant_id=payload.tenant_id,
                _hypothesis_id=payload.hypothesis_id,
                _claim_ids=payload.claim_ids,
                max_turns=payload.max_turns,
            )
            return DebateRunResponse(**result)

    app.include_router(debate_router)

    @app.post(
        "/recommendations",
        response_model=RecommendationOutcome,
        tags=["recommendations"],
    )
    async def generate_recommendation(
        payload: RecommendationRequest,
        _: str = Depends(require_idempotency_key),
    ) -> RecommendationOutcome:
        outcome = orchestrator_stub.generate_recommendation(
            tenant_id=payload.tenant_id,
            cep_id=payload.cep_id,
            jtbd_ids=payload.jtbd_ids,
            risk_tolerance=payload.risk_tolerance,
        )
        return outcome

    retrieval_router = APIRouter(prefix="/retrieval", tags=["retrieval"])

    @retrieval_router.post("/colbert/query", response_model=RetrievalQueryResponse)
    async def colbert_query(
        payload: RetrievalQueryRequest,
        _: str = Depends(require_idempotency_key),
    ) -> RetrievalQueryResponse:
        records = orchestrator_stub.query_retrieval(
            tenant_id=payload.tenant_id,
            query=payload.query,
            top_k=payload.top_k,
        )
        return RetrievalQueryResponse(records=records)

    @retrieval_router.post("/splade/query", response_model=RetrievalQueryResponse)
    async def splade_query(
        payload: RetrievalQueryRequest,
        _: str = Depends(require_idempotency_key),
    ) -> RetrievalQueryResponse:
        records = orchestrator_stub.query_retrieval(
            tenant_id=payload.tenant_id,
            query=payload.query,
            top_k=payload.top_k,
        )
        return RetrievalQueryResponse(records=records)

    app.include_router(retrieval_router)

    experiments_router = APIRouter(prefix="/experiments", tags=["experiments"])

    @experiments_router.post("", response_model=ExperimentCreateResponse)
    async def create_experiment(
        payload: ExperimentCreateRequest,
        _: str = Depends(require_idempotency_key),
    ) -> ExperimentCreateResponse:
        result = orchestrator_stub.create_experiment(
            tenant_id=payload.tenant_id,
            payload=payload.model_dump(),
        )
        return ExperimentCreateResponse(**result)

    app.include_router(experiments_router)

    forecasts_router = APIRouter(prefix="/forecasts", tags=["forecasts"])

    @forecasts_router.post("", response_model=ForecastCreateResponse)
    async def create_forecast(
        payload: ForecastCreateRequest,
        _: str = Depends(require_idempotency_key),
    ) -> ForecastCreateResponse:
        result = orchestrator_stub.create_forecast(
            tenant_id=payload.tenant_id,
            payload=payload.model_dump(),
        )
        return ForecastCreateResponse(**result)

    app.include_router(forecasts_router)

    evals_router = APIRouter(prefix="/evals", tags=["evals"])

    @evals_router.post("/run", response_model=EvalRunResponse)
    async def run_eval(
        payload: EvalRunRequest,
        _: str = Depends(require_idempotency_key),
    ) -> EvalRunResponse:
        result = orchestrator_stub.run_eval(
            tenant_id=payload.tenant_id,
            suite=payload.suite,
        )
        return EvalRunResponse(**result)

    app.include_router(evals_router)

    # Include experts router
    from .routers.experts import router as experts_router
    app.include_router(experts_router)

    # Include analytics router
    from .routers.analytics import router as analytics_router
    app.include_router(analytics_router)

    # Include industry templates router
    from .routers.templates import router as templates_router
    app.include_router(templates_router)

    # Include verification router
    from .routers.verification import router as verification_router
    app.include_router(verification_router)

<<<<<<< HEAD
    # Always register collaboration status endpoint; websocket route only when enabled
    try:
        from .routers.collaboration import setup_collaboration_websocket
        setup_collaboration_websocket(app)
    except Exception:
        logger.warning(
            "Collaboration routes setup failed; status may be unavailable",
            exc_info=True,
        )
=======
    # Add collaboration WebSocket endpoint if enabled
    from .collaboration import is_collaboration_enabled
    if is_collaboration_enabled():
        try:
            from .routers.collaboration import setup_collaboration_websocket
            setup_collaboration_websocket(app)
        except ImportError:
            logger.warning("Collaboration router not available. Collaboration features disabled.")
>>>>>>> 1cd0540 (chore: sync local changes (issue suite tooling, CI workflows, API flags))

    return app


def register_debug_config_endpoint(app: FastAPI) -> None:
    @app.get("/debug/config/{section}/{name:path}")
    async def get_config(section: str, name: str) -> dict[str, Any]:
        if os.getenv("STRATMASTER_ENABLE_DEBUG_ENDPOINTS") != "1":
            raise HTTPException(status_code=404, detail="not found")
        if section not in ALLOWED_SECTIONS:
            raise HTTPException(status_code=400, detail="invalid section")
        safe = _safe_name(name)
        data = _load_yaml_file(section, safe)

        validator = VALIDATORS.get(section)
        if validator is not None:
            cfg = validator(data)
        else:
            cfg = cast(
                dict[str, Any],
                dict(data) if isinstance(data, dict) else {"value": data},
            )
        return {"section": section, "name": safe, "config": cfg}


def _model_schemas_dir() -> Path:
    root = Path(__file__).resolve().parents[4]
    return root / "packages" / "api" / "schemas"


def _schema_name_from_stem(stem: str) -> str:
    suffix = f"-{SCHEMA_VERSION}"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def _load_model_schemas() -> dict[str, Any]:
    schemas_path = _model_schemas_dir()
    if not schemas_path.exists() or not schemas_path.is_dir():
        raise HTTPException(
            status_code=500, detail=f"Schemas directory not found: {schemas_path}"
        )
    schemas: dict[str, Any] = {}
    for json_file in sorted(schemas_path.glob("*.json")):
        # Skip hidden files or macOS resource fork files
        if json_file.name.startswith("._") or json_file.name.startswith("."):
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (JSONDecodeError, OSError) as e:  # pragma: no cover
            raise HTTPException(
                status_code=500, detail=f"Failed to parse {json_file.name}: {e}"
            ) from e
        name = _schema_name_from_stem(json_file.stem)
        schemas[name] = data
    if not schemas:
        raise HTTPException(status_code=500, detail="No model schemas found")
    return schemas


def register_model_schema_endpoints(app: FastAPI) -> None:
    @app.get("/schemas/models")
    async def list_model_schemas() -> dict[str, Any]:
        schemas = _load_model_schemas()
        return {"version": SCHEMA_VERSION, "schemas": schemas, "count": len(schemas)}

    @app.get("/schemas/models/{name}")
    async def get_model_schema(name: str) -> dict[str, Any]:
        safe = _safe_name(name)
        schemas = _load_model_schemas()
        schema = schemas.get(safe)
        if schema is None:
            raise HTTPException(status_code=404, detail=f"Schema not found: {safe}")
        if not isinstance(schema, dict):
            raise HTTPException(status_code=500, detail="invalid schema shape")
        return cast(dict[str, Any], schema)
