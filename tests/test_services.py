"""Unit tests for Palentir OSINT services."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.graph_visualization import (
    GraphNode,
    GraphRelationship,
    GraphVisualizationService,
)


class TestGraphNode:
    """Test GraphNode class."""

    @pytest.mark.unit
    def test_graph_node_creation(self):
        """Test creating a GraphNode."""
        node = GraphNode(
            node_id="node_123",
            label="Test Company",
            name="Test Company Inc.",
            node_type="Company",
            icon="building",
            description="A test company",
        )
        assert node.node_id == "node_123"
        assert node.label == "Test Company"
        assert node.name == "Test Company Inc."
        assert node.node_type == "Company"
        assert node.icon == "building"

    @pytest.mark.unit
    def test_graph_node_to_dict(self):
        """Test converting GraphNode to dictionary."""
        node = GraphNode(
            node_id="node_123",
            label="Test",
            name="Test Node",
            node_type="Company",
        )
        node_dict = node.to_dict()
        assert node_dict["id"] == "node_123"
        assert node_dict["label"] == "Test"
        assert node_dict["name"] == "Test Node"
        assert node_dict["type"] == "Company"
        assert "created_at" in node_dict
        assert "neighbours" in node_dict

    @pytest.mark.unit
    def test_graph_node_with_metadata(self):
        """Test GraphNode with metadata."""
        metadata = {"industry": "Technology", "country": "USA"}
        node = GraphNode(
            node_id="node_123",
            label="Test",
            name="Test Node",
            node_type="Company",
            metadata=metadata,
        )
        assert node.metadata == metadata

    @pytest.mark.unit
    def test_graph_node_agent_maker(self):
        """Test GraphNode agent maker tracking."""
        node = GraphNode(
            node_id="node_123",
            label="Test",
            name="Test Node",
            node_type="Company",
            agent_maker="NetworkAnalyzerAgent",
        )
        assert node.agent_maker == "NetworkAnalyzerAgent"


class TestGraphRelationship:
    """Test GraphRelationship class."""

    @pytest.mark.unit
    def test_graph_relationship_creation(self):
        """Test creating a GraphRelationship."""
        rel = GraphRelationship(
            rel_id="rel_123",
            source_id="node_1",
            target_id="node_2",
            rel_type="OWNS_DOMAIN",
            strength=0.95,
        )
        assert rel.rel_id == "rel_123"
        assert rel.source_id == "node_1"
        assert rel.target_id == "node_2"
        assert rel.rel_type == "OWNS_DOMAIN"
        assert rel.strength == 0.95

    @pytest.mark.unit
    def test_graph_relationship_strength_clamping(self):
        """Test GraphRelationship strength clamping."""
        # Test strength > 1.0 is clamped
        rel = GraphRelationship(
            rel_id="rel_123",
            source_id="node_1",
            target_id="node_2",
            rel_type="OWNS_DOMAIN",
            strength=1.5,
        )
        assert rel.strength == 1.0

        # Test strength < 0.0 is clamped
        rel = GraphRelationship(
            rel_id="rel_123",
            source_id="node_1",
            target_id="node_2",
            rel_type="OWNS_DOMAIN",
            strength=-0.5,
        )
        assert rel.strength == 0.0

    @pytest.mark.unit
    def test_graph_relationship_to_dict(self):
        """Test converting GraphRelationship to dictionary."""
        rel = GraphRelationship(
            rel_id="rel_123",
            source_id="node_1",
            target_id="node_2",
            rel_type="OWNS_DOMAIN",
        )
        rel_dict = rel.to_dict()
        assert rel_dict["id"] == "rel_123"
        assert rel_dict["source"] == "node_1"
        assert rel_dict["target"] == "node_2"
        assert rel_dict["type"] == "OWNS_DOMAIN"
        assert "created_at" in rel_dict


class TestGraphVisualizationService:
    """Test GraphVisualizationService class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_neo4j_service):
        """Test service initialization."""
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)
        assert service.neo4j == mock_neo4j_service
        assert service.nodes == {}
        assert service.relationships == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_icon_for_type(self, mock_neo4j_service):
        """Test icon mapping."""
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)
        assert service._get_icon_for_type("Company") == "building"
        assert service._get_icon_for_type("Person") == "user"
        assert service._get_icon_for_type("Domain") == "globe"
        assert service._get_icon_for_type("IPAddress") == "network"
        assert service._get_icon_for_type("Unknown") == "circle"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_color_for_type(self, mock_neo4j_service):
        """Test color mapping."""
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)
        assert service._get_color_for_type("Company") == "#FF6B6B"
        assert service._get_color_for_type("Person") == "#4ECDC4"
        assert service._get_color_for_type("Domain") == "#45B7D1"
        assert service._get_color_for_type("Unknown") == "#95A5A6"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_graphistry_data_empty(self, mock_neo4j_service):
        """Test getting Graphistry data with no results."""
        mock_neo4j_service.execute_query = AsyncMock(return_value=[])
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        data = await service.get_graphistry_data()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert "stats" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_graphistry_data_with_query(self, mock_neo4j_service):
        """Test getting Graphistry data with search query."""
        mock_neo4j_service.execute_query = AsyncMock(
            return_value=[
                {
                    "n": {
                        "id": "node_123",
                        "name": "Test Company",
                        "type": "Company",
                    }
                }
            ]
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        data = await service.get_graphistry_data(query="test")
        assert len(data["nodes"]) > 0
        assert data["nodes"][0]["id"] == "node_123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_node_details(self, mock_neo4j_service):
        """Test getting node details."""
        mock_neo4j_service.execute_query = AsyncMock(
            return_value=[
                {
                    "node": {"id": "node_123", "name": "Test"},
                    "neighbours": [{"neighbor": {"id": "node_456"}}],
                }
            ]
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        details = await service.get_node_details("node_123")
        assert details["node"]["id"] == "node_123"
        assert len(details["neighbours"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_relationship_path(self, mock_neo4j_service):
        """Test getting relationship path."""
        mock_neo4j_service.execute_query = AsyncMock(
            return_value=[{"path": "test_path", "path_length": 2}]
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        path = await service.get_relationship_path("node_1", "node_2")
        assert path["path"] == "test_path"
        assert path["path_length"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_graph_by_type(self, mock_neo4j_service):
        """Test filtering graph by node type."""
        mock_neo4j_service.execute_query = AsyncMock(
            return_value=[{"id": "node_123", "type": "Company"}]
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        result = await service.filter_graph(node_types=["Company"])
        assert result["count"] > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_graph_by_agent_maker(self, mock_neo4j_service):
        """Test filtering graph by agent maker."""
        mock_neo4j_service.execute_query = AsyncMock(
            return_value=[{"id": "node_123", "agent_maker": "NetworkAnalyzerAgent"}]
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        result = await service.filter_graph(agent_maker="NetworkAnalyzerAgent")
        assert result["count"] > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_graph_error_handling(self, mock_neo4j_service):
        """Test filter graph error handling."""
        mock_neo4j_service.execute_query = AsyncMock(
            side_effect=Exception("Database error")
        )
        service = GraphVisualizationService(neo4j_service=mock_neo4j_service)

        result = await service.filter_graph()
        assert result["nodes"] == []
        assert result["count"] == 0
