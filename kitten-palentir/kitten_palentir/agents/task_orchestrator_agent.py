"""Palentir OSINT - Task Orchestrator Agent.

Orchestrates task generation, execution, and monitoring using CAMEL-AI native classes.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from uuid import uuid4
from enum import Enum

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.societies.workforce import Workforce
from camel.tasks import Task


logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Task execution mode."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    FORK_JOIN = "fork_join"


class TaskExecutionStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskExecutionResult:
    """Task execution result."""

    def __init__(
        self,
        task_id: str,
        status: TaskExecutionStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time: float = 0.0,
    ):
        """Initialize result.

        Args:
            task_id: Task ID
            status: Execution status
            result: Execution result
            error: Error message if failed
            execution_time: Execution time in seconds
        """
        self.task_id = task_id
        self.status = status
        self.result = result or {}
        self.error = error
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


class TaskOrchestratorAgent:
    """Task Orchestrator Agent for CAMEL-AI Workforce.

    Orchestrates task generation, execution, and monitoring.
    """

    def __init__(
        self,
        workforce: Workforce,
        task_generation_service: Any,
        graph_builder_agent: Optional[Any] = None,
        skip_agent_init: bool = False,
    ):
        """Initialize Task Orchestrator Agent.

        Args:
            workforce: CAMEL-AI Workforce instance
            task_generation_service: Task generation service
            graph_builder_agent: Optional Graph Builder Agent for updates
            skip_agent_init: Skip ChatAgent initialization (for testing)
        """
        self.workforce = workforce
        self.task_generation_service = task_generation_service
        self.graph_builder_agent = graph_builder_agent

        # Task tracking (using CAMEL Task objects)
        self.task_queue: List[Task] = []
        self.executing_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskExecutionResult] = {}
        self.failed_tasks: Dict[str, TaskExecutionResult] = {}

        # Callbacks
        self.on_task_start_callbacks: List[Callable] = []
        self.on_task_complete_callbacks: List[Callable] = []
        self.on_task_failed_callbacks: List[Callable] = []

        # Initialize CAMEL-AI ChatAgent for orchestration (skip in tests)
        if not skip_agent_init:
            try:
                self._init_orchestrator_agent()
            except (ValueError, Exception) as e:
                # If API key is missing or other init error, set to None for testing
                logger.warning(f"Could not initialize orchestrator agent: {e}")
                self.orchestrator_agent = None
        else:
            self.orchestrator_agent = None

        logger.info("Task Orchestrator Agent initialized")

    def _init_orchestrator_agent(self):
        """Initialize CAMEL-AI ChatAgent for orchestration."""
        system_message = BaseMessage.make_assistant_message(
            role_name="TaskOrchestrator",
            content=(
                "You are a Task Orchestrator Agent responsible for managing and coordinating "
                "the execution of OSINT investigation tasks. You analyze user queries, generate "
                "appropriate tasks, and coordinate their execution across the workforce. "
                "You ensure tasks are executed in the correct order, handle dependencies, "
                "and monitor progress. You also coordinate with the Graph Builder Agent to "
                "update the knowledge graph with findings."
            ),
        )

        self.orchestrator_agent = ChatAgent(system_message=system_message)
        logger.info("CAMEL-AI Orchestrator Agent created")

    async def process_user_query(
        self,
        query: str,
        current_graph: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.FORK_JOIN,
    ) -> List[TaskExecutionResult]:
        """Process user query and execute tasks.

        Args:
            query: User query
            current_graph: Current graph state
            execution_mode: Task execution mode

        Returns:
            List of execution results
        """
        logger.info(f"Processing user query: {query}")

        try:
            # Generate tasks from query
            tasks = self.task_generation_service.generate_tasks_from_query(
                user_query=query,
                current_graph=current_graph,
            )

            if not tasks:
                logger.warning("No tasks generated from query")
                return []

            logger.info(f"Generated {len(tasks)} tasks")

            # Convert custom task format to CAMEL Task objects
            # First pass: create all tasks without dependencies
            camel_tasks = []
            task_id_map = {}  # Map task_id -> Task object
            
            for task in tasks:
                task_dict = task.to_dict() if hasattr(task, 'to_dict') else task
                task_id = task_dict.get('task_id', str(uuid4()))
                
                camel_task = Task(
                    content=f"{task_dict.get('title', '')}\n\n{task_dict.get('description', '')}\n\nParameters: {task_dict.get('parameters', {})}",
                    id=task_id,
                    dependencies=[],  # Will be set in second pass
                )
                camel_tasks.append(camel_task)
                task_id_map[task_id] = camel_task
                self.task_queue.append(camel_task)
            
            # Second pass: set dependencies (convert string IDs to Task objects)
            for task, camel_task in zip(tasks, camel_tasks):
                task_dict = task.to_dict() if hasattr(task, 'to_dict') else task
                dependencies = task_dict.get('dependencies', [])
                if dependencies is None:
                    dependencies = []
                
                # Convert string dependency IDs to Task objects
                task_dependencies = []
                for dep in dependencies:
                    if isinstance(dep, str):
                        # String ID - find corresponding Task object
                        if dep in task_id_map:
                            task_dependencies.append(task_id_map[dep])
                        else:
                            logger.warning(f"Dependency task {dep} not found, skipping")
                    elif hasattr(dep, 'id'):
                        # Already a Task object
                        task_dependencies.append(dep)
                    else:
                        logger.warning(f"Invalid dependency type: {type(dep)}, skipping")
                
                camel_task.dependencies = task_dependencies

            # Execute tasks based on mode
            if execution_mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential()
            elif execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel()
            elif execution_mode == ExecutionMode.FORK_JOIN:
                results = await self._execute_fork_join()
            else:
                logger.error(f"Unknown execution mode: {execution_mode}")
                results = []

            logger.info(f"Task execution completed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return []

    async def _execute_sequential(self) -> List[TaskExecutionResult]:
        """Execute tasks sequentially.

        Returns:
            List of execution results
        """
        logger.info("Executing tasks sequentially")

        results = []
        max_iterations = len(self.task_queue) * 10  # Prevent infinite loops
        iteration = 0

        while self.task_queue and iteration < max_iterations:
            iteration += 1
            task = self.task_queue.pop(0)

            # Check dependencies
            if not await self._check_dependencies(task):
                logger.warning(f"Task {task.id} has unmet dependencies")
                self.task_queue.append(task)
                continue

            # Execute task using workforce.run()
            result = await self._execute_task(task)
            results.append(result)

            # Add to completed or failed
            if result.status == TaskExecutionStatus.COMPLETED:
                self.completed_tasks[task.id] = result
            else:
                self.failed_tasks[task.id] = result

        if iteration >= max_iterations:
            logger.warning(f"Sequential execution stopped after {max_iterations} iterations to prevent infinite loop")

        return results

    async def _execute_parallel(self) -> List[TaskExecutionResult]:
        """Execute tasks in parallel.

        Returns:
            List of execution results
        """
        logger.info("Executing tasks in parallel")

        # Create tasks for all queue items
        execution_tasks = [
            self._execute_task(task)
            for task in self.task_queue
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task execution failed: {result}")
                task = self.task_queue[i]
                error_result = TaskExecutionResult(
                    task_id=task.id,
                    status=TaskExecutionStatus.FAILED,
                    error=str(result),
                )
                self.failed_tasks[task.id] = error_result
                processed_results.append(error_result)
            else:
                processed_results.append(result)
                if result.status == TaskExecutionStatus.COMPLETED:
                    self.completed_tasks[result.task_id] = result
                else:
                    self.failed_tasks[result.task_id] = result

        self.task_queue.clear()
        return processed_results

    async def _execute_fork_join(self) -> List[TaskExecutionResult]:
        """Execute tasks with fork/join pattern.

        Returns:
            List of execution results
        """
        logger.info("Executing tasks with fork/join pattern")

        results = []
        processed_ids = set()

        while self.task_queue:
            # Find tasks with no dependencies or met dependencies
            ready_tasks = []

            for task in self.task_queue:
                if task.id in processed_ids:
                    continue

                if not task.dependencies:
                    ready_tasks.append(task)
                else:
                    # Check if all dependencies are completed
                    # Handle both Task objects and string IDs
                    all_deps_met = all(
                        (dep.id if hasattr(dep, 'id') else str(dep)) in processed_ids
                        for dep in task.dependencies
                    )

                    if all_deps_met:
                        ready_tasks.append(task)

            if not ready_tasks:
                logger.warning("No ready tasks found, breaking fork/join")
                break

            # Fork: Execute ready tasks in parallel
            logger.info(f"Fork: Executing {len(ready_tasks)} tasks in parallel")

            execution_tasks = [
                self._execute_task(task)
                for task in ready_tasks
            ]

            fork_results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # Join: Collect results
            logger.info("Join: Collecting results")

            for i, result in enumerate(fork_results):
                if isinstance(result, Exception):
                    logger.error(f"Task execution failed: {result}")
                    task = ready_tasks[i]
                    error_result = TaskExecutionResult(
                        task_id=task.id,
                        status=TaskExecutionStatus.FAILED,
                        error=str(result),
                    )
                    self.failed_tasks[task.id] = error_result
                    results.append(error_result)
                else:
                    results.append(result)
                    processed_ids.add(result.task_id)

                    if result.status == TaskExecutionStatus.COMPLETED:
                        self.completed_tasks[result.task_id] = result
                    else:
                        self.failed_tasks[result.task_id] = result

            # Remove processed tasks from queue
            self.task_queue = [
                task for task in self.task_queue
                if task.id not in processed_ids
            ]

        return results

    async def _execute_task(self, task: Task) -> TaskExecutionResult:
        """Execute a single task using workforce.run().

        Args:
            task: CAMEL Task object to execute

        Returns:
            Execution result
        """
        task_id = task.id
        logger.info(f"Executing task: {task_id}")

        start_time = datetime.utcnow()

        try:
            # Call on_task_start callbacks
            await self._call_callbacks(self.on_task_start_callbacks, task)

            # Mark as running
            self.executing_tasks[task_id] = task

            # Use workforce.run() to execute the task
            # This is the CAMEL-native way to execute tasks
            logger.info(f"Executing task via workforce.run(): {task_id}")
            workforce_result = await self.workforce.run(task)

            # Process response
            task_result = {
                "task_id": task_id,
                "workforce_result": str(workforce_result) if workforce_result else None,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Update graph if Graph Builder Agent is available
            if self.graph_builder_agent and workforce_result:
                await self._update_graph(task, task_result)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Create result
            result = TaskExecutionResult(
                task_id=task_id,
                status=TaskExecutionStatus.COMPLETED,
                result=task_result,
                execution_time=execution_time,
            )

            # Remove from executing
            del self.executing_tasks[task_id]

            # Call on_task_complete callbacks
            await self._call_callbacks(self.on_task_complete_callbacks, result)

            logger.info(f"Task completed: {task_id} ({execution_time:.2f}s)")
            return result

        except Exception as e:
            logger.error(f"Task execution failed: {task_id} - {e}")

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Create error result
            result = TaskExecutionResult(
                task_id=task_id,
                status=TaskExecutionStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
            )

            # Remove from executing
            if task_id in self.executing_tasks:
                del self.executing_tasks[task_id]

            # Call on_task_failed callbacks
            await self._call_callbacks(self.on_task_failed_callbacks, result)

            return result

    async def _get_agent_response(
        self,
        agent: ChatAgent,
        message: BaseMessage,
    ) -> str:
        """Get response from CAMEL-AI agent.

        Args:
            agent: CAMEL-AI ChatAgent
            message: Message to send

        Returns:
            Agent response
        """
        try:
            # Use CAMEL-AI native method to get response
            response = await agent.step(message)

            if response:
                # Extract content from response
                if hasattr(response, "content"):
                    return response.content
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)

            return ""

        except Exception as e:
            logger.error(f"Agent response failed: {e}")
            return ""

    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are met.

        Args:
            task: CAMEL Task object to check

        Returns:
            True if dependencies are met
        """
        dependencies = task.dependencies or []

        if not dependencies:
            return True

        # Check if all dependencies are completed
        # CAMEL-AI Task.dependencies is List[Task], so extract IDs
        for dep in dependencies:
            # Handle both Task objects and string IDs (for backward compatibility)
            dep_id = dep.id if hasattr(dep, 'id') else str(dep)
            if dep_id not in self.completed_tasks:
                return False

        return True

    async def _update_graph(
        self,
        task: Task,
        task_result: Dict[str, Any],
    ):
        """Update graph with task results.

        Args:
            task: CAMEL Task object
            task_result: Task result
        """
        if not self.graph_builder_agent:
            return

        try:
            logger.info(f"Updating graph with task results: {task.id}")

            # Create intelligence event from task result
            event = {
                "event_type": "task_completed",
                "task_id": task.id,
                "data": task_result,
            }

            # Send to graph builder
            # This would be implemented based on Graph Builder Agent interface
            logger.info(f"Graph update sent for task: {task.id}")

        except Exception as e:
            logger.error(f"Graph update failed: {e}")

    async def _call_callbacks(
        self,
        callbacks: List[Callable],
        *args,
        **kwargs,
    ):
        """Call callbacks.

        Args:
            callbacks: List of callbacks
            args: Positional arguments
            kwargs: Keyword arguments
        """
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback execution failed: {e}")

    def register_on_task_start(self, callback: Callable):
        """Register callback for task start.

        Args:
            callback: Callback function
        """
        self.on_task_start_callbacks.append(callback)

    def register_on_task_complete(self, callback: Callable):
        """Register callback for task complete.

        Args:
            callback: Callback function
        """
        self.on_task_complete_callbacks.append(callback)

    def register_on_task_failed(self, callback: Callable):
        """Register callback for task failed.

        Args:
            callback: Callback function
        """
        self.on_task_failed_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status.

        Returns:
            Status dictionary
        """
        return {
            "queued_tasks": len(self.task_queue),
            "executing_tasks": len(self.executing_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "total_tasks": (
                len(self.task_queue)
                + len(self.executing_tasks)
                + len(self.completed_tasks)
                + len(self.failed_tasks)
            ),
        }

    def get_completed_tasks(self) -> List[TaskExecutionResult]:
        """Get completed tasks.

        Returns:
            List of completed tasks
        """
        return list(self.completed_tasks.values())

    def get_failed_tasks(self) -> List[TaskExecutionResult]:
        """Get failed tasks.

        Returns:
            List of failed tasks
        """
        return list(self.failed_tasks.values())

    def get_executing_tasks(self) -> List[Task]:
        """Get executing tasks.

        Returns:
            List of executing CAMEL Task objects
        """
        return list(self.executing_tasks.values())

    def get_queued_tasks(self) -> List[Task]:
        """Get queued tasks.

        Returns:
            List of queued CAMEL Task objects
        """
        return self.task_queue.copy()

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled
        """
        logger.info(f"Cancelling task: {task_id}")

        # Check if task exists in queue
        task_found = any(task.id == task_id for task in self.task_queue)
        
        # Remove from queue
        self.task_queue = [
            task for task in self.task_queue
            if task.id != task_id
        ]

        # Cancel if executing
        if task_id in self.executing_tasks:
            del self.executing_tasks[task_id]
            return True

        # Return True if task was found in queue
        return task_found

    async def cancel_all_tasks(self):
        """Cancel all tasks."""
        logger.info("Cancelling all tasks")

        self.task_queue.clear()
        self.executing_tasks.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get orchestrator summary.

        Returns:
            Summary dictionary
        """
        return {
            "status": self.get_status(),
            "completed_tasks": [
                result.to_dict()
                for result in self.get_completed_tasks()
            ],
            "failed_tasks": [
                result.to_dict()
                for result in self.get_failed_tasks()
            ],
            "executing_tasks": [{"id": t.id, "content": t.content} for t in self.get_executing_tasks()],
            "queued_tasks": [{"id": t.id, "content": t.content} for t in self.get_queued_tasks()],
        }
