"""Palentir OSINT - Task Orchestration API Routes.

Provides REST API endpoints for task orchestration.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from kitten_palentir.agents.task_orchestrator_agent import (
    TaskOrchestratorAgent,
    ExecutionMode,
    TaskExecutionStatus,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orchestration", tags=["orchestration"])

# Global orchestrator instance (would be injected in real app)
orchestrator: TaskOrchestratorAgent = None


class QueryRequest(BaseModel):
    """User query request."""

    query: str = Field(..., description="User query")
    execution_mode: str = Field(
        default="fork_join",
        description="Execution mode: sequential, parallel, or fork_join",
    )


class TaskStatusResponse(BaseModel):
    """Task status response."""

    queued_tasks: int
    executing_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: Optional[int] = None
    
    def __init__(self, **data):
        """Initialize with computed total_tasks if not provided."""
        if 'total_tasks' not in data:
            data['total_tasks'] = (
                data.get('queued_tasks', 0) +
                data.get('executing_tasks', 0) +
                data.get('completed_tasks', 0) +
                data.get('failed_tasks', 0)
            )
        super().__init__(**data)


class TaskResultResponse(BaseModel):
    """Task result response."""

    task_id: str
    status: str
    result: Dict[str, Any]
    error: str = None
    execution_time: float
    timestamp: str


@router.post("/query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """Process user query and execute tasks.

    Args:
        request: Query request

    Returns:
        Execution results
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    try:
        logger.info(f"Processing query: {request.query}")

        # Convert execution mode
        try:
            exec_mode = ExecutionMode(request.execution_mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution mode: {request.execution_mode}",
            )

        # Process query
        results = await orchestrator.process_user_query(
            query=request.query,
            execution_mode=exec_mode,
        )

        # Convert results to response
        response_results = [
            TaskResultResponse(
                task_id=result.task_id,
                status=result.status.value,
                result=result.result,
                error=result.error,
                execution_time=result.execution_time,
                timestamp=result.timestamp,
            ).dict()
            for result in results
        ]

        return {
            "query": request.query,
            "execution_mode": request.execution_mode,
            "results_count": len(response_results),
            "results": response_results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status() -> TaskStatusResponse:
    """Get orchestrator status.

    Returns:
        Status information
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    status = orchestrator.get_status()

    return TaskStatusResponse(**status)


@router.get("/tasks/completed")
async def get_completed_tasks() -> List[TaskResultResponse]:
    """Get completed tasks.

    Returns:
        List of completed tasks
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    tasks = orchestrator.get_completed_tasks()

    return [
        TaskResultResponse(
            task_id=task.task_id,
            status=task.status.value,
            result=task.result,
            error=task.error,
            execution_time=task.execution_time,
            timestamp=task.timestamp,
        ).dict()
        for task in tasks
    ]


@router.get("/tasks/failed")
async def get_failed_tasks() -> List[TaskResultResponse]:
    """Get failed tasks.

    Returns:
        List of failed tasks
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    tasks = orchestrator.get_failed_tasks()

    return [
        TaskResultResponse(
            task_id=task.task_id,
            status=task.status.value,
            result=task.result,
            error=task.error,
            execution_time=task.execution_time,
            timestamp=task.timestamp,
        ).dict()
        for task in tasks
    ]


@router.get("/tasks/executing")
async def get_executing_tasks() -> List[Dict[str, Any]]:
    """Get executing tasks.

    Returns:
        List of executing tasks
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    return orchestrator.get_executing_tasks()


@router.get("/tasks/queued")
async def get_queued_tasks() -> List[Dict[str, Any]]:
    """Get queued tasks.

    Returns:
        List of queued tasks
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    return orchestrator.get_queued_tasks()


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a task.

    Args:
        task_id: Task ID

    Returns:
        Cancellation result
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    try:
        logger.info(f"Cancelling task: {task_id}")

        cancelled = await orchestrator.cancel_task(task_id)

        return {
            "task_id": task_id,
            "cancelled": cancelled,
        }

    except Exception as e:
        logger.error(f"Task cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks")
async def cancel_all_tasks() -> Dict[str, Any]:
    """Cancel all tasks.

    Returns:
        Cancellation result
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    try:
        logger.info("Cancelling all tasks")

        await orchestrator.cancel_all_tasks()

        return {
            "message": "All tasks cancelled",
        }

    except Exception as e:
        logger.error(f"Task cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """Get orchestrator summary.

    Returns:
        Summary information
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    return orchestrator.get_summary()


def set_orchestrator(orch: TaskOrchestratorAgent):
    """Set the orchestrator instance.

    Args:
        orch: Task Orchestrator Agent
    """
    global orchestrator
    orchestrator = orch
    logger.info("Orchestrator instance set")
