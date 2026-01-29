"""Unit tests for Palentir OSINT agents."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.graph_aware_agents import (
    GraphAwareAgent,
    IntelligenceEnhancerAgent,
    RelationshipBuilderAgent,
    GraphQueryAgent,
)


class TestGraphAwareAgent:
    """Test GraphAwareAgent base class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="You are a test agent",
        )
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_query_graph(self):
        """Test agent graph query."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="Test prompt",
        )
        results = await agent.query_graph("test query")
        assert isinstance(results, list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_get_node_context(self):
        """Test agent get node context."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="Test prompt",
        )
        context = await agent.get_node_context("node_123")
        assert isinstance(context, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_find_missing_connections(self):
        """Test agent find missing connections."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="Test prompt",
        )
        missing = await agent.find_missing_connections("node_123")
        assert isinstance(missing, list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_add_to_graph(self):
        """Test agent add to graph."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="Test prompt",
        )
        node_id = await agent.add_to_graph(
            node_type="Company",
            name="Test Company",
        )
        assert isinstance(node_id, str)
        assert len(node_id) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_create_relationship(self):
        """Test agent create relationship."""
        agent = GraphAwareAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="Test prompt",
        )
        success = await agent.create_relationship(
            source_id="node_1",
            target_id="node_2",
            rel_type="OWNS_DOMAIN",
        )
        assert isinstance(success, bool)


class TestIntelligenceEnhancerAgent:
    """Test IntelligenceEnhancerAgent."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = IntelligenceEnhancerAgent()
        assert agent.name == "IntelligenceEnhancerAgent"
        assert "intelligence" in agent.description.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_and_enhance(self):
        """Test analyze and enhance."""
        agent = IntelligenceEnhancerAgent()
        result = await agent.analyze_and_enhance("node_123")
        assert isinstance(result, dict)
        assert "node_id" in result
        assert "missing_connections" in result
        assert "suggested_tasks" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_and_enhance_with_missing_data(self):
        """Test analyze and enhance with missing data."""
        agent = IntelligenceEnhancerAgent()

        # Mock find_missing_connections to return data
        agent.find_missing_connections = AsyncMock(
            return_value=[
                {"type": "email", "reason": "No email found"},
                {"type": "phone", "reason": "No phone found"},
            ]
        )

        result = await agent.analyze_and_enhance("node_123")
        assert len(result["missing_connections"]) == 2
        assert len(result["suggested_tasks"]) == 2


class TestRelationshipBuilderAgent:
    """Test RelationshipBuilderAgent."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = RelationshipBuilderAgent()
        assert agent.name == "RelationshipBuilderAgent"
        assert "relationship" in agent.description.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_build_relationships(self):
        """Test build relationships."""
        agent = RelationshipBuilderAgent()

        # Mock create_relationship
        agent.create_relationship = AsyncMock(return_value=True)

        result = await agent.build_relationships(
            source_id="node_1",
            target_ids=["node_2", "node_3"],
            rel_type="OWNS_DOMAIN",
        )

        assert isinstance(result, dict)
        assert "source_id" in result
        assert "created_relationships" in result
        assert "failed_relationships" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_build_relationships_partial_failure(self):
        """Test build relationships with partial failure."""
        agent = RelationshipBuilderAgent()

        # Mock create_relationship to fail on second call
        agent.create_relationship = AsyncMock(
            side_effect=[True, False, True]
        )

        result = await agent.build_relationships(
            source_id="node_1",
            target_ids=["node_2", "node_3", "node_4"],
            rel_type="OWNS_DOMAIN",
        )

        assert len(result["created_relationships"]) == 2
        assert len(result["failed_relationships"]) == 1


class TestGraphQueryAgent:
    """Test GraphQueryAgent."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = GraphQueryAgent()
        assert agent.name == "GraphQueryAgent"
        # Check for "queries" or "query" in description
        assert "queries" in agent.description.lower() or "query" in agent.description.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_intelligence(self):
        """Test search intelligence."""
        agent = GraphQueryAgent()

        # Mock query_graph
        agent.query_graph = AsyncMock(
            return_value=[
                {"id": "node_1", "type": "Company", "name": "Test"},
                {"id": "node_2", "type": "Person", "name": "John"},
            ]
        )

        result = await agent.search_intelligence("test query")
        assert isinstance(result, dict)
        assert "query" in result
        assert "results" in result
        assert "count" in result
        assert "analysis" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_intelligence_no_results(self):
        """Test search intelligence with no results."""
        agent = GraphQueryAgent()

        # Mock query_graph to return empty
        agent.query_graph = AsyncMock(return_value=[])

        result = await agent.search_intelligence("nonexistent")
        assert result["count"] == 0
        # analysis is a dict with "summary" and "insights"
        assert "No results" in result["analysis"]["summary"] or "No results found" in result["analysis"]["summary"]

    @pytest.mark.unit
    def test_analyze_results(self):
        """Test analyze results."""
        agent = GraphQueryAgent()

        results = [
            {"id": "node_1", "type": "Company"},
            {"id": "node_2", "type": "Company"},
            {"id": "node_3", "type": "Person"},
        ]

        analysis = agent._analyze_results(results)
        assert "Found 3 entities" in analysis
        assert "Company" in analysis
        assert "Person" in analysis

    @pytest.mark.unit
    def test_analyze_results_empty(self):
        """Test analyze results with empty list."""
        agent = GraphQueryAgent()

        analysis = agent._analyze_results([])
        assert "No results" in analysis


@pytest.mark.agent
class TestAgentIntegration:
    """Integration tests for agents."""

    @pytest.mark.asyncio
    async def test_agent_workflow(self):
        """Test complete agent workflow."""
        enhancer = IntelligenceEnhancerAgent()
        builder = RelationshipBuilderAgent()
        query = GraphQueryAgent()

        # Mock methods
        enhancer.find_missing_connections = AsyncMock(
            return_value=[{"type": "email"}]
        )
        builder.create_relationship = AsyncMock(return_value=True)
        query.query_graph = AsyncMock(return_value=[{"id": "node_1"}])

        # Run workflow
        analysis = await enhancer.analyze_and_enhance("node_123")
        assert len(analysis["missing_connections"]) > 0

        relationships = await builder.build_relationships(
            source_id="node_1",
            target_ids=["node_2"],
            rel_type="OWNS_DOMAIN",
        )
        assert len(relationships["created_relationships"]) > 0

        intelligence = await query.search_intelligence("test")
        assert intelligence["count"] > 0

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling."""
        agent = IntelligenceEnhancerAgent()

        # Mock with exception - should propagate
        agent.find_missing_connections = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Exception should propagate since method doesn't catch it
        with pytest.raises(Exception, match="Database error"):
            await agent.analyze_and_enhance("node_123")
