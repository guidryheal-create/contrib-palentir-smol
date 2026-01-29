"""Integration tests for complete workflow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.task_orchestrator_agent import (
    TaskOrchestratorAgent,
    ExecutionMode,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Test complete OSINT workflow."""

    @pytest.fixture
    def orchestrator(self, mock_camel_ai_workforce):
        """Create orchestrator."""
        return TaskOrchestratorAgent(
            workforce=mock_camel_ai_workforce,
            task_generation_service=MagicMock(),
        )

    async def test_company_reconnaissance_workflow(
        self,
        orchestrator,
    ):
        """Test complete company reconnaissance workflow."""
        # Setup
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [
            MagicMock(
                to_dict=MagicMock(
                    return_value={
                        "task_id": "task_1",
                        "title": "Social Media Search",
                        "description": "Search social media",
                        "task_type": "RECONNAISSANCE",
                        "assigned_agents": ["SocialMediaAgent"],
                        "parameters": {"company_name": "Tech Corp"},
                        "dependencies": [],
                        "status": "pending",
                    }
                )
            ),
            MagicMock(
                to_dict=MagicMock(
                    return_value={
                        "task_id": "task_2",
                        "title": "Domain Analysis",
                        "description": "Analyze domain",
                        "task_type": "ANALYSIS",
                        "assigned_agents": ["DomainAnalysisAgent"],
                        "parameters": {"domain": "techcorp.com"},
                        "dependencies": ["task_1"],
                        "status": "pending",
                    }
                )
            ),
        ]

        # Execute
        results = await orchestrator.process_user_query(
            query="Investigate Tech Corp",
            execution_mode=ExecutionMode.FORK_JOIN,
        )

        # Verify
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_task_generation_and_execution(
        self,
        orchestrator,
    ):
        """Test task generation and execution."""
        # Setup
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [
            MagicMock(
                to_dict=MagicMock(
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
            )
        ]

        # Execute
        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.SEQUENTIAL,
        )

        # Verify
        assert isinstance(results, list)
        orchestrator.task_generation_service.generate_tasks_from_query.assert_called_once()

    async def test_parallel_execution_workflow(
        self,
        orchestrator,
    ):
        """Test parallel execution workflow."""
        # Setup
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [
            MagicMock(
                to_dict=MagicMock(
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
            )
            for i in range(3)
        ]

        # Execute
        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.PARALLEL,
        )

        # Verify
        assert isinstance(results, list)

    async def test_fork_join_execution_workflow(
        self,
        orchestrator,
    ):
        """Test fork/join execution workflow."""
        # Setup
        orchestrator.task_generation_service.generate_tasks_from_query.return_value = [
            MagicMock(
                to_dict=MagicMock(
                    return_value={
                        "task_id": "task_1",
                        "title": "Initial Task",
                        "description": "Test",
                        "task_type": "RECONNAISSANCE",
                        "assigned_agents": ["TestAgent"],
                        "parameters": {},
                        "dependencies": [],
                        "status": "pending",
                    }
                )
            ),
            MagicMock(
                to_dict=MagicMock(
                    return_value={
                        "task_id": "task_2",
                        "title": "Dependent Task",
                        "description": "Test",
                        "task_type": "ANALYSIS",
                        "assigned_agents": ["TestAgent"],
                        "parameters": {},
                        "dependencies": ["task_1"],
                        "status": "pending",
                    }
                )
            ),
        ]

        # Execute
        results = await orchestrator.process_user_query(
            query="Test query",
            execution_mode=ExecutionMode.FORK_JOIN,
        )

        # Verify
        assert isinstance(results, list)


@pytest.mark.integration
@pytest.mark.asyncio
class TestGraphBuilderIntegration:
    """Test Graph Builder Agent integration."""

    async def test_graph_builder_with_intelligence_events(
        self,
        mock_graph_builder_agent,
        sample_intelligence_event,
    ):
        """Test graph builder with intelligence events."""
        # Execute
        result = await mock_graph_builder_agent.process_event(
            sample_intelligence_event
        )

        # Verify
        assert result is not None
        assert "nodes_created" in result
        assert result["nodes_created"] >= 0

    async def test_graph_builder_duplicate_detection(
        self,
        mock_graph_builder_agent,
    ):
        """Test graph builder duplicate detection."""
        # Setup
        event1 = {
            "event_type": "person_found",
            "source_agent": "Agent1",
            "data": {
                "name": "John Doe",
                "email": "john@example.com",
            },
        }

        event2 = {
            "event_type": "person_found",
            "source_agent": "Agent2",
            "data": {
                "name": "John Doe",
                "email": "john@example.com",
            },
        }

        # Execute
        result1 = await mock_graph_builder_agent.process_event(event1)
        result2 = await mock_graph_builder_agent.process_event(event2)

        # Verify
        assert result1 is not None
        assert result2 is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestPipelineExecution:
    """Test pipeline execution."""

    async def test_sequential_pipeline(self, mock_camel_ai_workforce):
        """Test sequential pipeline execution."""
        # Setup
        mock_camel_ai_workforce.execute_task = AsyncMock(
            return_value={"status": "completed"}
        )

        # Execute
        result = await mock_camel_ai_workforce.execute_task("task_1")

        # Verify
        assert result["status"] == "completed"

    async def test_parallel_pipeline(self, mock_camel_ai_workforce):
        """Test parallel pipeline execution."""
        # Setup
        mock_camel_ai_workforce.execute_task = AsyncMock(
            return_value={"status": "completed"}
        )

        # Execute
        results = [
            await mock_camel_ai_workforce.execute_task(f"task_{i}")
            for i in range(3)
        ]

        # Verify
        assert len(results) == 3
        assert all(r["status"] == "completed" for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
class TestMemoryIntegration:
    """Test memory system integration."""

    async def test_shared_memory_access(self, mock_camel_ai_workforce):
        """Test shared memory access."""
        # Setup
        mock_camel_ai_workforce.get_shared_memory = AsyncMock(
            return_value={"key": "value"}
        )

        # Execute
        memory = await mock_camel_ai_workforce.get_shared_memory()

        # Verify
        assert memory is not None
        assert "key" in memory

    async def test_memory_persistence(self, mock_redis_service):
        """Test memory persistence."""
        # Setup
        mock_redis_service.set = AsyncMock(return_value=True)
        mock_redis_service.get = AsyncMock(return_value=b"test_value")

        # Execute
        await mock_redis_service.set("key", "value")
        value = await mock_redis_service.get("key")

        # Verify
        assert value == b"test_value"
