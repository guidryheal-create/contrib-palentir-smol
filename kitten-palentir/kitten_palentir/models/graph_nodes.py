"""Palentir OSINT - Rich Graph Node and Edge Models.

Data classes for Graphistry visualization with complete metadata.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Node types in the knowledge graph."""

    COMPANY = "company"
    PERSON = "person"
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    EMAIL = "email"
    PHONE = "phone"
    TECHNOLOGY = "technology"
    SOCIAL_PROFILE = "social_profile"
    DOCUMENT = "document"
    LOCATION = "location"
    ORGANIZATION = "organization"
    EVENT = "event"


class RelationType(str, Enum):
    """Relationship types in the knowledge graph."""

    OWNS = "owns"
    WORKS_AT = "works_at"
    MANAGES = "manages"
    USES = "uses"
    LOCATED_IN = "located_in"
    HAS_EMAIL = "has_email"
    HAS_PHONE = "has_phone"
    HAS_SOCIAL = "has_social"
    REFERENCES = "references"
    RELATED_TO = "related_to"
    COMMUNICATES = "communicates"
    FOUNDED_BY = "founded_by"
    ACQUIRED_BY = "acquired_by"
    CONNECTED_TO = "connected_to"


class NodeMetadata(BaseModel):
    """Rich metadata for graph nodes."""

    node_id: str
    node_type: NodeType
    label: str
    title: str
    description: Optional[str] = None
    icon: str = "circle"
    color: str = "#1f77b4"
    size: int = 30

    # Source information
    source: str = "unknown"
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Tracking
    agent_maker: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_verified: Optional[str] = None

    # Relationships
    neighbors: List[Dict[str, Any]] = Field(default_factory=list)
    relationship_count: int = 0

    # Additional data
    properties: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    # Sharing
    shareable_url: Optional[str] = None
    is_public: bool = False


class PersonNodeMetadata(NodeMetadata):
    """Metadata for person nodes."""

    node_type: NodeType = NodeType.PERSON

    # Person-specific fields
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    bio: Optional[str] = None

    # Social profiles
    linkedin_profile: Optional[str] = None
    twitter_profile: Optional[str] = None
    facebook_profile: Optional[str] = None
    instagram_profile: Optional[str] = None
    github_profile: Optional[str] = None

    # Metrics
    connections_count: int = 0
    followers_count: int = 0
    posts_count: int = 0


class CompanyNodeMetadata(NodeMetadata):
    """Metadata for company nodes."""

    node_type: NodeType = NodeType.COMPANY

    # Company-specific fields
    company_name: Optional[str] = None
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    revenue: Optional[str] = None

    # Social presence
    linkedin_company: Optional[str] = None
    facebook_page: Optional[str] = None
    twitter_account: Optional[str] = None
    instagram_account: Optional[str] = None

    # Metrics
    employees_discovered: int = 0
    domains_discovered: int = 0
    technologies_discovered: int = 0


class IPAddressNodeMetadata(NodeMetadata):
    """Metadata for IP address nodes."""

    node_type: NodeType = NodeType.IP_ADDRESS

    # IP-specific fields
    ip_address: str
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    asn: Optional[str] = None

    # Services
    open_ports: List[int] = Field(default_factory=list)
    services: List[Dict[str, str]] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    vulnerabilities: List[str] = Field(default_factory=list)

    # Hosting
    hosting_provider: Optional[str] = None
    is_vpn: bool = False
    is_proxy: bool = False
    is_datacenter: bool = False


