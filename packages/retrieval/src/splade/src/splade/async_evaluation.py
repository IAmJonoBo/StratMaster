"""Async retrieval evaluation task runner.

Provides background task execution for retrieval benchmarking without 
heavy dependencies like Celery. Uses asyncio for task management.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from .beir_integration import BEIREnhancedEvaluator

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EvalTask:
    """Evaluation task definition."""
    task_id: str
    task_type: str
    dataset_name: str
    parameters: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    progress: float = 0.0


class AsyncEvalTaskRunner:
    """Async task runner for retrieval evaluations."""
    
    def __init__(self, max_concurrent_tasks: int = 2):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: dict[str, EvalTask] = {}
        self.running_tasks: dict[str, asyncio.Task] = {}
        self.task_queue = asyncio.Queue()
        self.evaluator = BEIREnhancedEvaluator()
        self._runner_task: asyncio.Task | None = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start the task runner."""
        if self._is_running:
            return
        
        self._is_running = True
        self._runner_task = asyncio.create_task(self._task_runner_loop())
        logger.info("✅ Async eval task runner started")
    
    async def stop(self) -> None:
        """Stop the task runner."""
        self._is_running = False
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled task: {task_id}")
        
        # Cancel runner task
        if self._runner_task and not self._runner_task.done():
            self._runner_task.cancel()
        
        logger.info("Async eval task runner stopped")
    
    async def submit_beir_benchmark(
        self,
        dataset_name: str,
        retrieval_function: Callable,
        limit_queries: int = 50,
        k: int = 10,
        task_id: str | None = None
    ) -> str:
        """Submit BEIR benchmark evaluation task."""
        if task_id is None:
            task_id = f"beir_{dataset_name}_{uuid4().hex[:8]}"
        
        task = EvalTask(
            task_id=task_id,
            task_type="beir_benchmark",
            dataset_name=dataset_name,
            parameters={
                "limit_queries": limit_queries,
                "k": k,
                "retrieval_function_name": getattr(retrieval_function, "__name__", "unknown")
            },
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put((task_id, retrieval_function))
        
        logger.info(f"Submitted BEIR benchmark task: {task_id}")
        return task_id
    
    async def submit_quality_gate_validation(
        self,
        dataset_name: str,
        retrieval_function: Callable,
        quality_gates: dict[str, float] | None = None,
        task_id: str | None = None
    ) -> str:
        """Submit quality gate validation task."""
        if task_id is None:
            task_id = f"quality_gates_{dataset_name}_{uuid4().hex[:8]}"
        
        task = EvalTask(
            task_id=task_id,
            task_type="quality_gates",
            dataset_name=dataset_name,
            parameters={
                "quality_gates": quality_gates or {},
                "retrieval_function_name": getattr(retrieval_function, "__name__", "unknown")
            },
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put((task_id, retrieval_function))
        
        logger.info(f"Submitted quality gate validation task: {task_id}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "dataset_name": task.dataset_name,
            "status": task.status.value,
            "progress": task.progress,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error,
            "has_result": task.result is not None
        }
    
    async def get_task_result(self, task_id: str) -> dict[str, Any] | None:
        """Get result of a completed task."""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            return None
        
        return task.result
    
    async def list_tasks(self, status_filter: str | None = None) -> list[dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        
        for task in self.tasks.values():
            if status_filter is None or task.status.value == status_filter:
                task_info = await self.get_task_status(task.task_id)
                if task_info:
                    tasks.append(task_info)
        
        return sorted(tasks, key=lambda x: x["created_at"] or "", reverse=True)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    async def _task_runner_loop(self) -> None:
        """Main task runner loop."""
        logger.info("Task runner loop started")
        
        while self._is_running:
            try:
                # Wait for tasks or timeout
                try:
                    task_id, retrieval_function = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if we have capacity
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # Re-queue the task
                    await self.task_queue.put((task_id, retrieval_function))
                    await asyncio.sleep(0.1)
                    continue
                
                # Start task execution
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                execution_task = asyncio.create_task(
                    self._execute_task(task, retrieval_function)
                )
                self.running_tasks[task_id] = execution_task
                
                logger.info(f"Started task execution: {task_id}")
                
            except Exception as e:
                logger.error(f"Error in task runner loop: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Task runner loop stopped")
    
    async def _execute_task(self, task: EvalTask, retrieval_function: Callable) -> None:
        """Execute a single task."""
        try:
            task.progress = 0.1
            
            if task.task_type == "beir_benchmark":
                result = await self.evaluator.run_beir_benchmark(
                    dataset_name=task.dataset_name,
                    retrieval_function=retrieval_function,
                    limit_queries=task.parameters["limit_queries"],
                    k=task.parameters["k"]
                )
                
            elif task.task_type == "quality_gates":
                result = await self.evaluator.validate_retrieval_quality_gates(
                    dataset_name=task.dataset_name,
                    retrieval_function=retrieval_function,
                    quality_gates=task.parameters.get("quality_gates")
                )
                
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            task.progress = 1.0
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            duration = (task.completed_at - task.started_at).total_seconds()
            logger.info(
                f"✅ Task completed: {task.task_id} in {duration:.1f}s "
                f"({task.task_type} on {task.dataset_name})"
            )
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"Task cancelled: {task.task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"❌ Task failed: {task.task_id}: {e}")
            
        finally:
            # Remove from running tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    def get_runner_status(self) -> dict[str, Any]:
        """Get status of the task runner."""
        return {
            "is_running": self._is_running,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queued_tasks": self.task_queue.qsize(),
            "running_tasks": len(self.running_tasks),
            "total_tasks": len(self.tasks),
            "running_task_ids": list(self.running_tasks.keys())
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed tasks."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        
        return len(tasks_to_remove)


# Global task runner instance
_task_runner: AsyncEvalTaskRunner | None = None


def get_task_runner() -> AsyncEvalTaskRunner:
    """Get global task runner instance."""
    global _task_runner
    if _task_runner is None:
        _task_runner = AsyncEvalTaskRunner()
    return _task_runner


async def initialize_task_runner() -> None:
    """Initialize and start the global task runner."""
    runner = get_task_runner()
    await runner.start()


async def shutdown_task_runner() -> None:
    """Shutdown the global task runner."""
    global _task_runner
    if _task_runner:
        await _task_runner.stop()
        _task_runner = None