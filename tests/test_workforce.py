"""Tests for CAMEL workforce integration."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, Mock
from typing import Dict, Any
import os

# Set mock API key before any imports
os.environ["OPENAI_API_KEY"] = "test_key_mock"

from src.workforce.camel_integrated_workforce import PalentirCAMELWorkforce
from camel.tasks import Task


class TestPalentirCAMELWorkforce:
    """Test Palentir CAMEL Workforce."""

    @pytest.fixture
    def mock_model(self):
        """Create mock model."""
        return MagicMock()

    @pytest.fixture
    def mock_chat_agent(self):
        """Create mock ChatAgent."""
        agent = MagicMock()
        agent.step = AsyncMock(return_value=MagicMock())
        agent.astep = AsyncMock(return_value=MagicMock())
        return agent

    @pytest.fixture
    def mock_workforce(self):
        """Create mock Workforce."""
        workforce = MagicMock()
        workforce.description = "Test Workforce"
        workforce.process_task = AsyncMock(return_value={"status": "success"})
        workforce.run = AsyncMock(return_value={"status": "success"})
        workforce.add_single_agent_worker = MagicMock()
        workforce.get_worker = MagicMock(return_value=None)
        workforce.to_mcp = MagicMock(return_value=MagicMock())
        return workforce

    @pytest.fixture
    def workforce(self, mock_model, mock_chat_agent, mock_workforce):
        """Create workforce instance."""
        with patch("src.workforce.camel_integrated_workforce.ModelFactory") as mock_factory:
            mock_factory.create.return_value = mock_model
            with patch("src.workforce.camel_integrated_workforce.ChatAgent") as mock_agent_class:
                mock_agent_class.return_value = mock_chat_agent
                with patch("src.workforce.camel_integrated_workforce.Workforce") as mock_workforce_class:
                    mock_workforce_class.return_value = mock_workforce
                    with patch("src.workforce.camel_integrated_workforce.NetworkAnalyzerAgent") as mock_net_agent:
                        mock_net_agent.return_value.agent = mock_chat_agent
                        with patch("src.workforce.camel_integrated_workforce.SocialMediaIntelligenceAgent") as mock_social_agent:
                            mock_social_agent.return_value.agent = mock_chat_agent
                            with patch("src.workforce.camel_integrated_workforce.DomainIntelligenceAgent") as mock_domain_agent:
                                mock_domain_agent.return_value.agent = mock_chat_agent
                                with patch("src.workforce.camel_integrated_workforce.DataBreachIntelligenceAgent") as mock_breach_agent:
                                    mock_breach_agent.return_value.agent = mock_chat_agent
                                    workforce = PalentirCAMELWorkforce(
                                        description="Test Workforce",
                                        enable_mcp=False,
                                        share_memory=True,
                                    )
                                    return workforce

    def test_initialization(self, workforce, mock_workforce):
        """Test workforce initialization."""
        assert workforce is not None
        assert hasattr(workforce, "workforce")
        assert hasattr(workforce, "agents")
        assert workforce.workforce == mock_workforce

    def test_list_agents(self, workforce):
        """Test list_agents."""
        agents = workforce.list_agents()
        assert isinstance(agents, list)

    def test_get_workforce_info(self, workforce):
        """Test get_workforce_info."""
        info = workforce.get_workforce_info()
        assert isinstance(info, dict)
        assert "description" in info
        assert "agents" in info
        assert "agent_count" in info

    @pytest.mark.asyncio
    async def test_process_task(self, workforce, mock_workforce):
        """Test process_task."""
        mock_workforce.process_task = AsyncMock(return_value={"status": "success", "result": "test"})
        
        result = await workforce.process_task("test query")
        
        assert isinstance(result, dict)
        assert "status" in result

    def test_to_mcp_server(self, workforce, mock_workforce):
        """Test to_mcp_server method."""
        mock_server = MagicMock()
        mock_workforce.to_mcp.return_value = mock_server
        
        server = workforce.to_mcp_server(port=8001, name="Test")
        
        mock_workforce.to_mcp.assert_called_once()
        assert server is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, workforce):
        """Test disconnect."""
        with patch.object(workforce, "mcp_toolkit", None):
            await workforce.disconnect()  # Should not raise


class TestWorkforceWithNeo4j:
    """Test workforce with Neo4j memory."""

    @pytest.fixture
    def mock_model(self):
        """Create mock model."""
        return MagicMock()

    @pytest.fixture
    def mock_chat_agent(self):
        """Create mock ChatAgent."""
        agent = MagicMock()
        agent.step = AsyncMock(return_value=MagicMock())
        agent.astep = AsyncMock(return_value=MagicMock())
        return agent

    @pytest.fixture
    def mock_workforce(self):
        """Create mock Workforce."""
        workforce = MagicMock()
        workforce.description = "Test Workforce"
        workforce.process_task = AsyncMock(return_value={"status": "success"})
        workforce.run = AsyncMock(return_value={"status": "success"})
        workforce.add_single_agent_worker = MagicMock()
        workforce.get_worker = MagicMock(return_value=None)
        workforce.to_mcp = MagicMock(return_value=MagicMock())
        return workforce

    @pytest.fixture
    def workforce_with_neo4j(self, mock_model, mock_chat_agent, mock_workforce):
        """Create workforce with Neo4j."""
        with patch("src.workforce.camel_integrated_workforce.ModelFactory") as mock_factory:
            mock_factory.create.return_value = mock_model
            with patch("src.workforce.camel_integrated_workforce.ChatAgent") as mock_agent_class:
                mock_agent_class.return_value = mock_chat_agent
                with patch("src.workforce.camel_integrated_workforce.Workforce") as mock_workforce_class:
                    mock_workforce_class.return_value = mock_workforce
                    with patch("src.workforce.camel_integrated_workforce.NetworkAnalyzerAgent") as mock_net_agent:
                        mock_net_agent.return_value.agent = mock_chat_agent
                        with patch("src.workforce.camel_integrated_workforce.SocialMediaIntelligenceAgent") as mock_social_agent:
                            mock_social_agent.return_value.agent = mock_chat_agent
                            with patch("src.workforce.camel_integrated_workforce.DomainIntelligenceAgent") as mock_domain_agent:
                                mock_domain_agent.return_value.agent = mock_chat_agent
                                with patch("src.workforce.camel_integrated_workforce.DataBreachIntelligenceAgent") as mock_breach_agent:
                                    mock_breach_agent.return_value.agent = mock_chat_agent
                                    with patch("src.workforce.camel_integrated_workforce.Neo4jGraph") as mock_neo4j:
                                        mock_neo4j.return_value = MagicMock()
                                        workforce = PalentirCAMELWorkforce(
                                            description="Test Workforce",
                                            neo4j_url="bolt://localhost:7687",
                                            neo4j_username="neo4j",
                                            neo4j_password="password",
                                        )
                                        return workforce

    def test_neo4j_initialization(self, workforce_with_neo4j):
        """Test Neo4j initialization."""
        assert workforce_with_neo4j is not None