class DomainNodeMetadata(NodeMetadata):
    """Metadata for domain nodes."""

    node_type: NodeType = NodeType.DOMAIN

    # Domain-specific fields
    domain_name: str
    registrar: Optional[str] = None
    registration_date: Optional[str] = None
    expiration_date: Optional[str] = None
    registrant: Optional[str] = None

    # DNS
    dns_records: Dict[str, List[str]] = Field(default_factory=dict)
    mx_records: List[str] = Field(default_factory=list)
    ns_records: List[str] = Field(default_factory=list)

    # SSL/TLS
    ssl_certificate: Optional[str] = None
    ssl_issuer: Optional[str] = None
    ssl_expiration: Optional[str] = None

    # Web
    website_title: Optional[str] = None
    website_description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class EdgeMetadata(BaseModel):
    """Rich metadata for graph edges."""

    edge_id: str
    source_id: str
    target_id: str
    label: str
    relationship_type: RelationType

    # Tracking
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Strength and confidence
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Source information
    source: str = "unknown"
    sources: List[str] = Field(default_factory=list)
    agent_maker: Optional[str] = None

    # Evidence
    evidence: Optional[str] = None
    evidence_count: int = 0

    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Visualization
    color: str = "#999"
    width: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Graphistry."""
        return {
            "id": self.edge_id,
            "label": self.label,
            "source": self.source_id,
            "target": self.target_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "confidence": self.confidence,
            "source_system": self.source,
            "agent_maker": self.agent_maker,
            "created_at": self.created_at,
            "properties": self.properties,
        }


class GraphNode(BaseModel):
    """Complete graph node with all metadata."""

    node_id: str
    metadata: NodeMetadata
    display_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Graphistry."""
        return {
            "id": self.node_id,
            "label": self.metadata.label,
            "title": self.metadata.title,
            "type": self.metadata.node_type.value,
            "description": self.metadata.description,
            "icon": self.metadata.icon,
            "color": self.metadata.color,
            "size": self.metadata.size,
            "source": self.metadata.source,
            "confidence": self.metadata.confidence,
            "agent_maker": self.metadata.agent_maker,
            "created_at": self.metadata.created_at,
            "updated_at": self.metadata.updated_at,
            "neighbors": self.metadata.neighbors,
            "properties": self.metadata.properties,
            "tags": self.metadata.tags,
        }

    def get_view_type(self) -> str:
        """Get the view type for this node."""
        if self.metadata.node_type == NodeType.PERSON:
            return "person_view"
        elif self.metadata.node_type == NodeType.COMPANY:
            return "company_view"
        elif self.metadata.node_type == NodeType.IP_ADDRESS:
            return "ip_view"
        elif self.metadata.node_type == NodeType.DOMAIN:
            return "domain_view"
        elif self.metadata.node_type == NodeType.DOCUMENT:
            return "document_view"
        elif self.metadata.node_type == NodeType.SOCIAL_PROFILE:
            return "social_view"
        else:
            return "generic_view"

    def get_display_data(self) -> Dict[str, Any]:
        """Get display data for the node view."""
        data = {
            "id": self.node_id,
            "label": self.metadata.label,
            "title": self.metadata.title,
            "type": self.metadata.node_type.value,
            "description": self.metadata.description,
            "source": self.metadata.source,
            "sources": self.metadata.sources,
            "confidence": self.metadata.confidence,
            "agent_maker": self.metadata.agent_maker,
            "created_at": self.metadata.created_at,
            "updated_at": self.metadata.updated_at,
            "tags": self.metadata.tags,
            "notes": self.metadata.notes,
            "shareable_url": self.metadata.shareable_url,
        }

        # Add type-specific data
        if isinstance(self.metadata, PersonNodeMetadata):
            data.update({
                "full_name": self.metadata.full_name,
                "email": self.metadata.email,
                "phone": self.metadata.phone,
                "location": self.metadata.location,
                "company": self.metadata.company,
                "job_title": self.metadata.job_title,
                "bio": self.metadata.bio,
                "linkedin": self.metadata.linkedin_profile,
                "twitter": self.metadata.twitter_profile,
                "facebook": self.metadata.facebook_profile,
                "instagram": self.metadata.instagram_profile,
                "github": self.metadata.github_profile,
                "connections": self.metadata.connections_count,
                "followers": self.metadata.followers_count,
            })
        elif isinstance(self.metadata, CompanyNodeMetadata):
            data.update({
                "company_name": self.metadata.company_name,
                "industry": self.metadata.industry,
                "founded_year": self.metadata.founded_year,
                "headquarters": self.metadata.headquarters,
                "website": self.metadata.website,
                "employee_count": self.metadata.employee_count,
                "revenue": self.metadata.revenue,
                "employees_discovered": self.metadata.employees_discovered,
                "domains_discovered": self.metadata.domains_discovered,
            })
        elif isinstance(self.metadata, IPAddressNodeMetadata):
            data.update({
                "ip_address": self.metadata.ip_address,
                "country": self.metadata.country,
                "city": self.metadata.city,
                "isp": self.metadata.isp,
                "asn": self.metadata.asn,
                "open_ports": self.metadata.open_ports,
                "services": self.metadata.services,
                "technologies": self.metadata.technologies,
                "vulnerabilities": self.metadata.vulnerabilities,
                "hosting_provider": self.metadata.hosting_provider,
            })
        elif isinstance(self.metadata, DomainNodeMetadata):
            data.update({
                "domain_name": self.metadata.domain_name,
                "registrar": self.metadata.registrar,
                "registration_date": self.metadata.registration_date,
                "expiration_date": self.metadata.expiration_date,
                "dns_records": self.metadata.dns_records,
                "ssl_certificate": self.metadata.ssl_certificate,
                "website_title": self.metadata.website_title,
                "technologies": self.metadata.technologies,
            })

        return data


class GraphEdge(BaseModel):
    """Complete graph edge with all metadata."""

    edge_id: str
    metadata: EdgeMetadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Graphistry."""
        return self.metadata.to_dict()
