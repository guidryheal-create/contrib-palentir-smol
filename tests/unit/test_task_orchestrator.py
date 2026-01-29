"""Unit tests for Task Orchestrator Agent."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from typing import Any, Dict, List, Optional

# Skip helpers available if needed, but not imported here to avoid import errors

# Mock camel modules before importing task_orchestrator_agent
# This must happen before the import statement below
try:
    import camel
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False
    
    # Create minimal mocks for camel modules
    mock_camel = Mock()
    mock_camel_agents = Mock()
    mock_camel_messages = Mock()
    mock_camel_societies = Mock()
    mock_camel_workforce = Mock()
    mock_camel_tasks = Mock()
    
    class MockTask:
        def __init__(self, content="", id="", dependencies=None):
            self.content = content
            self.id = id
            # Allow string dependencies for testing (CAMEL normally requires Task objects)
            self.dependencies = dependencies if dependencies is not None else []
            # Store original dependencies for validation bypass
            self._original_dependencies = self.dependencies
    
    class MockChatAgent:
        def __init__(self, *args, **kwargs):
            pass
    
    class MockBaseMessage:
        @staticmethod
        def make_assistant_message(*args, **kwargs):
            return Mock()
        
        @staticmethod
        def make_user_message(*args, **kwargs):
            return Mock()
    
    class MockWorkforce:
        def __init__(self, *args, **kwargs):
            pass
    
    mock_camel_tasks.Task = MockTask
    mock_camel_agents.ChatAgent = MockChatAgent
    mock_camel_messages.BaseMessage = MockBaseMessage
    mock_camel_workforce.Workforce = MockWorkforce
    
    mock_camel.agents = mock_camel_agents
    mock_camel.messages = mock_camel_messages
    mock_camel.societies = mock_camel_societies
    mock_camel.societies.workforce = mock_camel_workforce
    mock_camel.tasks = mock_camel_tasks
    
    # Insert mocks into sys.modules before import
    sys.modules['camel'] = mock_camel
    sys.modules['camel.agents'] = mock_camel_agents
    sys.modules['camel.messages'] = mock_camel_messages
    sys.modules['camel.societies'] = mock_camel_societies
    sys.modules['camel.societies.workforce'] = mock_camel_workforce
    sys.modules['camel.tasks'] = mock_camel_tasks

# Now import the module under test
from src.agents.task_orchestrator_agent import (
    TaskOrchestratorAgent,
    ExecutionMode,
    TaskExecutionStatus,
    TaskExecutionResult,
)


# Helper function to get Task class (MockTask or real Task)
def get_task_class():
    """Get Task class - MockTask if CAMEL not available, otherwise real Task."""
    if not CAMEL_AVAILABLE:
        return MockTask
    else:
        from camel.tasks import Task
        return Task


@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskOrchestratorAgent:
    """Test Task Orchestrator Agent."""

    @pytest.fixture
    def orchestrator(self, mock_camel_ai_workforce):
        """Create orchestrator instance."""
        return TaskOrchestratorAgent(
            workforce=mock_camel_ai_workforce,
            task_generation_service=MagicMock(),
            skip_agent_init=True,  # Skip ChatAgent initialization for tests
        )

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator is not None
        assert orchestrator.workforce is not None
        assert orchestrator.task_generation_service is not None
        assert len(orchestrator.task_queue) == 0
        assert len(orchestrator.executing_tasks) == 0
        assert len(orchestrator.completed_tasks) == 0
        assert len(orchestrator.failed_tasks) == 0

    def test_get_status(self, orchestrator):
        """Test get_status method."""
        status = orchestrator.get_status()

        assert "queued_tasks" in status
        assert "executing_tasks" in status
        assert "completed_tasks" in status
        assert "failed_tasks" in status
        assert "total_tasks" in status
        assert status["queued_tasks"] == 0

    def test_register_callbacks(self, orchestrator):
        """Test callback registration."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        orchestrator.register_on_task_start(callback1)
        orchestrator.register_on_task_complete(callback2)

        assert callback1 in orchestrator.on_task_start_callbacks
        assert callback2 in orchestrator.on_task_complete_callbacks

    async def test_process_user_query_sequential(
        self,
        orchestrator,
    ):
        """Test sequential task execution."""
        Task = get_task_class()
        
        # Mock task generation - return CAMEL Task objects
        mock_task = Task(
            content="Test Task: Test",
            id="task_1",
            dependencies=[],
        )
        
        # Create a mock object that has to_dict method for compatibility
        mock_task_obj = MagicMock()
        mock_task_obj.to_dict = MagicMock(
            return_value={
                "task_id": "task_1",
                "title": "Test Task",
                "description": "Test",
                "task_type": "RECONNAISSANCE",
                "assigned_agents": ["TestAgent"],
                "parameters": {},
                "dependencies": [],
                "status": "pending",
            }
        )
        # Make it return the Task when converted
        mock_task_obj.id = "task_1"
        mock_task_obj.content = "Test Task: Test"
        mock_task_obj.dependencies = []
        
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [mock_task_obj]
        
        # Mock workforce.run to return success
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})

        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.SEQUENTIAL,
        )

        assert isinstance(results, list)

    async def test_process_user_query_parallel(
        self,
        orchestrator,
    ):
        """Test parallel task execution."""
        Task = get_task_class()
        
        # Create mock task objects
        mock_tasks = []
        for i in range(3):
            mock_task = MagicMock()
            mock_task.to_dict = MagicMock(
                return_value={
                    "task_id": f"task_{i}",
                    "title": f"Task {i}",
                    "description": "Test",
                    "task_type": "RECONNAISSANCE",
                    "assigned_agents": ["TestAgent"],
                    "parameters": {},
                    "dependencies": [],
                    "status": "pending",
                }
            )
            mock_task.id = f"task_{i}"
            mock_task.content = f"Task {i}: Test"
            mock_task.dependencies = []
            mock_tasks.append(mock_task)
        
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = mock_tasks
        
        # Mock workforce.run to return success
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})

        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.PARALLEL,
        )

        assert isinstance(results, list)

    async def test_process_user_query_fork_join(
        self,
        orchestrator,
    ):
        """Test fork/join task execution."""
        Task = get_task_class()
        
        # Create mock task objects
        mock_task1 = MagicMock()
        mock_task1.to_dict = MagicMock(
            return_value={
                "task_id": "task_1",
                "title": "Task 1",
                "description": "Test",
                "task_type": "RECONNAISSANCE",
                "assigned_agents": ["TestAgent"],
                "parameters": {},
                "dependencies": [],
                "status": "pending",
            }
        )
        mock_task1.id = "task_1"
        mock_task1.content = "Task 1: Test"
        mock_task1.dependencies = []
        
        mock_task2 = MagicMock()
        mock_task2.to_dict = MagicMock(
            return_value={
                "task_id": "task_2",
                "title": "Task 2",
                "description": "Test",
                "task_type": "ANALYSIS",
                "assigned_agents": ["TestAgent"],
                "parameters": {},
                "dependencies": ["task_1"],
                "status": "pending",
            }
        )
        mock_task2.id = "task_2"
        mock_task2.content = "Task 2: Test"
        mock_task2.dependencies = ["task_1"]
        
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [
            mock_task1,
            mock_task2,
        ]
        
        # Mock workforce.run to return success
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})

        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.FORK_JOIN,
        )

        assert isinstance(results, list)

    async def test_cancel_task(self, orchestrator):
        """Test task cancellation."""
        Task = get_task_class()
        
        task = Task(content="Test task", id="task_1")
        orchestrator.task_queue.append(task)

        cancelled = await orchestrator.cancel_task("task_1")

        assert cancelled is True
        assert len(orchestrator.task_queue) == 0

    async def test_cancel_all_tasks(self, orchestrator):
        """Test cancel all tasks."""
        Task = get_task_class()
        
        task1 = Task(content="Test task 1", id="task_1")
        task2 = Task(content="Test task 2", id="task_2")
        orchestrator.task_queue.append(task1)
        orchestrator.task_queue.append(task2)

        await orchestrator.cancel_all_tasks()

        assert len(orchestrator.task_queue) == 0

    def test_get_completed_tasks(self, orchestrator):
        """Test get_completed_tasks."""
        result = TaskExecutionResult(
            task_id="task_1",
            status=TaskExecutionStatus.COMPLETED,
            result={"data": "test"},
        )
        orchestrator.completed_tasks["task_1"] = result

        completed = orchestrator.get_completed_tasks()

        assert len(completed) == 1
        assert completed[0].task_id == "task_1"

    def test_get_failed_tasks(self, orchestrator):
        """Test get_failed_tasks."""
        result = TaskExecutionResult(
            task_id="task_1",
            status=TaskExecutionStatus.FAILED,
            error="Test error",
        )
        orchestrator.failed_tasks["task_1"] = result

        failed = orchestrator.get_failed_tasks()

        assert len(failed) == 1
        assert failed[0].task_id == "task_1"

    def test_get_executing_tasks(self, orchestrator):
        """Test get_executing_tasks."""
        Task = get_task_class()
        
        task = Task(content="Test task", id="task_1")
        orchestrator.executing_tasks["task_1"] = task

        executing = orchestrator.get_executing_tasks()

        assert len(executing) == 1
        assert executing[0].id == "task_1"

    def test_get_queued_tasks(self, orchestrator):
        """Test get_queued_tasks."""
        Task = get_task_class()
        
        task = Task(content="Test task", id="task_1")
        orchestrator.task_queue.append(task)

        queued = orchestrator.get_queued_tasks()

        assert len(queued) == 1
        assert queued[0].id == "task_1"

    def test_get_summary(self, orchestrator):
        """Test get_summary."""
        summary = orchestrator.get_summary()

        assert "status" in summary
        assert "completed_tasks" in summary
        assert "failed_tasks" in summary
        assert "executing_tasks" in summary
        assert "queued_tasks" in summary


