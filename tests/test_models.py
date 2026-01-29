"""Unit tests for Palentir OSINT models."""

import pytest
from datetime import datetime

from src.models.metadata import (
    NodeType,
    RelationType,
    Neighbour,
    NodeMetadata,
    RelationshipMetadata,
    GraphSnapshot,
    GraphDiff,
    NodeFilter,
    RelationshipFilter,
)


class TestNodeType:
    """Test NodeType enum."""

    @pytest.mark.unit
    def test_node_type_values(self):
        """Test NodeType enum values."""
        assert NodeType.COMPANY.value == "Company"
        assert NodeType.PERSON.value == "Person"
        assert NodeType.DOMAIN.value == "Domain"
        assert NodeType.IP_ADDRESS.value == "IPAddress"
        assert NodeType.TECHNOLOGY.value == "Technology"

    @pytest.mark.unit
    def test_node_type_count(self):
        """Test NodeType has all expected types."""
        expected_types = [
            "COMPANY",
            "PERSON",
            "DOMAIN",
            "IP_ADDRESS",
            "EMAIL",
            "PHONE",
            "TECHNOLOGY",
            "SOCIAL_PROFILE",
            "DOCUMENT",
            "LOCATION",
            "ORGANIZATION",
            "RELATIONSHIP",
        ]
        actual_types = [member.name for member in NodeType]
        assert len(actual_types) == len(expected_types)


class TestRelationType:
    """Test RelationType enum."""

    @pytest.mark.unit
    def test_relation_type_values(self):
        """Test RelationType enum values."""
        assert RelationType.OWNS_DOMAIN.value == "OWNS_DOMAIN"
        assert RelationType.WORKS_AT.value == "WORKS_AT"
        assert RelationType.USES_TECHNOLOGY.value == "USES_TECHNOLOGY"

    @pytest.mark.unit
    def test_relation_type_count(self):
        """Test RelationType has all expected types."""
        expected_count = 15
        actual_count = len([member for member in RelationType])
        assert actual_count == expected_count


class TestNeighbour:
    """Test Neighbour model."""

    @pytest.mark.unit
    def test_neighbour_creation(self):
        """Test creating a Neighbour."""
        neighbour = Neighbour(
            id="node_123",
            type=NodeType.COMPANY,
            relation=RelationType.OWNS_DOMAIN,
            strength=0.95,
        )
        assert neighbour.id == "node_123"
        assert neighbour.type == NodeType.COMPANY
        assert neighbour.relation == RelationType.OWNS_DOMAIN
        assert neighbour.strength == 0.95

    @pytest.mark.unit
    def test_neighbour_strength_validation(self):
        """Test Neighbour strength validation."""
        # Valid strength
        neighbour = Neighbour(
            id="node_123",
            type=NodeType.COMPANY,
            relation=RelationType.OWNS_DOMAIN,
            strength=0.5,
        )
        assert neighbour.strength == 0.5

        # Strength should be clamped to [0, 1]
        with pytest.raises(ValueError):
            Neighbour(
                id="node_123",
                type=NodeType.COMPANY,
                relation=RelationType.OWNS_DOMAIN,
                strength=1.5,
            )

    @pytest.mark.unit
    def test_neighbour_metadata(self):
        """Test Neighbour with metadata."""
        metadata = {"confidence": 0.9, "source": "Shodan"}
        neighbour = Neighbour(
            id="node_123",
            type=NodeType.COMPANY,
            relation=RelationType.OWNS_DOMAIN,
            metadata=metadata,
        )
        assert neighbour.metadata == metadata


class TestNodeMetadata:
    """Test NodeMetadata model."""

    @pytest.mark.unit
    def test_node_metadata_creation(self, sample_company_data):
        """Test creating NodeMetadata."""
        node = NodeMetadata(
            id="node_123",
            name="Test Company",
            type=NodeType.COMPANY,
            description="A test company",
        )
        assert node.id == "node_123"
        assert node.name == "Test Company"
        assert node.type == NodeType.COMPANY
        assert node.description == "A test company"

    @pytest.mark.unit
    def test_node_metadata_defaults(self):
        """Test NodeMetadata default values."""
        node = NodeMetadata(
            id="node_123",
            name="Test Node",
            type=NodeType.PERSON,
        )
        assert node.icon == "circle"
        assert node.confidence == 1.0
        assert node.sources == []
        assert node.tags == []
        assert node.neighbours == []
        assert node.agent_maker is None

    @pytest.mark.unit
    def test_node_metadata_with_neighbours(self):
        """Test NodeMetadata with neighbours."""
        neighbour = Neighbour(
            id="node_456",
            type=NodeType.DOMAIN,
            relation=RelationType.OWNS_DOMAIN,
        )
        node = NodeMetadata(
            id="node_123",
            name="Test Company",
            type=NodeType.COMPANY,
            neighbours=[neighbour],
        )
        assert len(node.neighbours) == 1
        assert node.neighbours[0].id == "node_456"

    @pytest.mark.unit
    def test_node_metadata_confidence_validation(self):
        """Test NodeMetadata confidence validation."""
        node = NodeMetadata(
            id="node_123",
            name="Test",
            type=NodeType.COMPANY,
            confidence=0.95,
        )
        assert node.confidence == 0.95

        with pytest.raises(ValueError):
            NodeMetadata(
                id="node_123",
                name="Test",
                type=NodeType.COMPANY,
                confidence=1.5,
            )

    @pytest.mark.unit
    def test_node_metadata_timestamps(self):
        """Test NodeMetadata timestamps."""
        node = NodeMetadata(
            id="node_123",
            name="Test",
            type=NodeType.COMPANY,
        )
        assert node.created_at is not None
        assert node.last_updated is not None
        # Timestamps should be ISO format
        datetime.fromisoformat(node.created_at)
        datetime.fromisoformat(node.last_updated)


