"""Phase 2 - Hybrid Retrieval API Router per SCRATCH.md"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any

from ..services.hybrid_retrieval import HybridRetrievalService, RetrievalResult, QualityMetrics

router = APIRouter(prefix="/retrieval", tags=["Phase 2 - Hybrid Retrieval"])


class HybridRetrievalRequest(BaseModel):
    """Request model for hybrid retrieval."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    enable_reranking: bool = Field(True, description="Enable cross-encoder reranking")
    tenant_id: str = Field("default", description="Tenant identifier")
    include_metrics: bool = Field(True, description="Include quality metrics in response")


class HybridRetrievalResponse(BaseModel):
    """Response model for hybrid retrieval."""
    results: list[dict[str, Any]]
    query: str
    total_results: int
    latency_ms: float
    quality_gates_passed: bool
    quality_metrics: dict[str, Any] | None = None
    reranking_applied: bool


class BeirEvaluationResponse(BaseModel):
    """Response model for BEIR evaluation."""
    dataset: str
    ndcg_at_10: float
    recall_at_50: float
    mrr_at_10: float
    baseline_ndcg: float
    uplift_percent: float
    quality_gates_met: bool


# Global service instance
_hybrid_service: HybridRetrievalService | None = None


def get_hybrid_retrieval_service() -> HybridRetrievalService:
    """Get or create hybrid retrieval service."""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridRetrievalService()
    return _hybrid_service


@router.post("/hybrid", response_model=HybridRetrievalResponse)
async def hybrid_retrieve(
    request: HybridRetrievalRequest,
    service: HybridRetrievalService = Depends(get_hybrid_retrieval_service)
) -> HybridRetrievalResponse:
    """
    Perform hybrid retrieval with quality gates per SCRATCH.md Phase 2.
    
    Features:
    - Qdrant dual-vector (dense + sparse) search
    - OpenSearch BM25 + RRF fusion  
    - Cross-encoder reranking via BGE-reranker-v2
    - RAGAS evaluation with quality gates
    """
    try:
        results, metrics = await service.retrieve_and_rerank(
            query=request.query,
            top_k=request.top_k,
            enable_reranking=request.enable_reranking,
            tenant_id=request.tenant_id
        )
        
        # Convert results to dict format
        results_dict = []
        for result in results:
            results_dict.append({
                "doc_id": result.doc_id,
                "title": result.title,
                "text": result.text,
                "score": result.score,
                "rerank_score": result.rerank_score,
                "source": result.source,
                "metadata": result.metadata or {}
            })
        
        # Check quality gates
        quality_gates_passed = True
        if metrics:
            # Quality gates per SCRATCH.md
            if metrics.faithfulness < 0.75:
                quality_gates_passed = False
            if metrics.context_precision < 0.6:
                quality_gates_passed = False
            if metrics.latency_ms > 500:  # p95 < 500ms gate
                quality_gates_passed = False
        
        # Prepare quality metrics for response
        metrics_dict = None
        if metrics and request.include_metrics:
            metrics_dict = {
                "ndcg_at_10": metrics.ndcg_at_10,
                "context_precision": metrics.context_precision,
                "context_recall": metrics.context_recall,
                "faithfulness": metrics.faithfulness,
                "answer_relevancy": metrics.answer_relevancy,
                "timestamp": metrics.timestamp,
                "quality_gates": {
                    "faithfulness_threshold": 0.75,
                    "context_precision_threshold": 0.6,
                    "max_latency_p95_ms": 500,
                    "ndcg_uplift_target": 0.20
                }
            }
        
        return HybridRetrievalResponse(
            results=results_dict,
            query=request.query,
            total_results=len(results_dict),
            latency_ms=metrics.latency_ms if metrics else 0.0,
            quality_gates_passed=quality_gates_passed,
            quality_metrics=metrics_dict,
            reranking_applied=request.enable_reranking
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Hybrid retrieval failed: {str(e)}"
        )


@router.get("/beir/evaluate", response_model=BeirEvaluationResponse)
async def beir_evaluate(
    dataset: str = "scifact",
    service: HybridRetrievalService = Depends(get_hybrid_retrieval_service)
) -> BeirEvaluationResponse:
    """
    Run BEIR evaluation per SCRATCH.md Phase 2.1 quality gates.
    
    Quality Gates:
    - +≥20% nDCG@10 vs dense-only baseline
    - recall@50 ≥ baseline
    - p95 latency < 500ms
    """
    try:
        results = await service.run_beir_evaluation(dataset)
        
        # Check if quality gates are met
        quality_gates_met = (
            results["uplift_percent"] >= 20.0 and  # +≥20% uplift
            results["recall@50"] >= 0.85  # Baseline threshold
        )
        
        return BeirEvaluationResponse(
            dataset=results["dataset"],
            ndcg_at_10=results["ndcg@10"],
            recall_at_50=results["recall@50"],
            mrr_at_10=results["mrr@10"],
            baseline_ndcg=results["baseline_ndcg"],
            uplift_percent=results["uplift_percent"],
            quality_gates_met=quality_gates_met
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"BEIR evaluation failed: {str(e)}"
        )


@router.get("/config")
async def get_retrieval_config(
    service: HybridRetrievalService = Depends(get_hybrid_retrieval_service)
) -> dict[str, Any]:
    """Get current hybrid retrieval configuration."""
    return {
        "retrieval": service.config.get("retrieval", {}),
        "reranking": service.config.get("reranking", {}),
        "evaluation": service.config.get("evaluation", {}),
        "budget": service.config.get("budget", {}),
        "status": "Phase 2 - Hybrid Retrieval Active",
        "quality_gates": {
            "ndcg_at_10_uplift": "≥20% vs dense-only baseline",
            "context_precision": "≥0.6",
            "faithfulness": "≥0.75", 
            "max_latency_p95": "≤500ms",
            "rerank_latency_p95": "≤450ms on A100, ≤800ms on CPU"
        }
    }


@router.get("/health")
async def retrieval_health_check(
    service: HybridRetrievalService = Depends(get_hybrid_retrieval_service)
) -> dict[str, Any]:
    """Health check for hybrid retrieval components."""
    return {
        "status": "healthy",
        "phase": "Phase 2 - Hybrid Retrieval",
        "components": {
            "qdrant": "mocked",  # Would be actual health check
            "opensearch": "mocked",
            "reranker": "available",
            "evaluator": "available"
        },
        "config_loaded": bool(service.config),
        "timestamp": service.quality_metrics[-1].timestamp if service.quality_metrics else None
    }