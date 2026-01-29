"""
Test CAMEL-AI integrated agents and workforce.

Tests verify that agents are properly connected to their toolkits
using CAMEL-AI native methods.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.camel_integrated_agents import (
    NetworkAnalyzerAgent,
    SocialMediaIntelligenceAgent,
    DomainIntelligenceAgent,
    DataBreachIntelligenceAgent,
    get_agent,
    list_available_agents,
)
from src.workforce.camel_integrated_workforce import (
    PalentirCAMELWorkforce,
    create_workforce,
)


@pytest.mark.asyncio
class TestCAMELIntegratedAgents:
    """Test CAMEL-AI integrated agents."""

    @pytest.mark.skipif(
        not os.getenv("CENSYS_API_ID") or not os.getenv("CENSYS_SECRET") or not os.getenv("LIFERAFT_API_KEY"),
        reason="Missing Censys or Liferaft API credentials - test requires API keys"
    )
    def test_network_analyzer_agent_initialization(self):
        """Test NetworkAnalyzerAgent initialization with tools."""
        agent = NetworkAnalyzerAgent()
        
        assert agent is not None
        assert agent.agent is not None
        assert agent.model is not None
        assert agent.censys_toolkit is not None
        assert agent.liferaft_toolkit is not None

    def test_network_analyzer_agent_has_tools(self):
        """Test that NetworkAnalyzerAgent has tools."""
        agent = NetworkAnalyzerAgent()
        tools = agent.get_tools()
        
        # Tools should be available
        assert isinstance(tools, list)

    @pytest.mark.skipif(
        not os.getenv("SOCIAL_LINKS_API_KEY"),
        reason="Missing Social Links API key - test requires API key"
    )
    def test_social_media_agent_initialization(self):
        """Test SocialMediaIntelligenceAgent initialization with tools."""
        agent = SocialMediaIntelligenceAgent()
        
        assert agent is not None
        assert agent.agent is not None
        assert agent.model is not None
        assert agent.social_media_toolkit is not None
        assert agent.social_links_toolkit is not None

    def test_social_media_agent_has_tools(self):
        """Test that SocialMediaIntelligenceAgent has tools."""
        agent = SocialMediaIntelligenceAgent()
        tools = agent.get_tools()
        
        # Tools should be available
        assert isinstance(tools, list)

    @pytest.mark.skipif(
        not os.getenv("MALTEGO_API_KEY") or not os.getenv("CENSYS_API_ID") or not os.getenv("CENSYS_SECRET"),
        reason="Missing Maltego or Censys API credentials - test requires API keys"
    )
    def test_domain_intelligence_agent_initialization(self):
        """Test DomainIntelligenceAgent initialization with tools."""
        agent = DomainIntelligenceAgent()
        
        assert agent is not None
        assert agent.agent is not None
        assert agent.model is not None
        assert agent.maltego_toolkit is not None
        assert agent.censys_toolkit is not None

    def test_domain_intelligence_agent_has_tools(self):
        """Test that DomainIntelligenceAgent has tools."""
        agent = DomainIntelligenceAgent()
        tools = agent.get_tools()
        
        # Tools should be available
        assert isinstance(tools, list)

    @pytest.mark.skipif(
        not os.getenv("LIFERAFT_API_KEY"),
        reason="Missing Liferaft API key - test requires API key"
    )
    def test_data_breach_agent_initialization(self):
        """Test DataBreachIntelligenceAgent initialization with tools."""
        agent = DataBreachIntelligenceAgent()
        
        assert agent is not None
        assert agent.agent is not None
        assert agent.model is not None
        assert agent.liferaft_toolkit is not None

    def test_data_breach_agent_has_tools(self):
        """Test that DataBreachIntelligenceAgent has tools."""
        agent = DataBreachIntelligenceAgent()
        tools = agent.get_tools()
        
        # Tools should be available
        assert isinstance(tools, list)

    async def test_network_analyzer_agent_analyze_network(self):
        """Test NetworkAnalyzerAgent analyze_network method."""
        agent = NetworkAnalyzerAgent()
        
        # Mock the agent's astep method
        agent.agent.astep = AsyncMock(
            return_value=MagicMock(
                msgs=[MagicMock(content="Network analysis result")],
                info={"tool_calls": []},
            )
        )
        
        result = await agent.analyze_network("Analyze network 192.168.1.0/24")
        
        assert result["status"] == "success"
        assert "response" in result

    async def test_social_media_agent_search_profiles(self):
        """Test SocialMediaIntelligenceAgent search_social_profiles method."""
        agent = SocialMediaIntelligenceAgent()
        
        # Mock the agent's astep method
        agent.agent.astep = AsyncMock(
            return_value=MagicMock(
                msgs=[MagicMock(content="Social profile search result")],
                info={"tool_calls": []},
            )
        )
        
        result = await agent.search_social_profiles("Find John Doe on LinkedIn")
        
        assert result["status"] == "success"
        assert "response" in result

    async def test_domain_intelligence_agent_analyze_domain(self):
        """Test DomainIntelligenceAgent analyze_domain method."""
        agent = DomainIntelligenceAgent()
        
        # Mock the agent's astep method
        agent.agent.astep = AsyncMock(
            return_value=MagicMock(
                msgs=[MagicMock(content="Domain analysis result")],
                info={"tool_calls": []},
            )
        )
        
        result = await agent.analyze_domain("Analyze example.com")
        
        assert result["status"] == "success"
        assert "response" in result

    async def test_data_breach_agent_search_breaches(self):
        """Test DataBreachIntelligenceAgent search_breaches method."""
        agent = DataBreachIntelligenceAgent()
        
        # Mock the agent's astep method
        agent.agent.astep = AsyncMock(
            return_value=MagicMock(
                msgs=[MagicMock(content="Breach search result")],
                info={"tool_calls": []},
            )
        )
        
        result = await agent.search_breaches("Search breaches for john@example.com")
        
        assert result["status"] == "success"
        assert "response" in result

    def test_get_agent_by_name(self):
        """Test getting agent by name."""
        agent = get_agent("network_analyzer")
        
        assert agent is not None
        assert isinstance(agent, NetworkAnalyzerAgent)

    def test_get_agent_invalid_name(self):
        """Test getting agent with invalid name."""
        agent = get_agent("invalid_agent")
        
        assert agent is None

    def test_list_available_agents(self):
        """Test listing available agents."""
        agents = list_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert "network_analyzer" in agents
        assert "social_media_intelligence" in agents
        assert "domain_intelligence" in agents
        assert "data_breach_intelligence" in agents


@pytest.mark.asyncio
class TestCAMELIntegratedWorkforce:
    """Test CAMEL-AI integrated workforce."""

    def test_workforce_initialization(self):
        """Test workforce initialization."""
        workforce = PalentirCAMELWorkforce()
        
        assert workforce is not None
        assert workforce.workforce is not None
        assert len(workforce.agents) > 0

    def test_workforce_has_all_agents(self):
        """Test that workforce has all agents."""
        workforce = PalentirCAMELWorkforce()
        agents = workforce.list_agents()
        
        assert "network_analyzer" in agents
        assert "social_media_intelligence" in agents
        assert "domain_intelligence" in agents
        assert "data_breach_intelligence" in agents

    def test_workforce_get_agent(self):
        """Test getting agent from workforce."""
        workforce = PalentirCAMELWorkforce()
        agent = workforce.get_agent("network_analyzer")
        
        assert agent is not None
        assert isinstance(agent, NetworkAnalyzerAgent)

    def test_workforce_get_agent_tools(self):
        """Test getting agent tools from workforce."""
        workforce = PalentirCAMELWorkforce()
        tools = workforce.get_agent_tools("network_analyzer")
        
        assert isinstance(tools, list)

    def test_workforce_info(self):
        """Test getting workforce information."""
        workforce = PalentirCAMELWorkforce()
        info = workforce.get_workforce_info()
        
        assert "description" in info
        assert "agents" in info
        assert "agent_count" in info
        assert info["agent_count"] > 0

    async def test_workforce_process_task_with_agent(self):
        """Test workforce processing task with specific agent."""
        workforce = PalentirCAMELWorkforce()
        
        # Mock the agent's analyze_network method
        network_agent = workforce.get_agent("network_analyzer")
        network_agent.analyze_network = AsyncMock(
            return_value={"status": "success", "response": "Result"}
        )
        
        result = await workforce.process_task(
            "Analyze network",
            agent_name="network_analyzer",
        )
        
        assert result["status"] == "success"

    async def test_workforce_disconnect(self):
        """Test workforce disconnect."""
        workforce = PalentirCAMELWorkforce()
        
        # Should not raise any errors
        await workforce.disconnect()


@pytest.mark.asyncio
class TestWorkforceCreation:
    """Test workforce creation."""

    async def test_create_workforce(self):
        """Test creating workforce using factory function."""
        workforce = await create_workforce()
        
        assert workforce is not None
        assert isinstance(workforce, PalentirCAMELWorkforce)
        assert len(workforce.agents) > 0

    async def test_create_workforce_with_description(self):
        """Test creating workforce with custom description."""
        description = "Custom OSINT Workforce"
        workforce = await create_workforce(description=description)
        
        assert workforce is not None
        info = workforce.get_workforce_info()
        assert info["description"] == description


@pytest.mark.asyncio
class TestAgentToolkitIntegration:
    """Test agent toolkit integration."""

    @pytest.mark.skipif(
        not os.getenv("CENSYS_API_ID") or not os.getenv("CENSYS_SECRET"),
        reason="Missing Censys API credentials - test requires API keys"
    )
    def test_network_analyzer_has_censys_toolkit(self):
        """Test that NetworkAnalyzerAgent has Censys toolkit."""
        agent = NetworkAnalyzerAgent()
        
        assert agent.censys_toolkit is not None
        assert hasattr(agent.censys_toolkit, "get_tools")

    @pytest.mark.skipif(
        not os.getenv("LIFERAFT_API_KEY"),
        reason="Missing Liferaft API key - test requires API key"
    )
    def test_network_analyzer_has_liferaft_toolkit(self):
        """Test that NetworkAnalyzerAgent has Liferaft toolkit."""
        agent = NetworkAnalyzerAgent()
        
        assert agent.liferaft_toolkit is not None
        assert hasattr(agent.liferaft_toolkit, "get_tools")

    def test_social_media_has_social_media_toolkit(self):
        """Test that SocialMediaIntelligenceAgent has social media toolkit."""
        agent = SocialMediaIntelligenceAgent()
        
        assert agent.social_media_toolkit is not None
        assert hasattr(agent.social_media_toolkit, "get_tools")

    @pytest.mark.skipif(
        not os.getenv("SOCIAL_LINKS_API_KEY"),
        reason="Missing Social Links API key - test requires API key"
    )
    def test_social_media_has_social_links_toolkit(self):
        """Test that SocialMediaIntelligenceAgent has social links toolkit."""
        agent = SocialMediaIntelligenceAgent()
        
        assert agent.social_links_toolkit is not None
        assert hasattr(agent.social_links_toolkit, "get_tools")

    @pytest.mark.skipif(
        not os.getenv("MALTEGO_API_KEY"),
        reason="Missing Maltego API key - test requires API key"
    )
    def test_domain_intelligence_has_maltego_toolkit(self):
        """Test that DomainIntelligenceAgent has Maltego toolkit."""
        agent = DomainIntelligenceAgent()
        
        assert agent.maltego_toolkit is not None
        assert hasattr(agent.maltego_toolkit, "get_tools")

    @pytest.mark.skipif(
        not os.getenv("CENSYS_API_ID") or not os.getenv("CENSYS_SECRET"),
        reason="Missing Censys API credentials - test requires API keys"
    )
    def test_domain_intelligence_has_censys_toolkit(self):
        """Test that DomainIntelligenceAgent has Censys toolkit."""
        agent = DomainIntelligenceAgent()
        
        assert agent.censys_toolkit is not None
        assert hasattr(agent.censys_toolkit, "get_tools")

    @pytest.mark.skipif(
        not os.getenv("LIFERAFT_API_KEY"),
        reason="Missing Liferaft API key - test requires API key"
    )
    def test_data_breach_has_liferaft_toolkit(self):
        """Test that DataBreachIntelligenceAgent has Liferaft toolkit."""
        agent = DataBreachIntelligenceAgent()
        
        assert agent.liferaft_toolkit is not None
        assert hasattr(agent.liferaft_toolkit, "get_tools")