class TestRelationshipMetadata:
    """Test RelationshipMetadata model."""

    @pytest.mark.unit
    def test_relationship_metadata_creation(self):
        """Test creating RelationshipMetadata."""
        rel = RelationshipMetadata(
            id="rel_123",
            source_id="node_1",
            target_id="node_2",
            type=RelationType.OWNS_DOMAIN,
        )
        assert rel.id == "rel_123"
        assert rel.source_id == "node_1"
        assert rel.target_id == "node_2"
        assert rel.type == RelationType.OWNS_DOMAIN

    @pytest.mark.unit
    def test_relationship_metadata_defaults(self):
        """Test RelationshipMetadata default values."""
        rel = RelationshipMetadata(
            id="rel_123",
            source_id="node_1",
            target_id="node_2",
            type=RelationType.WORKS_AT,
        )
        assert rel.strength == 1.0
        assert rel.confidence == 1.0
        assert rel.evidence == []
        assert rel.sources == []
        assert rel.created_by is None

    @pytest.mark.unit
    def test_relationship_metadata_strength_validation(self):
        """Test RelationshipMetadata strength validation."""
        rel = RelationshipMetadata(
            id="rel_123",
            source_id="node_1",
            target_id="node_2",
            type=RelationType.WORKS_AT,
            strength=0.8,
        )
        assert rel.strength == 0.8

    @pytest.mark.unit
    def test_relationship_metadata_with_evidence(self):
        """Test RelationshipMetadata with evidence."""
        evidence = ["DNS records", "WHOIS lookup"]
        rel = RelationshipMetadata(
            id="rel_123",
            source_id="node_1",
            target_id="node_2",
            type=RelationType.OWNS_DOMAIN,
            evidence=evidence,
        )
        assert rel.evidence == evidence


class TestGraphSnapshot:
    """Test GraphSnapshot model."""

    @pytest.mark.unit
    def test_graph_snapshot_creation(self):
        """Test creating GraphSnapshot."""
        node = NodeMetadata(
            id="node_123",
            name="Test",
            type=NodeType.COMPANY,
        )
        snapshot = GraphSnapshot(
            snapshot_id="snap_123",
            nodes=[node],
        )
        assert snapshot.snapshot_id == "snap_123"
        assert len(snapshot.nodes) == 1
        assert snapshot.nodes[0].id == "node_123"

    @pytest.mark.unit
    def test_graph_snapshot_defaults(self):
        """Test GraphSnapshot default values."""
        snapshot = GraphSnapshot(snapshot_id="snap_123")
        assert snapshot.nodes == []
        assert snapshot.relationships == []
        assert snapshot.conversation_id is None
        assert snapshot.metadata == {}


class TestGraphDiff:
    """Test GraphDiff model."""

    @pytest.mark.unit
    def test_graph_diff_creation(self):
        """Test creating GraphDiff."""
        diff = GraphDiff(
            from_snapshot_id="snap_1",
            to_snapshot_id="snap_2",
        )
        assert diff.from_snapshot_id == "snap_1"
        assert diff.to_snapshot_id == "snap_2"

    @pytest.mark.unit
    def test_graph_diff_defaults(self):
        """Test GraphDiff default values."""
        diff = GraphDiff(
            from_snapshot_id="snap_1",
            to_snapshot_id="snap_2",
        )
        assert diff.added_nodes == []
        assert diff.removed_nodes == []
        assert diff.added_relationships == []
        assert diff.removed_relationships == []
        assert diff.modified_nodes == []


class TestNodeFilter:
    """Test NodeFilter model."""

    @pytest.mark.unit
    def test_node_filter_creation(self):
        """Test creating NodeFilter."""
        filter_obj = NodeFilter(
            node_types=[NodeType.COMPANY, NodeType.PERSON],
            agent_maker="TestAgent",
        )
        assert filter_obj.node_types == [NodeType.COMPANY, NodeType.PERSON]
        assert filter_obj.agent_maker == "TestAgent"

    @pytest.mark.unit
    def test_node_filter_defaults(self):
        """Test NodeFilter default values."""
        filter_obj = NodeFilter()
        assert filter_obj.node_types is None
        assert filter_obj.agent_maker is None
        assert filter_obj.min_confidence == 0.0
        assert filter_obj.search_text is None

    @pytest.mark.unit
    def test_node_filter_with_tags(self):
        """Test NodeFilter with tags."""
        filter_obj = NodeFilter(tags=["tech", "fortune500"])
        assert filter_obj.tags == ["tech", "fortune500"]


class TestRelationshipFilter:
    """Test RelationshipFilter model."""

    @pytest.mark.unit
    def test_relationship_filter_creation(self):
        """Test creating RelationshipFilter."""
        filter_obj = RelationshipFilter(
            relation_types=[RelationType.OWNS_DOMAIN, RelationType.WORKS_AT],
            min_strength=0.8,
        )
        assert filter_obj.relation_types == [
            RelationType.OWNS_DOMAIN,
            RelationType.WORKS_AT,
        ]
        assert filter_obj.min_strength == 0.8

    @pytest.mark.unit
    def test_relationship_filter_defaults(self):
        """Test RelationshipFilter default values."""
        filter_obj = RelationshipFilter()
        assert filter_obj.relation_types is None
        assert filter_obj.min_strength == 0.0
        # RelationshipFilter doesn't have min_confidence, only min_strength
        assert filter_obj.properties is None
