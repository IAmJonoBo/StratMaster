"""Performance and benchmarking router for StratMaster API."""

from typing import Any

from fastapi import APIRouter, HTTPException

performance_router = APIRouter(prefix="/performance", tags=["performance"])


@performance_router.post("/benchmark", response_model=dict[str, Any])
async def run_benchmark() -> dict[str, Any]:
    """Run comprehensive performance benchmark and quality gate validation.

    Executes all performance tests as specified in Upgrade.md:
    - Gateway latency tests (p50 < 5ms, p95 < 15ms)
    - Model routing performance (p50 < 20ms)
    - RAG evaluation (RAGAS metrics ≥ 0.7-0.8)
    - Retrieval improvement validation (≥10% NDCG@10)
    - Export functionality and idempotency
    - End-to-end integration workflows

    Returns:
        Dictionary containing benchmark results and quality gate status
    """
    try:
        from ..performance_benchmark import run_performance_benchmark  # deferred import
    except Exception as e:  # pragma: no cover - optional dependency path
        raise HTTPException(status_code=503, detail=f"Benchmarking unavailable: {e}") from e
    return await run_performance_benchmark()


@performance_router.get("/health")
async def performance_health():
    """Quick health check for performance monitoring."""
    return {"status": "ok", "component": "performance"}
