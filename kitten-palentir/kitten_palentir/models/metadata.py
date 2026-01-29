"""Metadata models for graph nodes and relationships."""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, computed_field, field_validator


class NodeType(str, Enum):
    """Node type enumeration."""

    COMPANY = "Company"
    PERSON = "Person"
    DOMAIN = "Domain"
    IP_ADDRESS = "IPAddress"
    EMAIL = "Email"
    PHONE = "Phone"
    TECHNOLOGY = "Technology"
    SOCIAL_PROFILE = "SocialProfile"
    DOCUMENT = "Document"
    LOCATION = "Location"
    ORGANIZATION = "Organization"
    RELATIONSHIP = "Relationship"


class RelationType(str, Enum):
    """Relationship type enumeration."""

    OWNS = "owns"
    OWNS_DOMAIN = "OWNS_DOMAIN"
    WORKS_FOR = "works_for"
    WORKS_AT = "WORKS_AT"
    USES_TECHNOLOGY = "USES_TECHNOLOGY"
    MANAGES = "manages"
    LOCATED_IN = "located_in"
    HAS_EMAIL = "has_email"
    HAS_PHONE = "has_phone"
    HAS_SOCIAL = "has_social"
    REFERENCES = "references"
    RELATED_TO = "related_to"
    COMMUNICATES = "communicates"
    FOUNDED_BY = "founded_by"
    ACQUIRED_BY = "acquired_by"


class Neighbour(BaseModel):
    """Neighbour node information."""

    id: str  # Alias for node_id for test compatibility
    type: NodeType  # Node type
    relation: RelationType  # Relationship type
    strength: float = 0.5  # Relationship strength [0, 1]
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
    
    def __init__(self, **data):
        """Initialize with validation."""
        # Validate strength is in [0, 1] range
        if 'strength' in data:
            strength = float(data['strength'])
            if strength < 0.0 or strength > 1.0:
                raise ValueError(f"Strength must be between 0 and 1, got {strength}")
            data['strength'] = strength
        super().__init__(**data)
    
    # For backward compatibility
    @property
    def node_id(self) -> str:
        """Get node ID."""
        return self.id
    
    @property
    def relationship_type(self) -> str:
        """Get relationship type as string."""
        return self.relation.value
    
    @property
    def properties(self) -> Dict[str, Any]:
        """Get properties."""
        return self.metadata or {}


class NodeMetadata(BaseModel):
    """Node metadata."""

    node_id: str
    node_type: NodeType
    properties: Dict[str, Any] = {}
    neighbours: List[Neighbour] = []
    created_at_dt: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    icon: str = "circle"
    confidence: float = 1.0
    sources: List[str] = []
    tags: List[str] = []
    agent_maker: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize with compatibility for both field names."""
        # Handle both id/node_id and type/node_type for test compatibility
        if 'id' in data and 'node_id' not in data:
            data['node_id'] = data.pop('id')
        if 'type' in data and 'node_type' not in data:
            data['node_type'] = data.pop('type')
        if 'name' in data:
            # Store name in properties if provided
            if 'properties' not in data:
                data['properties'] = {}
            data['properties']['name'] = data.pop('name')
        
        # Handle created_at - store as created_at_dt internally
        if 'created_at' in data:
            data['created_at_dt'] = data.pop('created_at')
        
        # Set default created_at_dt if not provided
        if 'created_at_dt' not in data or data.get('created_at_dt') is None:
            data['created_at_dt'] = datetime.utcnow()
        
        # Validate confidence
        if 'confidence' in data:
            conf = float(data['confidence'])
            if conf < 0.0 or conf > 1.0:
                raise ValueError(f"Confidence must be between 0 and 1, got {conf}")
            data['confidence'] = conf
        
        super().__init__(**data)
    
    @property
    def id(self) -> str:
        """Get node ID (alias for node_id)."""
        return self.node_id
    
    @property
    def type(self) -> NodeType:
        """Get node type (alias for node_type)."""
        return self.node_type
    
    @property
    def name(self) -> str:
        """Get node name from properties."""
        return self.properties.get('name', '')
    
    @property
    def created_at(self) -> Optional[str]:
        """Get created_at as ISO string."""
        if self.created_at_dt is None:
            return None
        if isinstance(self.created_at_dt, datetime):
            return self.created_at_dt.isoformat()
        return str(self.created_at_dt)
    
    @property
    def last_updated(self) -> Optional[str]:
        """Get last_updated as ISO string."""
        dt = self.updated_at or self.created_at_dt
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)


class RelationshipMetadata(BaseModel):
    """Relationship metadata."""

    relationship_id: str
    relationship_type: RelationType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    strength: float = 1.0
    confidence: float = 1.0
    evidence: List[str] = []
    sources: List[str] = []
    created_by: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize with compatibility for field names."""
        # Handle id/relationship_id
        if 'id' in data and 'relationship_id' not in data:
            data['relationship_id'] = data.pop('id')
        # Handle type/relationship_type
        if 'type' in data and 'relationship_type' not in data:
            data['relationship_type'] = data.pop('type')
        # Handle source_id/source_node_id
        if 'source_id' in data and 'source_node_id' not in data:
            data['source_node_id'] = data.pop('source_id')
        # Handle target_id/target_node_id
        if 'target_id' in data and 'target_node_id' not in data:
            data['target_node_id'] = data.pop('target_id')
        
        # Validate strength
        if 'strength' in data:
            strength = float(data['strength'])
            data['strength'] = max(0.0, min(1.0, strength))
        
        super().__init__(**data)
    
    @property
    def id(self) -> str:
        """Get relationship ID."""
        return self.relationship_id
    
    @property
    def type(self) -> RelationType:
        """Get relationship type."""
        return self.relationship_type
    
    @property
    def source_id(self) -> str:
        """Get source node ID."""
        return self.source_node_id
    
    @property
    def target_id(self) -> str:
        """Get target node ID."""
        return self.target_node_id


class GraphSnapshot(BaseModel):
    """Graph snapshot."""

    snapshot_id: str
    timestamp: Optional[datetime] = None
    nodes: List[NodeMetadata] = []
    relationships: List[RelationshipMetadata] = []
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """Initialize with default timestamp."""
        if 'timestamp' not in data:
            from datetime import datetime
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class GraphDiff(BaseModel):
    """Graph diff."""

    from_snapshot_id: Optional[str] = None
    to_snapshot_id: Optional[str] = None
    added_nodes: List[NodeMetadata] = []
    removed_nodes: List[str] = []
    modified_nodes: List[NodeMetadata] = []
    added_relationships: List[RelationshipMetadata] = []
    removed_relationships: List[str] = []
    modified_relationships: List[RelationshipMetadata] = []


class NodeFilter(BaseModel):
    """Node filter."""

    node_types: Optional[List[NodeType]] = None
    properties: Optional[Dict[str, Any]] = None
    agent_maker: Optional[str] = None
    tags: Optional[List[str]] = None
    min_confidence: float = 0.0
    search_text: Optional[str] = None


class RelationshipFilter(BaseModel):
    """Relationship filter."""

    relationship_types: Optional[List[RelationType]] = None
    properties: Optional[Dict[str, Any]] = None
    min_strength: float = 0.0
    
    def __init__(self, **data):
        """Initialize with compatibility for relation_types."""
        # Handle relation_types/relationship_types
        if 'relation_types' in data and 'relationship_types' not in data:
            data['relationship_types'] = data.pop('relation_types')
        super().__init__(**data)
    
    @property
    def relation_types(self) -> Optional[List[RelationType]]:
        """Alias for relationship_types."""
        return self.relationship_types

