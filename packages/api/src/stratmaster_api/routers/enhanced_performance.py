"""Enhanced performance router with BEIR benchmarking integration.

Provides endpoints for retrieval benchmarking using BEIR datasets,
async task management, and quality gate validation.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import retrieval benchmarking components
try:
    from splade.beir_integration import BEIREnhancedEvaluator, BEIRDatasetManager
    from splade.async_evaluation import AsyncEvalTaskRunner, get_task_runner, initialize_task_runner
    RETRIEVAL_BENCHMARKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Retrieval benchmarking not available: {e}")
    BEIREnhancedEvaluator = None
    BEIRDatasetManager = None
    AsyncEvalTaskRunner = None
    get_task_runner = None
    initialize_task_runner = None
    RETRIEVAL_BENCHMARKING_AVAILABLE = False


class BenchmarkRequest(BaseModel):
    """Request for benchmark evaluation."""
    dataset_name: str
    limit_queries: int = 50
    k: int = 10
    async_execution: bool = True


class QualityGateRequest(BaseModel):
    """Request for quality gate validation."""
    dataset_name: str
    quality_gates: dict[str, float] | None = None
    async_execution: bool = True


class TaskResponse(BaseModel):
    """Response for task submission."""
    task_id: str
    status: str
    message: str


# Create enhanced performance router
router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/retrieval/status")
async def get_retrieval_benchmarking_status() -> dict[str, Any]:
    """Get status of retrieval benchmarking system."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE:
        return {
            "available": False,
            "message": "Retrieval benchmarking components not available",
            "required_packages": ["splade", "pandas", "aiosqlite"]
        }
    
    dataset_manager = BEIRDatasetManager()
    datasets = dataset_manager.list_available_datasets()
    
    # Get task runner status if available
    task_runner_status = {}
    if get_task_runner:
        runner = get_task_runner()
        task_runner_status = runner.get_runner_status()
    
    return {
        "available": True,
        "beir_datasets": datasets,
        "task_runner": task_runner_status,
        "feature_flag": "ENABLE_RETRIEVAL_BENCHMARKS"
    }


@router.get("/retrieval/datasets")
async def list_beir_datasets() -> dict[str, Any]:
    """List available BEIR datasets."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Retrieval benchmarking not available"
        )
    
    dataset_manager = BEIRDatasetManager()
    datasets = dataset_manager.list_available_datasets()
    
    return {
        "datasets": datasets,
        "total": len(datasets),
        "available_types": list(set(d["task_type"] for d in datasets))
    }


@router.get("/retrieval/datasets/{dataset_name}")
async def get_dataset_info(dataset_name: str) -> dict[str, Any]:
    """Get detailed information about a BEIR dataset."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Retrieval benchmarking not available"
        )
    
    dataset_manager = BEIRDatasetManager()
    dataset_info = dataset_manager.get_dataset_info(dataset_name)
    
    if "error" in dataset_info:
        raise HTTPException(status_code=404, detail=dataset_info["error"])
    
    return dataset_info


@router.post("/retrieval/benchmark", response_model=TaskResponse)
async def run_beir_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """Run BEIR benchmark evaluation."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Retrieval benchmarking not available"
        )
    
    # Create a mock retrieval function for demonstration
    async def mock_retrieval_function(query_text: str, k: int = 10) -> list[dict[str, Any]]:
        """Mock retrieval function - replace with actual retrieval system."""
        import asyncio
        import time
        
        # Simulate retrieval latency
        await asyncio.sleep(0.1)
        
        # Mock results with realistic document IDs and scores
        return [
            {
                "doc_id": f"doc_{query_text[:10].replace(' ', '_')}_{i}",
                "score": 0.9 - (i * 0.08),
                "rank": i + 1,
                "content": f"Mock document {i} for query: {query_text[:30]}..."
            }
            for i in range(min(k, 10))
        ]
    
    if request.async_execution:
        # Submit async task
        runner = get_task_runner()
        if not runner._is_running:
            await initialize_task_runner()
        
        task_id = await runner.submit_beir_benchmark(
            dataset_name=request.dataset_name,
            retrieval_function=mock_retrieval_function,
            limit_queries=request.limit_queries,
            k=request.k
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"BEIR benchmark task submitted for dataset: {request.dataset_name}"
        )
    
    else:
        # Run synchronously (not recommended for large evaluations)
        background_tasks.add_task(
            _run_sync_benchmark,
            request.dataset_name,
            mock_retrieval_function,
            request.limit_queries,
            request.k
        )
        
        return TaskResponse(
            task_id="sync_execution",
            status="running",
            message="Benchmark running synchronously in background"
        )


@router.post("/retrieval/quality-gates", response_model=TaskResponse)
async def validate_quality_gates(
    request: QualityGateRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """Validate retrieval system against quality gates."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Retrieval benchmarking not available"
        )
    
    # Mock retrieval function
    async def mock_retrieval_function(query_text: str, k: int = 10) -> list[dict[str, Any]]:
        import asyncio
        await asyncio.sleep(0.1)
        return [
            {"doc_id": f"doc_{i}", "score": 0.85 - (i * 0.05), "rank": i + 1}
            for i in range(min(k, 10))
        ]
    
    if request.async_execution:
        runner = get_task_runner()
        if not runner._is_running:
            await initialize_task_runner()
        
        task_id = await runner.submit_quality_gate_validation(
            dataset_name=request.dataset_name,
            retrieval_function=mock_retrieval_function,
            quality_gates=request.quality_gates
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Quality gate validation submitted for dataset: {request.dataset_name}"
        )
    
    else:
        background_tasks.add_task(
            _run_sync_quality_gates,
            request.dataset_name,
            mock_retrieval_function,
            request.quality_gates
        )
        
        return TaskResponse(
            task_id="sync_quality_gates",
            status="running",
            message="Quality gate validation running in background"
        )


