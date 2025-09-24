"""FastAPI service for RAGAS evaluation with Langfuse integration."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from opentelemetry import trace

from .evaluator import RAGASEvaluator
from .models import EvaluationRequest, EvaluationResult

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# FastAPI router for evaluation endpoints
eval_router = APIRouter(prefix="/eval", tags=["evaluation"])


class EvaluationService:
    """Service for managing RAGAS evaluations and quality gates."""
    
    def __init__(self):
        self.evaluator = RAGASEvaluator()
        
    async def get_evaluator(self) -> RAGASEvaluator:
        """Dependency to get evaluator instance."""
        return self.evaluator


# Service instance
eval_service = EvaluationService()


@eval_router.post("/ragas", response_model=EvaluationResult)
async def evaluate_with_ragas(
    request: EvaluationRequest,
    evaluator: RAGASEvaluator = Depends(eval_service.get_evaluator),
) -> EvaluationResult:
    """Evaluate retrieval quality using RAGAS metrics.
    
    Quality Gates from Scratch.md:
    - RAGAS faithfulness ≥ 0.8 on internal set
    - Context precision/recall ≥ 0.7
    - Automatic CI thresholds with rollback capability
    """
    with tracer.start_as_current_span("ragas_evaluation") as span:
        span.set_attribute("experiment_name", request.experiment_name)
        span.set_attribute("model_name", request.model_name) 
        span.set_attribute("sample_count", len(request.questions))
        
        try:
            result = await evaluator.evaluate_retrieval(request)
            
            # Add tracing attributes for observability
            span.set_attribute("passes_quality_gates", result.passes_quality_gates)
            span.set_attribute("quality_score", result.quality_score)
            span.set_attribute("faithfulness", result.metrics.faithfulness)
            span.set_attribute("context_precision", result.metrics.context_precision)
            span.set_attribute("context_recall", result.metrics.context_recall)
            
            if not result.passes_quality_gates:
                span.set_attribute("failures", ",".join(result.failures))
                logger.warning(f"Quality gates failed for {request.model_name}: {result.failures}")
            
            return result
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            logger.error(f"RAGAS evaluation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


@eval_router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for evaluation service."""
    return {
        "status": "healthy",
        "ragas_available": True,  # Would check actual availability
        "langfuse_available": True,  # Would check actual availability
        "quality_gates": {
            "faithfulness_threshold": 0.8,
            "precision_threshold": 0.7,
            "recall_threshold": 0.7,
        }
    }


@eval_router.get("/metrics/{model_name}")
async def get_model_metrics(model_name: str) -> dict[str, Any]:
    """Get recent evaluation metrics for a specific model."""
    # This would query Langfuse for recent experiments
    return {
        "model_name": model_name,
        "recent_evaluations": [],
        "avg_quality_score": 0.0,
        "quality_gate_pass_rate": 0.0,
        "last_evaluation": None,
        "mock": True,
    }


@eval_router.post("/cascade")
async def evaluate_cascade_routing(
    questions: list[str],
    cheap_responses: list[str],
    strong_responses: list[str] | None = None,
    ground_truths: list[str] | None = None,
    evaluator: RAGASEvaluator = Depends(eval_service.get_evaluator),
) -> dict[str, Any]:
    """Evaluate effectiveness of cascade routing (cheap → strong).
    
    Implements FrugalGPT/RouteLLM evaluation from Scratch.md.
    """
    with tracer.start_as_current_span("cascade_evaluation") as span:
        span.set_attribute("question_count", len(questions))
        span.set_attribute("has_strong_responses", strong_responses is not None)
        span.set_attribute("has_ground_truths", ground_truths is not None)
        
        try:
            result = await evaluator.evaluate_model_cascade(
                questions=questions,
                cheap_model_responses=cheap_responses,
                strong_model_responses=strong_responses,
                ground_truths=ground_truths,
            )
            
            # Add metrics to span
            span.set_attribute("cascade_efficiency", result.get("cascade_efficiency", 0.0))
            span.set_attribute("cost_savings", result.get("cost_savings", 0.0))
            span.set_attribute("escalation_rate", result.get("escalation_rate", 0.0))
            
            return result
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            logger.error(f"Cascade evaluation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Cascade evaluation failed: {e}")


# Export router for inclusion in main FastAPI app
__all__ = ["eval_router", "EvaluationService"]