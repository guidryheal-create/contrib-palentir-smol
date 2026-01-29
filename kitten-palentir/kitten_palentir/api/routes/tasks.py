"""Palentir OSINT - Tasks API Routes.

Provides REST API endpoints for task management.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from kitten_palentir.api.models.schemas import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    ExecutionMode,
    ErrorResponse,
)
from kitten_palentir.agents.task_orchestrator_agent import (
    TaskOrchestratorAgent,
    ExecutionMode as OrchestratorExecutionMode,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# Global orchestrator instance (would be injected via dependency injection in production)
_orchestrator: Optional[TaskOrchestratorAgent] = None


def set_orchestrator(orch: TaskOrchestratorAgent):
    """Set the orchestrator instance.

    Args:
        orch: Task Orchestrator Agent instance
    """
    global _orchestrator
    _orchestrator = orch
    logger.info("Orchestrator instance set for tasks router")


def get_orchestrator() -> TaskOrchestratorAgent:
    """Get the orchestrator instance.

    Returns:
        Task Orchestrator Agent instance

    Raises:
        HTTPException: If orchestrator is not initialized
    """
    if _orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Task orchestrator not initialized. Please wait for service to be ready.",
        )
    return _orchestrator


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(request: TaskRequest) -> TaskResponse:
    """Create and execute a new task.

    Args:
        request: Task creation request

    Returns:
        Created task response
    """
    try:
        orchestrator = get_orchestrator()

        # Convert execution mode
        exec_mode_map = {
            ExecutionMode.SEQUENTIAL: OrchestratorExecutionMode.SEQUENTIAL,
            ExecutionMode.PARALLEL: OrchestratorExecutionMode.PARALLEL,
            ExecutionMode.FORK_JOIN: OrchestratorExecutionMode.FORK_JOIN,
        }
        exec_mode = exec_mode_map[request.execution_mode]

        logger.info(f"Creating task: {request.query[:50]}...")

        # Process query
        results = await orchestrator.process_user_query(
            query=request.query,
            execution_mode=exec_mode,
        )

        if not results:
            raise HTTPException(status_code=500, detail="No results returned from orchestrator")

        # Use first result as primary task
        result = results[0]

        return TaskResponse(
            task_id=result.task_id,
            query=request.query,
            status=TaskStatus(result.status.value),
            execution_mode=request.execution_mode,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            created_at=datetime.fromisoformat(result.timestamp.replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(result.timestamp.replace("Z", "+00:00")),
            metadata=request.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of tasks to return", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
) -> List[TaskResponse]:
    """List tasks with optional filtering.

    Args:
        status: Optional status filter
        limit: Maximum number of tasks to return
        offset: Offset for pagination

    Returns:
        List of tasks
    """
    try:
        orchestrator = get_orchestrator()

        # Get tasks based on status
        if status == TaskStatus.COMPLETED:
            tasks = orchestrator.get_completed_tasks()
        elif status == TaskStatus.FAILED:
            tasks = orchestrator.get_failed_tasks()
        elif status == TaskStatus.EXECUTING:
            tasks = orchestrator.get_executing_tasks()
        elif status == TaskStatus.QUEUED:
            tasks = orchestrator.get_queued_tasks()
        else:
            # Get all tasks
            all_tasks = (
                orchestrator.get_completed_tasks()
                + orchestrator.get_failed_tasks()
                + orchestrator.get_executing_tasks()
                + orchestrator.get_queued_tasks()
            )
            tasks = all_tasks

        # Apply pagination
        paginated_tasks = tasks[offset : offset + limit]

        # Convert to response models
        response_tasks = []
        for task in paginated_tasks:
            if hasattr(task, "task_id"):
                response_tasks.append(
                    TaskResponse(
                        task_id=task.task_id,
                        query=getattr(task, "query", "Unknown"),
                        status=TaskStatus(task.status.value) if hasattr(task.status, "value") else TaskStatus.COMPLETED,
                        execution_mode=ExecutionMode.FORK_JOIN,  # Default
                        result=task.result,
                        error=task.error,
                        execution_time=task.execution_time,
                        created_at=datetime.fromisoformat(task.timestamp.replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(task.timestamp.replace("Z", "+00:00")),
                    )
                )
            else:
                # Handle dict-like tasks
                response_tasks.append(
                    TaskResponse(
                        task_id=task.get("task_id", "unknown"),
                        query=task.get("query", "Unknown"),
                        status=TaskStatus(task.get("status", "completed")),
                        execution_mode=ExecutionMode.FORK_JOIN,
                        result=task.get("result"),
                        error=task.get("error"),
                        execution_time=task.get("execution_time", 0.0),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )

        return response_tasks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str = Path(..., description="Task ID")) -> TaskResponse:
    """Get a specific task by ID.

    Args:
        task_id: Task identifier

    Returns:
        Task response
    """
    try:
        orchestrator = get_orchestrator()

        # Search in all task lists
        all_tasks = (
            orchestrator.get_completed_tasks()
            + orchestrator.get_failed_tasks()
            + orchestrator.get_executing_tasks()
            + orchestrator.get_queued_tasks()
        )

        task = next((t for t in all_tasks if (hasattr(t, "task_id") and t.task_id == task_id) or (isinstance(t, dict) and t.get("task_id") == task_id)), None)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Convert to response model
        if hasattr(task, "task_id"):
            return TaskResponse(
                task_id=task.task_id,
                query=getattr(task, "query", "Unknown"),
                status=TaskStatus(task.status.value) if hasattr(task.status, "value") else TaskStatus.COMPLETED,
                execution_mode=ExecutionMode.FORK_JOIN,
                result=task.result,
                error=task.error,
                execution_time=task.execution_time,
                created_at=datetime.fromisoformat(task.timestamp.replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(task.timestamp.replace("Z", "+00:00")),
            )
        else:
            return TaskResponse(
                task_id=task.get("task_id", task_id),
                query=task.get("query", "Unknown"),
                status=TaskStatus(task.get("status", "completed")),
                execution_mode=ExecutionMode.FORK_JOIN,
                result=task.get("result"),
                error=task.get("error"),
                execution_time=task.get("execution_time", 0.0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.delete("/{task_id}", status_code=204)
async def cancel_task(task_id: str = Path(..., description="Task ID")) -> None:
    """Cancel a specific task.

    Args:
        task_id: Task identifier
    """
    try:
        orchestrator = get_orchestrator()

        logger.info(f"Cancelling task: {task_id}")

        cancelled = await orchestrator.cancel_task(task_id)

        if not cancelled:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.delete("", status_code=204)
async def cancel_all_tasks() -> None:
    """Cancel all tasks."""
    try:
        orchestrator = get_orchestrator()

        logger.info("Cancelling all tasks")

        await orchestrator.cancel_all_tasks()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel all tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel all tasks: {str(e)}")


@router.get("/status/summary")
async def get_task_summary() -> dict:
    """Get task execution summary.

    Returns:
        Task summary statistics
    """
    try:
        orchestrator = get_orchestrator()

        summary = orchestrator.get_summary()

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task summary: {str(e)}")

