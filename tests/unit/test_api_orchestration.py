"""Unit tests for API orchestration routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.main import app
from src.api.routes import orchestration


@pytest.mark.unit
class TestOrchestrationAPI:
    """Test orchestration API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_health_check(self, client):
        """Test API health check endpoint."""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/info")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert "message" in response.json()

    @patch("src.api.routes.orchestration.orchestrator", None)
    def test_query_endpoint_no_orchestrator(self, client):
        """Test query endpoint without orchestrator."""
        response = client.post(
            "/api/v1/orchestration/query",
            json={
                "query": "Test query",
                "execution_mode": "fork_join",
            },
        )

        assert response.status_code == 500

    @patch("src.api.routes.orchestration.orchestrator", None)
    def test_status_endpoint_no_orchestrator(self, client):
        """Test status endpoint without orchestrator."""
        response = client.get("/api/v1/orchestration/status")

        assert response.status_code == 500

    def test_set_orchestrator(self, mock_camel_ai_workforce):
        """Test setting orchestrator."""
        from src.agents.task_orchestrator_agent import TaskOrchestratorAgent

        mock_task_generation_service = MagicMock()
        orch = TaskOrchestratorAgent(
            workforce=mock_camel_ai_workforce,
            task_generation_service=mock_task_generation_service,
        )

        orchestration.set_orchestrator(orch)

        assert orchestration.orchestrator is not None


@pytest.mark.unit
class TestQueryRequest:
    """Test QueryRequest model."""

    def test_query_request_creation(self):
        """Test creating query request."""
        from src.api.routes.orchestration import QueryRequest

        request = QueryRequest(
            query="Test query",
            execution_mode="fork_join",
        )

        assert request.query == "Test query"
        assert request.execution_mode == "fork_join"

    def test_query_request_default_mode(self):
        """Test query request with default execution mode."""
        from src.api.routes.orchestration import QueryRequest

        request = QueryRequest(query="Test query")

        assert request.query == "Test query"
        assert request.execution_mode == "fork_join"


@pytest.mark.unit
class TestTaskStatusResponse:
    """Test TaskStatusResponse model."""

    def test_task_status_response_creation(self):
        """Test creating task status response."""
        from src.api.routes.orchestration import TaskStatusResponse

        response = TaskStatusResponse(
            queued_tasks=5,
            executing_tasks=2,
            completed_tasks=10,
            failed_tasks=1,
        )

        assert response.queued_tasks == 5
        assert response.executing_tasks == 2
        assert response.completed_tasks == 10
        assert response.failed_tasks == 1


@pytest.mark.unit
class TestTaskResultResponse:
    """Test TaskResultResponse model."""

    def test_task_result_response_creation(self):
        """Test creating task result response."""
        from src.api.routes.orchestration import TaskResultResponse

        response = TaskResultResponse(
            task_id="task_1",
            status="completed",
            result={"data": "test"},
            execution_time=10.5,
            timestamp="2025-12-28T10:00:00Z",
        )

        assert response.task_id == "task_1"
        assert response.status == "completed"
        assert response.execution_time == 10.5