@router.get("/retrieval/tasks")
async def list_evaluation_tasks(
    status: str | None = Query(None, description="Filter by task status")
) -> dict[str, Any]:
    """List evaluation tasks."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE or not get_task_runner:
        raise HTTPException(
            status_code=503,
            detail="Task management not available"
        )
    
    runner = get_task_runner()
    tasks = await runner.list_tasks(status_filter=status)
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "runner_status": runner.get_runner_status()
    }


@router.get("/retrieval/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get status of specific evaluation task."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE or not get_task_runner:
        raise HTTPException(
            status_code=503,
            detail="Task management not available"
        )
    
    runner = get_task_runner()
    status = await runner.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status


@router.get("/retrieval/tasks/{task_id}/result")
async def get_task_result(task_id: str) -> dict[str, Any]:
    """Get result of completed evaluation task."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE or not get_task_runner:
        raise HTTPException(
            status_code=503,
            detail="Task management not available"
        )
    
    runner = get_task_runner()
    result = await runner.get_task_result(task_id)
    
    if result is None:
        status = await runner.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        elif status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed. Current status: {status['status']}"
            )
        else:
            raise HTTPException(status_code=404, detail="Task result not available")
    
    return {"result": result, "task_id": task_id}


@router.delete("/retrieval/tasks/{task_id}")
async def cancel_task(task_id: str) -> dict[str, str]:
    """Cancel an evaluation task."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE or not get_task_runner:
        raise HTTPException(
            status_code=503,
            detail="Task management not available"
        )
    
    runner = get_task_runner()
    cancelled = await runner.cancel_task(task_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Task cannot be cancelled (not found or already completed)"
        )
    
    return {"message": f"Task {task_id} cancelled successfully"}


@router.post("/retrieval/tasks/cleanup")
async def cleanup_old_tasks(max_age_hours: int = 24) -> dict[str, Any]:
    """Clean up old completed tasks."""
    if not RETRIEVAL_BENCHMARKING_AVAILABLE or not get_task_runner:
        raise HTTPException(
            status_code=503,
            detail="Task management not available"
        )
    
    runner = get_task_runner()
    cleaned_count = await runner.cleanup_old_tasks(max_age_hours)
    
    return {
        "cleaned_tasks": cleaned_count,
        "max_age_hours": max_age_hours,
        "message": f"Cleaned up {cleaned_count} old tasks"
    }


# Background task functions
async def _run_sync_benchmark(
    dataset_name: str,
    retrieval_function: Any,
    limit_queries: int,
    k: int
) -> None:
    """Run benchmark synchronously in background."""
    try:
        evaluator = BEIREnhancedEvaluator()
        result = await evaluator.run_beir_benchmark(
            dataset_name=dataset_name,
            retrieval_function=retrieval_function,
            limit_queries=limit_queries,
            k=k
        )
        logger.info(f"Sync benchmark completed for {dataset_name}: {result.get('overall', {})}")
    except Exception as e:
        logger.error(f"Sync benchmark failed for {dataset_name}: {e}")


async def _run_sync_quality_gates(
    dataset_name: str,
    retrieval_function: Any,
    quality_gates: dict[str, float] | None
) -> None:
    """Run quality gate validation synchronously in background."""
    try:
        evaluator = BEIREnhancedEvaluator()
        result = await evaluator.validate_retrieval_quality_gates(
            dataset_name=dataset_name,
            retrieval_function=retrieval_function,
            quality_gates=quality_gates
        )
        logger.info(f"Sync quality gates completed for {dataset_name}: {result.get('quality_gates', {})}")
    except Exception as e:
        logger.error(f"Sync quality gates failed for {dataset_name}: {e}")