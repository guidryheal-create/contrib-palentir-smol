"""Unit tests for frontend components."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import streamlit as st

from src.models.graph_nodes import (
    GraphNode,
    GraphEdge,
    NodeType,
    PersonNodeMetadata,
    CompanyNodeMetadata,
    EdgeMetadata,
    RelationType,
)
from src.services.graph_visualization import GraphVisualizationService


class TestGraphVisualizationService:
    """Test GraphVisualizationService."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = GraphVisualizationService()
        assert service is not None
        assert isinstance(service, GraphVisualizationService)
        # Check it has neo4j attribute (may be None)
        assert hasattr(service, "neo4j")

    def test_get_nodes_empty(self):
        """Test getting nodes when graph is empty."""
        service = GraphVisualizationService()
        service.neo4j_service = Mock()
        service.neo4j_service.execute_query = AsyncMock(return_value=[])
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            nodes = loop.run_until_complete(service.get_nodes())
            assert nodes == []
        finally:
            loop.close()

    def test_get_relationships_empty(self):
        """Test getting relationships when graph is empty."""
        service = GraphVisualizationService()
        service.neo4j_service = Mock()
        service.neo4j_service.execute_query = AsyncMock(return_value=[])
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            relationships = loop.run_until_complete(service.get_relationships())
            assert relationships == []
        finally:
            loop.close()

    def test_get_graphistry_data(self):
        """Test getting graphistry data."""
        service = GraphVisualizationService()
        service.neo4j_service = Mock()
        service.neo4j_service.execute_query = AsyncMock(return_value=[])
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(service.get_graphistry_data())
            assert "nodes" in data
            assert "edges" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)
        finally:
            loop.close()


class TestGraphNodeModels:
    """Test graph node models."""

    def test_person_node_metadata_creation(self):
        """Test creating person node metadata."""
        metadata = PersonNodeMetadata(
            node_id="person_1",
            label="John Doe",
            title="John Doe",
            full_name="John Doe",
            email="john@example.com",
        )
        assert metadata.node_type == NodeType.PERSON
        assert metadata.full_name == "John Doe"
        assert metadata.email == "john@example.com"

    def test_company_node_metadata_creation(self):
        """Test creating company node metadata."""
        metadata = CompanyNodeMetadata(
            node_id="company_1",
            label="Tech Corp",
            title="Tech Corporation",
            company_name="Tech Corp",
            industry="Technology",
        )
        assert metadata.node_type == NodeType.COMPANY
        assert metadata.company_name == "Tech Corp"
        assert metadata.industry == "Technology"

    def test_graph_node_to_dict(self):
        """Test converting graph node to dictionary."""
        metadata = PersonNodeMetadata(
            node_id="person_1",
            label="John Doe",
            title="John Doe",
        )
        node = GraphNode(node_id="person_1", metadata=metadata)
        node_dict = node.to_dict()
        
        assert node_dict["id"] == "person_1"
        assert node_dict["label"] == "John Doe"
        assert node_dict["type"] == "person"

    def test_graph_edge_to_dict(self):
        """Test converting graph edge to dictionary."""
        edge_metadata = EdgeMetadata(
            edge_id="edge_1",
            source_id="person_1",
            target_id="company_1",
            label="Works At",
            relationship_type=RelationType.WORKS_AT,
            strength=0.9,
        )
        edge = GraphEdge(edge_id="edge_1", metadata=edge_metadata)
        edge_dict = edge.to_dict()
        
        assert edge_dict["id"] == "edge_1"
        assert edge_dict["source"] == "person_1"
        assert edge_dict["target"] == "company_1"
        assert edge_dict["label"] == "Works At"
        assert edge_dict["relationship_type"] == "works_at"


class TestFrontendComponents:
    """Test frontend components."""

    def test_app_initialization(self):
        """Test app initialization function exists and has correct signature."""
        # Just verify the function exists and can be imported
        from src.frontend.app import initialize_workforce, render_dashboard, render_chat_logs
        
        # Check functions exist and are callable
        assert callable(initialize_workforce)
        assert callable(render_dashboard)
        assert callable(render_chat_logs)
        
        # Verify function signature
        import inspect
        sig = inspect.signature(initialize_workforce)
        assert sig.return_annotation == "Optional[PalentirCAMELWorkforce]" or "Optional" in str(sig.return_annotation)

    def test_chat_message_structure(self):
        """Test chat message structure."""
        user_message = {
            "role": "user",
            "content": "Test query",
            "timestamp": datetime.now().isoformat(),
        }
        
        assert user_message["role"] == "user"
        assert "content" in user_message
        assert "timestamp" in user_message
        
        assistant_message = {
            "role": "assistant",
            "content": "Test response",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }
        
        assert assistant_message["role"] == "assistant"
        assert "status" in assistant_message

    def test_task_record_structure(self):
        """Test task record structure."""
        task_record = {
            "query": "Test query",
            "status": "success",
            "result": {"content": "Test result"},
            "timestamp": datetime.now().isoformat(),
            "duration": "1.23s",
            "agent": "workforce",
        }
        
        assert task_record["query"] == "Test query"
        assert task_record["status"] == "success"
        assert "duration" in task_record
        assert "timestamp" in task_record


class TestGraphDataProcessing:
    """Test graph data processing."""

    def test_node_type_counting(self):
        """Test counting nodes by type."""
        nodes = [
            {"type": "person", "id": "1"},
            {"type": "person", "id": "2"},
            {"type": "company", "id": "3"},
        ]
        
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        assert node_types["person"] == 2
        assert node_types["company"] == 1

    def test_edge_filtering(self):
        """Test filtering edges by source/target."""
        edges = [
            {"source": "1", "target": "2", "label": "related"},
            {"source": "2", "target": "3", "label": "related"},
            {"source": "1", "target": "3", "label": "related"},
        ]
        
        filtered = [e for e in edges if e["source"] == "1"]
        assert len(filtered) == 2
        
        filtered = [e for e in edges if e["target"] == "3"]
        assert len(filtered) == 2

    def test_graph_statistics(self):
        """Test calculating graph statistics."""
        nodes = [
            {"confidence": 0.8, "type": "person"},
            {"confidence": 0.9, "type": "person"},
            {"confidence": 0.7, "type": "company"},
        ]
        
        edges = [
            {"strength": 0.8, "confidence": 0.9},
            {"strength": 0.9, "confidence": 0.8},
        ]
        
        avg_node_confidence = sum(n["confidence"] for n in nodes) / len(nodes)
        avg_edge_strength = sum(e["strength"] for e in edges) / len(edges)
        
        assert abs(avg_node_confidence - 0.8) < 0.01
        assert abs(avg_edge_strength - 0.85) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