@pytest.mark.unit
class TestTaskExecutionResult:
    """Test TaskExecutionResult."""

    def test_initialization(self):
        """Test result initialization."""
        result = TaskExecutionResult(
            task_id="task_1",
            status=TaskExecutionStatus.COMPLETED,
            result={"data": "test"},
            execution_time=10.5,
        )

        assert result.task_id == "task_1"
        assert result.status == TaskExecutionStatus.COMPLETED
        assert result.result == {"data": "test"}
        assert result.execution_time == 10.5
        assert result.error is None

    def test_to_dict(self):
        """Test to_dict method."""
        result = TaskExecutionResult(
            task_id="task_1",
            status=TaskExecutionStatus.COMPLETED,
            result={"data": "test"},
            execution_time=10.5,
        )

        result_dict = result.to_dict()

        assert result_dict["task_id"] == "task_1"
        assert result_dict["status"] == "completed"
        assert result_dict["result"] == {"data": "test"}
        assert result_dict["execution_time"] == 10.5


@pytest.mark.unit
class TestExecutionMode:
    """Test ExecutionMode enum."""

    def test_execution_modes(self):
        """Test execution modes."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.FORK_JOIN.value == "fork_join"

    def test_execution_mode_from_string(self):
        """Test creating execution mode from string."""
        mode = ExecutionMode("sequential")
        assert mode == ExecutionMode.SEQUENTIAL


@pytest.mark.unit
class TestTaskExecutionStatus:
    """Test TaskExecutionStatus enum."""

    def test_execution_statuses(self):
        """Test execution statuses."""
        assert TaskExecutionStatus.PENDING.value == "pending"
        assert TaskExecutionStatus.RUNNING.value == "running"
        assert TaskExecutionStatus.COMPLETED.value == "completed"
        assert TaskExecutionStatus.FAILED.value == "failed"
        assert TaskExecutionStatus.CANCELLED.value == "cancelled"


@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskOrchestratorAgentAdvanced:
    """Advanced tests for Task Orchestrator Agent."""

    @pytest.fixture
    def orchestrator(self, mock_camel_ai_workforce, mock_environment):
        """Create orchestrator instance."""
        # Skip agent init to avoid API key requirement
        orchestrator = TaskOrchestratorAgent(
            workforce=mock_camel_ai_workforce,
            task_generation_service=MagicMock(),
            skip_agent_init=True,  # Skip ChatAgent initialization for tests
        )
        # Set a mock orchestrator_agent for tests that need it
        orchestrator.orchestrator_agent = MagicMock()
        return orchestrator

    async def test_execute_task_success(self, orchestrator):
        """Test successful task execution."""
        Task = get_task_class()
        task = Task(content="Test task", id="task_1")
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success", "result": "Task completed"})
        
        # Mock datetime.utcnow to simulate execution time
        # Calls: start_time, TaskExecutionResult.timestamp, end_time (execution_time calc)
        with patch('src.agents.task_orchestrator_agent.datetime') as mock_datetime_mod:
            start_time = datetime(2024, 1, 1, 0, 0, 0)
            end_time = datetime(2024, 1, 1, 0, 0, 1)  # 1 second later
            
            # Mock utcnow method - need multiple calls (start, timestamp, end)
            mock_datetime_mod.utcnow.side_effect = [start_time, end_time, end_time, end_time]
            
            result = await orchestrator._execute_task(task)
            
            assert result.task_id == "task_1"
            assert result.status == TaskExecutionStatus.COMPLETED
            assert result.result is not None
            assert result.error is None
            assert result.execution_time >= 1.0  # Should be 1 second

    async def test_execute_task_failure(self, orchestrator):
        """Test task execution failure."""
        Task = get_task_class()
        task = Task(content="Test task", id="task_1")
        orchestrator.workforce.run = AsyncMock(side_effect=Exception("Task failed"))
        
        # Mock datetime.utcnow to simulate execution time
        # Calls: start_time, TaskExecutionResult.timestamp (in error path), end_time (execution_time calc)
        with patch('src.agents.task_orchestrator_agent.datetime') as mock_datetime_mod:
            start_time = datetime(2024, 1, 1, 0, 0, 0)
            end_time = datetime(2024, 1, 1, 0, 0, 1)  # 1 second later
            
            # Mock utcnow method - need multiple calls (start, timestamp in error, end)
            mock_datetime_mod.utcnow.side_effect = [start_time, end_time, end_time, end_time]
            
            result = await orchestrator._execute_task(task)
            
            assert result.task_id == "task_1"
            assert result.status == TaskExecutionStatus.FAILED
            assert result.error == "Task failed"
            assert result.execution_time >= 1.0  # Should be 1 second

    async def test_execute_task_with_callbacks(self, orchestrator):
        """Test task execution with callbacks."""
        Task = get_task_class()
        
        start_callback = AsyncMock()
        complete_callback = AsyncMock()
        
        orchestrator.register_on_task_start(start_callback)
        orchestrator.register_on_task_complete(complete_callback)
        
        task = Task(content="Test task", id="task_1")
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        await orchestrator._execute_task(task)
        
        start_callback.assert_called_once()
        complete_callback.assert_called_once()

    async def test_execute_task_with_graph_builder(self, orchestrator, mock_graph_builder_agent):
        """Test task execution with graph builder agent."""
        Task = get_task_class()
        
        orchestrator.graph_builder_agent = mock_graph_builder_agent
        task = Task(content="Test task", id="task_1")
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success", "data": "test"})
        
        result = await orchestrator._execute_task(task)
        
        assert result.status == TaskExecutionStatus.COMPLETED

    async def test_check_dependencies_no_dependencies(self, orchestrator):
        """Test dependency check with no dependencies."""
        Task = get_task_class()
        task = Task(content="Test task", id="task_1", dependencies=[])
        
        result = await orchestrator._check_dependencies(task)
        
        assert result is True

    async def test_check_dependencies_met(self, orchestrator):
        """Test dependency check with met dependencies."""
        Task = get_task_class()
        
        # Add completed task
        completed_result = TaskExecutionResult(
            task_id="task_0",
            status=TaskExecutionStatus.COMPLETED,
        )
        orchestrator.completed_tasks["task_0"] = completed_result
        
        # Create dependency task object or use string ID based on Task type
        if CAMEL_AVAILABLE:
            # For real CAMEL Task, create a Task object for dependency
            dep_task = Task(content="Dependency task", id="task_0", dependencies=[])
            task = Task(content="Test task", id="task_1", dependencies=[dep_task])
        else:
            # For MockTask, can use string dependencies
            task = Task(content="Test task", id="task_1", dependencies=["task_0"])
        
        result = await orchestrator._check_dependencies(task)
        
        assert result is True

    async def test_check_dependencies_unmet(self, orchestrator):
        """Test dependency check with unmet dependencies."""
        Task = get_task_class()
        
        # Create dependency task object or use string ID based on Task type
        if CAMEL_AVAILABLE:
            # For real CAMEL Task, create a Task object for dependency
            dep_task = Task(content="Dependency task", id="task_0", dependencies=[])
            task = Task(content="Test task", id="task_1", dependencies=[dep_task])
        else:
            # For MockTask, can use string dependencies
            task = Task(content="Test task", id="task_1", dependencies=["task_0"])
        
        result = await orchestrator._check_dependencies(task)
        
        assert result is False

    async def test_check_dependencies_multiple_met(self, orchestrator):
        """Test dependency check with multiple met dependencies."""
        Task = get_task_class()
        
        # Add completed tasks
        for i in range(3):
            completed_result = TaskExecutionResult(
                task_id=f"task_{i}",
                status=TaskExecutionStatus.COMPLETED,
            )
            orchestrator.completed_tasks[f"task_{i}"] = completed_result
        
        # Create dependency task objects or use string IDs based on Task type
        if CAMEL_AVAILABLE:
            # For real CAMEL Task, create Task objects for dependencies
            dep_tasks = [Task(content=f"Dependency {i}", id=f"task_{i}", dependencies=[]) for i in range(3)]
            task = Task(content="Test task", id="task_3", dependencies=dep_tasks)
        else:
            # For MockTask, can use string dependencies
            task = Task(content="Test task", id="task_3", dependencies=["task_0", "task_1", "task_2"])
        
        result = await orchestrator._check_dependencies(task)
        
        assert result is True

    async def test_check_dependencies_multiple_partial(self, orchestrator):
        """Test dependency check with partially met dependencies."""
        Task = get_task_class()
        
        # Add only one completed task
        completed_result = TaskExecutionResult(
            task_id="task_0",
            status=TaskExecutionStatus.COMPLETED,
        )
        orchestrator.completed_tasks["task_0"] = completed_result
        
        # Create dependency task objects or use string IDs based on Task type
        if CAMEL_AVAILABLE:
            # For real CAMEL Task, create Task objects for dependencies
            dep_tasks = [Task(content=f"Dependency {i}", id=f"task_{i}", dependencies=[]) for i in range(3)]
            task = Task(content="Test task", id="task_3", dependencies=dep_tasks)
        else:
            # For MockTask, can use string dependencies
            task = Task(content="Test task", id="task_3", dependencies=["task_0", "task_1", "task_2"])
        
        result = await orchestrator._check_dependencies(task)
        
        assert result is False

    async def test_update_graph(self, orchestrator, mock_graph_builder_agent):
        """Test graph update."""
        Task = get_task_class()
        
        orchestrator.graph_builder_agent = mock_graph_builder_agent
        task = Task(content="Test task", id="task_1")
        task_result = {"task_id": "task_1", "data": "test"}
        
        await orchestrator._update_graph(task, task_result)
        
        # Graph update should complete without error

    async def test_update_graph_no_agent(self, orchestrator):
        """Test graph update without graph builder agent."""
        Task = get_task_class()
        
        orchestrator.graph_builder_agent = None
        task = Task(content="Test task", id="task_1")
        task_result = {"task_id": "task_1", "data": "test"}
        
        # Should not raise error
        await orchestrator._update_graph(task, task_result)

    async def test_call_callbacks_sync(self, orchestrator):
        """Test calling synchronous callbacks."""
        callback = MagicMock()
        
        await orchestrator._call_callbacks([callback], "arg1", "arg2", kwarg1="value1")
        
        callback.assert_called_once_with("arg1", "arg2", kwarg1="value1")

    async def test_call_callbacks_async(self, orchestrator):
        """Test calling asynchronous callbacks."""
        callback = AsyncMock()
        
        await orchestrator._call_callbacks([callback], "arg1", "arg2", kwarg1="value1")
        
        callback.assert_called_once_with("arg1", "arg2", kwarg1="value1")

    async def test_call_callbacks_mixed(self, orchestrator):
        """Test calling mixed sync and async callbacks."""
        sync_callback = MagicMock()
        async_callback = AsyncMock()
        
        await orchestrator._call_callbacks([sync_callback, async_callback], "arg")
        
        sync_callback.assert_called_once_with("arg")
        async_callback.assert_called_once_with("arg")

    async def test_call_callbacks_exception(self, orchestrator):
        """Test callback exception handling."""
        def failing_callback(*args, **kwargs):
            raise Exception("Callback failed")
        
        # Should not raise exception
        await orchestrator._call_callbacks([failing_callback], "arg")

    def test_register_on_task_failed(self, orchestrator):
        """Test failed callback registration."""
        callback = MagicMock()
        
        orchestrator.register_on_task_failed(callback)
        
        assert callback in orchestrator.on_task_failed_callbacks

    async def test_execute_sequential_with_dependencies(self, orchestrator):
        """Test sequential execution with dependencies."""
        Task = get_task_class()
        
        # Create tasks with dependencies
        task1 = Task(content="Task 1", id="task_1", dependencies=[])
        if CAMEL_AVAILABLE:
            task2 = Task(content="Task 2", id="task_2", dependencies=[task1])
        else:
            task2 = Task(content="Task 2", id="task_2", dependencies=["task_1"])
        
        orchestrator.task_queue = [task1, task2]
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        results = await orchestrator._execute_sequential()
        
        assert len(results) == 2
        assert results[0].task_id == "task_1"
        assert results[1].task_id == "task_2"

    async def test_execute_sequential_dependency_wait(self, orchestrator):
        """Test sequential execution waiting for dependencies."""
        Task = get_task_class()
        
        # Create task with unmet dependency
        task1 = Task(content="Task 1", id="task_1", dependencies=[])
        if CAMEL_AVAILABLE:
            dep_task = Task(content="Dependency", id="task_0", dependencies=[])
            task2 = Task(content="Task 2", id="task_2", dependencies=[dep_task])
        else:
            task2 = Task(content="Task 2", id="task_2", dependencies=["task_0"])
        
        orchestrator.task_queue = [task1, task2]
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        results = await orchestrator._execute_sequential()
        
        # Only task1 should execute, task2 should remain in queue
        assert len(results) == 1
        assert results[0].task_id == "task_1"
        assert len(orchestrator.task_queue) == 1

    async def test_execute_parallel_exception_handling(self, orchestrator):
        """Test parallel execution with exceptions."""
        Task = get_task_class()
        
        task1 = Task(content="Task 1", id="task_1", dependencies=[])
        task2 = Task(content="Task 2", id="task_2", dependencies=[])
        
        orchestrator.task_queue = [task1, task2]
        
        # First task succeeds, second fails
        async def mock_run(task):
            if task.id == "task_1":
                return {"status": "success"}
            else:
                raise Exception("Task failed")
        
        orchestrator.workforce.run = AsyncMock(side_effect=mock_run)
        
        results = await orchestrator._execute_parallel()
        
        assert len(results) == 2
        assert results[0].status == TaskExecutionStatus.COMPLETED
        assert results[1].status == TaskExecutionStatus.FAILED

    async def test_execute_fork_join_complex_dependencies(self, orchestrator):
        """Test fork/join with complex dependency graph."""
        Task = get_task_class()
        
        # Create dependency graph: task_1 -> task_2, task_3 -> task_4
        task1 = Task(content="Task 1", id="task_1", dependencies=[])
        task3 = Task(content="Task 3", id="task_3", dependencies=[])
        if CAMEL_AVAILABLE:
            task2 = Task(content="Task 2", id="task_2", dependencies=[task1])
            task4 = Task(content="Task 4", id="task_4", dependencies=[task3])
        else:
            task2 = Task(content="Task 2", id="task_2", dependencies=["task_1"])
            task4 = Task(content="Task 4", id="task_4", dependencies=["task_3"])
        
        orchestrator.task_queue = [task1, task2, task3, task4]
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        results = await orchestrator._execute_fork_join()
        
        assert len(results) == 4
        # Verify all tasks completed
        task_ids = {r.task_id for r in results}
        assert task_ids == {"task_1", "task_2", "task_3", "task_4"}

    async def test_execute_fork_join_no_ready_tasks(self, orchestrator):
        """Test fork/join with no ready tasks."""
        Task = get_task_class()
        
        # Create task with unmet dependency
        if CAMEL_AVAILABLE:
            dep_task = Task(content="Dependency", id="task_0", dependencies=[])
            task = Task(content="Task 1", id="task_1", dependencies=[dep_task])
        else:
            task = Task(content="Task 1", id="task_1", dependencies=["task_0"])
        
        orchestrator.task_queue = [task]
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        results = await orchestrator._execute_fork_join()
        
        # Should return empty results since no tasks are ready
        assert len(results) == 0

    async def test_process_user_query_empty_tasks(self, orchestrator):
        """Test processing query with no generated tasks."""
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = []
        
        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.SEQUENTIAL,
        )
        
        assert results == []

    async def test_process_user_query_invalid_mode(self, orchestrator):
        """Test processing query with invalid execution mode."""
        Task = get_task_class()
        
        mock_task = MagicMock()
        mock_task.to_dict = MagicMock(return_value={
            "task_id": "task_1",
            "title": "Test Task",
            "description": "Test",
            "dependencies": [],
        })
        mock_task.id = "task_1"
        mock_task.content = "Test Task: Test"
        mock_task.dependencies = []
        
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [mock_task]
        
        # Use invalid mode by directly setting it
        class InvalidMode:
            value = "invalid"
        
        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=InvalidMode(),
        )
        
        # Should return empty results for invalid mode
        assert results == []

    async def test_cancel_task_not_found(self, orchestrator):
        """Test cancelling non-existent task."""
        cancelled = await orchestrator.cancel_task("nonexistent_task")
        
        assert cancelled is False

    async def test_cancel_task_executing(self, orchestrator):
        """Test cancelling executing task."""
        Task = get_task_class()
        
        task = Task(content="Test task", id="task_1")
        orchestrator.executing_tasks["task_1"] = task
        
        cancelled = await orchestrator.cancel_task("task_1")
        
        assert cancelled is True
        assert "task_1" not in orchestrator.executing_tasks

    async def test_get_agent_response(self, orchestrator):
        """Test getting agent response."""
        from camel.agents import ChatAgent
        from camel.messages import BaseMessage
        
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_agent.step = AsyncMock(return_value=mock_response)
        
        message = BaseMessage.make_user_message(role_name="User", content="Test message")
        
        response = await orchestrator._get_agent_response(mock_agent, message)
        
        assert response == "Test response"
        mock_agent.step.assert_called_once()

    async def test_get_agent_response_string(self, orchestrator):
        """Test getting agent response as string."""
        from camel.agents import ChatAgent
        from camel.messages import BaseMessage
        
        mock_agent = AsyncMock()
        mock_agent.step = AsyncMock(return_value="String response")
        
        message = BaseMessage.make_user_message(role_name="User", content="Test message")
        
        response = await orchestrator._get_agent_response(mock_agent, message)
        
        assert response == "String response"

    async def test_get_agent_response_exception(self, orchestrator):
        """Test agent response exception handling."""
        from camel.agents import ChatAgent
        from camel.messages import BaseMessage
        
        mock_agent = AsyncMock()
        mock_agent.step = AsyncMock(side_effect=Exception("Agent error"))
        
        message = BaseMessage.make_user_message(role_name="User", content="Test message")
        
        response = await orchestrator._get_agent_response(mock_agent, message)
        
        assert response == ""

    def test_get_summary_with_tasks(self, orchestrator):
        """Test get_summary with various tasks."""
        Task = get_task_class()
        
        # Add completed task
        completed_result = TaskExecutionResult(
            task_id="task_1",
            status=TaskExecutionStatus.COMPLETED,
            result={"data": "test"},
        )
        orchestrator.completed_tasks["task_1"] = completed_result
        
        # Add failed task
        failed_result = TaskExecutionResult(
            task_id="task_2",
            status=TaskExecutionStatus.FAILED,
            error="Test error",
        )
        orchestrator.failed_tasks["task_2"] = failed_result
        
        # Add executing task
        executing_task = Task(content="Executing task", id="task_3")
        orchestrator.executing_tasks["task_3"] = executing_task
        
        # Add queued task
        queued_task = Task(content="Queued task", id="task_4")
        orchestrator.task_queue.append(queued_task)
        
        summary = orchestrator.get_summary()
        
        assert "status" in summary
        assert len(summary["completed_tasks"]) == 1
        assert len(summary["failed_tasks"]) == 1
        assert len(summary["executing_tasks"]) == 1
        assert len(summary["queued_tasks"]) == 1

    async def test_task_execution_with_current_graph(self, orchestrator):
        """Test task execution with current graph context."""
        Task = get_task_class()
        
        mock_task = MagicMock()
        mock_task.to_dict = MagicMock(return_value={
            "task_id": "task_1",
            "title": "Test Task",
            "description": "Test",
            "dependencies": [],
        })
        mock_task.id = "task_1"
        mock_task.content = "Test Task: Test"
        mock_task.dependencies = []
        
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [mock_task]
        orchestrator.workforce.run = AsyncMock(return_value={"status": "success"})
        
        current_graph = {
            "nodes": [{"id": "node_1", "type": "Company"}],
            "edges": [],
        }
        
        results = await orchestrator.process_user_query(
            query="Test query",
            current_graph=current_graph,
            execution_mode=ExecutionMode.SEQUENTIAL,
        )
        
        assert len(results) > 0
        # Verify graph was passed to task generation
        orchestrator.task_generation_service.generate_tasks_from_query.assert_called_once()
        call_args = orchestrator.task_generation_service.generate_tasks_from_query.call_args
        assert call_args.kwargs.get("current_graph") == current_graph
